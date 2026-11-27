"""Plan B01 forecast bot on made-up questions, a fake model and fake Metaculus pages. No network, no model, no key."""
import copy
import json
import urllib.error
from datetime import datetime, timezone

import pytest

from forecast_bot import bot, cdf, method, metaculus, models, questions, settings, state

NOW = datetime(2027, 3, 1, 12, 0, tzinfo=timezone.utc)
TOKEN = "tok_" + "a1B2c3D4e5F6g7H8i9J0" * 2
CFG = settings.load()


def numeric(lo=0.0, hi=100.0, lo_open=False, hi_open=False, n=200, zp=None, qtype="numeric", qid=1):
    return {"id": qid, "type": qtype, "status": "open", "title": "made-up", "inbound_outcome_count": n,
            "scaling": {"range_min": lo, "range_max": hi, "zero_point": zp},
            "open_lower_bound": lo_open, "open_upper_bound": hi_open, "scheduled_close_time": "2099-01-01T00:00:00Z"}


PCT = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]


def run(values):
    return list(zip(PCT, values))


def steps(c):
    return [b - a for a, b in zip(c, c[1:])]


# ------------------------------------------------------------------ the CDF builder
@pytest.mark.parametrize("lo_open,hi_open", [(False, False), (True, False), (False, True), (True, True)])
def test_cdf_bounds_each_way(lo_open, hi_open):
    q = numeric(lo_open=lo_open, hi_open=hi_open)
    c = cdf.build([run([10, 20, 35, 50, 65, 80, 90])], q)
    assert len(c) == 201
    assert all(d >= 0.01 / 200 - 1e-12 for d in steps(c))
    assert (c[0] == 0.0) != lo_open and (c[-1] == 1.0) != hi_open
    if lo_open:
        assert c[0] >= 0.001
    if hi_open:
        assert c[-1] <= 0.999
    assert cdf.check(c, q)


def test_cdf_monotone_strictly():
    c = cdf.build([run([1, 2, 3, 4, 5, 6, 7])], numeric(hi_open=True))
    assert all(b > a for a, b in zip(c, c[1:]))


@pytest.mark.parametrize("n", [2, 10, 32, 50, 200])
def test_cdf_point_count_is_outcomes_plus_one(n):
    q = numeric(lo=-0.5, hi=n - 0.5, n=n, qtype="discrete")
    c = cdf.build([run([1, 1.5, 2, 3, 4, 5, 6][:7])], q) if n > 7 else cdf.build([run([0, 0.2, 0.4, 0.5, 0.6, 0.8, 1])], q)
    assert len(c) == n + 1 and cdf.check(c, q)


def test_cdf_max_step_cap_holds_for_a_spike():
    q = numeric(lo_open=True, hi_open=True)
    c = cdf.build([run([49.9, 49.95, 49.99, 50, 50.01, 50.05, 50.1])], q)
    assert max(steps(c)) <= 0.2 + 1e-12
    assert cdf.check(c, q)


def test_cdf_discrete_cap_is_the_slider_limit():
    assert cdf.max_step(10) == 0.59 and cdf.max_step(200) == 0.2 and cdf.max_step(400) == 0.1


def test_cdf_min_step_scales_with_outcomes():
    assert cdf.min_step(200) == 0.00005 and cdf.min_step(10) == 0.001


def test_cdf_percentiles_outside_the_range():
    q = numeric(lo_open=True, hi_open=True)
    c = cdf.build([run([-50, -40, -30, -20, -10, 0, 5])], q)
    assert cdf.check(c, q) and c[0] > 0.85          # most mass below an open lower bound
    c3 = cdf.build([run([150, 160, 170, 180, 190, 200, 210])], q)
    assert cdf.check(c3, q) and c3[-1] < 0.15       # most mass above an open upper bound
    q2 = numeric()
    c2 = cdf.build([run([-50, -40, -30, -20, -10, 0, 5])], q2)
    assert cdf.check(c2, q2) and c2[0] == 0.0 and c2[-1] == 1.0


