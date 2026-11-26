"""Plan 23 engine: IPO fast-track stand-in, buy the first day's close, sell the fifth session's close.

Pure functions. No network, no file reads except the small loaders at the bottom, which take explicit paths.
Nothing here prints a price. Every number comes from the config block replay_23_plan in config/thresholds.yaml.
authorize() is the gate for collection, freeze and scoring: it needs the lead's approval commit.
"""
import bisect, csv, datetime as dt, hashlib, io, json, math, os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONFIG = os.path.join(ROOT, "config", "thresholds.yaml")     # fixed: no environment override (gate audit B1)
PLAN_NAME = "PREREG_23_ipo_fast_track.md"
PINNED_NAMES = (PLAN_NAME, "common_23.py", "fetch_23.py", "score_23.py", "report_23.py", "calibrate_23.py", "test_23.py")
CONFIG_PIN = "thresholds.yaml#replay_23_plan"
APPROVAL = "research_rig/APPROVAL_23.md"
APPROVAL_LINE = re.compile(r"(?m)^Approved by the lead: plan 23, one collection and one scored run, freeze commit ([0-9a-f]{40})\.$")


def config_block_sha256(raw):
    import yaml
    return hashlib.sha256(json.dumps(yaml.safe_load(raw)["replay_23_plan"]["value"], sort_keys=True,
                                     default=str).encode()).hexdigest()


def authorize(commit, root=ROOT, config=None):
    """Refuse collection, freeze and scoring unless HEAD is the lead's approval commit.
    The approval commit must: be HEAD with no tracked change; add research_rig/APPROVAL_23.md holding the exact
    approval line, which names the freeze commit; descend from that freeze commit, where the approval file did not
    exist; and carry every plan 23 file and the replay_23_plan block byte for byte as frozen, matching
    research_rig/PINNED_23.json. Returns the freeze commit."""
    def git(*a, ok=False):
        r = subprocess.run(["git", "-C", root, *a], capture_output=True)
        if r.returncode and not ok:
            raise Refused("P23_NOT_APPROVED git " + a[0])
        return r
    def show(c, path):
        return git("show", f"{c}:{path}").stdout
    if not re.fullmatch(r"[0-9a-f]{40}", commit or ""):
        raise Refused("P23_NOT_APPROVED no approval commit given")
    env = sorted(k for k in os.environ if k.startswith("P23_"))
    if env:                                            # no P23_ variable may steer a judged step
        raise Refused("P23_NOT_APPROVED environment " + ",".join(env))
    config = CONFIG if config is None else config
    if os.path.realpath(config) != os.path.realpath(os.path.join(root, "config", "thresholds.yaml")):
        raise Refused("P23_NOT_APPROVED config path")
    if git("rev-parse", "HEAD").stdout.decode().strip() != commit:
        raise Refused("P23_NOT_APPROVED HEAD is not the approval commit")
    if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        raise Refused("P23_NOT_APPROVED tracked files changed")
    r = git("show", f"{commit}:{APPROVAL}", ok=True)
    m = APPROVAL_LINE.search(r.stdout.decode("utf-8", "replace")) if not r.returncode else None
    if not m:
        raise Refused("P23_NOT_APPROVED " + APPROVAL)
    frozen = m.group(1)
    if frozen == commit or git("merge-base", "--is-ancestor", frozen, commit, ok=True).returncode:
        raise Refused("P23_NOT_APPROVED freeze commit is not an ancestor")
    if not git("cat-file", "-e", f"{frozen}:{APPROVAL}", ok=True).returncode:
        raise Refused("P23_NOT_APPROVED approval file already in the freeze commit")
    pins = json.loads(show(commit, "research_rig/PINNED_23.json"))
    for name in PINNED_NAMES:
        path = "research_rig/" + name
        h = sha256_bytes(show(commit, path))
        if h != pins.get(name) or h != sha256_bytes(show(frozen, path)) or h != sha256_file(os.path.join(root, path)):
            raise Refused("P23_NOT_APPROVED pin " + name)
    cfg = "config/thresholds.yaml"
    h = config_block_sha256(show(commit, cfg))
    with open(config, "rb") as fh:
        on_disk = config_block_sha256(fh.read())
    if h != pins.get(CONFIG_PIN) or h != config_block_sha256(show(frozen, cfg)) or h != on_disk:
        raise Refused("P23_NOT_APPROVED pin " + CONFIG_PIN)
    if not re.search(rb"(?m)^Status FROZEN\.", show(commit, "research_rig/" + PLAN_NAME)):
        raise Refused("P23_NOT_APPROVED plan not frozen")
    if not re.search(rb"(?m)^\| 160 \|[^\n]+PREREG_23_ipo_fast_track", show(commit, "research_rig/TRIAL_LEDGER.md")):
        raise Refused("P23_NOT_APPROVED ledger row 160")
    return frozen


