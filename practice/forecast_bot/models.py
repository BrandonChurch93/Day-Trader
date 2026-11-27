"""Model calls through the sandbox SDK (the same path desk E15's scouts use): one research call with the provider's
own web search, then independent runs with a fixed JSON reply form. No retries by us, finish_reason checked, and no
credential or Metaculus token is ever put into a prompt (the prompt is built only from the question packet).

`Caller` is the seam for tests: a caller is an async function (kind, model, prompt, schema_or_None, timeout, max_tokens)
returning {"text", "finish_ok", "secs"}; tests pass a fake that never touches the network."""
import asyncio
import time

from . import method


async def sdk_call(kind, model, prompt, schema, timeout, max_tokens):
    from pplx.python.sdks.llm_api import (BuiltInWebSearch, Client, Conversation, FinishReason, Identity, LLMAPIClient,
                                          ResponseFormat, RoundRobinRetryPolicy, SamplingParams,
                                          StructuredOutputParams, ToolParams)
    client = LLMAPIClient(grpc_max_retries=0)
    convo = Conversation()
    convo.add_user(prompt)
    extra = {}
    if kind == "research":
        extra["tool_params"] = ToolParams(tools=[BuiltInWebSearch()])
    else:
        extra["structured_output_params"] = StructuredOutputParams(
            response_format=ResponseFormat(name="forecast", schema=schema))
    t0 = time.monotonic()
    resp = await asyncio.wait_for(client.messages.create(
        model=model, identity=Identity(client=Client.ASI, use_case="pplx_sdk"), convo=convo,
        sampling_params=SamplingParams(max_tokens=max_tokens), retry_policy=RoundRobinRetryPolicy(rounds=1),
        **extra), timeout)
    return {"text": resp.text or "", "finish_ok": resp.finish_reason == FinishReason.END_TURN,
            "secs": round(time.monotonic() - t0, 2)}


def forecast_question(caller, cfg, q, pkt, brief):
    """Runs the configured models once each, at the same time, on the same packet and brief.
    Returns (valid beliefs, run records). A run that errors, times out, is cut off or breaks the form is recorded
    and left out; the question is forecast only if at least min_valid_runs are valid."""
    prompt = method.run_prompt(q["type"], pkt, brief)
    form = method.schema(q["type"])

    async def one(i, model):
        rec = {"run": i, "model": model}
        try:
            got = await caller("run", model, prompt, form, cfg["run_timeout_s"], cfg["run_max_tokens"])
        except asyncio.TimeoutError:
            return rec | {"status": "timeout"}, None
        except Exception as exc:                          # recorded by type only; messages may echo request data
            return rec | {"status": "call_error", "error": type(exc).__name__}, None
        if not got.get("finish_ok"):
            return rec | {"status": "incomplete"}, None
        try:
            belief, reasons = method.check_reply(got["text"], q)
        except method.BadReply as exc:
            return rec | {"status": f"bad_reply:{exc}"}, None
        return rec | {"status": "ok", "secs": got.get("secs"), "reasons": reasons[:600]}, belief

    async def all_runs():
        return await asyncio.gather(*(one(i, m) for i, m in enumerate(cfg["runs"])))
    results = asyncio.run(all_runs())
    records = [r for r, _ in results]
    for (r, b) in results:
        if b is not None:
            r["belief"] = b if q["type"] != "multiple_choice" else {k: round(v, 4) for k, v in b.items()}
    beliefs = [b for _, b in results if b is not None]
    return beliefs, records


def research(caller, cfg, pkt):
    """One research call with web search. A failure leaves the brief empty and the runs go ahead on knowledge alone."""
    if not cfg["research_web_search"]:
        return "", {"status": "off"}

    async def go():
        return await caller("research", cfg["research_model"], method.research_prompt(pkt), None,
                            cfg["research_timeout_s"], cfg["research_max_tokens"])
    try:
        got = asyncio.run(go())
    except asyncio.TimeoutError:
        return "", {"status": "timeout"}
    except Exception as exc:
        return "", {"status": "call_error", "error": type(exc).__name__}
    if not got.get("finish_ok") or not got.get("text", "").strip():
        return "", {"status": "incomplete"}
    return got["text"][:6000], {"status": "ok", "secs": got.get("secs")}


def sources(brief, limit=8):
    """URLs listed after SOURCES: in the brief (https only), for the comment."""
    out = []
    tail = brief.split("SOURCES:", 1)[1] if "SOURCES:" in brief else ""
    for line in tail.splitlines():
        u = line.strip().lstrip("-*0123456789. ").strip()
        if u.startswith("https://") and " " not in u and u not in out:
            out.append(u[:300])
        if len(out) >= limit:
            break
    return out
