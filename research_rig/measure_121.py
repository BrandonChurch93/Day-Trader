"""M121. Run --selftest on invented data; no historical access without a lead go.

The custodian runs the approved command inside its host-scoped credential proxy.
Only the proxy address is visible to this program; it is never written or printed.
See the accompanying test module and signed doc 166 for the decision rules.

Input handoff (all paths relative to the private M121 store):
* Place the hash-pinned roster_before_draw.json and price-free inputs.json in the
  store. Each fund_brackets entry names ticker and before/after references, each
  with accession and sha256, and a filing_list reference with sha256 and
  response_sha256. Put price-free extracts from the two filings and the frozen
  filing-list walk at evidence/<sha256>. The bracket is not daily listing proof. Each
  halt_days entry names session, coverage, and intervals (ticker, start, resume);
  when coverage or events are asserted, give its official source url and sha256.
  Put exact evidence bytes at evidence/<sha256>. The manifest has a
  config_sha256 and covers every originally selected fund. The validator checks
  the extracted rows, dates, identity and filing-list outcome; substantive
  independent review ties the extracts to the raw sources and filing order.
* --validate-inputs is local only. It prints the pinned *_sha256 fields to carry
  into GO.json, as well as current coverage counts and free bytes. The lead also
  writes authorization_id into GO.json and appends exactly
  ; Approved for one M121 historical pull: `M121_GO=<authorization_id>`
  at the end of the status cell in ledger row 223. The
  ledger_sha256 field is the hash of that final ledger file.
* Neither an empty go file nor the plan signature authorizes a pull. The
  custodian and lead must preserve the exclusive RUN.lock permanently, even
  on failure (it contains only price-free stop counts and input hashes), and
  verify the wrapper process group's resource budget before authorizing a real
  run. No incomplete result is reusable.
"""

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal, DecimalException, ROUND_CEILING
from fractions import Fraction
import gzip
import hashlib
import io
import json
from math import lcm
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import stat
import sys
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
STORE = Path('/home/user/workspace/rig/data/m121')
PLAN = ROOT / 'docs/research/166_m121_cef_resting_bid.md'
LEDGER = ROOT / 'research_rig/TRIAL_LEDGER.md'
CONFIG = ROOT / 'config/thresholds.yaml'
SIGNED_CONFIG = 'fe2e5a2b3ec734e0f632e9821c3d731fb766b5ab70117f937ac1e744d41ac1f0'
SIGNED_TEXT = '3143f7c7fe021d108e0528fcb2403fc48fc81e2812865c6eb37eed8c1e3b91b1'
SIGNED_AMENDMENT = '850f79840c1cc66f09d0bd5719af2b11442ea1b05569b9897477020edaab2e1a'
SIGNED_AMENDMENT_2 = '227b317db2780bcf5bf9f46597dad73083e4531509fba7c49b275d322ce5307e'
AMENDMENT_IDENTITY_EXCLUDED = frozenset({'FSCO'})
BRACKET_GAP = ('Two dated filings do not establish daily listing or rule out a ticker changing and changing back, '
               'or a historical vendor-feed ticker collision with another issuer.')