def load_config(path=CONFIG):
    import yaml
    with open(path, "rb") as fh:
        p = yaml.safe_load(fh)["replay_23_plan"]["value"]
    validate(p)
    return p


KEYS = {"first_pricing", "last_pricing", "bar_end", "bar_feed", "bar_adjustment", "judged_ratio_min", "band_ratio_min",
        "near_ratio_min", "near_ratio_max", "first_bar_window_bdays", "prior_bar_gap_bdays", "prior_listing_days", "fetch_after_days", "asof_days", "spy_start", "exit_session",
        "exit_window_sessions", "flat_run", "judged_bps", "shown_bps", "no_auction_bps", "min_trades", "min_t_stat", "drop_best",
        "min_year_trades", "min_year_share_pct", "recent_from", "mega_usd", "calibration_seed", "calibration_seeds",
        "calibration_edges_pct", "calibration_trade_sigma", "calibration_year_sigma", "calibration_spy_sigma",
        "calibration_beta", "calibration_tail_df", "ledger_row", "queue_row"}


class Refused(Exception):
    """A fixed-code refusal. The message holds a code and a path or key, never a price."""


def validate(p):
    if set(p) != KEYS:
        raise Refused(f"P23_CONFIG_KEYS {sorted(set(p) ^ KEYS)}")
    ok = (str(p["first_pricing"]) < str(p["last_pricing"]) < str(p["bar_end"]) <= "2026-11-24"
          and p["bar_feed"] == "sip" and p["bar_adjustment"] == "raw"
          and 0 < p["near_ratio_min"] < p["band_ratio_min"] < p["judged_ratio_min"] == p["near_ratio_max"]
          and str(p["spy_start"]) < str(p["first_pricing"]) and 0 < p["asof_days"] < p["fetch_after_days"]
          and 1 <= p["first_bar_window_bdays"] < p["prior_bar_gap_bdays"] and 1 < p["exit_session"] < p["exit_window_sessions"]
          and p["flat_run"] >= 2 and 0 <= p["judged_bps"] < p["shown_bps"] < p["no_auction_bps"] < 10000
          and p["min_trades"] >= 1 and p["drop_best"] >= 0 and 0 < p["min_year_share_pct"] <= 100)
    if not ok:
        raise Refused("P23_CONFIG_VALUES")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    with open(path, "rb") as fh:
        return sha256_bytes(fh.read())


# ------------------------------------------------------------------------------------------------ events (no prices)
def breakpoint_on(bps, day):
    """The 98% breakpoint of the latest chart dated on or before `day` (ISO strings). bps: list of (date, value)."""
    best = None
    for d, v in bps:
        if d <= day and (best is None or d > best[0]):
            best = (d, v)
    if best is None:
        raise Refused(f"P23_NO_BREAKPOINT {day}")
    return best


def group_of(ratio, p):
    if ratio >= p["judged_ratio_min"]:
        return "judged"
    if ratio >= p["band_ratio_min"]:
        return "band_1_0_to_1_5"
    if ratio >= p["near_ratio_min"]:
        return "near_0_67_to_1_0"
    return None


# What the kept 424B4 offers, from its cover text (the parse cache of the row 37 build). Offered security first,
# then the cover title. Only common shares (any class, including subordinate voting shares and common shares of
# beneficial interest) and American depositary shares count. Preferred stock, units, notes and any other
# depositary shares are listed and left out. A cover that names none of these refuses, so a person reads it.
_OFFER = re.compile(r"(?:we are offering|are offering|is offering|we are selling|is selling|being offered|initial public offering of|"
                    r"this is (?:an|the) (?:initial )?(?:public )?offering of)\s+(?:[\d,]+\s+)?(?:shares of\s+)?(?:our\s+|its\s+)?"
                    r"([\w%.,\"' -]{0,80}?)(american depositary shares|common stock|common shares|ordinary shares|"
                    r"subordinate voting shares|preferred stock|preferred shares|depositary shares|units|notes)", re.I)
