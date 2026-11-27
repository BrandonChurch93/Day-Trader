"""B01, our forecasting bot for the Metaculus FutureEval bot rounds. Plan: practice/PLAN_B01_forecast_bot_DRAFT.md.

Commands (python3 -m forecast_bot.bot <command>, run from practice/):
  selfcheck   proves without the network that the bot refuses to run without its ledger key; sends nothing
  dry-run     forecasts built-in made-up questions with a fake model (or --live-models for real model calls) and
              prints what it would submit; never builds a Metaculus client, so it cannot send anything
  pass        one armed pass over the configured tournaments (needs network_allowed and B01_START on the ledger row)
  loop        armed passes every poll_minutes, for as long as it runs; nobody needs to touch it
  testing     one armed pass on the unscored bot testing area (needs B01_TEST on the ledger row)
  status      counts only from the private log (passes, answered, failed, deferred, open claims, calls today);
              never a forecast or question text; no network

No human in the loop: once armed, the bot reads, forecasts and submits by itself. The log is for the record only.
"""
import argparse
import hashlib
import json
import os
import socket
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

from . import cdf, method, metaculus, models, questions, settings, state

UTC = timezone.utc


# ------------------------------------------------------------------ the submission
def forecast_item(q, value):
    if q["type"] == "binary":
        return {"question": q["id"], "probability_yes": value}
    if q["type"] == "multiple_choice":
        return {"question": q["id"], "probability_yes_per_category": value}
    return {"question": q["id"], "continuous_cdf": value}


def show(q, value):
    """The forecast in words, for the comment (the rules ask that each comment displays its forecast)."""
    name = q.get("label") or q.get("title") or f"question {q['id']}"
    if q["type"] == "binary":
        return f"{name}: {value * 100:.1f}% Yes"
    if q["type"] == "multiple_choice":
        return f"{name}: " + "; ".join(f"{o} {value[o] * 100:.1f}%" for o in q["options"])
    fmt = ((lambda x: datetime.fromtimestamp(x, UTC).strftime("%Y-%m-%d")) if q["type"] == "date"
           else (lambda x: f"{x:.4g}{(' ' + q['unit']) if q.get('unit') else ''}"))
    lo, mid, hi = (cdf.quantile(value, q, p) for p in (0.1, 0.5, 0.9))
    return (f"{name}: median {fmt(mid)}, 10th to 90th percentile {fmt(lo)} to {fmt(hi)} "
            f"(a {len(value)}-point CDF was submitted)")


def comment(cfg, items, run_records, brief_sources, research_status):
    """items: [(q, value)]. The private comment that goes with the forecast."""
    head = ["Forecast by B01, an autonomous bot whose full code is in a public repository. No human saw or changed "
            "this forecast.", ""]
    head += ["Forecast:"] + [f"- {show(q, v)}" for q, v in items] + [""]
    n_runs = len(cfg["runs"])
    head += [f"Method: one research step with web search ({cfg['research_model']}, {research_status}), then "
             f"{n_runs} independent runs ({', '.join(cfg['runs'])}). Aggregate: median for yes/no, mean per option "
             f"for multiple choice, the average of the runs' distributions for numbers and dates; probabilities kept "
             f"away from 0 and 1. The Community Prediction is not read.", ""]
    body = ["Runs:"]
    for qid, recs in run_records:
        for r in recs:
            reason = (r.get("reasons") or "").replace("\n", " ")
            body.append(f"- question {qid}, run {r['run'] + 1} ({r['model']}): {r['status']}"
                        + (f". {reason}" if reason else ""))
    tail = ([""] + ["Sources found by the research step:"] + [f"- {u}" for u in brief_sources]) if brief_sources else []
    text = "\n".join(head + body + tail)
    limit = cfg["comment_max_chars"]
    if len(text) > limit:
        keep = limit - len("\n".join(head + tail)) - 40
        text = "\n".join(head) + "\n" + "\n".join(body)[:max(0, keep)] + "\n(run notes cut for length)\n" + "\n".join(tail)
    return text[:limit]


def payload(post, items, text):
    return {"forecasts": [forecast_item(q, v) for q, v in items],
            "comments": [{"on_post": post["id"], "text": text, "is_private": True, "included_forecast": True}]}


