"""Plan 21 pure calendar, validation and scoring; no file/network access."""
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from math import sqrt
from statistics import mean, median, stdev
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
UTC = timezone.utc
ONE = Decimal(1)
ZERO = Decimal(0)


class Incomplete(ValueError):
    pass


POLICY = dict(start="2016-01-01", result_cutoff="2026-10-31", bar_end="2026-11-24",
              lag_minutes=30, election_sessions_before=3, election_sessions=2,
              election_switch="2024-05-28", fallback_payment_sessions=5,
              account_usd=500, share_cap=99, min_discount_bps=150, market_bps=10, market_min_cents=5,
              judged_fee_usd=0, sensitivity_fee_usd=50, stale_run=5, min_trades=30,
              min_t=2.0, remove_best=3, min_year_trades=3, min_positive_year_pct=60,
              annual_days=365, calibration_seed=21001, calibration_seeds=20,
              calibration_edges_pct=[0, 1, 2, 4], calibration_trades=54,
              calibration_trade_sigma=.06, calibration_year_sigma=.012,
              calibration_tail_chance=.08, calibration_tail_scale=2.0)


def policy(obj):
    if not isinstance(obj, dict) or set(obj) != set(POLICY):
        raise Incomplete("unexpected policy")
    if any(type(obj[k]) is not type(v) or obj[k] != v for k, v in POLICY.items()):
        raise Incomplete("changes require matching scorer and preregistration updates")
    return obj.copy()


def money(x):
    try:
        v = Decimal(str(x))
    except (ValueError, InvalidOperation):
        raise Incomplete("invalid numeric value") from None
    if not v.is_finite():
        raise Incomplete("invalid numeric value")
    return v


def d(x):
    return date.fromisoformat(x)


def stamp(s):
    if not isinstance(s, str) or len(s) != 20 or not s.endswith("Z"):
        raise Incomplete("expected UTC acceptance time to the second")
    out = datetime.fromisoformat(s[:-1] + "+00:00")
    if out.strftime("%Y-%m-%dT%H:%M:%SZ") != s:
        raise Incomplete("noncanonical UTC time")
    return out


def cited(s):
    return isinstance(s, str) and s.startswith("https://") and " " not in s


@dataclass
class Calendar:
    days: list
    opens: list

    @classmethod
    def from_rows(cls, rows):
        pairs = [(d(r["date"]), stamp(r["open_utc"])) for r in rows]
        if not pairs or pairs != sorted(set(pairs)) or len({x[0] for x in pairs}) != len(pairs):
            raise Incomplete("bad exchange calendar order")
        for day, opened in pairs:
            local = opened.astimezone(ET)
            if local.date() != day or local.time() != time(9, 30) or day.weekday() >= 5:
                raise Incomplete("unexpected cash-session open")
        return cls(*map(list, zip(*pairs)))

    def get(self, i):
        if not 0 <= i < len(self.days):
            raise Incomplete("exchange calendar does not cover a needed session")
        return self.days[i]

    def after_stamp(self, s, lag=0, strict=False):
        t = stamp(s) + timedelta(minutes=lag)
        return self.get((bisect_right if strict else bisect_left)(self.opens, t))

    def open_of(self, day):
        i = bisect_left(self.days, day)
        if self.get(i) != day:
            raise Incomplete("not a regular session")
        return self.opens[i]

    def before_day(self, day, n):
        return self.get(bisect_left(self.days, day) - n)

    def after_day(self, day, n=1):
        return self.get(bisect_right(self.days, day) + n - 1)

    def between(self, a, b):
        return self.days[bisect_left(self.days, a):bisect_right(self.days, b)]


def ordinary_ex_date(cal, record_date):
    record = d(record_date)
    if record < d("2017-09-05"):
        return cal.before_day(record, 2)
    if record < d("2024-05-28"):
        return cal.before_day(record, 1)
    return record