_TITLE = re.compile(r"[\d,]{5,}\s+(?:shares\s+)?(?:[\w.,&' -]{0,80}?)\s*(american depositary shares|(?:class [a-z0-9]+ )?common stock|"
                    r"common shares|ordinary shares|subordinate voting shares|[\w.%]*\s*(?:series [a-z]\s+)?(?:mandatory convertible\s+)?preferred stock|units)", re.I)
_COMMON = ("american depositary shares", "common stock", "common shares", "ordinary shares", "subordinate voting shares")


def classify_security(cover):
    """Returns 'common', 'ads', 'not_common' or 'unknown' for the security a 424B4 cover offers."""
    text = re.sub(r"\s+", " ", cover or "")
    offer, title = _OFFER.search(text), _TITLE.search(text)
    offer = offer.group(offer.lastindex).lower() if offer else ""
    title = title.group(title.lastindex).lower() if title else ""
    if "preferred" in title:
        return "not_common"
    lead = offer or title
    if not lead:
        m = re.search(r"shares of (?:our )?(?:class [a-z0-9]+ )?common stock", text, re.I)
        return "common" if m else "unknown"
    if lead == "american depositary shares":
        return "ads"
    if any(lead.endswith(k) for k in _COMMON):
        return "common"
    if any(w in lead for w in ("preferred", "units", "notes", "depositary shares")):
        return "not_common"
    return "unknown"