HOST = 'data.alpaca.markets'
MIB = 2**20
NS = 10**9
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
TIME_RE = re.compile(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(Z|[+-]\d\d:\d\d)')
SHA_RE = re.compile(r'[0-9a-f]{64}')
ACCESSION_RE = re.compile(r'[0-9]{10}-[0-9]{2}-[0-9]{6}')
TOKEN_RE = re.compile(r'[A-Za-z0-9_-]+')


class Stop(Exception):
    """A price-free stop code. Never put vendor content in the message."""


def require(ok, code):
    if not ok:
        raise Stop(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def pairs(items):
        out = dict(items)
        require(len(items) == len(out), 'duplicate_json_key')
        return out

    def invalid(_):
        raise Stop('nonfinite_json')

    return json.loads(raw, parse_float=Decimal, parse_constant=invalid, object_pairs_hook=pairs)


def json_bytes(obj):
    return (json.dumps(obj, sort_keys=True, allow_nan=False, separators=(',', ':')) + '\n').encode()


def timestamp(value):
    match = TIME_RE.fullmatch(value) if isinstance(value, str) else None
    if not match:
        return None
    prefix, fraction, zone = match.groups()
    if zone != 'Z' and (int(zone[1:3]) >= 24 or int(zone[4:]) >= 60):
        return None
    try:
        delta = datetime.fromisoformat(prefix + ('+00:00' if zone == 'Z' else zone)) - EPOCH
    except ValueError:
        return None
    return (delta.days * 24 * 60 * 60 + delta.seconds) * NS + int((fraction or '').ljust(9, '0'))


def wall(day, clock, zone):
    return timestamp(datetime.combine(date.fromisoformat(day), time.fromisoformat(clock), zone).isoformat())


def money(value):
    if type(value) not in (int, Decimal):
        return None
    try:
        n = Decimal(value)
        return n if n.is_finite() and n > 0 else None
    except DecimalException:
        return None


def quantity(value):
    return value if type(value) is int and value > 0 else None


def text(value):
    return value if isinstance(value, str) and value else None


def condition(value):
    return tuple(value) if isinstance(value, list) and all(isinstance(x, str) for x in value) else None


@dataclass(frozen=True)
class Settings:
    limits: dict
    sample: dict
    order: dict
    report: dict
    sizing: dict
    sha: str
    plan_sha: str
    excluded_tickers: frozenset

    def schedule(self):
        return [(group, ticker, day) for day in self.sample['sessions']
                for group in self.sample['walk_type_order']
                for ticker in self.sample['selected_in_hash_order'][group]]

    @property
    def page_cap(self):
        return self.limits['wire_and_decoded_page_cap_mib_each'] * MIB

    def clocks(self, day):
        o = self.order
        zone = ZoneInfo(o['time_zone'])
        return (wall(day, o['core_open'], zone), wall(day, o['core_close'], zone),
                wall(day, o['close_bid_clock'], zone), [wall(day, s, zone) for s in o['placement_times']])


def settings():
    import yaml

    raw, plan = CONFIG.read_bytes(), PLAN.read_bytes()
    base, marker, signature = plan.partition(b'### Signature')
    _, heading, tail = signature.partition(b'### Amendment 1')
    first_tail, second_heading, second_tail = tail.partition(b'### Amendment 2')
    amendment = (heading + first_tail).rstrip(b'\n') + b'\n'
    amendment_2 = (second_heading + second_tail.partition(b'### Identity evidence gaps')[0]).rstrip(b'\n') + b'\n'
    require(digest(raw) == SIGNED_CONFIG and bool(marker) and bool(signature.strip())
            and digest(base.rstrip(b'\n') + b'\n') == SIGNED_TEXT
            and digest(amendment) == SIGNED_AMENDMENT and digest(amendment_2) == SIGNED_AMENDMENT_2,
            'signed_configuration_or_text')
    values = yaml.safe_load(raw)
    c = Settings(*(values[f'm121_{k}']['value'] for k in ('limits', 'sample', 'order', 'reporting', 'sizing')),
                 digest(raw), digest(plan), AMENDMENT_IDENTITY_EXCLUDED)
    L, o = c.limits, c.order
    require(L['workers'] == 1 and not L['retry_cap']
            and L['job_disk_cap_mib'] + L['job_memory_cap_mib'] < L['job_total_peak_mib_exclusive']
            and L['kept_order_rows_cap_mib'] < L['job_disk_cap_mib']
            and L['max_kept_bytes_per_order'] * L['planned_order_slots'] <= L['kept_order_rows_cap_mib'] * MIB
            and c.page_cap <= L['decoded_bytes_cap_per_day_mib'] * MIB
            and len(c.schedule()) == len(set(c.schedule())) == L['planned_fund_days']
            and L['planned_fund_days'] * len(o['placement_times']) == L['planned_order_slots'], 'config_caps')
    for day in c.sample['sessions']:
        start, end, close, slots = c.clocks(day)
        require(start < slots[0] and close < end
                and all(b - a == o['rest_seconds'] * NS for a, b in zip(slots, slots[1:]))
                and slots[-1] + (o['entry_delay_seconds'] + o['rest_seconds']
                                 + max(o['mark_seconds_after_fill'].values())) * NS < close, 'config_clocks')
    return c


class Paged:
    """No retry. Count attempts before calling the injected transport."""

    def __init__(self, cfg, get):
        self.cfg, self.get = cfg, get
        self.requests = self.wire = self.decoded = self.day_decoded = 0

    def records(self, symbol, day, endpoint):
        require(endpoint in ('quotes', 'trades'), 'bad_endpoint')
        o = self.cfg.order
        zone = ZoneInfo(o['time_zone'])
        args = dict(start=datetime.combine(date.fromisoformat(day), time.fromisoformat(o['core_open']), zone).isoformat(),
                    end=datetime.combine(date.fromisoformat(day), time.fromisoformat(o['core_close']), zone).isoformat(),
                    asof=day, feed='sip', sort='asc', limit=self.cfg.limits['request_page_rows'])
        require(re.fullmatch(r'[A-Z0-9.]+', symbol), 'bad_ticker')
        url = f'https://{HOST}/v2/stocks/{symbol}/{endpoint}'
        seen, last, pages = set(), None, 0
        while True:
            require(self.requests < self.cfg.limits['history_requests_total']
                    and pages < self.cfg.limits['pages_per_endpoint_per_day'], 'request_cap')
            require(self.day_decoded < self.cfg.limits['decoded_bytes_cap_per_day_mib'] * MIB, 'day_decoded_cap')
            self.requests += 1
            pages += 1
            raw, wire = self.get(url, dict(args), min(self.cfg.page_cap,
                                 self.cfg.limits['decoded_bytes_cap_per_day_mib'] * MIB - self.day_decoded),
                                 self.cfg.page_cap)
            require(wire <= self.cfg.page_cap and len(raw) <= self.cfg.page_cap, 'page_cap')
            self.day_decoded += len(raw)
            self.decoded += len(raw)
            self.wire += wire
            require(self.day_decoded <= self.cfg.limits['decoded_bytes_cap_per_day_mib'] * MIB, 'day_decoded_cap')
            page = strict_json(raw)
            del raw
            require(isinstance(page, dict) and 'next_page_token' in page and endpoint in page
                    and page.get('symbol', symbol) == symbol, 'page_shape_or_symbol')
            items, token = page[endpoint], page['next_page_token']
            # Alpaca uses null as well as [] for an empty terminal single-symbol response.
            require((items is None and token is None) or isinstance(items, list), 'page_rows_shape')
            require(items is None or len(items) <= args['limit'], 'page_row_cap')
            if token is not None:
                require(isinstance(token, str) and bool(token.strip()) and token not in seen, 'bad_or_repeated_cursor')
                require(pages < self.cfg.limits['pages_per_endpoint_per_day']
                        and self.requests < self.cfg.limits['history_requests_total'], 'nonterminal_at_cap')
                seen.add(token)
            for item in items or ():
                require(isinstance(item, dict), 'page_row_shape')
                ns = timestamp(item.get('t'))
                if ns is not None:
                    require(last is None or ns >= last, 'page_timestamp_regression')
                    last = ns
                yield item, ns
            if token is None:
                return
            del page, items
            args['page_token'] = token


def read_page(response, decoded_cap, wire_cap):
    require(response.status_code == 200, 'vendor_http_status')
    encoding = (response.headers.get('Content-Encoding') or 'identity').strip().lower()
    require(encoding in ('identity', 'gzip'), 'vendor_encoding')
    advertised = response.headers.get('Content-Length')
    if advertised is not None:
        require(advertised.isdecimal() and int(advertised) <= wire_cap, 'wire_page_cap')
    wire = bytearray()
    while True:
        chunk = response.raw.read(min(io.DEFAULT_BUFFER_SIZE, wire_cap - len(wire) + 1), decode_content=False)
        if not chunk:
            break
        wire.extend(chunk)
        require(len(wire) <= wire_cap, 'wire_page_cap')
        require(encoding != 'identity' or len(wire) <= decoded_cap, 'decoded_page_cap')
    require(advertised is None or len(wire) == int(advertised), 'wire_length_mismatch')
    if encoding == 'identity':
        return wire, len(wire)
    with gzip.GzipFile(fileobj=io.BytesIO(wire)) as stream:
        raw = stream.read(decoded_cap + 1)
    require(len(raw) <= decoded_cap, 'decoded_page_cap')
    return raw, len(wire)


class Quotes:
    def __init__(self, cfg, rows, start, end):
        self.cfg, self.times, self.data, self.malformed_clock = cfg, [], [], False
        self.conditions = Counter()
        for r, ns in rows:
            if ns is None:
                self.malformed_clock = True
                continue
            if not start <= ns < end:
                continue
            c = condition(r.get('c'))
            self.conditions['unsupported' if c is not None and c not in self.allowed else
                            'allowed' if c is not None else 'malformed'] += 1
            q = (money(r.get('bp')), money(r.get('ap')), quantity(r.get('bs')), quantity(r.get('as')),
                 text(r.get('bx')), text(r.get('ax')), text(r.get('z')), c)
            if self.times and ns == self.times[-1]:
                if q != self.data[-1]:
                    self.data[-1] = None
            else:
                self.times.append(ns)
                self.data.append(q)

    @property
    def allowed(self):
        return tuple(map(tuple, self.cfg.order['continuous_quote_condition_arrays']))

    def at(self, target, halts, entry=False):
        o = self.cfg.order
        if any(a <= target and (b is None or target <= b) for a, b in halts):
            return None, 'halt'
        if self.malformed_clock:
            return None, 'quote_bad_timestamp'
        i = bisect_left(self.times, target)
        if i < len(self.times) and self.times[i] == target:
            return None, 'quote_exact_boundary'
        if not i:
            return None, 'quote_absent'
        ns, q = self.times[i - 1], self.data[i - 1]
        if any(b is not None and ns <= b < target for _, b in halts):
            return None, 'quote_before_resumption'
        if target - ns > o['quote_max_age_seconds'] * NS:
            return None, 'quote_stale'
        if q is None:
            return None, 'quote_conflict'
        bid, ask, bs, az, bx, ax, tape, c = q
        if any(x is None for x in q):
            return None, 'quote_critical_field'
        if (ask <= bid or c not in self.allowed or tape != self.cfg.sample['tape']
                or bx not in o['eligible_continuous_lit_venues'] or ax not in o['eligible_continuous_lit_venues']):
            return None, 'quote_ineligible'
        if entry and (bid < Decimal(o['min_bid_usd']) or Fraction(bid) % Fraction(o['tick_usd'])):
            return None, 'quote_bid_grid_or_floor'
        return q, None


def base_row(group, ticker, day, clock, state='unknown', reason=None):
    return dict(g=group, sym=ticker, day=day, clock=clock, state=state, reason=reason)


def unknown_day(cfg, group, ticker, day, reason):
    return [base_row(group, ticker, day, clock, reason=reason) for clock in cfg.order['placement_times']]


def halt_overlap(halts, placement, live, expiry):
    return any((a <= placement and (b is None or b >= placement))
               or (a < expiry and (b is None or b >= live)) for a, b in halts)


def measure_day(cfg, group, ticker, day, quote_rows, trade_rows, halts=()):
    start, end, close, clocks = cfg.clocks(day)
    o = cfg.order
    q = Quotes(cfg, quote_rows, start, end)
    rows = unknown_day(cfg, group, ticker, day, None)
    lives = [t + o['entry_delay_seconds'] * NS for t in clocks]
    expiries = [t + o['rest_seconds'] * NS for t in lives]
    orders = {}
    stats = Counter({f'quote_{k}': v for k, v in q.conditions.items()})
    for i, (place, live, expiry, row) in enumerate(zip(clocks, lives, expiries, rows)):
        if halt_overlap(halts, place, live, expiry):
            row['reason'] = 'halt_order'
            continue
        entry, reason = q.at(place, halts, entry=True)
        if reason:
            row['reason'] = 'placement_' + reason
            continue
        limit, ask, _, _, venue, *_ = entry
        size = int(Fraction(o['notional_usd']) // Fraction(limit))
        row.update(l=str(limit), a=str(ask), size=size)
        if not size:
            row.update(state='not_placed', reason='no_whole_shares')
            continue
        act, reason = q.at(live, halts)
        if reason:
            row['reason'] = 'activation_' + reason
            continue
        if act[0] != limit or act[4] != venue or act[1] <= limit:
            row.update(state='not_placed', reason='activation_moved')
            continue
        orders[i] = (limit, size, venue)

    tape = cfg.sample['tape']
    allowed = tuple(map(tuple, o['eligible_trade_condition_arrays']))
    cut = Fraction(o['tick_usd']) * o['through_ticks']
    first, uncertain, ids, collisions = {}, {}, {}, set()
    trade_count = 0
    for r, ns in trade_rows:
        if ns is not None and not start <= ns < end:
            continue
        trade_count += ns is not None
        x, z, c = text(r.get('x')), text(r.get('z')), condition(r.get('c'))
        if x is not None and (x == o['finra_trade_venue'] or x not in o['eligible_continuous_lit_venues']):
            stats['off_exchange' if x == o['finra_trade_venue'] else 'unknown_venue'] += 1
            continue
        p, s = money(r.get('p')), quantity(r.get('s'))
        identifier = r.get('i')
        key = (x, identifier) if x is not None and type(identifier) is int and identifier >= 0 else None
        if key is not None:
            normalized = ns, z, c, p, s
            if key in ids and ids[key] != normalized:
                collisions.add(key)
            else:
                ids[key] = normalized
        if ns is None:
            candidates = orders
        else:
            idx = bisect_right(lives, ns) - 1
            candidates = (idx,) if idx in orders and lives[idx] < ns < expiries[idx] else ()
        for i in candidates:
            limit, size, venue = orders[i]
            failures = {'trade_other_venue': x is not None and x != venue,
                        'trade_other_tape': z is not None and z != tape,
                        'trade_unsupported_condition': c is not None and c not in allowed,
                        'trade_not_through': p is not None and Fraction(p) > Fraction(limit) - cut,
                        'trade_short_size': s is not None and s < size}
            if any(failures.values()):
                stats.update(k for k, failed in failures.items() if failed)
                continue
            if any(v is None for v in (ns, x, z, c, p, s, key)):
                possible = ns if ns is not None else lives[i]
                uncertain[i] = min(uncertain.get(i, possible), possible)
                stats['trade_critical_field'] += 1
                continue
            if i not in first:
                first[i] = (ns, {key})
            elif ns == first[i][0]:
                first[i][1].add(key)

    if not trade_count:
        for i in orders:
            rows[i]['reason'] = 'trade_critical_field' if i in uncertain else 'trade_stream_empty'
        return rows, stats
    for i, (_, size, _) in orders.items():
        row = rows[i]
        hit = first.get(i)
        if (i in uncertain and (hit is None or uncertain[i] <= hit[0])) or (hit and hit[1] <= collisions):
            row['reason'] = 'trade_conflicting_id' if hit and hit[1] <= collisions else 'trade_critical_field'
            continue
        if hit is None:
            row.update(state='unfilled', reason='no_qualifying_print')
            continue
        fill = hit[0]
        kinds = {'odd_lot' if len(ids[k][2]) > 1 else 'regular' for k in hit[1] - collisions}
        row.update(state='filled', reason=None, fill=fill, marks={}, print_kind=next(iter(kinds)) if len(kinds) == 1 else 'mixed_tie')
        marks = {label: fill + secs * NS for label, secs in o['mark_seconds_after_fill'].items()}
        marks['close'] = close
        for label, horizon in marks.items():
            mark, reason = q.at(horizon, halts)
            if reason:
                row['marks'][label] = reason
            elif mark[2] * o['round_lot_shares'] < size:
                row['marks'][label] = 'quote_bid_size'
            else:
                row['marks'][label] = [str(mark[0]), str(mark[1])]
    return rows, stats


def vector(row, cfg):
    """Per-slot sufficient statistics. Pairs are numerator/denominator."""
    filled = row['state'] == 'filled'
    placed = filled or row['state'] == 'unfilled'
    out = {'fill_per_scheduled': (int(filled), 1), 'known_share': (int(row['state'] != 'unknown'), 1),
           'fill_rate': (int(filled), int(placed)), 'no_fill_rate': (int(placed and not filled), int(placed)),
           'no_placement_per_scheduled': (int(row['state'] == 'not_placed'), 1),
           'unknown_per_scheduled': (int(row['state'] == 'unknown'), 1)}
    medians = {}
    if 'l' in row:
        L, A = map(Fraction, (row['l'], row['a']))
        scale = cfg.report['bps_scale']
        def metric(key, x):
            out[key + '_usd'] = (x, 1)
            out[key + '_bps'] = (x * scale / L, 1)
            medians[key + '_usd'] = x
            medians[key + '_bps'] = x * scale / L

        if filled:
            metric('entry_ask_saved', A - L)
            midpoint = (L + A) / 2
            for label, value in row['marks'].items():
                available = isinstance(value, list)
                out[label + '_coverage'] = (int(available), 1)
                if not available:
                    continue
                bid, ask = map(Fraction, value)
                Mh = (bid + ask) / 2
                metric(label + '_gross', bid - L)
                metric(label + '_adverse', midpoint - Mh)
                metric(label + '_entry_half', midpoint - L)
                metric(label + '_exit_concession', Mh - bid)
                out[label + '_fraction_kept'] = (bid - L, midpoint - L)
    return out, medians


def ordinal(p, n):
    return max(1, int((Decimal(str(p)) * n).to_integral_value(rounding=ROUND_CEILING)))


def inference(rows, cfg, method):
    """Resample complete scheduled clusters (including all-unknown clusters)."""
    import numpy as np

    keys = sorted({(r['g'], r['sym'], r['day']) if method == 'fund_day' else r['day'] for r in rows})
    order = {k: i for i, k in enumerate(keys)}
    n = len(keys)
    groups = ['pooled', *cfg.sample['walk_type_order']]
    obs = defaultdict(lambda: defaultdict(list))
    mds = defaultdict(lambda: defaultdict(list))
    primary = defaultdict(Fraction)
    primary_n = defaultdict(int)
    threshold = Fraction(str(cfg.report['gross_bid_markout_lower_bound_bps_strictly_above']))
    horizon_keys = [*cfg.order['mark_seconds_after_fill'], 'close']
    amounts = [f'{h}_{m}' for h in horizon_keys for m in ('gross', 'adverse', 'entry_half', 'exit_concession')]
    amount_units = [f'{m}_{u}' for m in ['entry_ask_saved', *amounts] for u in ('usd', 'bps')]
    for group in groups:
        for key in [*amount_units, *(f'{h}_{m}' for h in horizon_keys for m in ('coverage', 'fraction_kept'))]:
            obs[group][key] = []
    for r in rows:
        i = order[(r['g'], r['sym'], r['day']) if method == 'fund_day' else r['day']]
        vals, median_vals = vector(r, cfg)
        for group in ('pooled', r['g']):
            for key, (x, y) in vals.items():
                obs[group][key].append((i, x, y))
            for key, x in median_vals.items():
                mds[group][key].append((i, x))
        if 'primary_gross_bps' in vals:
            primary[i] += vals['primary_gross_bps'][0] - threshold
            primary_n[i] += 1
    matrix, median_specs = [], []
    labels, totals = [], []
    for group in groups:
        for key, data in sorted(obs[group].items()):
            a = np.zeros(n)
            b = np.zeros(n)
            for i, x, y in data:
                a[i] += float(x)
                b[i] += float(y)
            matrix.extend((a, b))
            labels.append((group, key))
            den = sum(y for _, _, y in data)
            totals.append(float(sum(x for _, x, _ in data) / den) if den else None)
        for key, data in sorted(mds[group].items()):
            seq = sorted(data, key=lambda v: v[1])
            ids = np.array([i for i, _ in seq])
            numbers = np.array([float(x) for _, x in seq])
            median_specs.append((group, key, ids, numbers))
    matrix = np.asarray(matrix).T
    by_group = ({g: [i for i, k in enumerate(keys) if k[0] == g] for g in cfg.sample['walk_type_order']}
                if method == 'fund_day' else {'all': list(range(n))})
    rng = np.random.default_rng(cfg.report['bootstrap_seed'])
    runs = cfg.report['bootstrap_draws']
    out = defaultdict(lambda: np.full(runs, np.nan))
    exact_den = lcm(*(x.denominator for x in primary.values()))
    exact = [(i, int(x * exact_den)) for i, x in primary.items() if x]
    all_primary_counts = np.array([primary_n[i] for i in range(n)])
    undefined_primary = nonpositive = 0
    # Median expansion is draw-by-order, even when there are few date clusters.
    widest = max([n, *(len(ids) for _, _, ids, _ in median_specs)])
    chunk = max(1, io.DEFAULT_BUFFER_SIZE // widest)
    for start in range(0, runs, chunk):
        count = min(chunk, runs - start)
        weights = np.zeros((count, n), dtype=np.int32)
        # Interleave draws identically irrespective of batch size.
        for w in weights:
            for indexes in by_group.values():
                if indexes:
                    draws = rng.integers(len(indexes), size=len(indexes))
                    w[indexes] = np.bincount(draws, minlength=len(indexes))
        reduced = weights @ matrix
        for j, label in enumerate(labels):
            den = reduced[:, j * 2 + 1]
            ok = den > 0
            out[label][start + np.flatnonzero(ok)] = reduced[ok, j * 2] / den[ok]
        for group, key, ids, values in median_specs:
            cs = np.cumsum(weights[:, ids], axis=1)
            size = cs[:, -1]
            ok = size > 0
            low = np.sum(cs[ok] < ((size[ok] + 1) // 2)[:, None], axis=1)
            high = np.sum(cs[ok] < (size[ok] // 2 + 1)[:, None], axis=1)
            out[group, key + '_median'][start + np.flatnonzero(ok)] = (values[low] + values[high]) / 2
        for weight, count_primary in zip(weights, weights @ all_primary_counts):
            if not count_primary:
                undefined_primary += 1
            elif sum(int(weight[i]) * x for i, x in exact) <= 0:
                nonpositive += 1

    p = Decimal(str(cfg.report['interval_tail_probability']))
    def interval(xs=None):
        if xs is None:
            return dict(lower=None, upper=None, undefined_draws=runs)
        xs = xs[np.isfinite(xs)]
        xs.sort()
        return dict(lower=float(xs[ordinal(p, len(xs)) - 1]) if len(xs) else None,
                    upper=float(xs[ordinal(1 - p, len(xs)) - 1]) if len(xs) else None,
                    undefined_draws=runs - len(xs))

    groups_out = {g: {} for g in groups}
    for label, point in zip(labels, totals):
        g, key = label
        groups_out[g][key] = dict(estimate=point, **interval(out[label]))
    for g, key, _, values in median_specs:
        groups_out[g][key + '_median'] = dict(estimate=float(np.median(values)), **interval(out[g, key + '_median']))
    for group in groups:
        for key in amount_units:
            groups_out[group].setdefault(key + '_median', dict(estimate=None, **interval()))
    primary_row = groups_out['pooled'].setdefault('primary_gross_bps', dict(estimate=None, **interval()))
    require(primary_row['undefined_draws'] == undefined_primary, 'primary_bootstrap_inconsistent')
    primary_row.update(exact_lower_above_gate=not undefined_primary and nonpositive < ordinal(p, runs),
                       nonpositive_to_gate_draws=int(nonpositive))
    return groups_out


def summarize(rows, cfg):
    methods = {m: inference(rows, cfg, m) for m in ('fund_day', 'calendar_day')}
    groups = cfg.sample['walk_type_order']
    by = {}
    floors = True
    all_primary_dates = set()
    params = cfg.report
    for g in ['pooled', *groups]:
        subset = [r for r in rows if g == 'pooled' or r['g'] == g]
        states = Counter(r['state'] for r in subset)
        filled = [r for r in subset if r['state'] == 'filled']
        marks = {k: [r for r in filled if isinstance(r['marks'][k], list)]
                 for k in [*cfg.order['mark_seconds_after_fill'], 'close']}
        days = {(r['sym'], r['day']) for r in marks['primary']}
        dates = {day for _, day in days}
        funds = {sym for sym, _ in days}
        all_primary_dates |= dates
        known = len(subset) - states['unknown']
        placed = states['filled'] + states['unfilled']
        if g != 'pooled':
            floors &= bool(subset) and Fraction(known, len(subset)) >= Fraction(str(params['min_known_slot_share_per_type']))
            floors &= bool(filled) and Fraction(len(marks['primary']), len(filled)) >= Fraction(str(params['min_primary_mark_coverage_per_type']))
            floors &= len(days) >= params['min_primary_marked_fund_days_per_type'] and len(funds) >= params['min_primary_marked_funds_per_type']
        by[g] = dict(scheduled=len(subset), states=dict(states), known_slots=known, evaluable_placed=placed,
                     fill_rate_headline=len(filled) / placed if placed else None,
                     mark_available={k: len(v) for k, v in marks.items()},
                     mark_gap_reasons={k: dict(Counter(r['marks'][k] for r in filled if not isinstance(r['marks'][k], list))) for k in marks},
                     reasons=dict(Counter(r['reason'] for r in subset if r['reason'])),
                     odd_lot_splits={state: dict(Counter('odd_lot' if r['size'] < cfg.order['round_lot_shares'] else
                                                       'mixed_lot' if r['size'] % cfg.order['round_lot_shares'] else 'round_lot'
                                                       for r in subset if r['state'] == state)) for state in ('filled', 'unfilled')},
                     fill_print_kind=dict(Counter(r['print_kind'] for r in filled)),
                     opening_spread_usd_distribution=dict(Counter(str(Decimal(r['a']) - Decimal(r['l'])) for r in subset if 'l' in r)),
                     order_share_count_distribution=dict(Counter(r['size'] for r in subset if 'size' in r)),
                     primary_marked_fund_days=len(days), primary_marked_dates=len(dates), primary_marked_funds=len(funds))
    floors &= len(all_primary_dates) >= params['min_primary_marked_dates']
    return dict(by_group=by, bootstrap=methods, coverage_floors_met=floors,
                consider_later_strategy_test=floors and all(m['pooled']['primary_gross_bps']['exact_lower_above_gate'] for m in methods.values()),
                claim='internal gross displayed-bid measurement, not execution or profit')


def private_dir(path):
    v = path.lstat()
    require(stat.S_ISDIR(v.st_mode) and stat.S_IMODE(v.st_mode) == 0o700 and v.st_uid == os.getuid(), 'private_store_mode')
    require(path.resolve() == path, 'private_store_symlink')


def private_read(path, cap):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as f:
        st = os.fstat(f.fileno())
        require(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid() and stat.S_IMODE(st.st_mode) == 0o600
                and st.st_nlink == 1 and st.st_size <= cap, 'private_input_mode_or_cap')
        payload = f.read(cap + 1)
    require(len(payload) <= cap, 'private_input_cap')
    return payload


def footprint(path):
    st = path.lstat()
    total = max(st.st_size, st.st_blocks * 512)
    if stat.S_ISDIR(st.st_mode):
        require(st.st_uid == os.getuid() and stat.S_IMODE(st.st_mode) == 0o700, 'private_descendant_mode')
        return total + sum(footprint(p) for p in path.iterdir())
    require(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid() and stat.S_IMODE(st.st_mode) == 0o600
            and st.st_nlink == 1, 'private_descendant_mode')
    return total


def headroom(cfg, store, increment=0):
    require(footprint(store) + increment <= cfg.limits['job_disk_cap_mib'] * MIB, 'job_disk_cap')
    free = shutil.disk_usage(store).free
    require(free - increment >= cfg.limits['min_host_free_mib'] * MIB, 'free_disk_floor')
    return free


def evidence_bytes(store, cfg, tag):
    require(isinstance(tag, str) and bool(SHA_RE.fullmatch(tag)), 'evidence_hash_format')
    raw = private_read(store / 'evidence' / tag, cfg.page_cap)
    require(bool(raw) and digest(raw) == tag, 'evidence_hash_mismatch')
    return raw


def source(url, hosts):
    p = urlsplit(url)
    return p.scheme == 'https' and p.netloc in hosts and bool(p.path.strip('/'))


def identity_source(url):
    p = urlsplit(url)
    return source(url, {'www.sec.gov'}) and (p.path.startswith('/Archives/edgar/data/')
            or (p.path.startswith('/files/dera/data/form-n-cen-data-sets/') and p.path.endswith('.zip')))


def filing_evidence(store, cfg, ref, cik):
    record = strict_json(evidence_bytes(store, cfg, ref['sha256']))
    require(record['accession'] == ref['accession'] and bool(ACCESSION_RE.fullmatch(ref['accession']))
            and type(record['cik']) is int and record['cik'] == cik
            and record['form'] in ('N-CEN', 'N-CEN/A') and identity_source(record['source_url'])
            and bool(SHA_RE.fullmatch(record['source_sha256'])) and isinstance(record['listings'], list), 'identity_filing_record')
    return record, date.fromisoformat(record['filed'])


def listing_matches(cfg, record, sym, class_title=None):
    return any(item['TICKER_SYMBOL'] == sym and item['EXCHANGE'] == cfg.sample['venue_primary']
               and item['DESCRIPTION'] == cfg.sample['form_common_stock_label']
               and (class_title is None or item['SECURITY_CLASS_TITLE'] == class_title) for item in record['listings'])


def inputs(cfg, store):
    """Validate local evidence only. No quote, trade, network, or secret access."""
    private_dir(store)
    free = headroom(cfg, store)
    roster = private_read(store / 'roster_before_draw.json', cfg.page_cap)
    require(digest(roster) == cfg.sample['roster_before_draw_sha256'], 'roster_hash')
    ids = {r['ticker']: r for r in strict_json(roster) if not r['rules']}
    raw = private_read(store / 'inputs.json', cfg.page_cap)
    obj = strict_json(raw)
    require(obj['config_sha256'] == cfg.sha, 'inputs_config_hash')
    expected = {(sym, day): group for group, sym, day in cfg.schedule()}
    expected_funds = {sym: group for (sym, _), group in expected.items()}
    first, last = map(date.fromisoformat, (min(cfg.sample['sessions']), max(cfg.sample['sessions'])))
    require(cfg.excluded_tickers <= expected_funds.keys(), 'identity_exclusion_schedule')
    walk_sha = cfg.sample['delisting_walk_sha256']
    walk = strict_json(evidence_bytes(store, cfg, walk_sha))
    require(walk['completed'] is True and walk['selected'] == cfg.sample['selected_in_hash_order'], 'identity_filing_walk')
    walked = {r['ticker']: r for r in walk['visited'] if r['outcome'] == 'pass'}
    require(walked.keys() == expected_funds.keys(), 'identity_filing_walk')
    proved = {}
    for item in obj['fund_brackets']:
        sym = item['ticker']
        require(sym in expected_funds and sym not in proved and ids[sym]['group'] == expected_funds[sym], 'identity_schedule')
        roster_row, hit = ids[sym], walked[sym]
        walk_ref = item['filing_list']
        require(walk_ref['sha256'] == walk_sha and bool(SHA_RE.fullmatch(walk_ref['response_sha256']))
                and hit['cik'] == roster_row['cik'] and hit['group'] == expected_funds[sym] and hit['forms'] == []
                and hit['body_sha256'] == walk_ref['response_sha256'], 'identity_filing_list')
        before, lo = filing_evidence(store, cfg, item['before'], roster_row['cik'])
        after, hi = filing_evidence(store, cfg, item['after'], roster_row['cik'])
        require(lo < first <= last < hi and after['form'] == 'N-CEN'
                and listing_matches(cfg, before, sym, roster_row['security_class']), 'identity_bracket')
        proved[sym] = listing_matches(cfg, after, sym)
        require(proved[sym] == (sym not in cfg.excluded_tickers), 'identity_amendment_exclusions')
    require(proved.keys() == expected_funds.keys(), 'identity_missing_fund')
    selected = {(sym, day): proved[sym] for sym, day in expected}

    coverage, halts, checked = {}, defaultdict(list), set()
    for item in obj['halt_days']:
        day = item['session']
        require(day in cfg.sample['sessions'] and day not in coverage
                and item['coverage'] in ('available', 'unavailable', 'partial'), 'halt_coverage')
        coverage[day] = item['coverage']
        if item['coverage'] != 'unavailable' or item['intervals']:
            require(source(item['url'], {'www.nyse.com', 'ftp.nyse.com'}), 'halt_source')
            if item['sha256'] not in checked:
                evidence_bytes(store, cfg, item['sha256'])
                checked.add(item['sha256'])
        start, end, _, _ = cfg.clocks(day)
        for event in item['intervals']:
            sym = event['ticker']
            require((sym, day) in expected and 'start' in event and 'resume' in event, 'halt_identity')
            a = start if event['start'] is None else timestamp(event['start'])
            b = None if event['resume'] is None else timestamp(event['resume'])
            require(a is not None and a < end and (event['resume'] is None or (b is not None and b >= a)), 'halt_timestamp')
            halts[sym, day].append((a, b))
    require(set(coverage) == set(cfg.sample['sessions']), 'halt_missing_session')
    info = dict(config_sha256=cfg.sha, plan_sha256=cfg.plan_sha, runtime_sha256=digest(Path(__file__).read_bytes()),
                inputs_sha256=digest(raw), roster_sha256=digest(roster),
                bracket_proved_fund_days=sum(selected.values()), bracket_excluded_fund_days=len(selected) - sum(selected.values()),
                halt_coverage=dict(Counter(coverage.values())))
    return info, selected, coverage, halts, free


def go_context(cfg, store):
    private_dir(store)
    go = strict_json(private_read(store / 'GO.json', cfg.page_cap))
    token = go.get('authorization_id')
    require(isinstance(token, str) and bool(TOKEN_RE.fullmatch(token)), 'go_authorization_id')
    ledger = LEDGER.read_bytes()
    marker = f'; Approved for one M121 historical pull: `M121_GO={token}`'.encode()
    rows = [line for line in ledger.splitlines() if line.startswith(b'| 223 |')]
    status = rows[0].rsplit(b'|', 2)[1].strip() if len(rows) == 1 and rows[0].endswith(b'|') else b''
    require(go.get('ledger_sha256') == digest(ledger) and status.endswith(marker)
            and rows[0].count(b'M121_GO=') == 1, 'go_ledger_not_authorized')
    info, selected, coverage, halts, _ = inputs(cfg, store)
    required = {k: v for k, v in info.items() if k.endswith('_sha256')}
    require(all(go.get(k) == v for k, v in required.items()), 'go_hash_mismatch')
    require(not (store / 'completed').exists() and not (store / '.building').exists() and not (store / 'STOP.json').exists(), 'prior_attempt_artifact')
    return token, info, selected, coverage, halts


def private_write(path, payload):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())


def disk_charge(store, payload, cfg):
    block = os.statvfs(store).f_frsize
    headroom(cfg, store, ((len(payload) + block - 1) // block + 1) * block)


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def execution(cfg, store, context, get):
    token, info, verified, coverage, halts = context
    pager = Paged(cfg, get)
    lock = store / 'RUN.lock'
    reserved = os.statvfs(store).f_frsize
    locked = json_bytes(dict(authorization_id=token, **info))
    require(len(locked) <= reserved, 'run_lock_payload_cap')
    disk_charge(store, b' ' * reserved, cfg)
    private_write(lock, locked.ljust(reserved, b' '))
    sync_dir(store)
    stage = store / '.building'
    rows, tallies = [], defaultdict(Counter)
    excluded = Counter(group for group, sym, day in cfg.schedule() if not verified[sym, day])
    total_excluded = sum(excluded.values())
    kept = 0
    made_stage = False
    try:
        stage.mkdir(mode=0o700)
        made_stage = True
        with (stage / 'orders.jsonl').open('xb') as f:
            for group, sym, day in cfg.schedule():
                if not verified[sym, day]:
                    continue
                headroom(cfg, store)
                pager.day_decoded = 0
                new, stats = measure_day(cfg, group, sym, day, pager.records(sym, day, 'quotes'),
                                         pager.records(sym, day, 'trades'), halts[sym, day])
                tallies[group].update(stats)
                for row in new:
                    payload = json_bytes(row)
                    kept += len(payload)
                    require(len(payload) <= cfg.limits['max_kept_bytes_per_order']
                            and kept <= cfg.limits['kept_order_rows_cap_mib'] * MIB, 'order_row_cap')
                    disk_charge(store, payload, cfg)
                    f.write(payload)
                    f.flush()
                    rows.append(row)
            os.fsync(f.fileno())
        require(len(rows) == cfg.limits['planned_order_slots'] - total_excluded * len(cfg.order['placement_times']) and bool(rows),
                'incomplete_schedule')
        report = summarize(rows, cfg)
        report['identity'] = {'basis': 'bracket-proved', 'limit': BRACKET_GAP}
        for group, stats in report['by_group'].items():
            n = total_excluded if group == 'pooled' else excluded[group]
            stats['identity_excluded_fund_days'] = n
            stats['identity_excluded_slots'] = n * len(cfg.order['placement_times'])
            stats['bracket_proved_fund_days'] = stats['scheduled'] // len(cfg.order['placement_times'])
        pooled = Counter()
        for counts in tallies.values():
            pooled.update(counts)
        report['filtered_feed_events'] = dict(tallies, pooled=pooled)
        payload = json_bytes(report)
        disk_charge(store, payload, cfg)
        private_write(stage / 'summary.json', payload)
        receipt = json_bytes(dict(**info, authorization_id=token, attempted_requests=pager.requests,
                                  wire_bytes=pager.wire, decoded_bytes=pager.decoded, kept_order_bytes=kept,
                                  halt_days=coverage, summary_sha256=digest(payload),
                                  order_rows_sha256=hash_orders(stage / 'orders.jsonl')))
        disk_charge(store, receipt, cfg)
        private_write(stage / 'receipt.json', receipt)
        headroom(cfg, store)
        sync_dir(stage)
        stage.rename(store / 'completed')
    except BaseException as exc:
        if made_stage and stage.exists():
            shutil.rmtree(stage)
        require(not stage.exists() and not (store / 'completed').exists(), 'cleanup_failed')
        stop = json_bytes(dict(authorization_id=token, **info,
                               stop=dict(code=str(exc) if isinstance(exc, Stop) else 'processing_failure',
                                         attempted_requests=pager.requests, wire_bytes=pager.wire, decoded_bytes=pager.decoded)))
        require(len(stop) <= reserved, 'stop_receipt_payload_cap')
        # Reuse the preallocated lock block: a free-floor breach must not
        # require more space or unlink the one-shot record to log the stop.
        fd = os.open(lock, os.O_WRONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'wb') as f:
            f.write(stop.ljust(reserved, b' '))
            f.flush()
            os.fsync(f.fileno())
        sync_dir(store)
        raise
    sync_dir(store)


def hash_orders(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def live_transport(cfg, store):
    import requests

    proxy = os.environ.get('HTTPS_PROXY')
    require(bool(proxy), 'custodian_proxy_missing')
    session = requests.Session()
    session.trust_env = False  # Bypass netrc and NO_PROXY; preserve only the explicit wrapper proxy.
    ca = os.environ.get('REQUESTS_CA_BUNDLE') or os.environ.get('CURL_CA_BUNDLE') or True

    def get(url, args, decoded_cap, wire_cap):
        headroom(cfg, store)
        require(source(url, {HOST}), 'vendor_origin')
        try:
            with session.get(url, params=args, headers={'Accept': 'application/json', 'Accept-Encoding': 'gzip'},
                             stream=True, allow_redirects=False, timeout=60, verify=ca,
                             proxies={'https': proxy}) as response:
                return read_page(response, decoded_cap, wire_cap)
        except (requests.RequestException, OSError, EOFError):
            raise Stop('vendor_transport') from None

    return session, get


def limit_process(cfg):
    cap = cfg.limits['job_memory_cap_mib'] * MIB
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (min(soft, cap) if soft != resource.RLIM_INFINITY else cap, hard))
    desired = cfg.limits['niceness']
    current = os.getpriority(os.PRIO_PROCESS, 0)
    if current < desired:
        os.setpriority(os.PRIO_PROCESS, 0, desired)
    for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = str(cfg.limits['workers'])


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_mutually_exclusive_group(required=True)
    for mode in ('selftest', 'validate-inputs', 'go'):
        modes.add_argument('--' + mode, action='store_true')
    mode = p.parse_args(argv)
    if mode.selftest:
        import test_measure_121
        return test_measure_121.run()
    os.umask(0o077)
    try:
        cfg = settings()
        limit_process(cfg)
        if mode.validate_inputs:
            info, _, _, _, free = inputs(cfg, STORE)
            print(json_bytes(dict(**info, free_bytes=free, price_requests=0)).decode(), end='')
            return 0
        context = go_context(cfg, STORE)
        require(any(context[2].values()), 'no_verified_identity')
        def interrupted(*_):
            raise Stop('interrupted')
        signal.signal(signal.SIGTERM, interrupted)
        session, get = live_transport(cfg, STORE)
        with session:
            execution(cfg, STORE, context, get)
        print('MEASURED: M121 completed; restricted results are off repo.')
        return 0
    except (Stop, OSError, ValueError, KeyError, ArithmeticError, TypeError, ImportError, MemoryError, KeyboardInterrupt) as exc:
        print('STATED: M121 refused: ' + (str(exc) if isinstance(exc, Stop) else 'input_resource_or_processing_failure'), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