def test_cdf_closed_bounds_put_no_mass_outside():
    q = numeric()
    c = cdf.build([run([150, 160, 170, 180, 190, 200, 210])], q)
    assert c[0] == 0.0 and c[-1] == 1.0 and cdf.check(c, q)


def test_cdf_log_scaling_median_lands_where_asked():
    q = numeric(lo=1, hi=10000, zp=0, hi_open=True)
    c = cdf.build([run([5, 10, 30, 100, 300, 1000, 2000])], q)
    assert cdf.check(c, q)
    assert 80 < cdf.quantile(c, q, 0.5) < 125
    assert abs(cdf.to_internal(100, q) - 0.5) < 0.001   # 100 sits halfway on a 1 to 10000 log axis


def test_cdf_internal_axis_round_trip():
    for q in (numeric(), numeric(lo=1, hi=1000, zp=0)):
        for v in (1, 5, 50, 99):
            assert abs(cdf.from_internal(cdf.to_internal(v, q), q) - v) < 1e-9


def test_cdf_date_question():
    q = numeric(lo=1798761600, hi=1830297600, lo_open=True, hi_open=True, qtype="date")
    vals = ["2027-03-01", "2027-04-01", "2027-06-01", "2027-08-01", "2027-10-01", "2027-12-01", "2028-01-15"]
    c = cdf.build([run(vals)], q)
    assert cdf.check(c, q)
    mid = datetime.fromtimestamp(cdf.quantile(c, q, 0.5), timezone.utc)
    assert mid.year == 2027 and 7 <= mid.month <= 8


def test_cdf_mixture_is_between_its_runs():
    q = numeric()
    a, b = run([10, 12, 15, 20, 25, 28, 30]), run([60, 62, 65, 70, 75, 78, 80])
    m = cdf.build([a, b], q)
    assert 0.45 < m[100] < 0.55                     # half the mass below 50
    assert cdf.check(m, q)


def test_cdf_flat_percentiles_are_accepted():
    q = numeric()
    assert cdf.check(cdf.build([run([50, 50, 50, 50, 50, 50, 50])], q), q)


def test_cdf_rejects_bad_runs():
    q = numeric()
    with pytest.raises(cdf.CdfError):
        cdf.raw_curve(run([10, 9, 8, 7, 6, 5, 4]), q)
    with pytest.raises(cdf.CdfError):
        cdf.raw_curve([(0.5, 10)], q)
    with pytest.raises(cdf.CdfError):
        cdf.raw_curve([(0.0, 1), (0.5, 2)], q)
    with pytest.raises(cdf.CdfError):
        cdf.raw_curve([(0.2, float("nan")), (0.5, 2)], q)


def test_cdf_check_catches_each_rule():
    q = numeric()
    good = cdf.build([run([10, 20, 35, 50, 65, 80, 90])], q)
    bad = [good[:-1], [good[0] + 0.01] + good[1:], good[:-1] + [0.999], good[:100] + [good[100]] + good[101:200]]
    for b in bad:
        with pytest.raises(cdf.CdfError):
            cdf.check(b, q)
    flat = list(good)
    flat[50] = flat[49]
    with pytest.raises(cdf.CdfError):
        cdf.check(flat, q)
    jump = [0.0] + [0.3] + [0.3 + 0.7 * i / 199 for i in range(1, 200)]
    with pytest.raises(cdf.CdfError):
        cdf.check(jump, q)
    qo = numeric(lo_open=True)
    with pytest.raises(cdf.CdfError):
        cdf.check([0.0005] + good[1:], qo)


def test_cdf_bad_question_shape():
    with pytest.raises(cdf.CdfError):
        cdf.outcome_count({"inbound_outcome_count": 1})
    with pytest.raises(cdf.CdfError):
        cdf.bounds_open({"scaling": {}})
    with pytest.raises(cdf.CdfError):
        cdf.to_internal(5, {"type": "numeric", "scaling": {"range_min": 5, "range_max": 5}})