def validate(post, items, body, cfg, leaks=None):
    """Refuse a payload that breaks the public API's rules or holds a secret. `leaks` is the client's own check
    (Client.holds_token), so the token value itself never has to leave the client module."""
    settings.need(type(post.get("id")) is int, "post id")
    for (q, v), f in zip(items, body["forecasts"]):
        settings.need(f["question"] == q["id"], "question id")
        if q["type"] == "binary":
            lo, hi = cfg["binary_clip"]
            settings.need(isinstance(v, float) and lo <= v <= hi, "binary probability")
        elif q["type"] == "multiple_choice":
            settings.need(list(v) == list(q["options"]) and abs(sum(v.values()) - 1) < 1e-9
                          and min(v.values()) > 0, "multiple choice probabilities")
        else:
            cdf.check(v, q)
    settings.need(len(body["comments"]) == 1 and body["comments"][0]["is_private"] is True, "one private comment")
    text = json.dumps(body)
    settings.need(metaculus.redact(text) == text and not (leaks and leaks(text)), "payload holds a token")
    return True


def msg(x):
    """Exception or status text, safe to write anywhere: every held token removed."""
    return metaculus.redact_held(str(x))


def close_time(q):
    return questions.parse_time(q.get("actual_close_time") or q.get("scheduled_close_time"))


FAR = datetime(9999, 1, 1, tzinfo=UTC)


