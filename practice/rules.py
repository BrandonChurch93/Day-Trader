"""The two rules the practice trader watches. Pure functions, standard library only, no network, no model.

P1 is defined in research_rig/PREREG_01_daily_crypto_trend.md (row P1) and coded for the replays in research_rig/rules.py.
T1 is defined in research_rig/PREREG_05_stock_trend_free_data.md (row T1) and coded for the replay in research_rig/run_05.py.
Neither setting is changed here. practice/test_trader.py checks both against small cases worked by hand."""

P1_WINDOWS = (20, 50, 100, 200)
T1_MONTHS = 10


def p1_weight(closes):
    """Share of the four simple averages (20, 50, 100, 200 days) that the last close is above.
    closes: daily closes, oldest first, complete days only. Returns None if there are fewer than 200."""
    if len(closes) < max(P1_WINDOWS):
        return None
    last = closes[-1]
    return sum(1 for n in P1_WINDOWS if last > sum(closes[-n:]) / n) / len(P1_WINDOWS)


def t1_weight(month_end_closes):
    """1.0 if the last month-end close is above the average of the last ten month-end closes (the last one included), else 0.0.
    month_end_closes: oldest first, finished months only. Returns None if there are fewer than ten."""
    if len(month_end_closes) < T1_MONTHS:
        return None
    last = month_end_closes[-1]
    return 1.0 if last > sum(month_end_closes[-T1_MONTHS:]) / T1_MONTHS else 0.0


def month_ends(daily, current_month):
    """daily: list of (date 'YYYY-MM-DD' in New York time, close), oldest first. current_month: 'YYYY-MM' in New York time.
    Returns [(month 'YYYY-MM', date of its last price, that close)] for every month before current_month."""
    out = []
    for d, c in daily:
        m = d[:7]
        if m >= current_month:
            break
        if out and out[-1][0] == m:
            out[-1] = (m, d, c)
        else:
            out.append((m, d, c))
    return out


def month_end_closes(daily, current_month):
    """Returns (list of the last close of every month before current_month, the 'YYYY-MM' of the last one or None)."""
    rows = month_ends(daily, current_month)
    return [c for _, _, c in rows], (rows[-1][0] if rows else None)