def security_map(snips_path, wanted):
    """accession -> class for the accessions in `wanted`, streamed from snips.jsonl.gz. Covers only."""
    import gzip
    out = {}
    with gzip.open(snips_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if d["accession"] in wanted:
                out[d["accession"]] = classify_security(d.get("_cover", ""))
    return out


def select_events(ipos, bps, p, security=None):
    """Rows of ipos.csv priced first_pricing..last_pricing, us_screen_guess yes, a stand-in value present, with ratio
    = value / 98% breakpoint of the latest chart dated on or before the pricing date. Judged: ratio >= judged_ratio_min.
    Shown only: the two lower bands. Uses the prospectus only; no bar is read here.
    security: accession -> class from classify_security. A row that is not common shares or ADS is kept in the list
    with status not_common_security (left out before the lock); a row with no class or 'unknown' refuses."""
    out = []
    for r in ipos:
        d = r["pricing_date"]
        if not (str(p["first_pricing"]) <= d <= str(p["last_pricing"])):
            continue
        if r["us_screen_guess"] != "yes" or not r["standin_value_usd"] or r.get("excluded"):
            continue
        value = float(r["standin_value_usd"])
        chart, bp = breakpoint_on(bps, d)
        ratio = value / bp
        g = group_of(ratio, p)
        if g is None:
            continue
        check = r.get("shares_check", "")
        out.append(dict(accession=r["accession"], cik=r["cik"], company=r["company"], ticker=r["ticker"].strip().upper(),
                        pricing_date=d, filing_date=r["date_filed"],
                        prospectus_date=d if r.get("pricing_date_how", "") != "filing_date_fallback" else "",
                        offer_price=r["offer_price"], standin_value_usd=int(round(value)),
                        shares_after=r.get("shares_out_after", ""), shares_classes=r.get("shares_out_after_classes", ""),
                        shares_check=check,
                        breakpoint_chart=chart, breakpoint_usd=int(bp), ratio=round(ratio, 6), group=g,
                        mega=value > p["mega_usd"], security="",
                        status="" if check.startswith("verified") else "shares_unverified"))
    if security is not None:
        for e in out:
            cls = security.get(e["accession"], "unknown")
            if cls == "unknown":
                raise Refused(f"P23_SECURITY_UNKNOWN {e['accession']}")
            e["security"] = cls
            if cls not in ("common", "ads"):
                e["status"] = "not_common_security"      # comes before shares_unverified
    out.sort(key=lambda e: (e["pricing_date"], e["accession"]))
    return out


def around(sessions, day, k):
    """(k-th session strictly before `day`, k-th session strictly after `day`); None where the calendar ends."""
    i = bisect.bisect_left(sessions, day)
    j = bisect.bisect_right(sessions, day)
    return (sessions[i - k] if i - k >= 0 else None), (sessions[j + k - 1] if j + k - 1 < len(sessions) else None)


def resolve_dates(events, dates_by_event, sessions, p):
    """Dates, volume and the flat flag only; no price is used as a number.
    dates_by_event[accession] = (sorted dates of every bar in the file, set of dates that are real trades by clean()).
    One rule for every event, keyed on the 424B4 filing date F (lead's ruling on audit pass 1, B2):
      - first trading day = the first bar (any bar) from the first_bar_window_bdays-th session before F to the
        first_bar_window_bdays-th session after F (F itself counts when it is a session);
      - prior_bars (a reused ticker or another security): any bar on or before the session that is more than
        prior_bar_gap_bdays sessions before F; only this leaves an event out as a reused ticker;
      - bars_before_window: a bar between that point and the window, so the window's first bar may not be the
        first day; listed and left out (a case the ruling did not name);
      - late_first_bar: no bar in the window; no_bar: no bar at all from the window on.
    The prospectus's own date (prospectus_date) is recorded but does not decide.
    An event that already has a status from selection (not_common_security, shares_unverified) keeps it.
    Then: duplicate (count once: one listing per CIK and per (ticker, first bar date), earliest accession kept),
    entry_not_real_bar (first bar zero volume or in a flat run: left out), refused_no_exit_bar (real entry, no real
    bar in sessions 2..exit_window_sessions: a refusal of the run), ok."""
    w, g = p["first_bar_window_bdays"], p["prior_bar_gap_bdays"]
    seen_cik, seen_tk = set(), set()
    out = []
    for e in events:
        e = dict(e)
        e["first_trade_date"] = ""
        if e.get("status"):
            out.append(e)
            continue
        ds, real = dates_by_event.get(e["accession"], ([], set()))
        f = e["filing_date"]
        lo, hi = around(sessions, f, w)
        prior_cut = around(sessions, f, g + 1)[0]          # the session more than g sessions before F
        if lo is None or hi is None or prior_cut is None:
            raise Refused(f"P23_CALENDAR_SHORT {e['accession']}")
        inside = [d for d in ds if lo <= d <= hi]
        if not e["ticker"]:
            e["status"] = "no_ticker"
        elif any(d <= prior_cut for d in ds):
            e["status"] = "prior_bars"
        elif any(prior_cut < d < lo for d in ds):
            e["status"] = "bars_before_window"
        elif not inside:
            e["status"] = "late_first_bar" if any(d > hi for d in ds) else "no_bar"
        else:
            first = inside[0]
            e["first_trade_date"] = first
            if e["cik"] in seen_cik or (e["ticker"], first) in seen_tk:
                e["status"] = "duplicate"
            elif first not in real:
                e["status"] = "entry_not_real_bar"
            else:
                win = window(sessions, first, p)
                e["status"] = "ok" if any(d in real for d in win[1:]) else "refused_no_exit_bar"
            if e["status"] in ("ok", "refused_no_exit_bar"):
                seen_cik.add(e["cik"]); seen_tk.add((e["ticker"], first))
        out.append(e)
    return out


def window(sessions, first, p):
    """Sessions 1..exit_window_sessions, session 1 being the first trading day."""
    i = sessions.index(first) if first in sessions else None
    if i is None:
        raise Refused(f"P23_FIRST_DAY_NOT_A_SESSION {first}")
    w = sessions[i:i + p["exit_window_sessions"]]
    return w


# --------------------------------------------------------------------------------------------- bars and trades
def clean(bars, run):
    """Drop bars that are not real trades: zero volume, or inside a run of `run` or more bars in a row with identical
    open, high, low and close (the stock plans' flat-run scan, common_14.not_trades). bars: date-sorted dicts with
    keys d, o, h, l, c, v. Returns a dict date -> bar."""
    bad = {b["d"] for b in bars if not (b["v"] or 0) > 0}
    i = 0
    while i < len(bars):
        j = i
        key = (bars[i]["o"], bars[i]["h"], bars[i]["l"], bars[i]["c"])
        while j + 1 < len(bars) and (bars[j + 1]["o"], bars[j + 1]["h"], bars[j + 1]["l"], bars[j + 1]["c"]) == key:
            j += 1
        if j - i + 1 >= run:
            bad |= {bars[t]["d"] for t in range(i, j + 1)}
        i = j + 1
    return {b["d"]: b for b in bars if b["d"] not in bad}


def exit_day(good, win, p):
    """The fifth session's close if it is a real bar; else the first real bar in sessions 6..8; else the last real
    bar in sessions 2..4. None if there is no real bar in sessions 2..8."""
    k = p["exit_session"] - 1
    if win[k:k + 1] and win[k] in good:
        return win[k], "fifth_session"
    for d in win[k + 1:]:
        if d in good:
            return d, "later_inside_window"
    for d in reversed(win[1:k]):
        if d in good:
            return d, "last_close_before"
    return None, "none"


def net(entry, exit_, bps):
    c = bps / 10000.0
    return exit_ / entry - 1 - c * (1 + exit_ / entry)


def trade(e, bars, spy, sessions, p):
    """One event. Returns a dict with judged and shown figures, or a dict with status when no trade can be made.
    spy: date -> raw SPY bar (read as it is)."""
    good = clean(bars, p["flat_run"])
    first = e["first_trade_date"]
    win = window(sessions, first, p)
    if first not in good:
        raise Refused(f"P23_ENTRY_NOT_REAL_AFTER_FREEZE {e['accession']}")      # the freeze already left these out
    d_exit, how = exit_day(good, win, p)
    if d_exit is None:
        raise Refused(f"P23_NO_EXIT_AFTER_FREEZE {e['accession']}")             # the freeze already refused these
    a, b = good[first]["c"], good[d_exit]["c"]
    if first not in spy or d_exit not in spy:
        raise Refused(f"P23_SPY_MISSING {first} {d_exit}")
    spy_ret = spy[d_exit]["c"] / spy[first]["c"] - 1
    out = dict(accession=e["accession"], status="traded", group=e["group"], year=first[:4], pricing_date=e["pricing_date"],
               entry_date=first, exit_date=d_exit, exit_how=how, gross=b / a - 1,
               net_judged=net(a, b, p["judged_bps"]), net_shown=net(a, b, p["shown_bps"]),
               net_no_auction=net(a, b, p["no_auction_bps"]), spy=spy_ret,
               mega=bool(e["mega"]))
    out["excess_judged"] = out["net_judged"] - spy_ret
    offer = float(e["offer_price"]) if e.get("offer_price") else None
    out["first_close_vs_offer"] = "" if offer is None else ("below" if a < offer else "at_or_above")
    d2 = win[1] if len(win) > 1 else None
    if d2 and d2 in good and d2 <= d_exit and d2 != d_exit:
        out["net_second_open"] = net(good[d2]["o"], b, p["judged_bps"])
    else:
        out["net_second_open"] = None
    return out


# ------------------------------------------------------------------------------------------------------- marks
def mean(x):
    return sum(x) / len(x) if x else float("nan")


def tstat(x):
    n = len(x)
    if n < 2:
        return float("nan")
    m = mean(x)
    sd = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1))
    return m / (sd / math.sqrt(n)) if sd > 0 else float("nan")