# ------------------------------------------------------------------ one pass
def run_pass(client, caller, log, cfg, targets, now=None, dry=False, out=None, clock=None):
    """One pass. `now` fixes the clock (tests); otherwise the clock is read fresh before each post."""
    clock = clock or ((lambda: now) if now else (lambda: datetime.now(UTC)))
    start = clock()
    pass_id = start.strftime("%Y%m%dT%H%M%S%fZ")
    ix = state.index(log.rows())
    log.add(kind="pass_start", pass_id=pass_id, targets=targets, dry=dry)
    counts = {}
    leaks = getattr(client, "holds_token", None)

    def outcome(post_id, status, **extra):
        counts[status] = counts.get(status, 0) + 1
        return log.add(kind="outcome", pass_id=pass_id, post_id=post_id, status=status, **extra)

    posts, seen = [], set()
    for slug in targets:
        try:
            rows = client.open_posts(slug)
        except metaculus.ApiError as exc:
            log.add(kind="list_failed", pass_id=pass_id, target=slug, status=msg(exc.status))
            counts["list_failed"] = counts.get("list_failed", 0) + 1
            continue
        for p in rows:
            pid = p.get("id") if isinstance(p, dict) else None
            if type(pid) is not int:
                outcome(None, "bad_post_id", target=slug)
                continue
            if pid in seen:
                outcome(pid, "duplicate_in_pass", target=slug)
                continue
            seen.add(pid)
            posts.append((slug, p))

    plan = []
    for slug, p in posts:
        try:
            ts = questions.tasks(p, start)
        except questions.Skip as exc:
            outcome(p["id"], f"skipped:{msg(exc)}", target=slug)
            continue
        except questions.NotReady as exc:
            outcome(p["id"], f"not_ready:{msg(exc)}", target=slug)
            continue
        if not ts:
            outcome(p["id"], "no_open_question", target=slug)
            continue
        plan.append((min(close_time(q) or FAR for q, _ in ts), slug, p, ts))
    plan.sort(key=lambda x: (x[0], x[2]["id"]))            # soonest close first

    qids = sorted({q["id"] for *_, ts in plan for q, _ in ts} | {i for c in ix["open_claims"].values()
                                                               for i in c["question_ids"]})
    try:
        remote = client.my_forecasts(qids)
    except metaculus.ApiError as exc:
        for _, slug, p, _ in plan:                       # never submit without the guard
            outcome(p["id"], "deferred_guard_unavailable", target=slug, http=msg(exc.status))
        log.add(kind="pass_end", pass_id=pass_id, counts=counts)
        return counts

    for cid, c in list(ix["open_claims"].items()):       # settle claims left open by a crash or an unknown outcome
        ids = c["question_ids"]
        if all(remote.get(i, 0) > 0 for i in ids):
            log.add(kind="settle", pass_id=pass_id, post_id=c["post_id"], claim_id=cid, question_ids=ids,
                    status="submitted_confirmed_later")
            ix["submitted"].update(ids)
            ix["open_claims"].pop(cid)
        elif all(remote.get(i) == 0 for i in ids):       # every id reported, none with a forecast: nothing was saved
            log.add(kind="settle", pass_id=pass_id, post_id=c["post_id"], claim_id=cid, question_ids=ids,
                    status="claim_not_on_site")
            ix["open_claims"].pop(cid)
        else:                                            # an id omitted, or mixed: cannot tell; the claim stays open
            day = start.strftime("%Y-%m-%d")
            made = questions.parse_time(c.get("made_utc")) or start
            if start - made <= timedelta(hours=24) or day not in ix["cannot_check_days"].get(cid, set()):
                log.add(kind="settle", pass_id=pass_id, post_id=c["post_id"], question_ids=ids, open_claim_id=cid,
                        day=day, age_hours=round((start - made).total_seconds() / 3600, 1),
                        status="claim_cannot_check")
    held = {i for c in ix["open_claims"].values() for i in c["question_ids"]}
    pass_calls = 0

    for _, slug, p, ts in plan:
        pid = p["id"]
        now_p = clock()
        pending = [(q, ctx) for q, ctx in ts if q["id"] not in ix["submitted"] and remote.get(q["id"], 0) == 0]
        if not pending:
            outcome(pid, "already_answered", target=slug)
            continue
        if any(q["id"] in held for q, _ in pending):    # an unsettled claim: never send twice
            outcome(pid, "claim_still_open", target=slug)
            continue
        unseen = [q["id"] for q, _ in pending if q["id"] not in remote]
        if unseen:                                      # the site did not report these: cannot rule out a forecast
            outcome(pid, "guard_cannot_check", target=slug, question_ids=unseen)
            continue
        if ix["attempts"].get(pid, 0) >= cfg["max_attempts_per_post"]:
            outcome(pid, "gave_up_after_attempts", target=slug)
            continue
        closes = min(close_time(q) or FAR for q, _ in pending)
        if closes - now_p < timedelta(minutes=cfg["min_minutes_left"]):
            outcome(pid, "no_time", target=slug)
            continue
        planned = models.planned_calls(cfg, len(pending))
        day = now_p.strftime("%Y-%m-%d")
        if (pass_calls + planned > cfg["max_model_calls_per_pass"]
                or ix["calls_by_day"].get(day, 0) + planned > cfg["max_model_calls_per_day"]):
            outcome(pid, "deferred_call_cap", target=slug, planned_calls=planned, pass_calls=pass_calls,
                    day_calls=ix["calls_by_day"].get(day, 0))
            continue
        log.add(kind="calls", pass_id=pass_id, post_id=pid, day=day, n=planned)   # counted before the calls are made
        pass_calls += planned
        ix["calls_by_day"][day] = ix["calls_by_day"].get(day, 0) + planned
        log.add(kind="attempt", pass_id=pass_id, post_id=pid, target=slug)
        ix["attempts"][pid] = ix["attempts"].get(pid, 0) + 1
        q0, ctx0 = pending[0]
        jobs = [(q, questions.packet(p, q, ctx, now_p)) for q, ctx in pending]
        try:
            brief, rstat, results = models.forecast_post(caller, cfg, questions.packet(p, q0, ctx0, now_p), jobs)
        except models.OverBudget:
            outcome(pid, "failed_budget", target=slug, budget_s=models.post_budget(cfg, len(pending)))
            continue
        items, records, failed, no_dist = [], [], [], []
        for q, beliefs, recs in results:
            records.append((q["id"], recs))
            if len(beliefs) < cfg["min_valid_runs"]:
                failed.append(q["id"])
                continue
            try:
                items.append((q, method.aggregate(q, beliefs, cfg)))
            except cdf.CdfError as exc:
                (no_dist if str(exc) == "no_valid_distribution" else failed).append(q["id"])
            except ValueError:
                failed.append(q["id"])
        run_log = [{"question_id": i, "runs": [{k: v for k, v in r.items() if k != "reasons"} for r in recs]}
                   for i, recs in records]
        if failed or no_dist:
            outcome(pid, "no_valid_distribution" if no_dist and not failed else "failed_runs", target=slug,
                    question_ids=failed + no_dist, research=rstat["status"], runs=run_log)
            continue
        text = comment(cfg, items, records, models.sources(brief), rstat["status"])
        body = payload(p, items, text)
        try:
            validate(p, items, body, cfg, leaks)
        except (settings.Refuse, cdf.CdfError) as exc:
            outcome(pid, "failed_build", target=slug, reason=msg(exc), runs=run_log)
            continue
        qids_p = [q["id"] for q, _ in items]
        hashes = {q["id"]: state.text_hash(q, ctx) for q, ctx in pending}
        if dry:
            outcome(pid, "dry_run", target=slug, question_ids=qids_p, text_sha256=hashes, payload=body,
                    research=rstat["status"], runs=run_log)
            if out is not None:
                out.append(body)
            continue
        cid = f"{pass_id}-{pid}"
        log.add(kind="claim", pass_id=pass_id, claim_id=cid, post_id=pid, question_ids=qids_p, text_sha256=hashes,
                made_utc=now_p.isoformat(),
                forecasts=body["forecasts"], comment_sha256=hashlib.sha256(text.encode()).hexdigest())
        try:
            status = client.submit(body)
        except metaculus.ApiError as exc:
            if exc.status in (400, 403, 405):           # rejected; the endpoint saves nothing on rejection
                outcome(pid, f"failed_http_{exc.status}", target=slug, claim_id=cid, question_ids=qids_p)
            else:                                       # unknown outcome: the claim stays open for the next pass
                outcome(pid, "unknown_outcome", target=slug, http=msg(exc.status), question_ids=qids_p)
                held.update(qids_p)
            continue
        outcome(pid, "submitted", target=slug, claim_id=cid, question_ids=qids_p, http=status, runs=run_log,
                research=rstat["status"])
        ix["submitted"].update(qids_p)
    log.add(kind="pass_end", pass_id=pass_id, counts=counts)
    return counts


