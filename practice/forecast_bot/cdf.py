"""Continuous forecasts for numeric, discrete and date questions, written from the public API description
(Metaculus/metaculus docs/openapi.yml, "How to generate a continuous cdf?" and the ContinuousForecast schema).

A continuous forecast is a list of inbound_outcome_count + 1 CDF heights (201 for the usual 200) at evenly spaced
points of the question's internal [0, 1] axis. Rules this module enforces (each checked by `check`):
- strictly increasing by at least 0.01 / inbound_outcome_count per step;
- no step larger than min(0.59, 0.2 * 200 / inbound_outcome_count);
- closed lower bound: cdf[0] == 0.0; open lower bound: cdf[0] >= 0.001;
- closed upper bound: cdf[-1] == 1.0; open upper bound: cdf[-1] <= 0.999.
Standard library only.
"""
import math
from datetime import datetime, timezone

DEFAULT_COUNT = 200
OPEN_MIN_MASS = 0.001          # the site's floor for mass outside an open bound
MAX_STEP_SLIDER = 0.59         # "No two adjacent values of the CDF can differ by more than 0.59"


class CdfError(ValueError):
    pass


def outcome_count(q):
    n = q.get("inbound_outcome_count") or (q.get("scaling") or {}).get("inbound_outcome_count") or DEFAULT_COUNT
    if type(n) is not int or n < 2:
        raise CdfError("bad inbound_outcome_count")
    return n


def bounds_open(q):
    s = q.get("scaling") or {}
    lo = q.get("open_lower_bound") if q.get("open_lower_bound") is not None else s.get("open_lower_bound")
    hi = q.get("open_upper_bound") if q.get("open_upper_bound") is not None else s.get("open_upper_bound")
    if type(lo) is not bool or type(hi) is not bool:
        raise CdfError("bound openness missing")
    return lo, hi


def min_step(n):
    return 0.01 / n


def max_step(n):
    return min(MAX_STEP_SLIDER, 0.2 * DEFAULT_COUNT / n)


def nominal_value(value, qtype):
    """A nominal value as a float: a number, or for date questions an ISO date or time (UTC) as a Unix timestamp."""
    if qtype == "date":
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        text = str(value).strip().replace("Z", "+00:00")
        t = datetime.fromisoformat(text)
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return t.timestamp()
    if isinstance(value, bool):
        raise CdfError("bad value")
    v = float(value)
    if not math.isfinite(v):
        raise CdfError("bad value")
    return v


def to_internal(value, q):
    """Nominal value to the internal axis, where range_min is 0 and range_max is 1 (log scaling when zero_point is set)."""
    s = q.get("scaling") or {}
    lo, hi, zp = s.get("range_min"), s.get("range_max"), s.get("zero_point")
    if lo is None or hi is None or not hi > lo:
        raise CdfError("bad range")
    v = nominal_value(value, q.get("type"))
    if zp is None:
        return (v - lo) / (hi - lo)
    ratio = (hi - zp) / (lo - zp)
    if not ratio > 0 or ratio == 1:
        raise CdfError("bad log scaling")
    inner = (v - lo) * (ratio - 1) + (hi - lo)
    if inner <= 0:
        return -math.inf if ratio > 1 else math.inf
    return (math.log(inner) - math.log(hi - lo)) / math.log(ratio)


def from_internal(x, q):
    """Inverse of to_internal, for the comment's readable summary."""
    s = q["scaling"]
    lo, hi, zp = s["range_min"], s["range_max"], s.get("zero_point")
    if zp is None:
        return lo + x * (hi - lo)
    ratio = (hi - zp) / (lo - zp)
    return lo + ((hi - lo) * (ratio ** x) - (hi - lo)) / (ratio - 1)


def raw_curve(percentiles, q):
    """One run's belief as a function on the internal axis.

    percentiles: list of (probability in (0, 1), nominal value). Values must not decrease as probability rises.
    Beyond the outer percentiles the curve continues with the slope of the nearest segment, clamped to [0, 1].
    Returns heights at the grid points i / n, i = 0..n."""
    pts = sorted((float(p), to_internal(v, q)) for p, v in percentiles)
    if len(pts) < 2:
        raise CdfError("need at least two percentiles")
    for p, x in pts:
        if not 0 < p < 1 or not math.isfinite(x):
            raise CdfError("percentile out of range")
    clean, prev = [], None
    for p, x in pts:
        if clean and p <= clean[-1][0]:
            raise CdfError("repeated percentile")
        if prev is not None and x < prev:
            raise CdfError("percentile values decrease")
        prev = x
        if clean and x <= clean[-1][1]:
            x = clean[-1][1] + 1e-9                      # a flat run is made a very steep rise
        clean.append((p, x))
    n = outcome_count(q)

    def height(x):
        if x <= clean[0][1]:
            (p1, x1), (p2, x2) = clean[0], clean[1]
            slope = (p2 - p1) / (x2 - x1)
            return max(0.0, p1 - slope * (x1 - x))
        if x >= clean[-1][1]:
            (p1, x1), (p2, x2) = clean[-2], clean[-1]
            slope = (p2 - p1) / (x2 - x1)
            return min(1.0, p2 + slope * (x - x2))
        for (p1, x1), (p2, x2) in zip(clean, clean[1:]):
            if x1 <= x <= x2:
                return p1 + (p2 - p1) * (x - x1) / (x2 - x1)
        raise CdfError("unreachable")
    return [height(i / n) for i in range(n + 1)]