def median(x):
    s = sorted(x)
    n = len(s)
    if not n:
        return float("nan")
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def gt(v, lim):
    """Strictly above; NaN never passes."""
    return v == v and v > lim


def judge(trades, p, key="net_judged"):
    """The eight marks on judged trades. Undefined never passes."""
    x = [t[key] for t in trades]
    ex = [t["excess_judged"] for t in trades]
    n = len(x)
    drop = sorted(x)[:max(0, n - p["drop_best"])]
    years = {}
    for t in trades:
        years.setdefault(t["year"], []).append(t[key])
    counted = {y: v for y, v in years.items() if len(v) >= p["min_year_trades"]}
    pos_years = [y for y, v in counted.items() if mean(v) > 0]
    share = 100.0 * len(pos_years) / len(counted) if counted else float("nan")
    recent = [t[key] for t in trades if t["pricing_date"] >= str(p["recent_from"])]
    m = dict(
        n_trades=n >= p["min_trades"],
        mean_above_zero=gt(mean(x), 0),
        t_stat=(tstat(x) == tstat(x) and tstat(x) >= p["min_t_stat"]),
        mean_without_best=gt(mean(drop), 0) if drop else False,
        median_above_zero=gt(median(x), 0),
        year_share=(share == share and share >= p["min_year_share_pct"]),
        excess_vs_spy=gt(mean(ex), 0) and (tstat(ex) == tstat(ex) and tstat(ex) >= p["min_t_stat"]),
        recent_mean=gt(mean(recent), 0) if recent else False)
    figures = dict(n=n, mean=mean(x), t=tstat(x), mean_without_best=mean(drop) if drop else float("nan"),
                   median=median(x), years_counted=sorted(counted), years_positive=sorted(pos_years),
                   year_share_pct=share, excess_mean=mean(ex), excess_t=tstat(ex), recent_n=len(recent),
                   recent_mean=mean(recent))
    return dict(marks=m, passed=all(m.values()), figures=figures)