# ------------------------------------------------------------------ replies and the aggregate
def test_binary_median_and_clip():
    q = {"type": "binary"}
    assert method.aggregate(q, [0.1, 0.2, 0.9], CFG) == 0.2
    assert method.aggregate(q, [0.0, 0.0, 0.001], CFG) == CFG["binary_clip"][0]
    assert method.aggregate(q, [1.0, 1.0, 1.0], CFG) == CFG["binary_clip"][1]


def test_multiple_choice_floor_and_sum():
    q = {"type": "multiple_choice", "options": ["A", "B", "C", "D"]}
    p = method.aggregate(q, [{"A": 1.0, "B": 0.0, "C": 0.0, "D": 0.0}, {"A": 0.98, "B": 0.02, "C": 0.0, "D": 0.0}], CFG)
    assert list(p) == ["A", "B", "C", "D"]
    assert abs(sum(p.values()) - 1) < 1e-9 and min(p.values()) >= CFG["mc_floor"] - 1e-9


def test_check_reply_each_type():
    assert method.check_reply('{"probability": 0.4, "reasons": "r"}', {"type": "binary"})[0] == 0.4
    mc = {"type": "multiple_choice", "options": ["A", "B"]}
    got, _ = method.check_reply(json.dumps({"probabilities": [{"option": "A", "probability": 0.6},
                                                              {"option": "B", "probability": 0.4}], "reasons": "r"}), mc)
    assert got == {"A": 0.6, "B": 0.4}
    num = {k: float(i) for i, (k, _) in enumerate(method.PERCENTILES)} | {"reasons": "r"}
    assert len(method.check_reply(json.dumps(num), numeric())[0]) == 7
    date = {k: f"2027-0{i + 1}-01" for i, (k, _) in enumerate(method.PERCENTILES)} | {"reasons": "r"}
    assert method.check_reply(json.dumps(date), numeric(qtype="date"))[0][0] == (0.05, "2027-01-01")


@pytest.mark.parametrize("text,q", [
    ("not json", {"type": "binary"}),
    ('{"probability": 1.2, "reasons": "r"}', {"type": "binary"}),
    ('{"probability": true, "reasons": "r"}', {"type": "binary"}),
    ('{"probability": 0.5}', {"type": "binary"}),
    ('{"probability": 0.5, "reasons": ""}', {"type": "binary"}),
    ('{"probabilities": [{"option": "A", "probability": 1}], "reasons": "r"}',
     {"type": "multiple_choice", "options": ["A", "B"]}),
    ('{"probabilities": [{"option": "A", "probability": 0.2}, {"option": "B", "probability": 0.2}], "reasons": "r"}',
     {"type": "multiple_choice", "options": ["A", "B"]}),
])
def test_check_reply_rejects(text, q):
    with pytest.raises(method.BadReply):
        method.check_reply(text, q)


def test_check_reply_rejects_falling_percentiles():
    num = {k: float(-i) for i, (k, _) in enumerate(method.PERCENTILES)} | {"reasons": "r"}
    with pytest.raises(method.BadReply):
        method.check_reply(json.dumps(num), numeric())


def test_prompt_hash_is_stable_and_schemas_are_closed():
    assert method.prompt_hash() == method.prompt_hash()
    for t in method.FORMS:
        s = method.schema(t)
        assert s["additionalProperties"] is False and set(s["required"]) == set(s["properties"])


# ------------------------------------------------------------------ questions and the packet
def post_with(q, pid=50):
    return {"id": pid, "title": "made-up post", "question": q}


def test_packet_never_holds_the_community_prediction():
    q = numeric() | {"aggregations": {"recency_weighted": {"latest": {"centers": [0.7]}}},
                     "my_forecasts": {"latest": {"forecast_values": [0.1]}}, "description": "d"}
    p = questions.packet(post_with(q), q, None, NOW)
    text = json.dumps(p)
    assert "aggregations" not in text and "recency_weighted" not in text and "my_forecasts" not in text
    assert set(p) <= set(questions.PACKET_FIELDS) | {"today_utc", "post_title", "group", "range"}


