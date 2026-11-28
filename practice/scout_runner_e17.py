"""Serve E17 scout requests inside one live command, then drain and exit."""
import argparse
import asyncio
import os
import sys
import time

if __package__:
    from . import scout_spool_e17 as spool
    from . import desk_e17 as desk
else:
    import scout_spool_e17 as spool
    import desk_e17 as desk


def rpc_status(exc):
    todo, seen = [(exc, 0)], set()
    while todo:
        current, depth = todo.pop(0)
        if current is None or depth >= 8 or id(current) in seen:
            continue
        seen.add(id(current))
        try:
            name = current.code().name
            if type(name) is str and name in spool.SERVICE_CODES:
                return name
        except Exception:
            pass
        todo.extend(((current.__cause__, depth + 1), (current.__context__, depth + 1)))
    return "UNKNOWN"


async def sdk_call(req):
    # The SDK resolves its own platform session inside this live command.
    from pplx.python.sdks.llm_api import (Client, Conversation, FinishReason, Identity, LLMAPIClient,
                                          ResponseFormat, RoundRobinRetryPolicy, SamplingParams,
                                          StructuredOutputParams)
    client = LLMAPIClient(grpc_max_retries=0)
    convo = Conversation()
    convo.set_system(req["system_text"])
    convo.add_user(req["user_text"])
    resp = await client.messages.create(
        model=req["model"], identity=Identity(client=Client.ASI, use_case="pplx_sdk"), convo=convo,
        sampling_params=SamplingParams(max_tokens=req["max_tokens"]),
        structured_output_params=StructuredOutputParams(
            response_format=ResponseFormat(name="scout_reply", schema=req["reply_schema"])),
        retry_policy=RoundRobinRetryPolicy(rounds=1))
    usage = getattr(resp, "usage", None)
    return {"finish": str(getattr(resp.finish_reason, "value", resp.finish_reason)).lower(),
            "end_turn": resp.finish_reason == FinishReason.END_TURN, "text": resp.text or "",
            "usage": {k: getattr(usage, k) for k in spool.USAGE_KEYS if type(getattr(usage, k, None)) is int},
            "model_reported": str(getattr(resp, "model", "") or "")}


async def finish(folder, req, build, clock, caller):
    rid = req["request_id"]
    started = time.monotonic()
    deadline = spool.utc(req["deadline"])

    async def call_before_deadline():
        # The scheduled task can start later than the wait was set up.
        return await caller(req) if clock() < deadline else {"status": "reply_late"}

    try:
        budget = min(req["timeout_s"], (deadline - clock()).total_seconds())
        result = (await asyncio.wait_for(call_before_deadline(), budget) if budget > 0
                  else {"status": "reply_late"})
    except TimeoutError:
        result = {"status": "call_timeout"}
    except Exception as exc:
        result = {"status": "call_error", "error": type(exc).__name__, "service_status": rpc_status(exc)}
    reply = spool.reply_envelope(req, build, result) | {"secs": round(time.monotonic() - started, 2)}
    if spool.reply_result(reply, req) is None:
        reply["result"] = {"status": "call_error", "error": "InvalidRunnerResult", "service_status": "UNKNOWN"}
    folder.write(spool.filename("reply", rid), reply, swept_ok=True)


async def serve(until, *, build, path=None, clock=spool.now_utc, sleep=asyncio.sleep, caller=None):
    caller = caller or sdk_call
    pending, ignored = set(), set()
    with spool.private(path, create=True) as folder:
        heartbeat_at = None

        def heartbeat(phase):
            folder.write("heartbeat.json", {"made_utc": clock().isoformat(), "until": until.isoformat(),
                                           "phase": phase, "ignored_requests": len(ignored), "build": build}, swept_ok=True)

        while clock() < until:
            if heartbeat_at is None or (clock() - heartbeat_at).total_seconds() >= 2:
                heartbeat("serving")
                heartbeat_at = clock()
            for name in sorted(folder.names()):
                if not name.startswith("request-") or not name.endswith(".json") or clock() >= until:
                    continue
                rid = name[len("request-"):-len(".json")]
                req, exists = spool.peek(folder, name)
                if not exists:
                    continue
                if not spool.valid_request(req, rid, clock()) or req["build"] != build:
                    ignored.add(name)
                    continue
                if not folder.take(req, build, clock, until):
                    continue
                pending.add(asyncio.create_task(finish(folder, req, build, clock, caller)))
            complete = {task for task in pending if task.done()}
            pending.difference_update(complete)
            for task in complete:
                task.result()
            left = (until - clock()).total_seconds()
            if left > 0:
                await sleep(min(spool.POLL_S, left))
        heartbeat("draining")
        if pending:
            await asyncio.gather(*pending)
        heartbeat("stopped")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--until", required=True, help="UTC timestamp after which to claim no new requests")
    args = parser.parse_args()
    try:
        until = spool.utc(args.until)
    except (ValueError, TypeError):
        parser.error("--until must be an ISO UTC timestamp")
    prior = os.umask(0o077)
    try:
        build = desk.checked_build()
        asyncio.run(serve(until, build=build))
        return 0
    except desk.bx.Refuse:
        print("REFUSED scout runner build", file=sys.stderr)
        return 2
    except (spool.Refuse, OSError, ValueError):
        print("REFUSED scout runner storage", file=sys.stderr)
        return 2
    finally:
        os.umask(prior)


if __name__ == "__main__":
    raise SystemExit(main())
