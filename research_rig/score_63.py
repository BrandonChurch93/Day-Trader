"""Draft Plan 63 gates and aggregate marks. No packet loader or executable mode."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from fractions import Fraction
import json
from math import ceil, sqrt


FLOOR = 230
YEARS = tuple(range(2016, 2027))
BUDGET = Fraction(500)
BP = Fraction(1, 10_000)
CENT = Fraction(1, 100)


class Stop(Exception):
    """Closed packet or unsupported condition; never include private values."""


@dataclass(frozen=True)
class Facts:
    day: date
    filer: str
    identity_verified: bool
    basis_verified: bool
    action_coverage_verified: bool
    action_sources_agree: bool
    # Values are execution necessities only. No exit price/action amounts.
    exit_state: str
    fund_entry_positive_volume: bool
    benchmark_entry_positive_volume: bool
    benchmark_exit_positive_volume: bool
    fund_entry_close: Fraction | None
    benchmark_entry_close: Fraction | None
    entry_measured_half: Fraction | None


@dataclass(frozen=True)
class BlindFacts:
    """Pre-go attestation; no price, quote, units affordable or dollar amount."""
    day: date
    filer: str
    identity_verified: bool
    basis_verified: bool
    action_coverage_verified: bool
    action_sources_agree: bool
    terminal_coverage_verified: bool
    fund_entry_bar_present_positive_volume: bool
    fund_exit_print_or_resolved_terminal: bool
    benchmark_entry_bar_present_positive_volume: bool
    benchmark_exit_bar_present_positive_volume: bool


def fund_half(measured):
    if measured is None:
        return 50 * BP
    if measured < 0:
        raise Stop("QUOTE_SHAPE")
    return max(10 * BP, measured)


def fund_rates(entry_half, exit_half):
    e, x = fund_half(entry_half), fund_half(exit_half)
    return e + 5 * BP, max(e, x) + 5 * BP


def measure_half(quotes):
    """Quotes already scoped and ordered by exact ns offset from session close.

    Each quote is (offset_ns, bid, ask); invalid/crossed/locked quotes
    supersede old quotes but do not contribute coverage. Same timestamp
    must be collapsed upstream using audited vendor order, never price.
    """
    minute = 60_000_000_000
    w0, w1 = -6 * minute, -minute
    prior, segments = -7 * minute - 1, []
    for i, (t, b, a) in enumerate(quotes):
        if not (-7 * minute <= t < w1 and prior < t):
            raise Stop("QUOTE_SHAPE")
        prior = t
        right = min(t + minute, w1, quotes[i + 1][0] if i + 1 < len(quotes) else w1)
        dt = right - max(t, w0)
        if dt > 0 and 0 < b < a:
            segments.append((Fraction(a - b, a + b), dt))
    covered = sum(dt for _, dt in segments)
    if covered < 3 * minute:
        return None
    seen = 0
    for half, dt in sorted(segments):
        seen += dt
        if 2 * seen >= covered:
            return half
    raise Stop("QUOTE_COVERAGE")


def entry_shares(price, fee):
    if price is None or price <= 0 or fee < 0:
        raise Stop("ENTRY_BAR_SHAPE")
    return BUDGET // (price + fee)


def disposition(f):
    if not f.identity_verified:
        return "identity_unresolved"
    if not f.action_coverage_verified or not f.action_sources_agree:
        # Missing independent or vendor evidence is not a reason to silently
        # discard an event whose economic proceeds could change the result.
        raise Stop("ACTION_UNRESOLVED")
    if not f.basis_verified:
        raise Stop("BASIS_UNRESOLVED")
    if f.exit_state == "unresolved_action":
        raise Stop("TERMINAL_ACTION_UNRESOLVED")
    if f.exit_state in ("cash_out", "successor", "cash_in_lieu"):
        # No production handling before lead rules the legal term accounting.
        raise Stop("TERMINAL_ACTION_RULE_PENDING")
    if f.exit_state not in ("printed_positive_volume", "missing"):
        raise Stop("EXIT_STATE")
    if f.exit_state == "missing":
        return "fund_exit_bar_missing"
    if not f.fund_entry_positive_volume:
        return "fund_entry_bar_missing"
    if not f.benchmark_entry_positive_volume or not f.benchmark_exit_positive_volume:
        return "benchmark_bar_missing"
    if f.fund_entry_close is None or f.benchmark_entry_close is None:
        raise Stop("ENTRY_BAR_SHAPE")
    a, b = f.fund_entry_close, f.benchmark_entry_close
    if entry_shares(a, a * (fund_half(f.entry_measured_half) + 5 * BP)) < 1:
        return "fund_no_whole_share"
    if entry_shares(b, max(b * 5 * BP, CENT)) < 1:
        return "benchmark_no_whole_share"
    return "placed"


def validate_inputs(facts):
    """Exact placement inside a separately authorized go; requires entry close."""
    counts, placed = Counter(), set()
    for f in facts:
        gate = disposition(f)
        counts[gate] += 1
        if gate == "placed":
            placed.add((f.day, f.filer))
    return {"placed_filer_days": len(placed), "meets_floor": len(placed) >= FLOOR,
            "gate_counts_fund_days": dict(sorted(counts.items()))}


def price_free_validation(facts):
    counts, upper = Counter(), set()
    for f in facts:
        if type(f) is not BlindFacts or f.day.year not in YEARS:
            raise Stop("BLIND_VALIDATION_SHAPE")
        if not f.identity_verified:
            k = "identity_unresolved"
        elif not all((f.action_coverage_verified, f.action_sources_agree, f.basis_verified,
                      f.terminal_coverage_verified)):
            raise Stop("BLIND_COVERAGE_UNRESOLVED")
        elif not f.fund_entry_bar_present_positive_volume:
            k = "fund_entry_bar_missing"
        elif not f.fund_exit_print_or_resolved_terminal:
            k = "fund_exit_unavailable"
        elif not f.benchmark_entry_bar_present_positive_volume or not f.benchmark_exit_bar_present_positive_volume:
            k = "benchmark_bar_missing"
        else:
            k = "placement_upper_bound"
            upper.add((f.day, f.filer))
        counts[k] += 1
    return {"placed_filer_days_upper_bound": len(upper), "floor_possible": len(upper) >= FLOOR,
            "gate_counts_fund_days": dict(sorted(counts.items()))}


def print_price_free_validation(facts, stream):
    stream.write(json.dumps(price_free_validation(facts), sort_keys=True) + "\n")


BLIND_FLAGS = (
    "identity_verified", "basis_verified", "action_coverage_verified", "action_sources_agree",
    "terminal_coverage_verified", "fund_entry_bar_present_positive_volume",
    "fund_exit_print_or_resolved_terminal", "benchmark_entry_bar_present_positive_volume",
    "benchmark_exit_bar_present_positive_volume",
)


def load_blind_facts(packet, planned):
    """Verify exact price-free accession coverage against the pinned docket.

    planned maps an approved current-hold accession to (filing day, filer).
    Nothing depending on a target price may be produced as a flag. In
    particular basis means evidence of raw feed-view and known split actions,
    not a raw/adjusted close comparison that is deferred to the go.
    """
    if (type(packet) is not dict or set(packet) != {"schema", "gates"}
            or packet["schema"] != "plan63-price-free-target-gates-v1" or type(packet["gates"]) is not list):
        raise Stop("BLIND_PACKET")
    expected = {"accession", *BLIND_FLAGS}
    covered = set()
    for row in packet["gates"]:
        if type(row) is not dict or set(row) != expected or any(type(row[k]) is not bool for k in BLIND_FLAGS):
            raise Stop("BLIND_PACKET")
        k = row["accession"]
        if type(k) is not str or k not in planned or k in covered:
            raise Stop("BLIND_DOCKET")
        covered.add(k)
    if covered != planned.keys():
        raise Stop("BLIND_DOCKET")
    return [BlindFacts(*planned[r["accession"]], *(r[k] for k in BLIND_FLAGS)) for r in packet["gates"]]


def average(values):
    values = list(values)
    return sum(values, Fraction(0)) / len(values) if values else None


def filer_days(rows):
    """Input (filing day, filer key, paired return bps); no public row output."""
    grouped = defaultdict(list)
    for day, filer, value in rows:
        if day.year not in YEARS:
            raise Stop("FILING_YEAR")
        grouped[(day, filer)].append(value)
    return [(day, filer, average(xs)) for (day, filer), xs in sorted(grouped.items())]


def variance(rows, center):
    by_date = defaultdict(Fraction)
    for day, _, value in rows:
        by_date[day] += value - center
    g, n = len(by_date), len(rows)
    if g < 2:
        return None
    return Fraction(g, (g - 1) * n * n) * sum(v * v for v in by_date.values())


def marks(rows, saba, cap_bps):
    """Pure aggregate marks on already equal-weighted filer-day pairs, in bps."""
    if cap_bps <= 0 or len({(d, f) for d, f, _ in rows}) != len(rows):
        raise Stop("MARK_INPUT")
    n = len(rows)
    raw = average(v for _, _, v in rows)
    winsor = [(d, f, max(-cap_bps, min(cap_bps, v))) for d, f, v in rows]
    center = average(v for _, _, v in winsor)
    var = variance(winsor, center) if n else None
    drop = ceil(Fraction(n, 100))
    trimmed = average(sorted(v for _, _, v in rows)[:n-drop])
    non_saba = average(v for _, f, v in rows if f != saba)
    by_year = {y: average(v for d, _, v in rows if d.year == y) for y in YEARS}
    positive = lambda x: x is not None and x > 0
    evidence = lambda x: positive(center) and positive(var) and center * center >= x * x * var
    flags = {"placement": n >= FLOOR, "money": positive(raw), "evidence": evidence(2),
             "trim": positive(trimmed), "year_breadth": sum(map(positive, by_year.values())) >= 7,
             "filer_breadth": positive(non_saba)}
    t = float(center) / sqrt(float(var)) if positive(var) else None
    if all(flags.values()):
        status = "passed_evidence"
    elif (raw is not None and raw <= 0) or (t is not None and not evidence(1)):
        status = "close_row"
    elif positive(raw) and evidence(1) and not evidence(2):
        status = "not_shown_not_refuted_forward_pretend_only"
    else:
        status = "not_shown_no_forward_disposition"
    return {"placed_filer_days": n, "marks": flags, "disposition": status, "raw_mean_bps": raw,
            "winsor_mean_bps": center, "winsor_t": t, "trim_removed": drop,
            "trimmed_mean_bps": trimmed, "non_saba_mean_bps": non_saba, "year_mean_bps": by_year}


@dataclass(frozen=True)
class PairOutcome:
    """Only consumed by a separately authorized scorer inside go."""
    day: date
    filer: str
    paired_bps: Fraction
    intersects_cusip_unverified_segment: bool


def judged_and_shown_only(outcomes, saba, cap_bps):
    all_rows, sensitive, removed = [], [], 0
    for record in outcomes:
        row = record.day, record.filer, record.paired_bps
        all_rows.append(row)
        if record.intersects_cusip_unverified_segment:
            removed += 1
        else:
            sensitive.append(row)
    full, without = filer_days(all_rows), filer_days(sensitive)
    # Rebuild filer-day means after eliminating the marked fund pairs, not
    # whole filer-days preserving the old pair weights. The sensitivity does
    # not produce a second verdict, choose N or determine the judged result.
    w = marks(without, saba, cap_bps)
    return {"judged": marks(full, saba, cap_bps),
            "shown_only_without_cusip_unverified_segments": {
                "fund_pairs_removed": removed, "filer_days_removed": len(full) - len(without),
                **{k: w[k] for k in ("placed_filer_days", "raw_mean_bps", "winsor_mean_bps", "winsor_t",
                                     "trimmed_mean_bps", "non_saba_mean_bps", "year_mean_bps")}
            }}