# ------------------------------------------------------------------ arming, the log header and the loop
def arm(cfg, mode):
    """Every check that must pass before the first request to Metaculus. Raises settings.Refuse otherwise."""
    settings.required(cfg)
    settings.need(cfg["network_allowed"] is True, "network_allowed is false in config forecast_bot")
    commit = settings.checked_build()
    key = cfg["start_key"] if mode == "tournament" else cfg["test_key"]
    settings.require_key(cfg["ledger_row"], key, commit)
    return commit


def header(log, cfg, commit, mode):
    rows = log.rows()
    frozen = settings.frozen(cfg)
    heads = [r for r in rows if r.get("kind") == "header"]
    if not heads:
        log.add(kind="header", commit=commit, mode=mode, frozen=frozen, made_utc=datetime.now(UTC).isoformat())
        return
    settings.need(heads[-1]["commit"] == commit and heads[-1]["frozen"] == frozen,
                  "the build or a setting changed since the log began: that is a new attempt with a new log folder")


def log_for(cfg, mode):
    return state.Log(cfg["private_dir"] if mode == "tournament" else cfg["private_dir"] + "_testing")


def armed_pass(cfg, mode, caller=None):
    commit = arm(cfg, mode)
    client = metaculus.Client(cfg, armed=True)
    log = log_for(cfg, mode)
    with log.locked():
        header(log, cfg, commit, mode)
        targets = cfg["targets"] if mode == "tournament" else [cfg["testing_target"]]
        return run_pass(client, caller or models.sdk_call, log, cfg, targets)


MAX_BAD_PASSES = 4


def loop(cfg, caller=None, sleep=time.sleep, clock=lambda: datetime.now(UTC), one_pass=None, passes=None,
         err=sys.stderr):
    """Passes every poll_minutes until stopped, needing nobody.
    Stops (returns 2, with a `loop` row if one can be written and a line on stderr either way) when:
    - a changed build or setting is found (settings.Refuse): that would be a new attempt;
    - the private log is corrupt (a line that is not JSON): the duplicate guard cannot be trusted;
    - MAX_BAD_PASSES passes in a row end in an unhandled exception or an OSError on the log.
    Goes on to the next pass after: no token or a refused client (metaculus.Refuse), an HTTP failure (ApiError), or
    another pass holding the lock (state.Busy). Every error text passes through redact_held."""
    one_pass = one_pass or (lambda: armed_pass(cfg, "tournament", caller))
    period, n, bad = cfg["poll_minutes"] * 60, 0, 0
    while passes is None or n < passes:
        n += 1
        row = {"pass_utc": clock().isoformat()}
        try:
            row["counts"] = one_pass()
            bad = 0
        except settings.Refuse as exc:
            row["stopped"] = msg(exc)
        except json.JSONDecodeError:
            row["stopped"] = "corrupt private log: a line is not JSON"
        except (metaculus.Refuse, metaculus.ApiError, state.Busy) as exc:
            row["error"] = f"{type(exc).__name__}: {msg(exc)}"
        except Exception as exc:                       # unhandled, or an OSError on the log: counted
            bad += 1
            row["error"] = type(exc).__name__
            row["bad_in_a_row"] = bad
            if bad >= MAX_BAD_PASSES:
                row["stopped"] = f"{bad} passes in a row ended in an unhandled error"
        if "stopped" in row:
            print(json.dumps({"stopped": row["stopped"]}), file=err, flush=True)
            record_error(cfg, row)
            return 2
        if "error" in row:
            record_error(cfg, row)
        print(json.dumps(row), flush=True)
        now = clock().timestamp()
        sleep(period - now % period + 5)
    return 0


