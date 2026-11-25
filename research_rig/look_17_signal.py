"""Ledger 152, a descriptive look on the previously viewed snapshots only."""
import argparse
from bisect import bisect_left
from collections import defaultdict
from pathlib import Path
import json
import math
import random

import numpy as np

from . import score_16 as A

C, F, M, I = A.C, A.F, A.M, A.I
H, WEEK = M.H, C.WEEK
HORIZONS = (1, 4, 12, 24, 72)
LABELS = ("all", "first", "later")
SEED, DRAWS = 152, 200
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"research_rig/look_17_signal.json"
PAGE = ROOT/"docs/research/61_look_after_the_peak_signal.md"


def load_symbol(files, cutoff, spot=False):
    size = sum(m["n"] for key,m in files if "/fundingRate/" not in key)
    ts = np.empty(size,dtype=np.int64)
    vals = np.empty((size,3 if spot else 5))
    filled, funding = 0, {}
    for key, meta in files:
        if meta["where"] not in (("replay_13","replay_16") if spot else ("replay_16",)):
            raise ValueError(f"unexpected source {key}")
        raw = F.archive_root(key,meta["where"]).read_bytes()
        if F.digest(raw)!=meta["sha256"]:
            raise ValueError(f"changed archive {key}")
        count = 0
        for row in F.F.zip_rows(raw):
            count += 1
            t = F.F.open_epoch(row[0])
            if "/fundingRate/" in key:
                t = (t+30)//60*60
                if t<=cutoff:
                    if t%H or t in funding:
                        raise ValueError(f"duplicate or non-hourly funding {key}")
                    funding[t] = 0.  # A clock check only; no funding rates are read.
            elif t<=cutoff:
                if t%H:
                    raise ValueError(f"non-hourly trade {key}")
                close = float(row[4])
                if spot:
                    values = (close,close,close)
                else:
                    op,volume = float(row[1]),float(row[5])
                    values = (op,max(op,close),close,min(op,close),volume)
                if not all(math.isfinite(v) for v in values) or close<=0 or (
                    not spot and (op<=0 or volume<0)):
                    raise ValueError(f"bad price or volume {key}")
                ts[filled] = t
                vals[filled] = values
                filled += 1
        if count!=meta["n"]:
            raise ValueError(f"archive row count changed {key}")
    order = np.argsort(ts[:filled])
    times = ts[order]
    if np.any(times[1:]<=times[:-1]):
        raise ValueError("overlapping hourly trade archives")
    series = C.Series.__new__(C.Series)
    series.bars = A.Packed(times,vals[order],C.Bar if spot else M.FBar)
    series.times = times
    return series if spot else M.Tape(series,C.Series({}),funding,())


def groups(manifest,spot=False):
    by_symbol = defaultdict(list)
    for key,meta in manifest["archives"].items():
        if "/klines/" in key or (not spot and "/fundingRate/" in key):
            by_symbol[key.split("/")[4 if spot else 5]].append((key,meta))
    return by_symbol


def hot_five(weeks, archives, p, cutoff):
    jobs, ranks = defaultdict(list), defaultdict(list)
    for (year,t,end,snap,spot_ids,_) in weeks:
        if not snap:
            continue
        seen = set()
        prev,old = t-H,t-(24*p["rise_days"]+1)*H
        for row in sorted(snap["kept"],key=lambda r:r.get("cmcRank",float("inf"))):
            for lo,hi,symbol in F.spot_segments(row):
                cid = row["id"]
                if (cid,symbol) not in spot_ids or not lo<=t<hi or symbol in seen:
                    continue
                lo,hi = M.hour_bounds(max(lo,I.asset_floor(spot_ids,cid,symbol)),hi)
                if not lo<=t<hi or prev<lo:
                    continue
                seen.add(symbol)
                if lo<=old and symbol in archives:
                    jobs[symbol].append((t,old,prev,cid))
    for pair, jobs_for_pair in jobs.items():
        series = load_symbol(archives[pair],cutoff,True)
        for t,old,prev,cid in jobs_for_pair:
            if series.usable_lookback(old,prev,p["max_missing_hours"]):
                ranks[t].append((series.bars[prev].c/series.bars[old].c-1,cid))
    return {t:{cid for _,cid in sorted(rows,key=lambda r:(-r[0],r[1]))[:p["hot_n"]]}
            for t,rows in ranks.items()}


