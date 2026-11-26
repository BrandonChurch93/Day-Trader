#!/usr/bin/env python3
"""Plan 69 search only. No order endpoint, vault mode, or individual trade output."""

import argparse
from bisect import bisect_right
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time as sleep_clock
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zoneinfo import ZoneInfo

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

HERE = Path(__file__).resolve().parent
STORE = Path('/home/user/workspace/rig/data/sweep_69')
FIRST, LAST = date(2016, 1, 4), date(2021, 12, 31)
SECOND = date(2019, 1, 1)
SETTLE_CHANGE = date(2017, 9, 5)
NY, UTC = ZoneInfo('America/New_York'), timezone.utc
ENDPOINT = 'https://data.alpaca.markets/v2/stocks/bars'
FIELDS = ('o', 'h', 'l', 'c', 'v', 'vw')
BARS = 78
CASH = 500
YEARS = 6


def date_fence(start, end):
    if not FIRST <= start <= end <= LAST:
        raise ValueError('Plan 69 accepts dates only from 2016-01-04 through 2021-12-31')


def parse_time(stamp):
    value = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    if value.utcoffset() != timedelta(0):
        raise ValueError('Bar timestamps must be UTC')
    return value


def guard_stamp(stamp, start, end):
    value = parse_time(stamp)
    date_fence(value.date(), value.date())
    day = value.astimezone(NY).date()
    date_fence(day, day)
    if not start <= day <= end:
        raise ValueError('Bar timestamp outside requested date range')
    return value, day


def session_list(start=FIRST, end=LAST):
    date_fence(start, end)
    records = json.loads((HERE / 'calendar_65.json').read_text())['sessions']
    lo, hi = start.isoformat(), end.isoformat()
    return [(date.fromisoformat(d), parse_time(o), parse_time(c))
            for d, o, c in records if lo <= d <= hi]


def offset(clock):
    h, m = map(int, clock.split(':'))
    minutes = 60 * h + m - 570
    if not 0 <= minutes <= 390 or minutes % 5:
        raise ValueError('Not a valid five-minute regular-hours clock')
    return minutes // 5


def print_spec(spec):
    i = offset(spec['clock_et'])
    mode = spec['print']
    if mode not in ('open', 'close') or not (0 <= i - (mode == 'close') < BARS):
        raise ValueError('Invalid trade print')
    return i, mode


def load_grid():
    grid = json.loads((HERE / 'GRID_69.json').read_text())
    rules = grid['rules']
    if not 1 <= len(rules) <= 300 or len({r['id'] for r in rules}) != len(rules):
        raise ValueError('Bad rule count or duplicate ID')
    for r in rules:
        e, _ = print_spec(r['entry'])
        x, _ = print_spec(r['exit'])
        if r['family'] not in grid['families'] or r['pool'] not in grid['pools']:
            raise ValueError('Rule has an unknown family or pool')
        if r['exit']['session_offset'] not in (0, 1) or (not r['exit']['session_offset'] and x <= e):
            raise ValueError('Rule has an invalid exit clock')
        if r['latest_signal_close_et'] is not None and offset(r['latest_signal_close_et']) >= e:
            raise ValueError('Rule may use a bar not closed strictly before entry')
        if r['side'] not in ('long', 'short') or r['cash_500'] != (r['side'] == 'long'):
            raise ValueError('Only a long position in a listed security can be cash judged')
    return grid


def roster(grid):
    return tuple(sorted({s for symbols in grid['universe'].values() for s in symbols}))


def data_path(name):
    p = STORE / name
    if p.resolve() != p or p.parent.resolve() != STORE:
        raise ValueError('Plan 69 data must stay in its off-repo directory; no symlinks')
    return p


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def approval():
    """Independent sign-off binds the program, the grid and the identity file."""
    status = json.loads(data_path('search_approval.json').read_text())
    expected = {name: sha(HERE / name) for name in ('GRID_69.json', 'sweep_69.py', 'calendar_65.json')}
    expected['identity.json'] = sha(data_path('identity.json'))
    if (status.get('scope') != 'plan-69-search-only-2016-01-04_2021-12-31'
            or status.get('sha256') != expected
            or not isinstance(status.get('approved_by'), str) or not status['approved_by'].strip()):
        raise ValueError('Missing or mismatched independent Plan 69 search approval')