@dataclass(frozen=True)
class Bar:
    o: Decimal
    h: Decimal
    l: Decimal
    c: Decimal
    v: Decimal

    @classmethod
    def parse(cls, x):
        b = cls(*(money(x[k]) for k in "ohlcv"))
        if b.l <= 0 or b.h < max(b.o, b.c) or b.l > min(b.o, b.c) or b.v < 0:
            raise Incomplete("invalid daily OHLCV")
        return b

    @property
    def flat_key(self):
        return (self.o, self.h, self.l, self.c)


def stale_dates(days, adjusted, n):
    """Zero-volume bars and identical OHLC runs; a missing session breaks a run."""
    invalid, run, key = set(), [], None
    for day in days:
        b = adjusted.get(day)
        if b is None or b.flat_key != key:
            run = []
        key = None if b is None else b.flat_key
        if b is None:
            continue
        if b.v == 0:
            invalid.add(day)
        run.append(day)
        if len(run) == n:
            invalid.update(run)
        elif len(run) > n:
            invalid.add(day)
    return invalid


def same_tape(primary, check, dates):
    """Paired positive-volume adjusted OHLCV fingerprints under explicit as-of dates."""
    ratios = []
    for day in dates:
        a, b = primary.get(day), check.get(day)
        if not a or not b or min(a.v, b.v) <= 0:
            continue
        # All four price ratios must agree to within 1 bp (same daily movement).
        p = a.o / b.o
        if any(abs((x / y) / p - ONE) > Decimal(".0001")
               for x, y in zip(a.flat_key, b.flat_key)):
            return False
        ratios.append(a.v / b.v)
    return len(ratios) >= 3 and sum(abs(b / a - ONE) < Decimal(".01")
                                    for a, b in zip(ratios, ratios[1:])) / (len(ratios) - 1) >= .98


def judgment(trades, p=POLICY):
    if any(not isinstance(y, int) or not -float("inf") < r < float("inf") for y, r in trades):
        raise Incomplete("invalid trade return")
    xs = sorted(r for _, r in trades)
    n = len(xs)
    m = mean(xs) if xs else None
    med = median(xs) if xs else None
    se = stdev(xs) / sqrt(n) if n > 1 else None
    t = m / se if se else None
    reduced = mean(xs[:-p["remove_best"]]) if n > p["remove_best"] else None
    by_year = defaultdict(list)
    for y, r in trades:
        by_year[y].append(r)
    years = {y: dict(trades=len(xs), mean=mean(xs)) for y, xs in sorted(by_year.items())}
    eligible = [v["mean"] for v in years.values() if v["trades"] >= p["min_year_trades"]]
    good = sum(x > 0 for x in eligible)
    marks = dict(min_trades=n >= p["min_trades"], positive_mean=m is not None and m > 0,
                 t_at_least_2=t is not None and t >= p["min_t"],
                 positive_without_best_three=reduced is not None and reduced > 0,
                 positive_median=med is not None and med > 0,
                 positive_year_share=bool(eligible) and 100 * good >= p["min_positive_year_pct"] * len(eligible))
    return dict(n=n, mean=m, median=med, t=t, mean_without_best_three=reduced, years=years,
                positive_eligible_years=good, eligible_years=len(eligible), marks=marks, passes=all(marks.values()))


@dataclass
class Event:
    row: dict
    entry: date
    no_trade: str | None
    mode: str
    terminal: date
    exit_candidates: dict
    entry_floor: Decimal

    @property
    def accession(self):
        return self.row["accession"]

    @property
    def required(self):
        return set() if self.no_trade else {self.entry, *self.exit_candidates}

    @property
    def market_end(self):
        return max(self.required or {self.entry})

    @property
    def actions_through(self):
        expiry = self.row.get("final_expiry") or self.row["initial_expiry"]
        return max(self.terminal, self.market_end, d(expiry))


