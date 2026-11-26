"""Draft Plan 63 dispersion kernel. No packet loader, CLI, or path lookup."""
from collections import Counter
from bisect import bisect_left
from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from math import isfinite
from statistics import median, stdev

from count_63 import CUTOFF, HOLDS, SABA, candidates, intersects_target, placebo_span, select, target_intervals
from score_63 import Stop, filer_days


MAD_FACTOR = 1.482602218505602


@dataclass(frozen=True)
class Leg:
    # Only the two approved endpoint closes, on the raw split basis.
    identity: str
    start: date
    end: date
    entry: Fraction
    exit: Fraction
    basis_verified: bool
    actions_verified: bool
    # Only agreed, effective-date-scoped rows; split before cash at the
    # same date, with verified entitlement on then-current shares.
    actions: tuple[tuple[date, str, Fraction], ...]


def leg_return(leg, identity, start, end):
    if (leg.identity, leg.start, leg.end) != (identity, start, end):
        raise Stop("PLACEBO_SCOPE")
    if not (leg.entry > 0 and leg.exit > 0 and leg.basis_verified and leg.actions_verified):
        raise Stop("PLACEBO_UNVERIFIED")
    shares, cash, prior = Fraction(1), Fraction(0), (start, 1)
    for when, kind, amount in leg.actions:
        order = (when, 0 if kind == "split" else 1)
        # Canonicalization must independently verify and combine distinct
        # same-day cash components on the same entitlement basis upstream.
        if not start < when <= end or order <= prior or amount <= 0:
            raise Stop("PLACEBO_ACTION")
        prior = order
        if kind == "split":
            shares *= amount
        elif kind == "cash_usd":
            cash += shares * amount
        else:
            raise Stop("PLACEBO_ACTION")
    return (shares * leg.exit + cash) / leg.entry - 1


def touches_deny(deny, subject, start, end):
    return any(a <= end and start <= b for a, b in deny.get(subject, ()))


def placebo_embargo(raw, active_days, sessions, successor_marks=()):
    """Every raw event contributes its full inclusive 60-session interval."""
    blocked = target_intervals(raw, active_days)
    for key, day in successor_marks:
        if day not in sessions or key == "PCEF":
            raise Stop("SUCCESSOR_MARK")
        blocked[key].append((day, day))
    return blocked


def admissible(raw_census, sessions, successor_marks=(), deny=None, placebo_exclusions=()):
    """Enumerate whole placebo windows; target scheduling stays unchanged."""
    raw, deduped, active_days, closes = candidates(raw_census, sessions)
    deny = {} if deny is None else deny
    blocked = placebo_embargo(raw, active_days, sessions, successor_marks)
    all_days = sorted(sessions)
    result = {}
    for n in HOLDS:
        ctx = []
        for row in select(deduped, closes, n):
            if active_days[row["exit"]] > CUTOFF:
                continue
            if touches_deny(deny, row["fund"], active_days[row["entry"]], active_days[row["exit"]]):
                continue
            if row["fund"] in placebo_exclusions:
                ctx.append((row, "capture_embargo_purge", None))
                continue
            span = placebo_span(all_days, active_days, closes, row["at"], n)
            if span is None:
                ctx.append((row, "pre_sip_start", None))
                continue
            start, end = span
            if touches_deny(deny, row["fund"], start, end):
                ctx.append((row, "deny_segment", None))
                continue
            if intersects_target(blocked, row["fund"], span):
                ctx.append((row, "target_overlap", None))
                continue
            end_slot = bisect_left(active_days, end)
            if (not start < end < active_days[row["entry"]] or
                    end_slot != bisect_left(closes, row["at"]) - 5 or
                    closes[end_slot] >= row["at"]):
                raise Stop("PLACEBO_CLOCK")
            ctx.append((row, "eligible", span))
        result[n] = ctx
    return result


def measure(raw_census, sessions, read_leg, successor_marks=(), deny=None, placebo_exclusions=()):
    """Inputs supplied externally, only after independent audit and approval.

    The future adapter must require exact (CIK/benchmark, start, end)
    membership in the separately sealed, non-browsable slice. A missing
    positive-volume endpoint returns None and is not replaced. No target
    packets or quote data are passed to this kernel.
    """
    result = {}
    seen = {}

    def scoped_return(key, start, end):
        scope = key, start, end
        if scope not in seen:
            leg = read_leg(*scope)
            seen[scope] = None if leg is None else leg_return(leg, key, start, end)
        return seen[scope]

    for n, planned in admissible(raw_census, sessions, successor_marks, deny, placebo_exclusions).items():
        counts, values = Counter(), []
        for row, gate, span in planned:
            counts["scheduled_fund_windows"] += 1
            if gate != "eligible":
                counts[gate] += 1
                continue
            start, end = span
            a, b = (scoped_return(key, start, end) for key in (row["fund"], "PCEF"))
            if a is None or b is None:
                counts["missing_endpoint_or_identity"] += 1
                continue
            values.append((row["day"], row["filer"], (a - b) * 10_000))
            counts["contributing_fund_windows"] += 1
        groups = filer_days(values)
        xs = [float(value) for _, _, value in groups]
        if len(xs) < 2 or not all(map(isfinite, xs)):
            raise Stop("PLACEBO_COUNT")
        center = median(xs)
        mad = MAD_FACTOR * median(abs(v - center) for v in xs)
        if not mad > 0:
            raise Stop("PLACEBO_MAD_ZERO")
        result[str(n)] = {**{k: counts[k] for k in ("scheduled_fund_windows", "capture_embargo_purge",
                         "pre_sip_start", "target_overlap", "deny_segment",
                         "missing_endpoint_or_identity", "contributing_fund_windows")},
                         "placebo_filer_days": len(xs), "placebo_non_saba_filer_days": sum(f != SABA for _, f, _ in groups),
                         "sample_sd_bps": stdev(xs),
                         "scaled_mad_bps": mad, "winsor_cap_bps": 5 * mad}
    return result