def weekly_futures(weeks,archives,p,cutoff):
    jobs, live, pools = defaultdict(set), set(), {}
    for year,t,end,snap,_,future_ids in weeks:
        if not snap:
            continue
        row_assets = [[M.hourly_asset(I.bound_asset(a,future_ids))
                       for a in F.perp_segments(r) if (a.coin,a.pair) in future_ids and a.pair in archives]
                      for r in snap["kept"]]
        pools[t] = [[a for a in aset if a.begin<=t<a.end] for aset in row_assets]
        for aset in pools[t]:
            for a in aset:
                jobs[a.pair].add((t,end,a))
    for pair,items in jobs.items():
        tape = load_symbol(archives[pair],cutoff)
        for t,end,a in items:
            if M.live(a,tape,t,end,p)[0]:
                live.add((t,a))
    pool = {}
    for t, choices in pools.items():
        taken = set()
        pool[t] = {}
        for aset in choices:
            for a in aset:
                if (t,a) in live and a.pair not in taken:
                    pool[t][a.coin] = a
                    taken.add(a.pair)
                    break
    return pool


def observe(op,closes,opens):
    """Return horizons in percent, first side, and separate next-open overshoots in bp."""
    x = [100*(closes[h-1]/op-1) if math.isfinite(closes[h-1]) else math.nan for h in HORIZONS]
    side = target = stop = math.nan
    for i,close in enumerate(closes):
        if not math.isfinite(close):
            break  # Could have crossed the other threshold in the missing hour.
        if close<=.95*op:
            side = 1.
            target = 10000*(.95*op-opens[i])/op
            break
        if close>=1.05*op:
            side = -1.
            stop = 10000*(opens[i]-1.05*op)/op
            break
    else:
        side = 0.
    return x+[side,target,stop]


def coin_week(tape,a,t,end,cutoff,p):
    tape = tape.within(a)
    hours = range(t,end+72*H,H)
    bars = [tape.executable(x) if a.begin<=x<a.end and x<=cutoff else None for x in hours]
    closes = [b.c if b is not None and x<cutoff else math.nan for x,b in zip(hours,bars)]
    opens = [b.o if b is not None else math.nan for b in bars]
    i = bisect_left(tape.payments,t)-1
    last_pay = tape.payments[i] if i>=0 else -10**12
    control, signals, missing = [], [], [0,0]
    seen_signal = False
    retire = False
    for i,x in enumerate(range(t,end,H)):
        if x>=a.end or tape.no_volume(x) or retire:
            break
        if x in tape.funding:
            last_pay = x
        old = x-(24*p["rise_days"]+1)*H
        eligible = (old>=a.begin and not tape.impassable(old,x) and
                    tape.trade.usable_lookback(old,x-H,p["max_missing_hours"]))
        signal = eligible and C.dip_signal(tape.trade,a,x,p)
        if eligible and math.isfinite(opens[i]):
            obs = observe(opens[i],closes[i:i+72],opens[i+1:i+73])
            control.append(obs)
            if signal:
                signals.append((len(control)-1,not seen_signal))
        elif signal:
            missing[int(seen_signal)] += 1
        seen_signal |= signal
        retire = x-last_pay>=p["live_funding_lookback_hours"]*H
    return np.asarray(control,dtype=float).reshape(-1,8), signals, missing


def weights(n, signals, rng):
    counts = np.zeros((2,n),dtype=np.int32)
    for _ in range(DRAWS):
        pick = sorted(rng.sample(range(n),len(signals)))
        for ix,(_,first) in zip(pick,signals):
            counts[int(not first),ix] += 1
    return counts