def read_identity(grid):
    """Dated, non-price identity and split data. No substitution for delisted securities."""
    obj = json.loads(data_path('identity.json').read_text())
    if obj.get('coverage_start') != FIRST.isoformat() or obj.get('coverage_end') != LAST.isoformat():
        raise ValueError('The identity register must cover exactly the search dates')
    members = obj['members']
    if set(members) != set(roster(grid)):
        raise ValueError('The identity register must retain every original member')
    spans, splits = [], {}
    by_alias = defaultdict(list)
    for member, rec in sorted(members.items()):
        if not rec.get('sources') or not all(str(u).startswith('https://') for u in rec['sources']):
            raise ValueError('Every original member needs identity provenance')
        prev = FIRST - timedelta(days=1)
        for p in rec['aliases']:
            start, end = date.fromisoformat(p['start']), date.fromisoformat(p['end'])
            date_fence(start, end)
            alias = p['ticker']
            if start <= prev or not re.fullmatch(r'[A-Z][A-Z0-9.-]{0,12}', alias):
                raise ValueError('Invalid or overlapping identity spans')
            spans.append((member, alias, start, end))
            by_alias[alias].append((start, end))
            prev = end
        for p in rec['splits']:
            day, factor = date.fromisoformat(p['effective_date']), float(p['new_per_old'])
            date_fence(day, day)
            if (not math.isfinite(factor) or factor <= 0 or (member, day) in splits
                    or not any(m == member and lo <= day <= hi for m, _, lo, hi in spans)):
                raise ValueError('Invalid split register row')
            splits[member, day] = factor
    for periods in by_alias.values():
        periods.sort()
        if any(later[0] <= earlier[1] for earlier, later in zip(periods, periods[1:])):
            raise ValueError('A ticker cannot represent two original members at once')
    return spans, splits


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def bars_pages(ticker, start, end, get):
    date_fence(start, end)
    window = {'symbols': ticker, 'timeframe': '5Min', 'feed': 'sip', 'adjustment': 'raw',
              'asof': '-', 'sort': 'asc', 'limit': 10000,
              'start': datetime.combine(start, time(9, 30), NY).astimezone(UTC).isoformat(),
              'end': datetime.combine(end, time(15, 55), NY).astimezone(UTC).isoformat()}
    tokens = set()
    while True:
        packet = get(window)
        bars = packet.get('bars') or {}
        if set(bars) - {ticker}:
            raise ValueError('Vendor returned an unexpected ticker')
        for row in bars.get(ticker, ()):
            guard_stamp(row['t'], start, end)
            yield row
        token = packet.get('next_page_token')
        if not token:
            break
        if token in tokens:
            raise ValueError('Vendor returned a repeated page token')
        tokens.add(token)
        window['page_token'] = token


def collect(grid, start, end):
    date_fence(start, end)
    if (start, end) != (FIRST, LAST):
        raise ValueError('The persisted collection must cover the entire frozen search')
    approval()
    spans, _ = read_identity(grid)
    final, temp = data_path('bars_sip_5min.jsonl.gz'), data_path('bars_sip_5min.partial.jsonl.gz')
    if final.exists() or temp.exists():
        raise ValueError('Existing search data or partial collection; do not overwrite')
    opener = build_opener(NoRedirect())
    headers = {'APCA-API-KEY-ID': os.environ['APCA_API_KEY_ID'],
               'APCA-API-SECRET-KEY': os.environ['APCA_API_SECRET_KEY']}

    def get(query):
        for delay in (0, 2, 4, 8, 16):
            if delay:
                sleep_clock.sleep(delay)
            try:
                with opener.open(Request(ENDPOINT + '?' + urlencode(query), headers=headers), timeout=60) as r:
                    return json.load(r)
            except HTTPError as err:
                if err.code not in (429, 500, 502, 503, 504) or delay == 16:
                    raise ValueError(f'Alpaca bars HTTP {err.code}; no response body logged') from None
        raise AssertionError('unreachable')

    with gzip.open(temp, 'xt', encoding='utf-8') as out:
        header = {'feed': 'sip', 'timeframe': '5Min', 'adjustment': 'raw', 'asof': '-',
                  'start': start.isoformat(), 'end': end.isoformat(),
                  'identity_sha256': sha(data_path('identity.json'))}
        out.write(json.dumps(header) + '\n')
        for member, alias, a, b in spans:
            for row in bars_pages(alias, a, b, get):
                out.write(json.dumps([member, alias, row['t'], *(row.get(k) for k in FIELDS)],
                                     allow_nan=False, separators=(',', ':')) + '\n')
    os.link(temp, final)  # atomic, no overwrite if another process created it
    temp.unlink()


