"""Pure helpers of the decision autopsy: table cells, the under-30 rule, cost per fill, round trips from the desk's
closed list, and the label id check. No file or price access here, so test_autopsy.py can run them on made-up records."""
import collections
import re
import statistics

SMALL = 30                       # a cell with fewer items is flagged small=true and no conclusion is drawn from it
H24, H48, H120, D7 = 86400, 2 * 86400, 5 * 86400, 7 * 86400


def mean(x):
    x = [v for v in x if v is not None]
    return sum(x) / len(x) if x else None


def med(x):
    x = [v for v in x if v is not None]
    return statistics.median(x) if x else None


def share(x):
    x = [v for v in x if v is not None]
    return (sum(1 for v in x if v) / len(x)) if x else None


def r6(v):
    return None if v is None else round(v, 6)


def cell(vals):
    """n, mean, median, share above and below zero of a list of numbers (None skipped); small when n < SMALL."""
    v = [x for x in vals if x is not None]
    return dict(n=len(v), mean=r6(mean(v)), median=r6(med(v)), share_pos=r6(share([x > 0 for x in v])),
                share_neg=r6(share([x < 0 for x in v])), small=len(v) < SMALL)


def group(rows, keyf):
    d = collections.defaultdict(list)
    for r in rows:
        d[keyf(r)].append(r)
    return d


def cid_pick(cid):
    """Client order id 'pt1.b01-opus.20260801t0000z.0' -> ('20260801T0000Z', 0). Exit orders do not match: (None, None)."""
    m = re.search(r"\.(\d{8}t\d{4}z)\.(\d+)$", cid or "")
    if m:
        return m.group(1).upper(), int(m.group(2))
    return None, None


def fill_spread(side, qty, fill_price, half_spread):
    """Dollars of half-spread inside one fill. The desk fills a buy at mid*(1+hs) and a sell at mid*(1-hs),
    so the spread paid is qty*fill*hs/(1+hs) on a buy and qty*fill*hs/(1-hs) on a sell."""
    hs = half_spread
    return qty * fill_price * (hs / (1 + hs) if side == "buy" else hs / (1 - hs))


def round_trips(closed, buys, sells):
    """Round trips of one session from the desk's own closed list.

    closed: [{symbol, opened_ts, closed_ts, gain_usd, gain_pct}] (times in epoch seconds)
    buys, sells: fill rows {sym, t, fee, spread, cat, ...}; a sell row may carry exit_pick and written.
    Every fill of the symbol from opening to closing belongs to the trip (partial sells included). The entry reason is
    the first buy's, the exit reason the last sell's; costs are fee plus spread of every fill in the trip.
    Sets trip_gain on each sell of the trip (the last sell keeps the trip's gain).
    """
    out = []
    for c in closed:
        a, z = c["opened_ts"], c["closed_ts"]
        eb = [b for b in buys if b["sym"] == c["symbol"] and a <= b["t"] <= z]
        es = [s for s in sells if s["sym"] == c["symbol"] and a <= s["t"] <= z]
        first = min(eb, key=lambda b: b["t"]) if eb else None
        last = max(es, key=lambda s: s["t"]) if es else None
        out.append(dict(sym=c["symbol"], gain=c["gain_usd"], gain_pct=c["gain_pct"], hold_h=(z - a) / 3600,
                        costs=sum(x["fee"] + x["spread"] for x in eb + es), n_buys=len(eb), n_sells=len(es),
                        entry_cat=first["cat"] if first else "UNCLEAR", exit_cat=last["cat"] if last else "UNCLEAR",
                        entry_pick=first.get("pick_id") if first else None, exit_pick=last.get("exit_pick") if last else None,
                        exit_written=last.get("written") if last else None, entry_exits=first.get("exits") if first else None,
                        entry_fill=first.get("fill") if first else None, entry_flags=first.get("flags") if first else None,
                        exit_f24=last.get("f24") if last else None, exit_f48=last.get("f48") if last else None))
        if last is not None:
            last["trip_gain"] = c["gain_usd"]
        for s in es:
            s.setdefault("trip_gain", c["gain_usd"])
    return out


def trip_table(rows):
    g = [r["gain"] for r in rows]
    wins = [r for r in rows if r["gain"] > 0]
    losses = [r for r in rows if r["gain"] <= 0]
    costs = sum(r["costs"] for r in rows)
    net = sum(g)
    return dict(n=len(rows), small=len(rows) < SMALL, wins=len(wins), share_win=r6(len(wins) / len(rows)) if rows else None,
                mean_gain_usd=r6(mean(g)), median_gain_usd=r6(med(g)), mean_gain_pct=r6(mean([r["gain_pct"] for r in rows])),
                median_gain_pct=r6(med([r["gain_pct"] for r in rows])), net_usd=r6(net), mean_hold_h=r6(mean([r["hold_h"] for r in rows])),
                costs_usd=r6(costs), gross_before_costs_usd=r6(net + costs),
                costs_share_of_net_loss=r6(costs / -net) if net < 0 else None,
                winners_mean_hold_h=r6(mean([r["hold_h"] for r in wins])), losers_mean_hold_h=r6(mean([r["hold_h"] for r in losses])),
                winners_median_hold_h=r6(med([r["hold_h"] for r in wins])), losers_median_hold_h=r6(med([r["hold_h"] for r in losses])),
                winners_mean_gain_pct=r6(mean([r["gain_pct"] for r in wins])), losers_mean_gain_pct=r6(mean([r["gain_pct"] for r in losses])),
                winners_sum_usd=r6(sum(r["gain"] for r in wins)), losers_sum_usd=r6(sum(r["gain"] for r in losses)))


def check_label_ids(labels, known_ids):
    """labels: rows {id, ...}; known_ids: every text id found in the run folders. Returns the label ids not found."""
    known = set(known_ids)
    return [r["id"] for r in labels if r["id"] not in known]


def shared_runs(text, news_texts, n=5):
    """Runs of n words that a text shares with any news text (lower case, punctuation dropped). Used to keep news text
    out of the quotes."""
    norm = lambda s: re.sub(r"[^a-z0-9$.% ]", "", (s or "").lower()).split()
    w = norm(text)
    heads = [" ".join(norm(h)) for h in news_texts]
    hits = set()
    for i in range(len(w) - n + 1):
        g = " ".join(w[i:i + n])
        if any(g in h for h in heads):
            hits.add(g)
    return sorted(hits)