def test_tasks_types_and_skips():
    assert len(questions.tasks(post_with({"id": 1, "type": "binary", "status": "open", "title": "t"}), NOW)) == 1
    assert questions.tasks(post_with({"id": 1, "type": "binary", "status": "closed", "title": "t"}), NOW) == []
    with pytest.raises(questions.Skip):
        questions.tasks({"id": 2, "conditional": {}}, NOW)
    with pytest.raises(questions.Skip):
        questions.tasks(post_with({"id": 1, "type": "conditional_x", "status": "open", "title": "t"}), NOW)
    with pytest.raises(questions.Skip):
        questions.tasks(post_with({"id": 1, "type": "multiple_choice", "status": "open", "title": "t"}), NOW)
    group = bot.SAMPLES[4]
    assert [q["id"] for q, _ in questions.tasks(group, NOW)] == [910005, 910006]


def test_tasks_respects_open_and_close_times():
    q = {"id": 1, "type": "binary", "status": "open", "title": "t", "open_time": "2027-03-01T13:00:00Z"}
    assert questions.tasks(post_with(q), NOW) == []
    q = {"id": 1, "type": "binary", "status": "open", "title": "t", "scheduled_close_time": "2027-03-01T11:00:00Z"}
    assert questions.tasks(post_with(q), NOW) == []


# ------------------------------------------------------------------ a whole pass, end to end
class Pages:
    """Fake Metaculus: a list of posts, our forecasts on the site, and a record of what was sent."""
    def __init__(self, posts, on_site=None, fail=None):
        self.posts, self.on_site, self.sent, self.fail = posts, dict(on_site or {}), [], fail or {}

    def open_posts(self, slug):
        if "list" in self.fail:
            raise metaculus.ApiError(503, "GET /api/posts/")
        return copy.deepcopy(self.posts)

    def my_forecasts(self, qids):
        if "read" in self.fail:
            raise metaculus.ApiError(503, "POST read")
        return {i: self.on_site.get(i, 0) for i in qids}

    def submit(self, body):
        if "submit" in self.fail:
            err = self.fail["submit"]
            raise metaculus.ApiError(err, "POST submit")
        self.sent.append(body)
        for f in body["forecasts"]:
            self.on_site[f["question"]] = 1
        return 201


def outcomes(log, pass_no=-1):
    rows = log.rows()
    ids = [r["pass_id"] for r in rows if r["kind"] == "pass_start"]
    return {r["post_id"]: r["status"] for r in rows if r["kind"] == "outcome" and r["pass_id"] == ids[pass_no]}


def do_pass(pages, log, now=NOW, caller=bot.fake_caller, cfg=CFG):
    with log.locked():
        return bot.run_pass(pages, caller, log, cfg, ["minibench"], now=now)


def test_every_type_end_to_end(tmp_path):
    pages, log = Pages(bot.SAMPLES), state.Log(tmp_path)
    do_pass(pages, log)
    assert set(outcomes(log).values()) == {"submitted"} and len(pages.sent) == 5
    kinds = [sorted(k for f in b["forecasts"] for k in f if k != "question") for b in pages.sent]
    assert kinds == [["probability_yes"], ["probability_yes_per_category"], ["continuous_cdf"], ["continuous_cdf"],
                     ["continuous_cdf", "probability_yes"]]
    group = pages.sent[4]["forecasts"]
    assert len(group[0]["continuous_cdf"]) == 33
    for b in pages.sent:
        c = b["comments"]
        assert len(c) == 1 and c[0]["is_private"] is True and c[0]["included_forecast"] is True
        assert "Forecast:" in c[0]["text"] and len(c[0]["text"]) <= CFG["comment_max_chars"]


