"""Calendar-day chronology from saved listing inventory and manifest clocks."""
from calendar import monthrange
from datetime import date

TOLERANCE = 60


def gap_bounds(cmc_days,retained_day,month=None,segment_floor=None):
    """Earliest saved UTC day, or the published month bound if retained later."""
    if not cmc_days or not (month or retained_day):
        return None
    since = min(map(date.fromisoformat,cmc_days))
    if month and (not retained_day or month<retained_day[:7]):
        lo = date.fromisoformat(month+"-01")
        hi = lo.replace(day=monthrange(lo.year,lo.month)[1])
    else:
        lo = hi = date.fromisoformat(retained_day)
    if segment_floor:
        floor = date.fromisoformat(segment_floor)
        lo,hi = max(lo,floor),max(hi,floor)
    return (since-hi).days,(since-lo).days


def bucket(bounds):
    def cat(i):
        return "not_earlier" if i<=0 else "1_to_7" if i<=7 else "8_to_60" if i<=60 else "over_60"
    if bounds is None:
        return "no_clock_or_date"
    lo,hi = map(cat,bounds)
    return lo if lo==hi else "unresolved_bucket"


def soft_removal(row,bounds):
    """Relax date-only exclusions, not exclusions for wrong or mixed assets."""
    reason = row["reason"]
    only_chronology = ("excluded under the chronology rule" in reason or
                       (reason.startswith("Verified as ") and "predates saved CMC dateAdded" in reason) or
                       "a date-gate exclusion, not an unrelated ticker" in reason)
    return (row.get("notice_status")=="REMOVED" and only_chronology
            and bounds is not None and 0<bounds[1]<=TOLERANCE)
