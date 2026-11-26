"""Synthetic power and optional fixed, invented-prompt sampling probe. No replay inputs."""

import argparse
from collections import Counter
import hashlib
import json
from math import ceil, sqrt
from pathlib import Path


def power():
    import numpy as np
    from scipy.stats import chi2, f
    import yaml

    cfg = yaml.safe_load((Path(__file__).resolve().parents[1] / "config/thresholds.yaml").read_text())
    s = cfg["screen_122_124"]["value"]
    tm = cfg["tm09"]["value"]
    share = tm["marks"]["positive_weeks_min"] / tm["window"]["weeks"]
    t_min = tm["marks"]["primary_t_min"]
    gap = s["weekly_repeat_gap_bp"]
    rng = np.random.default_rng(s["seed"])
    rho_w, rho_x = s["illustrative_family_correlations"]
    rows = {
        "122 unchanged": gap,
        "122 half gap": gap * sqrt((1 + s["tilt_gap_ratio"] ** 2) / 2),
        "123 equal correlations": gap / 2,
        "123 illustrative correlation gap": gap / 2 * sqrt((1 - rho_x) / (1 - rho_w)),
        "124 unchanged": gap,
        "124 three-quarter gap": gap * sqrt((1 + s["weekly_wake_gap_ratio"] ** 2) / 2),
    }
    registered_full_week = s["full_week_trading_days"] * len(cfg[tm["clock"]["wake_hours_key"]]["value"])
    results = []
    for n in s["weeks"]:
        needed = ceil(n * share)
        dt = np.float64
        counts = {row: dict.fromkeys(s["edge_bp"], 0) for row in rows}
        for remaining in range(0, s["worlds"], s["batch"]):
            z = rng.standard_normal((min(s["batch"], s["worlds"] - remaining), n), dtype=dt)
            avg, se = z.mean(axis=1), z.std(axis=1, ddof=1) / sqrt(n)
            sign_order = np.partition(z, n - needed, axis=1)[:, n - needed]
            required_standardized_edge = np.maximum(t_min * se - avg, -sign_order)
            for row, sd in rows.items():
                for edge in s["edge_bp"]:
                    counts[row][edge] += int(np.sum(edge / sd > required_standardized_edge))
        alpha = 1 - s["noise_interval"]
        sd_interval = [sqrt((n - 1) / chi2.ppf(q, n - 1)) for q in (1 - alpha / 2, alpha / 2)]
        results.append({
            "weeks": n, "positive_min": needed, "boss_sessions": 4 * n,
            "extra_sessions_for_123_if_one_family_reuses": 2 * n,
            "portfolio_calls_for_124_one_vs_five": 2 * n * (1 + s["queue_comparator_wakes"]),
            "portfolio_calls_for_124_registered_full_weeks": 2 * n * (1 + registered_full_week),
            "single_gap_sd_interval_multipliers": [round(v, 3) for v in sd_interval],
            "detect_any_sd_reduction_at_one_sided_90pct": {
                str(r): round(float(f.cdf(f.ppf(alpha, n - 1, n - 1) / r**2, n - 1, n - 1)), 4)
                for r in (s["tilt_gap_ratio"], s["weekly_wake_gap_ratio"])
            },
            "marks": {row: {"contrast_sd_bp": round(sd, 2),
                            "pass_counts": counts[row]}
                      for row, sd in rows.items()},
        })
    return {
        "worlds_per_case": s["worlds"], "seed": s["seed"],
        "t_min": t_min, "positive_share": share, "rows": results,
        "registered_full_week_wakes": registered_full_week,
        "123_illustrative_ratio": round(sqrt((1 + rho_x) / (1 + rho_w)), 4),
        "123_illustrative_n_eff": [round(2 / (1 + rho), 4) for rho in (rho_w, rho_x)],
    }


MODEL_IDS = ("claude_sonnet_4_5", "gemini_3_flash", "gpt5_mini",
             "claude_fable_5_2", "claude_opus_5_5")