def test_duplicate_guard_second_pass_sends_nothing(tmp_path):
    pages, log = Pages(bot.SAMPLES), state.Log(tmp_path)
    do_pass(pages, log)
    do_pass(pages, log, now=NOW.replace(minute=15))
    assert len(pages.sent) == 5
    assert set(outcomes(log).values()) == {"already_answered"}


def test_duplicate_guard_local_log_alone(tmp_path):
    pages, log = Pages(bot.SAMPLES), state.Log(tmp_path)
    do_pass(pages, log)
    pages.on_site = {}                                 # the site read shows nothing, the log still blocks
    do_pass(pages, log, now=NOW.replace(minute=15))
    assert len(pages.sent) == 5


def test_duplicate_guard_site_alone(tmp_path):
    pages = Pages(bot.SAMPLES[:1], on_site={910001: 1})
    log = state.Log(tmp_path)
    do_pass(pages, log)
    assert pages.sent == [] and outcomes(log) == {900001: "already_answered"}


def test_post_listed_twice_in_one_pass(tmp_path):
    pages, log = Pages(bot.SAMPLES[:1] * 2), state.Log(tmp_path)
    do_pass(pages, log)
    rows = [r for r in log.rows() if r["kind"] == "outcome"]
    assert len(pages.sent) == 1 and sorted(r["status"] for r in rows) == ["duplicate_in_pass", "submitted"]


def test_group_partly_answered_sends_only_the_rest(tmp_path):
    pages, log = Pages(bot.SAMPLES[4:5], on_site={910005: 1}), state.Log(tmp_path)
    do_pass(pages, log)
    assert [f["question"] for f in pages.sent[0]["forecasts"]] == [910006]


def test_every_post_gets_an_outcome(tmp_path):
    posts = bot.SAMPLES + [{"id": 77, "conditional": {}}, post_with({"id": 5, "type": "binary", "status": "closed",
                                                                     "title": "t"}, pid=78)]
    pages, log = Pages(posts), state.Log(tmp_path)
    do_pass(pages, log)
    got = outcomes(log)
    assert set(got) == {p["id"] for p in posts}
    assert got[77] == "skipped:conditional_not_supported" and got[78] == "no_open_question"


def test_unknown_http_outcome_leaves_claim_open_then_settles(tmp_path):
    pages, log = Pages(bot.SAMPLES[:1], fail={"submit": 502}), state.Log(tmp_path)
    do_pass(pages, log)
    assert outcomes(log) == {900001: "unknown_outcome"}
    assert len(state.index(log.rows())["open_claims"]) == 1
    pages.fail, pages.on_site = {}, {910001: 1}        # it was saved after all
    do_pass(pages, log, now=NOW.replace(minute=15))
    ix = state.index(log.rows())
    assert ix["open_claims"] == {} and 910001 in ix["submitted"] and pages.sent == []


def test_unknown_outcome_not_on_site_is_retried(tmp_path):
    pages, log = Pages(bot.SAMPLES[:1], fail={"submit": "TimeoutError"}), state.Log(tmp_path)
    do_pass(pages, log)
    pages.fail = {}
    do_pass(pages, log, now=NOW.replace(minute=15))
    assert len(pages.sent) == 1 and state.index(log.rows())["open_claims"] == {}


def test_rejected_submission_settles_the_claim(tmp_path):
    pages, log = Pages(bot.SAMPLES[:1], fail={"submit": 400}), state.Log(tmp_path)
    do_pass(pages, log)
    assert outcomes(log) == {900001: "failed_http_400"} and state.index(log.rows())["open_claims"] == {}


def test_attempts_cap(tmp_path):
    pages, log = Pages(bot.SAMPLES[:1], fail={"submit": 400}), state.Log(tmp_path)
    for m in range(CFG["max_attempts_per_post"] + 1):
        do_pass(pages, log, now=NOW.replace(minute=m))
    assert outcomes(log) == {900001: "gave_up_after_attempts"}


