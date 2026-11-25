"""Pure draft funding-carry mechanics. No files, archive reader or live route."""
from dataclasses import dataclass
from datetime import datetime, timezone
from math import fsum, isfinite, sqrt
from random import Random
from statistics import mean, stdev

ROLL = 72
FUND = 8
LEGS = 3
COSTS = (1, 12, 24)
DRAWS = 200
SEED = 18027
START = int(datetime(2022,1,1,tzinfo=timezone.utc).timestamp()//3600)
END = int(datetime(2026,10,26,tzinfo=timezone.utc).timestamp()//3600)


class Incomplete(ValueError):
    """An occupied position cannot be accounted for without inventing data."""


@dataclass(frozen=True)
class Contract:
    coin_id: int
    rank: int
    key: str                  # unique dated contract segment, not bare ticker
    begin: int                # all times in UTC hours since the epoch
    end: int                  # exclusive full-bar boundary


@dataclass(frozen=True)
class Snapshot:
    known_at: int
    contracts: tuple[Contract, ...]


@dataclass(frozen=True)
class Result:
    sharpe: float | None
    max_drawdown: float
    years: dict
    final: float
    traded: int
    too_few: int
    no_open: int
    marks: tuple[bool, bool, bool]


@dataclass(frozen=True)
class Draw:
    seed: int
    result: Result | None
    refusal: str | None = None


def latest(snapshots, t):
    visible = [s for s in snapshots if s.known_at <= t]
    if not visible:
        raise Incomplete(f"no known monthly snapshot at {t}")
    snap = max(visible, key=lambda s: s.known_at)
    if t - snap.known_at > 45*24 or sum(s.known_at == snap.known_at for s in visible) != 1:
        raise Incomplete(f"stale or ambiguous monthly snapshot at {t}")
    return snap


def eligible(tape, snap, t, roster=None):
    """Adapter must supply exact completed-bar and settlement coverage, not guessed zeros."""
    chosen = [c for c in snap.contracts
              if (1 <= c.rank <= 30 if roster is None else c.coin_id in roster)
              and c.begin <= t-ROLL and t < c.end]
    if len({c.coin_id for c in chosen}) != len(chosen) or len({c.key for c in chosen}) != len(chosen):
        raise Incomplete(f"ambiguous dated mapping at {t}")
    pool = []
    for c in chosen:
        if not tape.traded(c.key, t-1):
            continue
        rates = []
        for h in range(t-ROLL, t):
            covered, rate = tape.funding(c.key, h)
            if not covered or (rate is not None) != (h % FUND == 0) or (
                    rate is not None and not isfinite(rate)):
                break
            if rate is not None:
                rates.append(rate)
        else:
            pool.append((fsum(rates), c))
    return sorted(pool, key=lambda q: (q[0], q[1].coin_id, q[1].key))


def selection(pool, rng=None):
    if len(pool) < 2*LEGS:
        return ()
    if rng is None:
        sides = pool[:LEGS] + pool[-LEGS:]
    else:
        universe = sorted(pool, key=lambda q: (q[1].coin_id, q[1].key))
        sides = rng.sample(universe, 2*LEGS)
    return tuple((c, 1 if i < LEGS else -1) for i, (_, c) in enumerate(sides))


def valid(price):
    return price is not None and isfinite(price) and price > 0


def utc_year(t):
    return datetime.fromtimestamp(t*3600, timezone.utc).year


def run_book(tape, snapshots, start, end, bps=12, *, roster=None, rng=None):
    if start % 24 or end % 24 or end <= start or bps not in COSTS:
        raise ValueError("use UTC day boundaries and a declared fee")
    fee = bps/10_000
    nav = peak = 1.
    dd = 0.
    daily = {start: nav}
    traded = too_few = no_open = 0

    def value(h, equity, save_day=True):
        nonlocal peak, dd
        if not isfinite(equity) or equity <= 0:
            raise Incomplete(f"nonpositive or invalid proxy equity at {h}; no marks")
        peak = max(peak, equity)
        dd = max(dd, 1-equity/peak)
        if save_day and h % 24 == 0:
            daily[h] = equity

    for t in range(start, end, ROLL):
        e = min(end, t+ROLL)
        if e-t < ROLL:
            for h in range(t+24, e+1, 24):
                value(h, nav)
            break
        picks = selection(eligible(tape, latest(snapshots, t), t, roster), rng)
        if not picks:
            too_few += 1
        fills = [tape.open_price(c.key, t) for c, _ in picks]
        if not picks or not all(map(valid, fills)):
            no_open += bool(picks)
            for h in range(t+24, e+1, 24):
                value(h, nav)
            continue
        traded += 1
        cash = nav - nav*fee
        positions = [(c, side*nav/(2*LEGS*px), px) for (c,side),px in zip(picks,fills)]
        value(t, cash, save_day=False)
        for h in range(t+1, e+1):
            if any(h-1 >= c.end for c, _, _ in positions):
                raise Incomplete(f"occupied basket reaches dated fence at {h}")
            last = [tape.mark_close(c.key,h-1) for c,_,_ in positions]
            if not all(map(valid,last)):
                raise Incomplete(f"missing mark close at {h-1}")
            unrealized = fsum(q*(px-op) for (_,q,op),px in zip(positions,last))
            value(h, cash+unrealized, save_day=False)
            # The completed mark is used for settlement. The incoming sleeve
            # never gets the payment at its own entry hour.
            for (c,q,_), mark in zip(positions, last):
                if h >= c.end:
                    raise Incomplete(f"occupied basket reaches dated fence at {h}")
                covered, rate = tape.funding(c.key, h)
                if not covered or (rate is not None and not isfinite(rate)):
                    raise Incomplete(f"unaccounted funding for {c.key} at {h}")
                if rate is not None:
                    cash -= q*mark*rate
            value(h, cash+unrealized)
            if h == e:
                fills = [tape.open_price(c.key,h) for c,_,_ in positions]
                if not all(map(valid, fills)):
                    raise Incomplete(f"missing exact exit at {h}")
                nav = cash + fsum(q*(px-op)-abs(q)*px*fee
                                 for (_,q,op),px in zip(positions,fills))
                value(h, nav)
    if len(daily) != (end-start)//24+1:
        raise Incomplete("missing daily equity")
    changes, years = [], {}
    for h in range(start, end, 24):
        ret = daily[h+24]/daily[h]
        changes.append(ret-1)
        year = utc_year(h)
        years[year] = years.get(year,1.)*ret
    years = {y:v-1 for y,v in years.items()}
    sd = stdev(changes) if len(changes)>1 else 0.
    sharpe = sqrt(365)*mean(changes)/sd if sd else None
    judged = (start,end,bps) == (START,END,12) and roster is None and rng is None
    marks = (judged and sharpe is not None and sharpe >= 1.,
             judged and dd <= .25 and traded > 0,
             judged and sum(v > 0. for v in years.values()) >= 3)
    return Result(sharpe, dd, years, nav, traded, too_few, no_open, marks)


def random_books(tape, snapshots, start, end, bps=12, *, roster=None, draws=DRAWS):
    results = []
    for seed in range(SEED,SEED+draws):
        try:
            result = run_book(tape, snapshots, start, end, bps, roster=roster, rng=Random(seed))
        except Incomplete as exc:
            results.append(Draw(seed,None,str(exc)))
        else:
            results.append(Draw(seed,result))
    return tuple(results)