def load_collection(grid, start, end):
    date_fence(start, end)
    if (start, end) != (FIRST, LAST):
        raise ValueError('The registered search uses the whole search period')
    approval()
    spans, splits = read_identity(grid)
    sessions, names = session_list(start, end), roster(grid)
    dates = [x[0] for x in sessions]
    di, si = {d: i for i, d in enumerate(dates)}, {s: i for i, s in enumerate(names)}
    active = {(m, d): a for m, a, lo, hi in spans for d in dates if lo <= d <= hi}
    a = np.full((len(FIELDS), len(dates), len(names), BARS), np.nan, dtype=np.float32)
    with gzip.open(data_path('bars_sip_5min.jsonl.gz'), 'rt', encoding='utf-8') as f:
        header = json.loads(next(f))
        expected = {'feed': 'sip', 'timeframe': '5Min', 'adjustment': 'raw', 'asof': '-',
                    'start': start.isoformat(), 'end': end.isoformat(),
                    'identity_sha256': sha(data_path('identity.json'))}
        if header != expected:
            raise ValueError('Collection header does not match the registered inputs')
        for line in f:
            member, alias, stamp, *vals = json.loads(line)
            when, day = guard_stamp(stamp, start, end)
            if active.get((member, day)) != alias:
                raise ValueError('Bar has undocumented instrument identity')
            if day not in di:
                continue  # not a scheduled NYSE trading day
            d, n = di[day], si[member]
            _, session_open, session_close = sessions[d]
            if not session_open <= when < session_close:
                continue  # never use extended hours
            seconds = (when - session_open).total_seconds()
            if seconds % 300 or len(vals) != len(FIELDS):
                raise ValueError('Off-grid or malformed regular-hours bar')
            i = int(seconds / 300)
            o, h, low, c, v, vw = vals
            if (not all(isinstance(x, (int, float)) and math.isfinite(x) and x > 0 for x in vals[:5])
                    or low > min(o, c) or h < max(o, c)
                    or (vw is not None and (not math.isfinite(vw) or vw <= 0))
                    or np.isfinite(a[0, d, n, i])):
                raise ValueError('Invalid or duplicate regular-hours bar')
            a[:, d, n, i] = vals
    for member, _, lo, hi in spans:
        span_days = [di[day] for day in dates if lo <= day <= hi]
        if span_days and not np.any(np.isfinite(a[0, span_days, si[member]])):
            raise ValueError('A documented active symbol span has no regular SIP bars; audit coverage first')
    split_array = np.ones((len(dates), len(names)))
    for (member, day), factor in splits.items():
        if day not in di:
            raise ValueError('Split date must be its first effective search session')
        split_array[di[day], si[member]] = factor
    return Tape(dates, names, a, [int((c - o).total_seconds() / 300) for _, o, c in sessions], split_array)


def ratio(end, start):
    return end.astype(np.float64) / start - 1


def lag(x, days):
    y = np.full_like(x, np.nan)
    y[days:] = x[:-days]
    return y


def past(x, length, fn):
    y = np.full_like(x, np.nan)
    if len(x) > length:
        y[length:] = fn(sliding_window_view(x[:-1], length, axis=0), axis=-1)
    return y


def prior_top(val, eligible, fraction):
    """Per-session top fraction, rounded up, with original symbol sorting ties."""
    valid = np.isfinite(val) & eligible[None, :]
    order = np.argsort(np.where(valid, -val, np.inf), axis=1, kind='stable')
    rank = np.argsort(order, axis=1)
    return valid & (rank < np.ceil(valid.sum(axis=1) * fraction)[:, None])