def test_too_few_valid_runs(tmp_path):
    async def broken(kind, model, prompt, schema, timeout, max_tokens):
        if kind == "research":
            raise RuntimeError("no research")
        return {"text": "nonsense", "finish_ok": True}
    pages, log = Pages(bot.SAMPLES[:1]), state.Log(tmp_path)
    do_pass(pages, log, caller=broken)
    assert outcomes(log) == {900001: "failed_runs"} and pages.sent == []


def test_runs_tolerate_a_minority_failing(tmp_path):
    async def some_fail(kind, model, prompt, schema, timeout, max_tokens):
        if kind == "run" and model == "gpt_5_4":
            return {"text": "", "finish_ok": False}
        return await bot.fake_caller(kind, model, prompt, schema, timeout, max_tokens)
    pages, log = Pages(bot.SAMPLES[:1]), state.Log(tmp_path)
    do_pass(pages, log, caller=some_fail)
    assert outcomes(log) == {900001: "submitted"}


def test_question_missing_from_the_site_read_is_not_sent(tmp_path):
    pages, log = Pages(bot.SAMPLES[:1]), state.Log(tmp_path)
    pages.my_forecasts = lambda qids: {}
    do_pass(pages, log)
    assert pages.sent == [] and outcomes(log) == {900001: "guard_cannot_check"}


def test_bulk_read_is_a_get_with_repeated_ids(monkeypatch):
    monkeypatch.setenv("METACULUS_TOKEN", TOKEN)
    opener = FakeOpener(body=b'{"results": [{"question_id": 1, "forecasts": [{}]}, {"question_id": 2, "forecasts": []}]}')
    c = metaculus.Client(CFG | {"network_allowed": True}, armed=True, opener=opener)
    assert c.my_forecasts([2, 1]) == {1: 1, 2: 0}
    req = opener.reqs[0]
    assert req.get_method() == "GET" and req.full_url.endswith("/api/questions/bulk-forecast-read/?question_ids=1&question_ids=2")


def test_submit_posts_json_to_the_bulk_endpoint(monkeypatch):
    monkeypatch.setenv("METACULUS_TOKEN", TOKEN)
    opener = FakeOpener(status=201, body=b"")
    c = metaculus.Client(CFG | {"network_allowed": True}, armed=True, opener=opener)
    q = bot.SAMPLES[0]["question"]
    assert c.submit(bot.payload(bot.SAMPLES[0], [(q, 0.3)], "text")) == 201
    req = opener.reqs[0]
    assert req.get_method() == "POST" and req.full_url == "https://www.metaculus.com/api/questions/bulk-forecast-comment/"
    body = json.loads(req.data)
    assert body["forecasts"] == [{"question": 910001, "probability_yes": 0.3}]
    assert body["comments"][0] == {"on_post": 900001, "text": "text", "is_private": True, "included_forecast": True}


def test_guard_unavailable_sends_nothing(tmp_path):
    pages, log = Pages(bot.SAMPLES, fail={"read": True}), state.Log(tmp_path)
    do_pass(pages, log)
    assert pages.sent == [] and set(outcomes(log).values()) == {"deferred_guard_unavailable"}


def test_list_failure_is_recorded(tmp_path):
    pages, log = Pages(bot.SAMPLES, fail={"list": True}), state.Log(tmp_path)
    counts = do_pass(pages, log)
    assert counts == {"list_failed": 1} and any(r["kind"] == "list_failed" for r in log.rows())


def test_no_time_left(tmp_path):
    q = dict(bot.SAMPLES[0]["question"], scheduled_close_time="2027-03-01T12:03:00Z")
    pages, log = Pages([post_with(q)]), state.Log(tmp_path)
    do_pass(pages, log)
    assert outcomes(log) == {50: "no_time"}