def record_error(cfg, row):
    """Append a loop-level row to the private log without the pass lock (it is one O_APPEND write)."""
    try:
        log = log_for(cfg, "tournament")
        log.ensure()
        log.add(kind="loop", **row)
    except OSError:
        pass


# ------------------------------------------------------------------ status: counts only
FAILED_PREFIXES = ("failed", "no_valid_distribution", "gave_up")


def status(cfg, mode="tournament", now=None):
    """Counts from the private log, for the lead's hourly wake. Never a forecast, question text, comment or reason:
    only counts, day totals, claim ages and the last pass time."""
    now = now or datetime.now(UTC)
    log = log_for(cfg, mode)
    rows = log.rows() if log.path.exists() else []
    ix = state.index(rows)
    out = {"mode": mode, "passes": 0, "answered_questions": len(ix["submitted"]), "outcomes_failed": 0,
           "outcomes_deferred": 0, "open_claims": len(ix["open_claims"]),
           "open_claim_age_hours": sorted(round((now - (questions.parse_time(c.get("made_utc")) or now))
                                                .total_seconds() / 3600, 1) for c in ix["open_claims"].values()),
           "calls_today": ix["calls_by_day"].get(now.strftime("%Y-%m-%d"), 0),
           "call_caps": [cfg["max_model_calls_per_pass"], cfg["max_model_calls_per_day"]],
           "loop_errors": 0, "loop_stopped": False, "last_pass_utc": None}
    for r in rows:
        k, st = r.get("kind"), str(r.get("status", ""))
        if k == "pass_start":
            out["passes"] += 1
            out["last_pass_utc"] = r.get("pass_id")
        elif k == "outcome" and st.startswith(FAILED_PREFIXES):
            out["outcomes_failed"] += 1
        elif k == "outcome" and st.startswith("deferred"):
            out["outcomes_deferred"] += 1
        elif k == "loop":
            out["loop_errors"] += "error" in r
            out["loop_stopped"] = out["loop_stopped"] or "stopped" in r
    return out


# ------------------------------------------------------------------ dry run and selfcheck
SAMPLES = [
    {"id": 900001, "title": "Made-up: Will the town fair in Exampleville draw over 10,000 visitors in 2027?",
     "question": {"id": 910001, "type": "binary", "status": "open", "title": "Made-up binary question",
                  "description": "Invented for a dry run.", "resolution_criteria": "Yes if the organizer reports more "
                  "than 10,000 visitors.", "fine_print": "", "scheduled_close_time": "2099-01-01T00:00:00Z"}},
    {"id": 900002, "title": "Made-up: Which colour will the Exampleville bridge be painted?",
     "question": {"id": 910002, "type": "multiple_choice", "status": "open", "title": "Made-up multiple choice",
                  "options": ["Red", "Green", "Blue"], "description": "Invented.", "resolution_criteria": "The colour "
                  "the council announces.", "scheduled_close_time": "2099-01-01T00:00:00Z"}},
    {"id": 900003, "title": "Made-up: How many ferries will cross the Example river on 1 May?",
     "question": {"id": 910003, "type": "numeric", "status": "open", "title": "Made-up numeric", "unit": "ferries",
                  "scaling": {"range_min": 0, "range_max": 500, "zero_point": None}, "open_lower_bound": False,
                  "open_upper_bound": True, "inbound_outcome_count": 200, "description": "Invented.",
                  "resolution_criteria": "The harbour count.", "scheduled_close_time": "2099-01-01T00:00:00Z"}},
    {"id": 900004, "title": "Made-up: When will the Exampleville library reopen?",
     "question": {"id": 910004, "type": "date", "status": "open", "title": "Made-up date",
                  "scaling": {"range_min": 1798761600, "range_max": 1830297600, "zero_point": None},
                  "open_lower_bound": True, "open_upper_bound": True, "inbound_outcome_count": 200,
                  "description": "Invented.", "resolution_criteria": "The reopening day.",
                  "scheduled_close_time": "2099-01-01T00:00:00Z"}},
    {"id": 900005, "title": "Made-up: Exampleville rainfall by month (group)",
     "group_of_questions": {"description": "Invented group.", "resolution_criteria": "Weather office totals.",
                            "group_variable": "Month", "questions": [
         {"id": 910005, "type": "discrete", "status": "open", "label": "March", "title": "March rain days",
          "scaling": {"range_min": -0.5, "range_max": 31.5, "zero_point": None}, "open_lower_bound": False,
          "open_upper_bound": False, "inbound_outcome_count": 32, "scheduled_close_time": "2099-01-01T00:00:00Z"},
         {"id": 910006, "type": "binary", "status": "open", "label": "April over 10 days",
          "title": "April over 10 rain days", "scheduled_close_time": "2099-01-01T00:00:00Z"}]}},
]