class Tape:
    def __init__(self, dates, names, a, lengths, splits):
        if not dates or any(a >= b for a, b in zip(dates, dates[1:])):
            raise ValueError('Search session dates must be strictly ordered')
        date_fence(dates[0], dates[-1])
        if tuple(names) != tuple(sorted(set(names))):
            raise ValueError('Stable symbols must be unique and sorted')
        self.dates, self.names, self.a, self.splits = dates, names, a, splits
        self.lengths = np.asarray(lengths)
        self.d = len(dates)
        self.first_half = np.array([d < SECOND for d in dates])
        self.prior_indices = np.arange(self.d)
        clearing = [i for i, d in enumerate(dates) if clearing_session(d)]
        self.settles = [clearing[j] if j < len(clearing) else self.d
                        for i, d in enumerate(dates)
                        for j in [bisect_right(clearing, i) + settlement_delay(d) - 1]]
        self.cache = {}

    def cached(self, key, make):
        if key not in self.cache:
            self.cache[key] = make()
        return self.cache[key]

    def print(self, index, mode):
        return self.a[0 if mode == 'open' else 3, :, :, index - (mode == 'close')]

    def reg_close(self):
        return self.a[3, self.prior_indices, :, self.lengths - 1]

    def sizing_reference(self, index):
        # At 09:30 or 09:35 no same-day bar was closed strictly earlier than the fill clock.
        if index < 2:
            return lag(self.reg_close().astype(np.float64), 1) / self.splits
        return self.print(index - 1, 'close')

    def period_return(self, lo, hi):
        return self.cached(('ret', lo, hi), lambda: ratio(self.print(hi, 'close'), self.print(lo, 'open')))

    def volume_multiple(self, lo, hi, length):
        def calc():
            v = np.sum(self.a[4, :, :, lo:hi], axis=-1, dtype=np.float64)
            # Number of bars and clock must match; exact past sessions, never fill missing volumes.
            return v / past(v, length, np.median)
        return self.cached(('vol', lo, hi, length), calc)

    def high_low(self, lo, hi):
        return self.cached(('hi-lo', lo, hi), lambda: (
            np.max(self.a[1, :, :, lo:hi], axis=-1), np.min(self.a[2, :, :, lo:hi], axis=-1)))

    def history_vol(self, length):
        def calc():
            raw = self.reg_close().astype(np.float64)
            daily = ratio(raw * self.splits, lag(raw, 1))
            return past(daily, length, np.std)
        return self.cached(('rv', length), calc)

    def signals(self, r, grid):
        """Candidate rank from data already closed at the declared signal cutoff."""
        fam, p = r['family'], r['signal']
        allowed = frozenset(grid['pools'][r['pool']])
        elig = np.array([n in allowed for n in self.names])
        cut = None if r['latest_signal_close_et'] is None else offset(r['latest_signal_close_et'])
        earliest = lambda: offset(p['from_et'])
        limit = p.get('threshold')

        if fam == 'S1':
            val = self.period_return(earliest(), cut)
            test = val >= limit
        elif fam in ('S2', 'S3', 'S7', 'S12'):
            val = -self.period_return(earliest(), cut)
            test = val >= limit
            if 'volume_multiple' in p:
                test &= self.volume_multiple(offset(p['volume_from_et']), cut, p['volume_days']) >= p['volume_multiple']
            if fam == 'S12':
                # This uses only the published calendar; no actual data beyond the fence.
                # Dec 31 2021 cannot enter an overnight trade in any case.
                last = np.array([d.month != n.month for d, n in zip(self.dates[:-1], self.dates[1:])] + [False])
                if p['period'] == 'quarter':
                    last &= np.array([d.month % 3 == 0 for d in self.dates])
                test &= last[:, None]
        elif fam == 'S4':
            val = -ratio(self.print(earliest(), 'open').astype(np.float64) * self.splits,
                         lag(self.reg_close(), 1))
            test = ((val >= limit) & (self.period_return(earliest(), cut) > 0)
                    & (self.volume_multiple(earliest(), cut, p['volume_days']) >= p['volume_multiple']))
        elif fam == 'S5':
            if p['benchmark'] not in self.names:
                raise ValueError('ETF-basis benchmark is missing')
            z = self.period_return(earliest(), cut)
            val = z[:, self.names.index(p['benchmark']), None] - z
            test = (val >= limit) & (self.volume_multiple(offset(p['volume_from_et']), cut,
                                                          p['volume_days']) >= p['volume_multiple'])
        elif fam == 'S6':
            range_end = offset(p['range_end_et'])
            hi, lo = self.high_low(earliest(), range_end)
            range_size = (hi.astype(np.float64) - lo) / self.print(earliest(), 'open')
            mult = self.cached(('range', range_end, p['range_days']),
                               lambda: range_size / past(range_size, p['range_days'], np.median))
            hi, lo = self.high_low(earliest(), cut)
            loc = (self.print(cut, 'close') - lo) / (hi.astype(np.float64) - lo)
            val = loc if p['location'] == 'top' else 1 - loc
            test = (mult >= limit) & (val >= p['fraction_from_other_end'])
        elif fam == 'S8':
            hi = offset(p['to_et'])
            val = self.cached(('periodic', earliest(), hi, p['past_days']),
                              lambda: past(self.period_return(earliest(), hi), p['past_days'], np.mean))
            test = (val >= limit) if limit is not None else prior_top(val, elig, p['top_fraction'])
        elif fam == 'S9':
            v = self.a[4, :, :, earliest():cut]
            vw = self.a[5, :, :, earliest():cut]
            anchor = self.cached(('vwap', earliest(), cut), lambda: np.sum(v * vw, axis=-1, dtype=np.float64)
                                 / np.sum(v, axis=-1, dtype=np.float64))
            val = -ratio(self.print(cut, 'close'), anchor)
            test = (val >= limit) & prior_top(-self.period_return(earliest(), cut), elig, p['bottom_fraction'])
        elif fam == 'S10':
            if p['type'] == 'low_vol':
                val = -self.history_vol(p['vol_days'])
                test = prior_top(val, elig, p['bottom_fraction'])
            else:
                val = -self.period_return(earliest(), cut)
                raw = self.reg_close().astype(np.float64)
                length = p['past_days']
                adj = past(self.splits, length, np.prod)
                old = lag(raw, length + 1)
                test = (val >= limit) & (ratio(lag(raw, 1) * adj, old) > 0)
            friday_monday = [d.weekday() == 4 and n.weekday() == 0
                             for d, n in zip(self.dates[:-1], self.dates[1:])] + [False]
            test &= np.array(friday_monday)[:, None]
        elif fam == 'S11':
            val = -self.period_return(earliest(), cut)
            vol = self.history_vol(p['risk_days'])
            ref = self.cached(('risk', p['risk_days'], p['risk_median_days']),
                              lambda: past(vol, p['risk_median_days'], np.median))
            test = ((val >= limit) & (self.volume_multiple(earliest(), cut, p['volume_days']) >= p['volume_multiple'])
                    & (vol > ref))
        elif fam == 'TEST':
            val = np.zeros((self.d, len(self.names)))
            test = np.ones_like(val, dtype=bool)
        else:
            raise ValueError('Unknown scoring family')
        return np.where(test & elig & np.isfinite(val), val, -np.inf)

    def paired(self, r):
        e, et = print_spec(r['entry'])
        x, xt = print_spec(r['exit'])
        over = r['exit']['session_offset']
        key = e, et, x, xt, over

        def calc():
            entry = self.print(e, et).astype(np.float64)
            exit = self.print(x, xt).astype(np.float64)
            mult = np.ones_like(entry)
            if over:
                exit = np.vstack((exit[1:], np.full_like(exit[:1], np.nan)))
                mult = np.vstack((self.splits[1:], np.ones_like(self.splits[:1])))
            gross = ratio(exit * mult, entry)
            out = []
            for block in (np.ones(self.d, dtype=bool), self.first_half, ~self.first_half):
                good = block.copy()
                if over:
                    good[-1] = False
                    good[:-1] &= block[1:]
                rows = gross[good]
                num = np.isfinite(rows).sum(axis=0)
                out.append(np.divide(np.nansum(rows, axis=0), num,
                                     out=np.full(len(self.names), np.nan), where=num > 0))
            return entry, exit, mult, out
        return self.cached(('paired', key), calc)


