"""Model calls through the sandbox SDK (the same path desk E15's scouts use): one research call with the provider's
own web search, then independent runs with a fixed JSON reply form. No retries by us, finish_reason checked, and no
credential or Metaculus token is ever put into a prompt (the prompt is built only from the question packet).

`Caller` is the seam for tests: a caller is an async function (kind, model, prompt, schema_or_None, timeout, max_tokens)
returning {"text", "finish_ok", "secs"}; tests pass a fake that never touches the network."""
import asyncio
import time
import urllib.parse

from . import method
from .metaculus import redact_held


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


async def run_one(caller, cfg, q, prompt, form, i, model):
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
        return rec | {"status": f"bad_reply:{redact_held(exc)}"}, None
    rec = rec | {"status": "ok", "secs": got.get("secs"), "reasons": reasons[:600]}
    rec["belief"] = belief if q["type"] != "multiple_choice" else {k: round(v, 4) for k, v in belief.items()}
    return rec, belief


async def research_step(caller, cfg, pkt):
    """One research call with web search. A failure leaves the brief empty and the runs go ahead on knowledge alone."""
    if not cfg["research_web_search"]:
        return "", {"status": "off"}
    try:
        got = await caller("research", cfg["research_model"], method.research_prompt(pkt), None,
                           cfg["research_timeout_s"], cfg["research_max_tokens"])
    except asyncio.TimeoutError:
        return "", {"status": "timeout"}
    except Exception as exc:
        return "", {"status": "call_error", "error": type(exc).__name__}
    if not got.get("finish_ok") or not got.get("text", "").strip():
        return "", {"status": "incomplete"}
    return got["text"][:6000], {"status": "ok", "secs": got.get("secs")}


class OverBudget(Exception):
    """research plus runs for one post took longer than question_budget_s."""


IN_FLIGHT = 6        # model calls at once for one post, whatever its size


def planned_calls(cfg, n_questions):
    """Model calls one post will make: research (if on) plus every run for every open question."""
    return (1 if cfg["research_web_search"] else 0) + len(cfg["runs"]) * n_questions


def post_budget(cfg, n_questions):
    """The hard wall-clock limit for one post: question_budget_s for the first wave of runs, plus run_timeout_s for
    each further wave that the IN_FLIGHT cap makes a large group need."""
    waves = -(-len(cfg["runs"]) * n_questions // IN_FLIGHT)
    return cfg["question_budget_s"] + (waves - 1) * cfg["run_timeout_s"]


def forecast_post(caller, cfg, research_packet, tasks):
    """tasks: [(q, packet)] for the open, unanswered questions of one post.
    One research call, then every run for every question, at most IN_FLIGHT calls at once, all under one hard
    wall-clock limit (post_budget). Returns (brief, research record, [(q, valid beliefs, run records)]).
    Raises OverBudget."""
    async def go():
        gate = asyncio.Semaphore(IN_FLIGHT)

        async def gated(*a):
            async with gate:
                return await caller(*a)
        brief, rstat = await research_step(gated, cfg, research_packet)
        jobs = []
        for q, pkt in tasks:
            prompt, form = method.run_prompt(q["type"], pkt, brief), method.schema(q["type"])
            jobs.append(asyncio.gather(*(run_one(gated, cfg, q, prompt, form, i, m) for i, m in enumerate(cfg["runs"]))))
        results = await asyncio.gather(*jobs)
        out = []
        for (q, _), res in zip(tasks, results):
            out.append((q, [b for _, b in res if b is not None], [r for r, _ in res]))
        return brief, rstat, out

    async def bounded():
        try:
            return await asyncio.wait_for(go(), post_budget(cfg, len(tasks)))
        except asyncio.TimeoutError:
            raise OverBudget() from None
    return asyncio.run(bounded())


def research(caller, cfg, pkt):
    return asyncio.run(research_step(caller, cfg, pkt))


BARRED_HOSTS = ("metaculus.com", "manifold.markets", "polymarket.com", "kalshi.com", "predictit.org",
                "goodjudgment.com", "gjopen.com")


def sources(brief, limit=8):
    """URLs listed after SOURCES: in the brief (https only), for the comment."""
    out = []
    tail = brief.split("SOURCES:", 1)[1] if "SOURCES:" in brief else ""
    for line in tail.splitlines():
        u = line.strip().lstrip("-*0123456789. ").strip()
        host = (urllib.parse.urlsplit(u).hostname or "") if u.startswith("https://") else ""
        if any(host == h or host.endswith("." + h) for h in BARRED_HOSTS):
            continue
        if u.startswith("https://") and " " not in u and u not in out:
            out.append(u[:300])
        if len(out) >= limit:
            break
    return out