def test_log_holds_hashes_not_question_text(tmp_path):
    pages, log = Pages(bot.SAMPLES), state.Log(tmp_path)
    do_pass(pages, log)
    raw = log.path.read_text()
    assert "Exampleville" not in raw and "organizer reports" not in raw
    assert oct(tmp_path.stat().st_mode & 0o777) == "0o700" and oct(log.path.stat().st_mode & 0o777) == "0o600"


def test_lock_refuses_a_second_pass(tmp_path):
    log = state.Log(tmp_path)
    with log.locked():
        with pytest.raises(RuntimeError):
            with state.Log(tmp_path).locked():
                pass


def test_dry_run_sends_nothing_and_has_no_submit():
    assert not hasattr(bot.OfflineClient([]), "submit")
    with bot.NoNetwork() as guard:
        out, rows = bot.dry_run(CFG)
    assert guard.tries == 0 and len(out) == 5 and {r["status"] for r in rows} == {"dry_run"}


# ------------------------------------------------------------------ secrets
def test_client_refuses_without_network_allowed_arming_or_token():
    with pytest.raises(metaculus.Refuse):
        metaculus.Client(CFG, armed=True, environ={"METACULUS_TOKEN": TOKEN})
    open_cfg = CFG | {"network_allowed": True}
    with pytest.raises(metaculus.Refuse):
        metaculus.Client(open_cfg, armed=False, environ={"METACULUS_TOKEN": TOKEN})
    for env in ({}, {"METACULUS_TOKEN": ""}, {"METACULUS_TOKEN": "short"}, {"METACULUS_TOKEN": "has space in it ok"}):
        with pytest.raises(metaculus.Refuse):
            metaculus.Client(open_cfg, armed=True, environ=env)
    with pytest.raises(metaculus.Refuse):
        metaculus.Client(open_cfg | {"api_base": "http://www.metaculus.com"}, armed=True, environ={"METACULUS_TOKEN": TOKEN})


class FakeOpener:
    def __init__(self, status=200, body=b'{"results": [], "next": null}', exc=None):
        self.reqs, self.status, self.body, self.exc = [], status, body, exc

    def open(self, req, timeout):
        self.reqs.append(req)
        if self.exc:
            raise self.exc
        return _Resp(self.status, self.body)


class _Resp:
    def __init__(self, status, body):
        self.status, self._b = status, body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, n):
        return self._b


def test_token_only_in_the_auth_header_and_never_in_errors(monkeypatch):
    monkeypatch.setenv("METACULUS_TOKEN", TOKEN)
    opener = FakeOpener()
    c = metaculus.Client(CFG | {"network_allowed": True}, armed=True, opener=opener)
    assert TOKEN not in json.dumps(vars(c), default=str)
    c.open_posts("minibench")
    req = opener.reqs[0]
    assert req.get_header("Authorization") == "Token " + TOKEN
    assert TOKEN not in req.full_url and req.full_url.startswith("https://www.metaculus.com/api/posts/?")
    opener.exc = urllib.error.HTTPError(req.full_url, 403, "Token " + TOKEN, {}, None)
    with pytest.raises(metaculus.ApiError) as e:
        c.my_forecasts([1])
    assert TOKEN not in str(e.value) and e.value.__cause__ is None and e.value.__suppress_context__


def test_redirects_are_refused():
    h = metaculus.NoRedirect()
    assert h.redirect_request(None, None, 302, "Found", {}, "https://evil.example/") is None


def test_redact():
    assert TOKEN not in metaculus.redact("Authorization: Token " + TOKEN)
    assert metaculus.redact("x " + TOKEN, TOKEN) == "x [redacted]"


def test_token_never_reaches_prompts_payloads_or_log(tmp_path, monkeypatch):
    monkeypatch.setenv("METACULUS_TOKEN", TOKEN)
    seen = []

    async def spy(kind, model, prompt, schema, timeout, max_tokens):
        seen.append(prompt)
        return await bot.fake_caller(kind, model, prompt, schema, timeout, max_tokens)
    pages, log = Pages(bot.SAMPLES), state.Log(tmp_path)
    do_pass(pages, log, caller=spy)
    assert seen and all(TOKEN not in p for p in seen)
    assert TOKEN not in json.dumps(pages.sent) and TOKEN not in log.path.read_text()