def cost_bps(grid, symbol, spec):
    e, mode = print_spec(spec)
    i = e - (mode == 'close')
    bucket = 0 if i < 6 else 2 if i >= 72 else 1
    model = grid['cost_bps_per_side']
    group = next((g for g, symbols in grid['measured_cost_symbols'].items() if symbol in symbols), 'cautious')
    if mode == 'close' and e == BARS:
        group = 'cautious'
    return model[group][bucket]


def settlement_delay(day):
    return 3 if day < SETTLE_CHANGE else 2


def clearing_session(day):
    # Exchange-open does not imply CNS settles. Conservatively skip the usual
    # bank-observed Veterans Day too, including the Friday before a Saturday.
    if day.month == 10 and day.weekday() == 0 and 8 <= day.day <= 14:
        return False
    veterans = date(day.year, 11, 11)
    if veterans.weekday() == 5:
        veterans -= timedelta(days=1)
    elif veterans.weekday() == 6:
        veterans += timedelta(days=1)
    return day != veterans


def execute(tape, grid, r, scores):
    en, ex, mult, bases = tape.paired(r)
    blocks = [[], [], []]
    first = tape.first_half
    over = r['exit']['session_offset']
    e, emode = print_spec(r['entry'])
    x, xmode = print_spec(r['exit'])
    ref = tape.sizing_reference(e)
    balance, next_free, missing_entries = float(CASH), 0, 0
    out = []
    ec = [cost_bps(grid, sym, r['entry']) / 1e4 for sym in tape.names]
    xc = [cost_bps(grid, sym, r['exit']) / 1e4 for sym in tape.names]
    winners = np.argmax(scores, axis=1)
    selected = np.isfinite(scores[tape.prior_indices, winners])
    for d in np.flatnonzero(selected):
        if (d < next_free or d + over >= tape.d or e - (emode == 'close') >= tape.lengths[d]
                or x - (xmode == 'close') >= tape.lengths[d + over]):
            continue
        n = winners[d]
        # Fix whole shares using only an earlier completed bar. A cash-limited order
        # is modeled as unfilled if its single print would spend more than settled cash.
        cash_available = min(CASH, balance)
        if not np.isfinite(ref[d, n]):
            continue
        shares = math.floor(cash_available / (float(ref[d, n]) * (1 + ec[n])))
        if shares <= 0:
            continue
        if not np.isfinite(en[d, n]):
            missing_entries += 1
            continue  # fixed failed entry attempt; never try another ticker that day
        buy = en[d, n] * (1 + ec[n])
        if shares * buy > cash_available:
            continue
        if not np.isfinite(ex[d, n]):
            return out, blocks, missing_entries, True  # no erasing a taken trade with an unknown exit
        sell = ex[d, n] * mult[d, n] * (1 - xc[n])
        pnl = shares * (sell - buy)
        balance += pnl
        nxt = d + over
        next_free = tape.settles[nxt]
        net = sell / buy - 1
        out.append((d, net, pnl / CASH))
        blocks[0].append((d, net - bases[0][n]))
        if first[d] == first[nxt]:
            b = 1 if first[d] else 2
            blocks[b].append((d, net - bases[b][n]))
    return out, blocks, missing_entries, False


def clustered(rows):
    if len(rows) < 2:
        return math.nan
    days, y = np.array(rows, dtype=np.float64).T
    avg = y.mean()
    group = np.bincount(days.astype(int), weights=y - avg)
    g = len(np.unique(days))
    if g < 2:
        return math.nan
    se = math.sqrt(float(group @ group) * g / (g - 1)) / len(rows)
    return float(avg / se) if se > 1e-15 else math.nan


def trim_mean(net):
    n = len(net)
    k = math.ceil(n * 0.01)
    return float(np.sort(net)[:n - k].mean()) if n > k else math.nan