class OfflineClient:
    """Stands in for metaculus.Client in a dry run: made-up posts, no forecasts on the site, and no send method."""
    def __init__(self, posts):
        self.posts = posts

    def open_posts(self, slug):
        return [p for p in self.posts]

    def my_forecasts(self, qids):
        return {i: 0 for i in qids}


async def fake_caller(kind, model, prompt, schema, timeout, max_tokens):
    """A fixed, plausible reply in the right form, so the dry run shows the whole path without a model."""
    if kind == "research":
        return {"text": "Made-up brief: no real research in a dry run.\nSOURCES:\nhttps://example.org/made-up",
                "finish_ok": True, "secs": 0.0}
    props = schema["properties"]
    if "probability" in props:
        r = {"probability": {"claude_sonnet_5_5": 0.3, "gpt_5_4": 0.4}.get(model, 0.35), "reasons": "Made-up reasons."}
    elif "probabilities" in props:
        opts = json.loads(prompt.split("QUESTION (JSON):\n", 1)[1].split("\n\nRESEARCH BRIEF", 1)[0])["options"]
        r = {"probabilities": [{"option": o, "probability": 1 / len(opts)} for o in opts], "reasons": "Made-up."}
    else:
        pkt = json.loads(prompt.split("QUESTION (JSON):\n", 1)[1].split("\n\nRESEARCH BRIEF", 1)[0])
        rng = pkt["range"]
        if pkt["type"] == "date":
            base = datetime.fromisoformat(rng["range_min"]).replace(tzinfo=UTC)
            r = {k: (base + timedelta(days=60 + 40 * i)).strftime("%Y-%m-%d")
                 for i, (k, _) in enumerate(method.PERCENTILES)}
        else:
            lo, hi = rng["range_min"], rng["range_max"]
            r = {k: lo + (hi - lo) * (0.1 + 0.12 * i) for i, (k, _) in enumerate(method.PERCENTILES)}
        r["reasons"] = "Made-up reasons."
    return {"text": json.dumps(r), "finish_ok": True, "secs": 0.0}


def dry_run(cfg, live_models=False, posts=None, folder=None, caller=None):
    out, calls = [], {"research": 0, "run": 0}
    base = caller or (models.sdk_call if live_models else fake_caller)

    async def counted(kind, *a):
        calls[kind] += 1
        return await base(kind, *a)
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        log = state.Log(folder or tmp)
        with log.locked():
            run_pass(OfflineClient(posts or SAMPLES), counted, log, cfg, ["made-up"], dry=True, out=out)
            rows = [r for r in log.rows() if r.get("kind") == "outcome"]
    summary = {"made_utc": datetime.now(UTC).isoformat(timespec="seconds"), "live_models": live_models,
               "prompt_sha256": method.prompt_hash(), "posts": len(rows),
               "questions": sum(len(r.get("question_ids") or []) for r in rows), "calls": calls,
               "seconds": round(time.monotonic() - t0, 1), "outcomes": {}, "research": {}, "runs": {}}
    for r in rows:
        summary["outcomes"][r["status"]] = summary["outcomes"].get(r["status"], 0) + 1
        summary["research"][r.get("research")] = summary["research"].get(r.get("research"), 0) + 1
        for q in r.get("runs") or []:
            for run in q["runs"]:
                key = f"{run['model']}:{run['status']}"
                summary["runs"][key] = summary["runs"].get(key, 0) + 1
    return out, rows, summary