def test_validate_refuses_a_payload_holding_a_token():
    q = bot.SAMPLES[0]["question"]
    body = bot.payload(bot.SAMPLES[0], [(q, 0.3)], "Authorization: Token " + TOKEN)
    with pytest.raises(settings.Refuse):
        bot.validate(bot.SAMPLES[0], [(q, 0.3)], body, CFG)


# ------------------------------------------------------------------ the ledger key and selfcheck
LEDGER = "| 238 | other |\n| 239 | B01 forecast bot | B01_START={c} |\n"


def test_require_key_accepts_only_the_exact_build():
    c = "a" * 40
    assert settings.require_key(239, "B01_START", c, LEDGER.format(c=c))
    for text in (LEDGER.format(c="b" * 40), "| 239 | no key |\n", LEDGER.format(c=c) + LEDGER.format(c=c),
                 "| 239 | B01_START=" + c + " B01_START=" + "b" * 40 + " |\n", "| 240 | B01_START=" + c + " |\n",
                 "| 239 | XB01_START=" + c + " |\n"):
        with pytest.raises(settings.Refuse):
            settings.require_key(239, "B01_START", c, text)
    with pytest.raises(settings.Refuse):
        settings.require_key(239, "B01_START", "not-a-hash", LEDGER.format(c=c))


def test_config_block_is_complete_and_safe():
    assert CFG["ledger_row"] == 239 and CFG["network_allowed"] is False and CFG["asknews_enabled"] is False
    assert CFG["targets"][0] == "minibench" and settings.required(CFG)
    assert TOKEN not in json.dumps(CFG) and CFG["token_env"] == "METACULUS_TOKEN"


def test_selfcheck_refuses_without_the_network():
    ok, checks = bot.selfcheck(CFG)
    assert ok and checks["connection_attempts"] == 0
    assert checks["arm_tournament"].startswith("refused")


def test_selfcheck_fails_if_a_start_path_would_run(monkeypatch):
    monkeypatch.setattr(bot, "arm", lambda cfg, mode: "a" * 40)
    ok, checks = bot.selfcheck(CFG)
    assert not ok and checks["arm_tournament"] == "WOULD RUN"


def test_arm_refuses_with_network_allowed_but_no_key(monkeypatch):
    monkeypatch.setattr(settings, "checked_build", lambda: "c" * 40)
    monkeypatch.setattr(settings, "literal_git", lambda *a: "| 239 | B01 waiting |\n")
    with pytest.raises(settings.Refuse):
        bot.arm(CFG | {"network_allowed": True}, "tournament")
    monkeypatch.setattr(settings, "literal_git", lambda *a: "| 239 | B01_START=" + "c" * 40 + " |\n")
    assert bot.arm(CFG | {"network_allowed": True}, "tournament") == "c" * 40
    with pytest.raises(settings.Refuse):                 # the testing area needs its own key
        bot.arm(CFG | {"network_allowed": True}, "testing")


def test_header_refuses_a_changed_setting(tmp_path):
    log = state.Log(tmp_path)
    log.ensure()
    bot.header(log, CFG, "c" * 40, "tournament")
    bot.header(log, CFG, "c" * 40, "tournament")
    with pytest.raises(settings.Refuse):
        bot.header(log, CFG | {"runs": ["gpt_5_4"] * 5}, "c" * 40, "tournament")
    with pytest.raises(settings.Refuse):
        bot.header(log, CFG, "d" * 40, "tournament")


def test_sources_are_https_only():
    brief = "facts\nSOURCES:\n- https://a.example/x\n- http://b.example\n2. https://c.example/y\njunk"
    assert models.sources(brief) == ["https://a.example/x", "https://c.example/y"]