def schedule(row, cal, p=POLICY):
    """Filing-only planning. All potential market exit dates are mandatory, before seeing prices."""
    lag = p["lag_minutes"]
    accepted = stamp(row["acceptance_utc"])
    entry = cal.after_stamp(row["acceptance_utc"], lag)
    cutoff = datetime.combine(d(p["result_cutoff"]) + timedelta(days=1), time(), ET)
    result = row["result"] if row["known_terminal_by_cutoff"] else None
    expiry = latest = d(row["initial_expiry"])
    entry_floor = money(row["floor"])
    post_entry_prices = []
    exits = defaultdict(list)
    entry_time = cal.open_of(entry)
    for am in row["amendments"]:
        t = stamp(am["acceptance_utc"])
        if not accepted < t or t >= cutoff:
            continue
        effective = t + timedelta(minutes=lag)
        if am.get("new_expiry"):
            latest = d(am["new_expiry"])
            if effective <= entry_time:
                expiry = latest
        if am.get("new_floor"):
            f = money(am["new_floor"])
            if f <= ZERO:
                raise Incomplete("bad revised price")
            if effective <= entry_time:
                entry_floor = f
            else:
                post_entry_prices.append((f, am))
    max_entry = entry_floor * (ONE - money(p["min_discount_bps"]) / 10000)
    no = None
    wait = p["election_sessions_before"] if entry < d(p["election_switch"]) else p["election_sessions"]
    if entry >= cal.before_day(expiry, wait):
        no = "election_cutoff"
    if result and stamp(result["acceptance_utc"]) + timedelta(minutes=lag) <= entry_time:
        no = "outcome_already_known"
    if no:
        return Event(row, entry, no, "no_trade", entry, {}, entry_floor)
    for f, am in post_entry_prices:
        if f < max_entry or row["corporate_actions"]:
            exits[cal.after_stamp(am["acceptance_utc"], lag)].append(("cut", f, am["accession"]))
    if not result:
        terminal = cal.after_day(latest)
        mode = "unresolved_fallback"
        exits[terminal].append(("forced", None, None))
    elif result["status"] == "withdrawn":
        terminal = cal.after_stamp(result["acceptance_utc"], lag)
        mode = "withdrawn"
        exits[terminal].append(("forced", None, result["accession"]))
    elif result["status"] == "completed":
        ex = d(row["final_expiry"])
        if latest != ex:
            raise Incomplete("final expiry differs from accession-linked amendment history")
        terminal = d(result["payment_date"]) if result.get("payment_date") else cal.after_day(ex, p["fallback_payment_sessions"])
        if terminal < ex:
            raise Incomplete("payment date precedes final expiry")
        mode = "completed"
        if row["priority"] == "no" and money(result["proration"]) < ONE:
            t = cal.after_stamp(result["acceptance_utc"], strict=True)
            exits[t].append(("remainder", None, result["accession"]))
            terminal = max(terminal, t)
        # A reduction announced in the results counts as an exit only if explicitly a
        # new offer-price amendment, not merely a lawful clearing price within the range.
        exits = {k: v for k, v in exits.items()
                 if k <= ex or any(x[0] == "remainder" for x in v)}
        exits = {k: [x for x in v if k <= ex or x[0] == "remainder"] for k, v in exits.items()}
    else:
        raise Incomplete("invalid matched outcome")
    exits = {k: v for k, v in exits.items() if entry < k <= terminal and v}
    if terminal <= entry:
        raise Incomplete("nonpositive holding period")
    return Event(row, entry, None, mode, terminal, exits, entry_floor)


def action_basis(e, end):
    """Share conversion and dated cash earned per original share."""
    ratio, earned = ONE, []
    for a in e.row["corporate_actions"]:
        if not e.entry < d(a["date"]) <= end:
            continue
        if a["kind"] == "split":
            ratio *= money(a["ratio"])
        elif a["kind"] == "cash_distribution":
            earned.append((d(a["payment_date"]), ratio * money(a["cash_per_share"])))
        else:
            raise Incomplete("unresolved corporate action")
    return ratio, earned


def unit_basis(e, end):
    ratio, earned = action_basis(e, end)
    return ratio, sum((amt for _, amt in earned), ZERO)