PROMPT = ("Invented game pieces: label A has number 17, B has 29, C has 43, D has 61, "
          "E has 73, F has 89. All labels are equally eligible. Choose any one, no "
          "preference for position or number, and output only its number.")


async def probe(boss_only=False):
    import asyncio
    import logging
    import re
    import warnings
    import grpc
    from pplx.python.sdks.llm_api import (
        Client, Conversation, DeltaType, Identity, LLMAPIClient, SamplingParams,
        StreamEventType, ToolChoiceNone, ToolParams, sampling_params_for_model,
    )

    logging.disable(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    identity = Identity(client=Client.DEV, use_case="unclassified")
    llm = LLMAPIClient(grpc_max_retries=0, stream_open_timeout_seconds=12)

    async def one(model, variant):
        try:
            convo = Conversation()
            convo.set_system("Follow the user's toy game instruction. No tools.")
            convo.add_user(PROMPT)
            kwargs = {"temperature": 0.0} if variant == "t0" else (
                {"top_p": 0.5} if variant == "top_p" else {})
            async with asyncio.timeout(18):
                stream = await llm.messages.stream(
                    model=model, convo=convo, identity=identity, automatic_cache=False,
                    sampling_params=SamplingParams(max_tokens=256, **kwargs),
                    tool_params=ToolParams(tool_choice=ToolChoiceNone()),
                )
                chunks = []
                async for event in stream:
                    if (event.type == StreamEventType.CONTENT_BLOCK_DELTA and
                            event.delta.type == DeltaType.TEXT_DELTA):
                        chunks.append(event.delta.text)
                if stream.model_id != model:
                    state = "NO_REPORTED_MODEL" if stream.model_id is None else "DIFFERENT_MODEL"
                    return state, None, None
                raw = "".join(chunks)
                answer = raw.strip()
                if not re.fullmatch(r"(17|29|43|61|73|89)", answer):
                    return ("NO_TEXT" if not raw else "INVALID_TOY_ANSWER"), None, None
                return "OK", answer, hashlib.sha256(raw.encode()).hexdigest()
        except grpc.aio.AioRpcError as exc:
            return exc.code().name, None, None
        except Exception as exc:
            return type(exc).__name__, None, None

    def summarize(items):
        return {
            "outcomes": dict(Counter(x[0] for x in items)),
            "answer_counts": dict(Counter(x[1] for x in items if x[1] is not None)),
            "distinct_raw_answers": len({x[2] for x in items if x[2] is not None}),
        }

    out = {}
    for model in MODEL_IDS:
        if boss_only:
            if model in MODEL_IDS[-2:]:
                print(json.dumps({model: {"raw_t0": summarize([await one(model, "t0")])}},
                                 sort_keys=True), flush=True)
            continue
        default = [await one(model, "default")]
        helper_t0 = sampling_params_for_model(model).temperature
        result = {"helper_t0": helper_t0, "default": None, "t0": None, "top_p": None}
        if default[0][0] == "OK":
            result["top_p"] = summarize([await one(model, "top_p")])
            if helper_t0 == 0.0:
                low = [await one(model, "t0")]
                if low[0][0] == "OK":
                    for i in range(1, 10):
                        if i % 2:
                            low.append(await one(model, "t0"))
                            default.append(await one(model, "default"))
                        else:
                            default.append(await one(model, "default"))
                            low.append(await one(model, "t0"))
                result["t0"] = summarize(low)
        result["default"] = summarize(default)
        out[model] = result
        print(json.dumps({model: result}, sort_keys=True), flush=True)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--toy-sdk-probe", action="store_true")
    mode.add_argument("--toy-boss-check", action="store_true")
    args = p.parse_args()
    if args.toy_sdk_probe or args.toy_boss_check:
        import asyncio
        asyncio.run(probe(boss_only=args.toy_boss_check))
    else:
        print(json.dumps(power(), indent=2))