def mixture(curves):
    """The average of several runs' curves, point by point (an equal-weight mixture of the distributions)."""
    if not curves:
        raise CdfError("no curves")
    k = len(curves[0])
    if any(len(c) != k for c in curves):
        raise CdfError("curve lengths differ")
    return [math.fsum(c[i] for c in curves) / len(curves) for i in range(k)]


def standardize(raw, q, uniform_mix=0.02, open_mass=0.002):
    """Turn raw heights into a CDF the site accepts.

    - Closed bound: no mass outside it. Open bound: the run's own outside mass, but at least `open_mass`.
    - Inside the bounds the shape is kept and mixed with a little uniform mass so every step clears the minimum.
    - Steps above the cap are cut to the cap and the excess is spread over the other steps by their size."""
    n = outcome_count(q)
    if len(raw) != n + 1:
        raise CdfError("wrong number of points")
    lo_open, hi_open = bounds_open(q)
    if not (OPEN_MIN_MASS < open_mass < 0.01):
        raise CdfError("bad open_mass")
    f0, fn = raw[0], raw[-1]
    lo = min(max(f0, open_mass), 0.89) if lo_open else 0.0          # keep at least 0.1 inside the bounds
    hi = max(min(fn, 1.0 - open_mass), lo + 0.1) if hi_open else 1.0
    span = fn - f0
    if span <= 1e-9 and ((f0 > 0.5 and not lo_open) or (fn < 0.5 and not hi_open)):
        raise CdfError("no_valid_distribution")       # all belief sits beyond a closed bound: no honest CDF to send
    shape = [(r - f0) / span for r in raw] if span > 1e-9 else [i / n for i in range(n + 1)]
    shape = [min(1.0, max(0.0, v)) for v in shape]
    for i in range(1, n + 1):                             # make the shape non-decreasing (it is, up to rounding)
        shape[i] = max(shape[i], shape[i - 1])
    mass = hi - lo
    w = max(uniform_mix, 1.25 * min_step(n) * n / mass)
    if w >= 1:
        raise CdfError("bounds leave no room for the minimum step")
    cdf = [lo + mass * ((1 - w) * shape[i] + w * i / n) for i in range(n + 1)]
    steps = [cdf[i] - cdf[i - 1] for i in range(1, n + 1)]
    cap = max_step(n) * 0.98
    if mass > cap * n:
        raise CdfError("cap too small for the mass")
    for _ in range(200):
        over = [i for i, d in enumerate(steps) if d > cap]
        if not over:
            break
        excess = math.fsum(steps[i] - cap for i in over)
        for i in over:
            steps[i] = cap
        room = [i for i, d in enumerate(steps) if d < cap]
        total = math.fsum(steps[i] for i in room)
        for i in room:
            steps[i] += excess * steps[i] / total
    else:
        raise CdfError("cap did not settle")
    out = [lo]
    for d in steps:
        out.append(out[-1] + d)
    out = [round(v, 10) for v in out]
    out[0] = 0.0 if not lo_open else out[0]
    out[-1] = 1.0 if not hi_open else out[-1]
    check(out, q)
    return out


def check(cdf, q):
    """Raise CdfError unless `cdf` meets every rule of the public API description."""
    n = outcome_count(q)
    lo_open, hi_open = bounds_open(q)
    if not isinstance(cdf, list) or len(cdf) != n + 1:
        raise CdfError(f"need {n + 1} points")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in cdf):
        raise CdfError("values must be finite and in [0, 1]")
    lo_step, hi_step = min_step(n), max_step(n)
    for a, b in zip(cdf, cdf[1:]):
        d = b - a
        if d < lo_step - 1e-12:
            raise CdfError("a step is below the minimum")
        if d > hi_step + 1e-12:
            raise CdfError("a step is above the cap")
    if lo_open and cdf[0] < OPEN_MIN_MASS:
        raise CdfError("open lower bound needs at least 0.001 below it")
    if not lo_open and cdf[0] != 0.0:
        raise CdfError("closed lower bound needs cdf[0] == 0")
    if hi_open and cdf[-1] > 1 - OPEN_MIN_MASS:
        raise CdfError("open upper bound needs at least 0.001 above it")
    if not hi_open and cdf[-1] != 1.0:
        raise CdfError("closed upper bound needs cdf[-1] == 1")
    return True


def quantile(cdf, q, p):
    """The nominal value where the submitted CDF reaches p (linear between grid points), for the comment."""
    n = len(cdf) - 1
    if p <= cdf[0]:
        return from_internal(0.0, q)
    for i in range(1, n + 1):
        if cdf[i] >= p:
            a, b = cdf[i - 1], cdf[i]
            x = (i - 1 + (p - a) / (b - a)) / n
            return from_internal(x, q)
    return from_internal(1.0, q)


def build(runs, q, uniform_mix=0.02, open_mass=0.002):
    """runs: one list of (probability, nominal value) per valid model run. Returns the submitted CDF."""
    return standardize(mixture([raw_curve(r, q) for r in runs]), q, uniform_mix, open_mass)