def market_cost(open_price, p=POLICY):
    """Per-share friction on any market fill; tender payments are not fills."""
    return max(open_price * money(p["market_bps"]) / 10000, money(p["market_min_cents"]) / 100)


def shares_at(open_price, p=POLICY, budget=None):
    limit = money(p["account_usd"]) if budget is None else min(money(p["account_usd"]), money(budget))
    return max(0, min(p["share_cap"], int(limit // (open_price + market_cost(open_price, p)))))


def simulate(e, bars, fee=0, p=POLICY, budget=None):
    """Only call after the one-shot lock. Returns trade or counted no-trade reason."""
    if e.no_trade:
        return None, e.no_trade
    entry = bars[e.entry].o
    if entry > e.entry_floor * (ONE - money(p["min_discount_bps"]) / 10000):
        return None, "entry_discount"
    shares = shares_at(entry, p, budget)
    if shares < 1:
        return None, "zero_affordable_shares"
    invested = shares * (entry + market_cost(entry, p))
    tender = ZERO
    sold = ZERO
    used_fee = ZERO
    exit_accession = None
    last = e.terminal
    outcome = e.mode
    for day, specs in sorted(e.exit_candidates.items()):
        ratio, earned = action_basis(e, day)
        trigger = next((s for s in specs if s[0] == "forced" or (s[0] == "cut" and s[1] * ratio < entry)), None)
        if trigger:
            o = bars[day].o
            sold = shares * ratio * (o - market_cost(o, p))
            last, outcome, exit_accession = day, ("price_cut" if trigger[0] == "cut" else e.mode), trigger[2]
            break
    else:
        result = e.row["result"]
        if e.mode != "completed" or not result:
            raise Incomplete("no realizable exit")
        expiry = d(e.row["final_expiry"])
        ratio, _ = unit_basis(e, expiry)
        actual = shares * ratio
        if actual != int(actual):
            raise Incomplete("unresolved fractional share disposition")
        factor = ONE if e.row["priority"] == "yes" else money(result["proration"])
        if e.row["priority"] == "yes" and actual >= 100:
            raise Incomplete("split invalidates odd-lot eligibility")
        filled = int(actual * factor)
        tender = filled * money(result["price"])
        used_fee = money(fee)
        exit_accession = result["accession"]
        if filled < actual:
            day = next(day for day, options in e.exit_candidates.items() if any(x[0] == "remainder" for x in options))
            next_ratio, _ = unit_basis(e, day)
            o = bars[day].o
            sold = (actual - filled) * next_ratio / ratio * (o - market_cost(o, p))
        # After tender expiry only an unaccepted remainder can earn a distribution.
        _, earned = action_basis(e, expiry)
        if filled < actual and day > expiry:
            _, extended = action_basis(e, day)
            earned += [(pay, amt * (actual - filled) / actual) for pay, amt in extended[len(earned):]]
    days = (last - e.entry).days
    if days <= 0:
        raise Incomplete("return annualization requires positive calendar days")
    distributions = defaultdict(lambda: ZERO)
    for pay, amount in earned:
        distributions[pay] += amount * shares
    principal = tender + sold - used_fee
    payout = principal + sum(distributions.values(), ZERO)
    net = (payout - invested) / invested
    return dict(accession=e.accession, cik=e.row["cik"], entry=e.entry.isoformat(), exit=last.isoformat(),
                year=d(e.row["filing_date"]).year, offer_type=e.row["offer_type"], outcome=outcome,
                exit_accession=exit_accession, shares=shares, investment=float(invested), fee=float(used_fee),
                cash_payout=float(payout), balance_delta_exact=str(payout - invested),
                principal_delta_exact=str(principal - invested),
                distribution_credits={pay.isoformat():str(amt) for pay, amt in sorted(distributions.items())},
                net_return=float(net), annualized_linear=float(net * p["annual_days"] / days), days=days), None


def peak_open(trades):
    days = defaultdict(int)
    for t in trades:
        days[d(t["entry"])] += 1
        days[d(t["exit"]) + timedelta(days=1)] -= 1
    peak = active = 0
    for day in sorted(days):
        active += days[day]
        peak = max(peak, active)
    return peak


def single_account(events, tapes, p=POLICY):
    cash, release = money(p["account_usd"]), None
    delta, skipped, trades, receivable = ZERO, Counter(), [], defaultdict(lambda: ZERO)
    for e in sorted(events, key=lambda x: (stamp(x.row["acceptance_utc"]), x.accession)):
        if e.no_trade:
            skipped[e.no_trade] += 1
            continue
        if release is not None and e.entry <= release:
            skipped["cash_tied_up"] += 1
            continue
        cash += delta
        delta = ZERO
        for pay in sorted(due for due in receivable if due <= e.entry):
            cash += receivable.pop(pay)
        t, skip = simulate(e, tapes[e.accession], p["judged_fee_usd"], p, budget=cash)
        if t is None:
            skipped[skip] += 1
            continue
        delta, release = money(t["principal_delta_exact"]), d(t["exit"])
        for pay, amt in t["distribution_credits"].items():
            receivable[d(pay)] += money(amt)
        trades.append(t)
    cash += delta + sum(receivable.values(), ZERO)
    return dict(initial_cash=p["account_usd"], final_cash=float(cash), trades=trades, no_trade=dict(skipped),
                return_on_initial_cash=float(cash / money(p["account_usd"]) - ONE))


def report(events, tapes, meta, p=POLICY):
    out = {}
    for label, select, fee in (
        ("judged", lambda e: e.row["priority"] == "yes" and e.mode != "unresolved_fallback"
         and e.row["known_terminal_by_cutoff"], p["judged_fee_usd"]),
        ("fee_50_shown_only", lambda e: e.row["priority"] == "yes" and e.row["known_terminal_by_cutoff"], p["sensitivity_fee_usd"]),
        ("without_form_wording_shown_only", lambda e: e.row["priority"] == "yes"
         and e.mode != "unresolved_fallback" and e.row["known_terminal_by_cutoff"]
         and not e.row.get("form_wording"), p["judged_fee_usd"]),
        ("without_div_source_ir_shown_only", lambda e: e.row["priority"] == "yes"
         and e.mode != "unresolved_fallback" and e.row["known_terminal_by_cutoff"]
         and not e.row.get("div_source_ir"), p["judged_fee_usd"]),
        ("no_priority_treatment_at_99_shares_shown_only", lambda e: e.row["priority"] == "no", p["judged_fee_usd"]),
        ("unresolved_fallback_shown_only", lambda e: e.row["priority"] == "yes" and not e.row["known_terminal_by_cutoff"], p["judged_fee_usd"]),
    ):
        trades, no = [], Counter()
        for e in filter(select, events):
            t, skip = simulate(e, tapes.get(e.accession, {}), fee, p)
            if t:
                trades.append(t)
            else:
                no[skip] += 1
        by_type = {}
        for kind in ("fixed", "dutch_auction"):
            rs = [t["net_return"] for t in trades if t["offer_type"] == kind]
            by_type[kind] = dict(n=len(rs), mean=mean(rs) if rs else None)
        out[label] = dict(trades=trades, no_trade=dict(no), by_offer_type=by_type,
                          mean_annualized_linear=mean(t["annualized_linear"] for t in trades) if trades else None)
        if label == "judged":
            out[label]["judgment"] = judgment([(t["year"], t["net_return"]) for t in trades], p)
    shown = [e for e in events if e.row["priority"] == "yes" and e.row["known_terminal_by_cutoff"]]
    return dict(metadata=meta, arms=out,
                form_wording_flagged_filings=sum(bool(e.row.get("form_wording")) for e in shown),
                div_source_ir_flagged_filings=sum(bool(e.row.get("div_source_ir")) for e in shown),
                peak_holdings_open_shown_only=peak_open(out["judged"]["trades"]),
                single_500_account_shown_only=single_account(shown, tapes, p))