def summarize(r, trades, blocks, missing_entries=0, missing_exit=False):
    n = len(trades)
    days = [len({d for d, _ in block}) for block in blocks]
    t, h1, h2 = map(clustered, blocks)
    net = np.array([x[1] for x in trades])
    annual = sum(x[2] for x in trades) / YEARS
    plain = float(net.mean()) if n else math.nan
    half_plain = [float(np.mean([net_i for d, net_i, _ in trades if d in ids])) if ids else math.nan
                  for ids in ({d for d, _ in b} for b in blocks[1:])]
    trim = trim_mean(net)
    ok = (plain > 0 and min(half_plain) > 0 and t >= 3.5 and h1 >= 1.5 and h2 >= 1.5
          and trim > 0 and annual >= 0.12)
    status = ('unpriced_exit' if missing_exit else 'too_thin' if n < 200 or days[0] < 100 or min(days[1:]) < 40
              else 'eligible' if ok else 'miss')
    return {'id': r['id'], 'family': r['family'], 'status': status, 'trades': n, 'days': days[0],
            'days_h1': days[1], 'days_h2': days[2], 'net_mean': plain, 'net_mean_h1': half_plain[0],
            'net_mean_h2': half_plain[1], 'annual_net_500': annual, 't': t, 't_h1': h1, 't_h2': h2,
            'trimmed_net': trim, 'missed_entry_prints': missing_entries, 'duplicate_of': None}


def overlap_corr(a, b):
    common = sorted(a.keys() & b.keys())
    if len(common) < 2:
        return math.nan
    x, y = np.array([(a[d], b[d]) for d in common]).T
    if x.std() == 0 or y.std() == 0:
        return math.nan
    return float(np.corrcoef(x, y)[0, 1])


def search(tape, grid):
    date_fence(tape.dates[0], tape.dates[-1])
    summaries, eligible = [], []
    for r in grid['rules']:
        if not r['cash_500']:
            summaries.append({'id': r['id'], 'family': r['family'], 'status': 'shown_short_unscored'})
            continue
        if r['family'] == 'S12':
            summaries.append({'id': r['id'], 'family': r['family'], 'status': 'too_thin',
                              'structural_max_entries': 72 if r['signal']['period'] == 'month' else 24})
            continue
        trades, blocks, absent, no_exit = execute(tape, grid, r, tape.signals(r, grid))
        row = summarize(r, trades, blocks, absent, no_exit)
        summaries.append(row)
        if row['status'] == 'eligible':
            eligible.append((row, {d: n for d, n, _ in trades}))
    finalists = []
    for row, pnl in sorted(eligible, key=lambda item: (-item[0]['t'], item[0]['id'])):
        dup = next((prior['id'] for prior, p in finalists if overlap_corr(pnl, p) > .7), None)
        if dup is not None:
            row['status'], row['duplicate_of'] = 'duplicate', dup
        elif len(finalists) < 3:
            row['status'] = 'finalist'
            finalists.append((row, pnl))
        else:
            row['status'] = 'cap'
    return summaries


def synthetic_tape(grid, seed, case='noise'):
    rng = np.random.default_rng(seed)
    sessions = session_list()
    # Small fake cross-section exercises the same families, clocks and scoring. Real names are never used here.
    source_pools = ['stocks'] * 7 + ['sector'] * 4 + ['broad'] * 2 + ['bond'] * 2 + ['bull', 'inverse']
    names = tuple('FAKE%02d' % i for i in range(len(source_pools)))
    n, d = len(names), len(sessions)
    early_lengths = [int((c - o).total_seconds() / 300) for _, o, c in sessions]
    full = np.arange(BARS)[None, :] < np.array(early_lengths)[:, None]
    a = np.empty((len(FIELDS), d, n, BARS), dtype=np.float32)
    shock = rng.normal(0, 0.0034, (d, n, BARS)).astype(np.float32)
    shock += rng.normal(0, 0.0019, (d, 1, BARS)).astype(np.float32)
    hot = (rng.random(d) < .18)
    shock *= np.where(hot, 2.2, .8)[:, None, None]
    shock -= .5 * (0.0034**2 + 0.0019**2) * np.where(hot, 2.2, .8)[:, None, None]**2
    shock *= full[:, None, :]
    gap = rng.normal(-0.00005, 0.010, (d, n)).astype(np.float32)
    if case == 'drift':
        gap[:] = 0.018  # identical drift each night; no timed predictive information
        shock *= .025
    if case == 'plant':
        # Fix two isolated, causal blocks for fake sector member 07, the rest pure noise.
        # One signal interval ends at 15:25 and an independent reward starts strictly after 15:30.
        known = np.arange(d) % 4 == 0
        shock[:, 7, :] *= .05
        shock[known, 7, 9:70] += .042 / 61
        shock[known, 7, 74:78] += .030 / 4
    gap += np.vstack((np.zeros((1, n)), shock[:-1].sum(axis=2)))
    start = np.cumsum(gap, axis=0) if case == 'noise' else np.zeros((d, n))
    if case == 'drift':
        # Keep only the tiny within-day changes; additive drift would make all prices unaffordable.
        # The overnight return is put into the prior close versus next open without a price trend.
        shock[:, 0, 20:68] -= np.log(1.018) / 48
    open0 = 28 + np.arange(n) * .4
    log_close = np.cumsum(shock, axis=2)
    a[0, :, :, 0] = np.exp(start) * open0
    a[3] = a[0, :, :, :1] * np.exp(log_close)
    a[0, :, :, 1:] = a[3, :, :, :-1]
    a[1] = np.maximum(a[0], a[3]) * 1.0003
    a[2] = np.minimum(a[0], a[3]) * .9997
    a[4] = rng.lognormal(7, .75, size=(d, n, BARS)).astype(np.float32)
    a[5] = (a[0] + a[3]) / 2
    np.copyto(a, np.nan, where=~full[None, :, None, :])
    fake_grid = dict(grid, pools={pool: [names[i] for i, p in enumerate(source_pools)
                                         if set(grid['pools'][pool]) & set(grid['universe'].get(p, []))]
                                       for pool in grid['pools']}, measured_cost_symbols={})
    # Fake 11 plays the role of SPY in the relative basis calculation, but no real bars are loaded.
    fake_grid['rules'] = [dict(r, signal=dict(r['signal'], benchmark=names[11])) if r['family'] == 'S5' else r
                          for r in grid['rules']]
    fake_grid['measured_cost_symbols'] = {
        'broad': [names[11], names[12]], 'bond': [names[13]], 'stocks': list(names[:3]),
        'sector': list(names[7:10]),
    }
    return Tape([s[0] for s in sessions], names, a, early_lengths, np.ones((d, n))), fake_grid