def summary(xs):
    return dict(n=len(xs), mean=mean(xs), median=median(xs), t=tstat(xs))


def shown(trades, p):
    j = [t for t in trades if t["group"] == "judged"]
    band = [t for t in trades if t["group"] == "band_1_0_to_1_5"]
    near = [t for t in trades if t["group"] in ("band_1_0_to_1_5", "near_0_67_to_1_0")]
    by_year = {}
    for t in j:
        by_year.setdefault(t["year"], []).append(t["net_judged"])
    return dict(
        second_day_open=summary([t["net_second_open"] for t in j if t["net_second_open"] is not None]),
        band_1_0_to_1_5=summary([t["net_judged"] for t in band]),
        near_0_67_to_1_5=summary([t["net_judged"] for t in near]),
        by_year={y: summary(v) for y, v in sorted(by_year.items())},
        at_shown_bps=summary([t["net_shown"] for t in j]),
        at_no_auction_bps=summary([t["net_no_auction"] for t in j]),
        without_mega=summary([t["net_judged"] for t in j if not t["mega"]]),
        first_close_below_offer=summary([t["net_judged"] for t in j if t["first_close_vs_offer"] == "below"]),
        first_close_at_or_above_offer=summary([t["net_judged"] for t in j if t["first_close_vs_offer"] == "at_or_above"]),
        exit_how={k: sum(1 for t in j if t["exit_how"] == k) for k in ("fifth_session", "later_inside_window", "last_close_before")})


# ---------------------------------------------------------------------------------------------------- loaders
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_breakpoints(path):
    return sorted((r["ranking_date"], float(r["bp98_usd"])) for r in read_csv(path))


EVENT_FIELDS = ["accession", "cik", "company", "ticker", "pricing_date", "filing_date", "prospectus_date", "offer_price",
                "standin_value_usd", "shares_after", "shares_classes", "shares_check",
                "breakpoint_chart", "breakpoint_usd", "ratio", "group", "mega", "security", "first_trade_date", "status"]


def events_csv_bytes(events):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=EVENT_FIELDS, lineterminator="\n")
    w.writeheader()
    for e in events:
        w.writerow({k: e.get(k, "") for k in EVENT_FIELDS})
    return buf.getvalue().encode()


def parse_events(raw):
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    for r in rows:
        r["mega"] = r["mega"] == "True"
    return rows


def bars_from_json(raw):
    """Alpaca daily bars as stored by fetch_23 (a JSON list). Returns date-sorted dicts d, o, h, l, c, v."""
    out = [dict(d=b["t"][:10], o=b["o"], h=b["h"], l=b["l"], c=b["c"], v=b["v"]) for b in json.loads(raw)]
    out.sort(key=lambda b: b["d"])
    return out


def real_dates_from_json(raw, run, bar_end):
    """For the pre-lock checks: every bar date up to bar_end, and the dates that are real trades (volume above zero
    and not in a flat run). Open, high, low and close are compared for equality only, never used as numbers.
    The same bar_end cut as the scorer, so the flat-run scan sees the same bars before and after the lock."""
    bars = sorted(({"d": b["t"][:10], "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
                   for b in json.loads(raw) if b["t"][:10] <= str(bar_end)), key=lambda b: b["d"])
    return [b["d"] for b in bars], set(clean(bars, run))


def dates_from_json(raw):
    """Dates only, for the pre-lock checks. Reads the t field and nothing else."""
    return sorted({b["t"][:10] for b in json.loads(raw)})