def weighted(values,w):
    ok = np.isfinite(values)&(w>0)
    values,w = values[ok],w[ok]
    n = int(w.sum())
    if not n:
        return {"n":0,"mean":None,"median":None}
    ix = np.argsort(values)
    cumul = w[ix].cumsum()
    mid = ((n-1)//2,n//2)
    med = values[ix[np.searchsorted(cumul,mid,side="right")]].mean()
    return {"n":n,"mean":float(np.dot(values,w)/n),"median":float(med)}


def summarize(items,group,label):
    data = np.concatenate([x[0] for x in items]) if items else np.empty((0,8))
    w = (np.concatenate([x[group].sum(axis=0) if label=="all" else x[group][LABELS.index(label)-1]
                         for x in items]) if items else np.empty(0,dtype=int))
    n = int(w.sum())
    v = data[:,5]
    return {"entries":n,
            "moves_pct":{str(h):weighted(data[:,i],w) for i,h in enumerate(HORIZONS)},
            "barrier":{"target_first":int(w[v==1].sum()),"stop_first":int(w[v==-1].sum()),
                       "neither":int(w[v==0].sum()),"unknown":int(w[~np.isfinite(v)].sum())},
            "target_next_open_overshoot_bps":weighted(data[:,6],w),
            "stop_next_open_overshoot_bps":weighted(data[:,7],w)}


def run():
    p13,p16 = F.config()
    cfg = (ROOT/"config/thresholds.yaml").read_bytes()
    p17 = F.F.yaml.safe_load(cfg)["replay_17_plan"]["value"]
    p = p13|p16|p17
    raw = (F.F.DATA/"snapshots.json").read_bytes()
    snapshots = json.loads(raw)
    fp = F.json_read(F.DATA/"snapshot_fingerprints.json")
    canonical = json.dumps(snapshots,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    if F.digest(raw)!=fp["source_sha256"] or F.digest(canonical)!=fp["viewed_sha256"]:
        raise ValueError("viewed snapshot differs from the frozen fingerprint")
    iraw = (F.DATA/A.IDENTITY).read_bytes()
    if F.digest(iraw)!="5b6aca5959b5c2a4a30033278794937f447f2c899cb6bd828eff81d3df3a248c":
        raise ValueError("dated policy has changed")
    policy = json.loads(iraw)
    manifests = {}
    for key in ("manifest_spot.json","manifest_futures.json"):
        blob = (F.DATA/key).read_bytes()
        if F.digest(blob)!=policy["archive_manifest_sha256"][key]:
            raise ValueError(f"changed viewed archive manifest {key}")
        manifests[key] = json.loads(blob)
        m = manifests[key]
        if m["errors"] or m["snapshots_sha256"]!=fp["combined_sha256"]:
            raise ValueError(f"invalid manifest {key}")
    digests = {"viewed_snapshots":F.digest(raw),"identity":F.digest(iraw),"config":F.digest(cfg),
               **{k:policy["archive_manifest_sha256"][k] for k in manifests}}
    cutoff = A.funding_cutoff(p16,p13,A.source_ranges(manifests["manifest_futures.json"]))
    ids = {r["id"] for snap in snapshots for r in snap["kept"]}
    timeline = I.Timeline({"as_of_rows":[r for r in policy["as_of_rows"] if r["id"] in ids]},cutoff)
    del policy, raw, iraw, blob, m
    windows = list(C.year_windows(p|{"end":F.F.utc(cutoff).date().isoformat()}))
    weeks = [(y,t,min(end,t+WEEK),M.snapshot_at(snapshots,t),*I.week_allowlist(timeline,t))
             for y,start,end in windows for t in range(start,end,WEEK)]
    print("Verified viewed-only inputs; ranking on spot",flush=True)
    hot = hot_five(weeks,groups(manifests.pop("manifest_spot.json"),True),p,cutoff)
    archives = groups(manifests.pop("manifest_futures.json"))
    print("Checking futures eligibility on viewed tape",flush=True)
    pools = weekly_futures(weeks,archives,p,cutoff)
    jobs = defaultdict(list)
    for y,t,end,_,_,_ in weeks:
        for cid in sorted(hot.get(t,set())):
            a = pools.get(t,{}).get(cid)
            if a is not None:
                jobs[a.pair].append((str(y),t,end,a))
    del pools,weeks,hot,timeline,snapshots
    archives = {pair:archives[pair] for pair in jobs}
    collected, missed, counts = defaultdict(list),defaultdict(int),defaultdict(int)
    rng = random.Random(SEED)
    print(f"Measuring {sum(map(len,jobs.values()))} live hot coin-weeks",flush=True)
    for pair,j in sorted(jobs.items()):
        tape = load_symbol(archives[pair],cutoff)
        for y,t,end,a in j:
            counts[y] += 1
            data,selected,missing = coin_week(tape,a,t,end,cutoff,p)
            missed[y,"first"] += missing[0]
            missed[y,"later"] += missing[1]
            if not selected:
                continue
            w = np.zeros((2,len(data)),dtype=np.int32)
            for i,first in selected:
                w[int(not first),i] += 1
            random_w = weights(len(data),selected,rng)
            collected[y].append((data,w,random_w))
    result = {
        "ledger":152,"seed":SEED,"draws":DRAWS,"cutoff_utc":F.F.utc(cutoff).isoformat(),
        "input_digests":digests,
        "years":{}
    }
    for year,_,_ in windows:
        y = str(year)
        result["years"][y] = {"live_hot_coin_weeks":counts[y],
            "signals_without_exact_open":{"first":missed[y,"first"],"later":missed[y,"later"]},
            **{g:{label:summarize(collected[y],i,label) for label in LABELS}
               for i,g in enumerate(("signal","random"),1)}}
    return result


def render(r):
    lines = ["# After the peak: what followed the entry signal","","MEASURED. Ledger 152 is a look, not a test. "
             "There is no pass mark. It cannot support a method. It can only shape a later plan, which needs "
             "its own ledger row and unseen data. Only the already viewed Plan 13 list and its archive "
             "inputs were used; the held-back list was not read.","",
             "Each Monday's hot five were ranked on spot exactly on the Plan 17 clock. Live perpetuals "
             "used the dated identity, full hourly bars, executable volume and recent funding clocks. "
             "We measured every eligible entry signal, even while a live strategy would already have "
             "a position. A first signal without an exact next open remains first but has no measured entry. "
             "The study ends at "+r["cutoff_utc"]+".","",
             "Price move means the perpetual's percentage move from the next hour's executable open to "
             "the close after the stated number of elapsed hours; negative is favorable to a short. "
             "The fixed look-forward can cross a weekly or year boundary, not an identity fence or the "
             "archive cutoff. A missing horizon is dropped from that horizon only.","",
             "For the ±5% race we watch the first 72 hourly closes after entry. A gap, dead spell, fence "
             "or cutoff before a first hit makes the order unknown, not a tie or a loss. Next-open "
             "overshoot is measured from the threshold in basis points of entry; positive means "
             "farther below the downside threshold or farther above the upside threshold. A negative "
             "overshoot means a rebound inside the threshold. Missing exact next opens have no fill statistic.","",
             f"The comparison has {r['draws']} draws (seed {r['seed']}). Each draw samples the same number of "
             "eligible entry hours without replacement in each observed coin-week, using the same old-bar "
             "requirements and entry-open screen but not the dip condition. Signal hours are not excluded. "
             "Sampled hours are sorted before applying the corresponding first/later labels. Random rows pool "
             "all draws; they are not independent market observations. Numbers below are descriptive, not trades "
             "with costs, and are not a result for US execution.","",
             "## Coverage","","| Year | Live hot coin-weeks | First signals missing exact open | Later signals missing exact open |",
             "|---|---:|---:|---:|"]
    for y,d in r["years"].items():
        a = d["signals_without_exact_open"]
        lines.append(f"| {y} | {d['live_hot_coin_weeks']} | {a['first']} | {a['later']} |")
    def cell(x):
        return "n/a (0)" if not x["n"] else f"{x['mean']:+.2f} / {x['median']:+.2f} ({x['n']:,})"
    for label in LABELS:
        lines += ["",f"## {label.capitalize()} signal hours","",
                  "Each move cell gives mean / median in percent, then usable observation count.","",
                  "| Year | Hours | Entries | 1h | 4h | 12h | 24h | 72h |","|---|---|---:|---:|---:|---:|---:|---:|"]
        for y,d in r["years"].items():
            for g in ("signal","random"):
                s = d[g][label]
                vals = " | ".join(cell(s["moves_pct"][str(h)]) for h in HORIZONS)
                lines.append(f"| {y} | {g} | {s['entries']:,} | {vals} |")
        lines += ["","Overshoot cells give mean / median in bp, then usable next opens. The target-first "
                  "rate uses all resolved paths, including paths that reached neither line.","",
                  "| Year | Hours | Target first | Stop first | Neither | Unknown | Target first % resolved | Target overshoot | Stop overshoot |",
                  "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for y,d in r["years"].items():
            for g in ("signal","random"):
                s = d[g][label]
                a = s["barrier"]
                places = [a[k] for k in ("target_first","stop_first","neither","unknown")]
                resolved = sum(places[:3])
                rate = f"{100*places[0]/resolved:.2f}%" if resolved else "n/a"
                counts = " | ".join(f"{num:,}" for num in places)
                lines.append(f"| {y} | {g} | {counts} | {rate} | "
                             f"{cell(s['target_next_open_overshoot_bps'])} | {cell(s['stop_next_open_overshoot_bps'])} |")
    lines += ["","The machine-readable counts and input digests are in `research_rig/look_17_signal.json`.",
              "This page was written by `research_rig/look_17_signal.py`."]
    return "\n".join(lines)+"\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--measure",action="store_true")
    mode.add_argument("--render-only",action="store_true")
    args = parser.parse_args()
    if args.measure:
        if any(x.exists() or x.is_symlink() for x in (OUT,PAGE)):
            raise SystemExit("refused: an output already exists")
        result = run()
        with OUT.open("x") as out:
            json.dump(result,out,indent=2,sort_keys=True,allow_nan=False)
            out.write("\n")
    else:
        result = json.loads(OUT.read_bytes())
    PAGE.write_text(render(result))


if __name__=="__main__":
    main()