def assert_raises(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError('Expected a ValueError')


def internal_tests(grid):
    poison = date(2022, 1, 3)
    assert_raises(lambda: date_fence(FIRST, poison))
    assert_raises(lambda: session_list(FIRST, poison))
    assert_raises(lambda: next(bars_pages('FAKE', FIRST, poison, lambda _: 1 / 0)))
    assert_raises(lambda: next(bars_pages('FAKE', FIRST, LAST, lambda _: {
        'bars': {'FAKE': [{'t': '2022-01-03T14:30:00Z'}]}})))
    assert_raises(lambda: guard_stamp('2022-01-01T00:01:00Z', FIRST, LAST))
    assert_raises(lambda: Tape([FIRST, poison], ('FAKE',), None, None, None))
    touched = []

    def mock_page(q):
        touched.append(dict(q))
        return {'bars': {'FAKE': [{'t': '2016-01-04T14:30:00Z'}]},
                'next_page_token': None if len(touched) > 1 else 'next'}
    assert len(list(bars_pages('FAKE', FIRST, LAST, mock_page))) == 2
    assert touched[0]['feed'] == 'sip' and touched[0]['timeframe'] == '5Min' and touched[0]['asof'] == '-'
    assert touched[1]['page_token'] == 'next' and touched[1]['end'].startswith('2021-12-31')
    assert math.isclose(clustered([(0, .03), (1, -.01), (2, .02)]), np.mean([.03, -.01, .02]) / (
        np.std([.03, -.01, .02], ddof=1) / math.sqrt(3)))
    assert settlement_delay(date(2017, 9, 1)) == 3 and settlement_delay(date(2017, 9, 5)) == 2
    assert not clearing_session(date(2018, 10, 8)) and not clearing_session(date(2018, 11, 12))
    assert trim_mean(np.array([0., 1., 100.])) == .5
    assert overlap_corr({1: 1, 2: 2, 4: 4}, {1: 11, 2: 12, 4: 14, 8: 1}) > .7
    assert overlap_corr({1: 1, 2: 2, 4: 4}, {1: -11, 2: -12, 4: -14}) < -.7

    tape, fake = synthetic_tape(grid, 691000, 'plant')
    res = search(tape, fake)
    found = [r for r in res if r['status'] == 'finalist' and r['family'] == 'S1']
    if not found:
        raise AssertionError(f'Planted S1 not found: {[r for r in res if r["family"] == "S1"]}')
    # Every executable rule: poison all its signal-day bars whose closing time is >= entry,
    # including the entry-bar open and exit print, and all future days. Prior dates are invariant.
    for r in fake['rules']:
        if not r['cash_500']:
            continue
        i, _ = print_spec(r['entry'])
        for d in (251, 808):
            alt = tape.a.copy()
            alt[:, d, :, max(0, i - 1):] *= 17
            alt[:, d + 1:] *= 5
            probe = Tape(tape.dates, tape.names, alt, tape.lengths, tape.splits)
            before = tape.signals(r, fake)[d]
            after = probe.signals(r, fake)[d]
            if (not np.array_equal(before, after) or not np.array_equal(
                    tape.sizing_reference(i)[d], probe.sizing_reference(i)[d], equal_nan=True)):
                raise AssertionError(f'Entry selection looked ahead: {r["id"]}')
    print(json.dumps({'test': 'plant_and_no_lookahead', 'found': [r['id'] for r in found],
                      'prospective_rules_tested': sum(r['cash_500'] for r in fake['rules']),
                      'date_fence_mocked_pages': True}), flush=True)

    tape, fake = synthetic_tape(grid, 691001, 'drift')
    r = {'id': 'always-long-overnight-control', 'family': 'TEST', 'signal': {}, 'pool': 'drift_control',
         'cash_500': True, 'side': 'long', 'latest_signal_close_et': None,
         'entry': {'clock_et': '16:00', 'print': 'close'},
         'exit': {'clock_et': '09:35', 'print': 'open', 'session_offset': 1}}
    fake['pools']['drift_control'] = [tape.names[0]]
    row = search(tape, dict(fake, rules=[r]))[0]
    if not (row['annual_net_500'] >= .12 and row['net_mean'] > 0 and row['trades'] >= 200
            and row['t'] < 3.5 and row['status'] == 'miss'):
        raise AssertionError(f'Positive upward drift did not demonstrate the matched-baseline guard: {row}')
    print(json.dumps(row | {'test': 'upward_drift'}), flush=True)


def power():
    # Whole mark, conditional one true rule with zero gross clock baseline, one trade per day,
    # equal halves, no duplicate competitor, fixed 90% deployed, fixed trade counts.
    rng = np.random.default_rng(690001)
    for n in (200, 400, 480):
        for sd in (.005, .010, .020):
            simulations = 20000
            x = rng.normal(0, sd, (simulations, n))
            avg = x.mean(axis=1)
            se = x.std(axis=1, ddof=1) / np.sqrt(n)
            h = x.reshape(simulations, 2, n // 2)
            ha = h.mean(axis=2)
            hs = h.std(axis=2, ddof=1) / np.sqrt(n // 2)
            trim = np.sort(x, axis=1)[:, :-math.ceil(n / 100)].mean(axis=1)
            min_edge = np.maximum.reduce([3.5 * se - avg,
                                         np.max(1.5 * hs - ha, axis=1),
                                         .12 * YEARS / (n * .9) - avg, -trim])
            p50, p80 = np.quantile(min_edge, [.50, .80])
            print(json.dumps({'test': 'power', 'trades': n, 'days': n, 'sd_bp': sd * 1e4,
                              'simulations': simulations, 'net_edge_bp_50': round(p50 * 1e4, 2),
                              'net_edge_bp_80': round(p80 * 1e4, 2)}))


def synthetic(grid):
    internal_tests(grid)
    failures, max_t = [], -np.inf
    reached_floors = set()
    max_eligible_by_seed = 0
    for seed in range(690100, 690200):
        tape, fake = synthetic_tape(grid, seed)
        rows = search(tape, fake)
        hits = [r['id'] for r in rows if r['status'] == 'finalist']
        eligible = [r for r in rows if r['status'] in {'finalist', 'duplicate', 'cap', 'miss'}]
        max_eligible_by_seed = max(max_eligible_by_seed, len(eligible))
        for r in eligible:
            max_t = max(max_t, r['t'])
            reached_floors.add(r['family'])
        if hits:
            failures.append({'seed': seed, 'rules': hits})
    print(json.dumps({'test': 'whole_mark_pure_noise', 'clean_seeds': 100 - len(failures),
                      'first_seed': 690100, 'last_seed': 690199, 'all_registered_rules': len(grid['rules']),
                      'families_with_any_rule_at_floors': sorted(reached_floors),
                      'max_rules_reaching_floors_in_seed': max_eligible_by_seed,
                      'largest_t_among_rules_at_floors': round(max_t, 6), 'failures': failures}), flush=True)
    if len(failures) > 5:
        raise ValueError('Synthetic luck gate failed: stop. No rule, cost, seed or mark was retuned.')
    power()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    for name in ('collect', 'search', 'synthetic'):
        mode.add_argument('--' + name, action='store_true')
    p.add_argument('--start', type=date.fromisoformat, default=FIRST)
    p.add_argument('--end', type=date.fromisoformat, default=LAST)
    args = p.parse_args()
    date_fence(args.start, args.end)
    grid = load_grid()
    if args.collect:
        collect(grid, args.start, args.end)
    else:
        # Missing feature windows are represented by NaN and can never select a candidate.
        with np.errstate(invalid='ignore', divide='ignore'):
            if args.synthetic:
                if (args.start, args.end) != (FIRST, LAST):
                    raise ValueError('Synthetic fixtures use the whole frozen search calendar')
                synthetic(grid)
            else:
                for row in search(load_collection(grid, args.start, args.end), grid):
                    print(json.dumps({k: (None if isinstance(v, float) and not math.isfinite(v) else v)
                                      for k, v in row.items()}, allow_nan=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as e:
        sys.exit(str(e))