def save_summary(cfg, summary):
    """Counts only (no model text, no question text) under the private folder, for the plan page to cite."""
    folder = state.Log(cfg["private_dir"] + "_dry_runs")
    folder.ensure()
    path = folder.dir / f"live_dry_{summary['made_utc'].replace(':', '').replace('+0000', 'Z')}.json"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(summary, f, indent=1, sort_keys=True)
    return str(path)


class NoNetwork:
    """Blocks every socket connection while active, and counts attempts."""
    def __init__(self):
        self.tries = 0

    def __enter__(self):
        self.saved = (socket.socket.connect, socket.socket.connect_ex, socket.create_connection, socket.getaddrinfo)

        def block(*a, **k):
            self.tries += 1
            raise OSError("network blocked by selfcheck")
        socket.socket.connect = block
        socket.socket.connect_ex = block
        socket.create_connection = block
        socket.getaddrinfo = block
        return self

    def __exit__(self, *exc):
        socket.socket.connect, socket.socket.connect_ex, socket.create_connection, socket.getaddrinfo = self.saved
        return False


def selfcheck(cfg):
    """Every way to start must refuse on this build: no key on the ledger row (or network_allowed false), no client
    without arming, and no client without a token. Runs with sockets blocked; reports any attempt to connect."""
    checks = {}
    with NoNetwork() as guard:
        try:
            settings.required(cfg)
            checks["settings"] = "ok"
        except settings.Refuse as exc:
            checks["settings"] = f"refused: {msg(exc)}"
        try:
            arm(cfg, "tournament")
            checks["arm_tournament"] = "WOULD RUN"
        except settings.Refuse as exc:
            checks["arm_tournament"] = f"refused: {msg(exc)}"
        try:
            arm(cfg | {"network_allowed": True}, "tournament")
            checks["arm_with_network_allowed"] = "WOULD RUN"
        except settings.Refuse as exc:
            checks["arm_with_network_allowed"] = f"refused: {msg(exc)}"
        try:
            metaculus.Client(cfg | {"network_allowed": True}, armed=False)
            checks["client_unarmed"] = "WOULD RUN"
        except metaculus.Refuse as exc:
            checks["client_unarmed"] = f"refused: {msg(exc)}"
        try:
            metaculus.Client(cfg | {"network_allowed": True}, armed=True, environ={})
            checks["client_without_token"] = "WOULD RUN"
        except metaculus.Refuse as exc:
            checks["client_without_token"] = f"refused: {msg(exc)}"
        try:
            settings.require_key(cfg["ledger_row"], cfg["start_key"], "0" * 40)
            checks["ledger_key"] = "WOULD RUN"
        except settings.Refuse as exc:
            checks["ledger_key"] = f"refused: {msg(exc)}"
        checks["connection_attempts"] = guard.tries
    ok = (checks["settings"] == "ok" and checks["connection_attempts"] == 0
          and all(str(checks[k]).startswith("refused") for k in
                  ("arm_tournament", "arm_with_network_allowed", "client_unarmed", "client_without_token", "ledger_key")))
    return ok, checks


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("selfcheck", "dry-run", "pass", "loop", "testing", "status"))
    ap.add_argument("--live-models", action="store_true", help="dry-run only: real model calls on made-up questions")
    args = ap.parse_args(argv)
    cfg = settings.load()
    try:
        if args.command == "selfcheck":
            ok, checks = selfcheck(cfg)
            print(json.dumps({"selfcheck": "pass" if ok else "FAIL", "checks": checks}, indent=1))
            return 0 if ok else 1
        if args.command == "dry-run":
            out, rows, summary = dry_run(cfg, live_models=args.live_models)
            if args.live_models:
                summary["saved_to"] = save_summary(cfg, summary)
            print(json.dumps({"would_submit": out, "summary": summary}, indent=1))
            return 0
        if args.command == "status":
            print(json.dumps(status(cfg), sort_keys=True))
            return 0
        if args.command == "loop":
            return loop(cfg)
        counts = armed_pass(cfg, "tournament" if args.command == "pass" else "testing")
        print(json.dumps({"counts": counts}))
        return 0
    except (settings.Refuse, metaculus.Refuse) as exc:
        print(json.dumps({"refused": msg(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
