"""Turn one post from GET /api/posts/ into forecast tasks, and the tasks into the packet a model sees.

Field names follow the public API description (Metaculus/metaculus docs/openapi.yml, schemas Post, Question,
GroupOfQuestions, QuestionScaling). The gateway hides fields by setting them to null, so every read tolerates null.

The packet is built from a fixed list of fields. Community Prediction (`aggregations`), our own past forecasts
(`my_forecasts`) and every other field are never copied into it: the rules bar copying the crowd, and this code
never reads it at all.
"""
from datetime import datetime, timezone

SUPPORTED = ("binary", "multiple_choice", "numeric", "discrete", "date")
TEXT_FIELDS = ("title", "description", "resolution_criteria", "fine_print")
PACKET_FIELDS = ("title", "label", "type", "description", "resolution_criteria", "fine_print", "options", "unit",
                 "open_lower_bound", "open_upper_bound", "scheduled_close_time", "scheduled_resolve_time")


class Skip(Exception):
    """A post or question this bot does not forecast, with the reason recorded in the pass log."""


def parse_time(s):
    if not s:
        return None
    t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def is_open(q, now):
    if q.get("status") != "open":
        return False
    opened, closes = parse_time(q.get("open_time")), parse_time(q.get("actual_close_time") or q.get("scheduled_close_time"))
    return (opened is None or opened <= now) and (closes is None or now < closes)


def tasks(post, now):
    """[(question dict, group context or None)] for the open questions of one post, oldest kind first.

    - single question: one task
    - group of questions: one task per open subquestion, all submitted together in one request
    - conditional and notebook posts: Skip (not a FutureEval question type; see the plan's UNKNOWN list)"""
    if post.get("conditional") is not None:
        raise Skip("conditional_not_supported")
    group = post.get("group_of_questions")
    if group:
        ctx = {k: group.get(k) for k in ("description", "resolution_criteria", "fine_print", "group_variable")}
        out = [(q, ctx) for q in group.get("questions") or [] if is_open(q, now)]
    elif post.get("question"):
        q = post["question"]
        out = [(q, None)] if is_open(q, now) else []
    else:
        raise Skip("no_question")
    for q, _ in out:
        if q.get("type") not in SUPPORTED:
            raise Skip(f"type_not_supported:{q.get('type')}")
        if type(q.get("id")) is not int:
            raise Skip("question_id_missing")
        if q.get("type") == "multiple_choice" and not (isinstance(q.get("options"), list) and len(q["options"]) >= 2):
            raise Skip("options_missing")
        if q.get("type") in ("numeric", "discrete", "date"):
            s = q.get("scaling") or {}
            if s.get("range_min") is None or s.get("range_max") is None:
                raise Skip("scaling_missing")
        if not q.get("title") and not post.get("title"):
            raise Skip("text_missing")
    return out


def nominal_range(q):
    s = q.get("scaling") or {}
    lo, hi = s.get("range_min"), s.get("range_max")
    if q.get("type") == "date":
        iso = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")
        return {"range_min": iso(lo), "range_max": iso(hi), "scale": "dates (UTC)"}
    return {"range_min": lo, "range_max": hi, "scale": "logarithmic" if s.get("zero_point") is not None else "linear"}


def packet(post, q, ctx, now):
    """What a model is shown for one question: fixed fields only, plus today's date."""
    p = {"today_utc": now.strftime("%Y-%m-%d"), "post_title": post.get("title")}
    for k in PACKET_FIELDS:
        if q.get(k) is not None:
            p[k] = q[k]
    if ctx:
        p["group"] = {k: v for k, v in ctx.items() if v is not None}
    if q.get("type") in ("numeric", "discrete", "date"):
        p["range"] = nominal_range(q)
    return p
