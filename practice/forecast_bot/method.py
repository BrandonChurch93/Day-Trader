"""The forecasting method, fixed before the first live question: prompts, reply forms, reply checks and the
plain aggregate. Nothing here reads the Community Prediction; the packet never holds it (see questions.py)."""
import hashlib
import json
import math
import statistics

from . import cdf

PERCENTILES = (("p05", 0.05), ("p10", 0.10), ("p25", 0.25), ("p50", 0.50), ("p75", 0.75), ("p90", 0.90), ("p95", 0.95))

RESEARCH_PROMPT = """You are the research step of an autonomous forecasting bot. Search the web for current, dated facts
that bear on the question below: the latest values of anything it measures, scheduled events before its close, base
rates for similar events, and what official sources say. Do not give a forecast. Write a brief of at most 400 words with
dated facts, then a line SOURCES: followed by one URL per line (at most 8). If the search finds nothing useful, say so.

QUESTION (JSON):
"""

RUN_PROMPT = """You are one of several independent forecasters in an autonomous bot. Forecast the question below using
the research brief and your own knowledge. Read the resolution criteria and fine print closely; the question resolves
only as they say. Think about the base rate first, then the specific evidence, then how much time is left before the
resolve date. Avoid overconfidence: extreme forecasts that turn out wrong are scored very badly.

{form}

QUESTION (JSON):
{question}

RESEARCH BRIEF (from a web search by another model; may be incomplete or wrong):
{brief}
"""

FORMS = {
    "binary": "Give `probability`: the chance (0 to 1) that the question resolves Yes, and `reasons` in at most 120 words.",
    "multiple_choice": "Give `probabilities`: one entry per option, using each option's exact text once, probabilities "
                       "summing to 1; and `reasons` in at most 120 words.",
    "numeric": "Give your 5th, 10th, 25th, 50th, 75th, 90th and 95th percentiles of the outcome in the question's units "
               "(`p05` to `p95`, rising), and `reasons` in at most 120 words. The question's range is in the packet; "
               "outcomes outside it are possible only where that bound is open.",
    "discrete": "Give your 5th, 10th, 25th, 50th, 75th, 90th and 95th percentiles of the outcome (`p05` to `p95`, rising), "
                "and `reasons` in at most 120 words. The question's range is in the packet; outcomes outside it are "
                "possible only where that bound is open.",
    "date": "Give your 5th, 10th, 25th, 50th, 75th, 90th and 95th percentiles of the date as YYYY-MM-DD (`p05` to `p95`, "
            "rising), and `reasons` in at most 120 words. The question's range is in the packet; dates outside it are "
            "possible only where that bound is open.",
}


def schema(qtype):
    reasons = {"type": "string"}
    if qtype == "binary":
        props = {"probability": {"type": "number"}, "reasons": reasons}
    elif qtype == "multiple_choice":
        item = {"type": "object", "additionalProperties": False, "required": ["option", "probability"],
                "properties": {"option": {"type": "string"}, "probability": {"type": "number"}}}
        props = {"probabilities": {"type": "array", "items": item}, "reasons": reasons}
    else:
        kind = {"type": "string"} if qtype == "date" else {"type": "number"}
        props = {k: kind for k, _ in PERCENTILES} | {"reasons": reasons}
    return {"type": "object", "additionalProperties": False, "required": list(props), "properties": props}


def run_prompt(qtype, packet, brief):
    return RUN_PROMPT.format(form=FORMS[qtype], question=json.dumps(packet, sort_keys=True, ensure_ascii=False),
                             brief=brief or "(no research brief)")


def research_prompt(packet):
    return RESEARCH_PROMPT + json.dumps(packet, sort_keys=True, ensure_ascii=False)


def prompt_hash():
    text = json.dumps({"research": RESEARCH_PROMPT, "run": RUN_PROMPT, "forms": FORMS,
                       "schemas": {t: schema(t) for t in FORMS}}, sort_keys=True)
    return hashlib.sha256(text.encode()).hexdigest()


class BadReply(ValueError):
    pass


def check_reply(text, q):
    """A run's reply in the fixed form, or BadReply. Returns the parsed belief:
    binary: float; multiple_choice: {option: p}; numeric/discrete/date: [(p, value), ...]."""
    try:
        r = json.loads(text)
    except (TypeError, ValueError):
        raise BadReply("not_json") from None
    qtype = q["type"]
    if not isinstance(r, dict) or set(r) != set(schema(qtype)["required"]):
        raise BadReply("fields")
    if not isinstance(r["reasons"], str) or not r["reasons"].strip():
        raise BadReply("reasons")
    num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    if qtype == "binary":
        p = r["probability"]
        if not num(p) or not 0 <= p <= 1:
            raise BadReply("probability")
        return float(p), r["reasons"]
    if qtype == "multiple_choice":
        got = {}
        for e in r["probabilities"]:
            if not isinstance(e, dict) or set(e) != {"option", "probability"} or e["option"] in got:
                raise BadReply("options")
            if not num(e["probability"]) or e["probability"] < 0:
                raise BadReply("option_probability")
            got[e["option"]] = float(e["probability"])
        if set(got) != set(q["options"]):
            raise BadReply("options")
        total = math.fsum(got.values())
        if not 0.9 <= total <= 1.1:
            raise BadReply("sum")
        return {k: v / total for k, v in got.items()}, r["reasons"]
    pts = []
    for k, p in PERCENTILES:
        v = r[k]
        if qtype == "date":
            if not isinstance(v, str):
                raise BadReply("percentile")
        elif not num(v):
            raise BadReply("percentile")
        try:
            x = cdf.nominal_value(v, qtype)
        except (ValueError, TypeError):
            raise BadReply("percentile") from None
        if pts and x < pts[-1][2]:
            raise BadReply("percentiles_not_rising")
        pts.append((p, v, x))
    return [(p, v) for p, v, _ in pts], r["reasons"]


def aggregate(q, beliefs, cfg):
    """The plain aggregate of the valid runs' beliefs.
    binary: median, clipped to cfg binary_clip; multiple choice: mean per option with a floor, summing to 1;
    numeric, discrete, date: the average of the runs' distributions, made valid by cdf.standardize."""
    qtype = q["type"]
    if qtype == "binary":
        lo, hi = cfg["binary_clip"]
        return round(min(hi, max(lo, statistics.median(beliefs))), 4)
    if qtype == "multiple_choice":
        opts = q["options"]
        mean = {o: math.fsum(b[o] for b in beliefs) / len(beliefs) for o in opts}
        return floor_and_normalize(mean, opts, cfg["mc_floor"])
    return cdf.build(beliefs, q, cfg["cdf_uniform_mix"], cfg["cdf_open_bound_mass"])


def floor_and_normalize(probs, opts, floor):
    if not 0 < floor * len(opts) < 1:
        raise ValueError("bad floor")
    p = {o: max(0.0, probs[o]) for o in opts}
    fixed = set()
    for _ in range(len(opts) + 1):                      # raise options under the floor to it, scale the rest
        free = [o for o in opts if o not in fixed]
        left = 1.0 - floor * len(fixed)
        total = math.fsum(p[o] for o in free) or 1.0
        for o in free:
            p[o] = p[o] * left / total
        low = [o for o in free if p[o] < floor]
        if not low:
            break
        for o in low:
            p[o] = floor
            fixed.add(o)
    out = {o: round(p[o], 6) for o in opts}
    top = max(opts, key=lambda o: out[o])
    out[top] = round(1.0 - math.fsum(out[o] for o in opts if o != top), 6)
    return out
