"""E13: one Binance.US USD forward practice venue; no accounts or orders."""
import argparse
import ast
import fcntl
import json
import math
import os
import re
import stat
import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import SimpleNamespace
from urllib import error, parse, request

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
OFF = Path('/home/user/workspace/rig/data/forward_e13')
PUBLIC = ROOT / 'practice/forward/E13_log.json'
CARD = 'practice/traders/E13_coin_trend_ratchet_binance_us.md'
RULE_SOURCE = 'research_rig/score_75.py'
CONFIG = 'config/thresholds.yaml'
LEDGER = 'research_rig/TRIAL_LEDGER.md'
PINNED = (CARD, 'practice/forward_e13.py', RULE_SOURCE, CONFIG)
HOST = 'https://api.binance.us'
ENDPOINTS = frozenset(('/api/v3/exchangeInfo', '/api/v3/klines', '/api/v3/depth'))
UTC = timezone.utc


class Refuse(Exception):
    pass


class Blocked(Refuse):
    pass


def need(ok, reason):
    if not ok:
        raise Refuse(reason)


def settings():
    raw = yaml.safe_load((ROOT / CONFIG).read_text())
    spec = raw['forward_e13']['value']
    inherited = raw[spec['operations_ref']]['value']
    used = ('bankroll_usd', 'day_s', 'wake_delay_s', 'quote_offsets_s', 'score_days', 'request_gap_s',
            'timeout_s', 'request_attempts', 'candle_page_days', 'rate_backoff_s', 'rate_backoff_cap_s', 'reference_coin')
    return ({k: inherited[k] for k in used} | spec, raw[inherited['rule_key']]['value'],
            raw[inherited['second_fee_key']]['value'])


@lru_cache(maxsize=4)
def frozen(pin):
    """Compile only pinned rule definitions. Never import or execute the source script."""
    raw = (ROOT / RULE_SOURCE).read_bytes()
    need(sha256(raw).hexdigest() == pin, 'frozen rule changed')
    tree = ast.parse(raw)
    definitions = {'Book', 'indicators', 'calendar', 'daily_simple', 'matched_btc'}
    keep, play = [], None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in definitions:
            keep.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == 'play':
            play = ast.get_source_segment(raw.decode(), node)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'NAMES':
            keep.append(node)
    need(len(keep) == len(definitions) + 1 and play, 'frozen rule definitions missing')
    scope = dict(__name__=__name__, np=np, dataclass=dataclass, require=need)
    exec(compile(ast.Module(body=keep, type_ignores=[]), RULE_SOURCE, 'exec'), scope)
    # The same narrow execution and terminal seams as the original forward card.
    seams = ('*, mode="trend", override=None, shift=0):',
             '        sells, buys = np.minimum(delta, 0), np.maximum(delta, 0)',
             '        shares += np.divide(delta, px[:, None], out=np.zeros_like(shares), where=px[:, None] > 0)',
             'float(abs(net[j]) * cost)', 'balance -= net.sum() + debit(net)', '        if d == nd - 1:')
    need(all(play.count(s) == 1 for s in seams), 'frozen execution seam changed')
    signature, left, right, charge, cash, terminal = seams
    lo, hi = play.index(left), play.index(right)
    play = play[:lo] + '        delta, net, charges = execution(d, delta, px, balance, queued)\n' + play[hi:]
    play = (play.replace(signature, '*, execution, mode="trend", override=None, shift=0):')
            .replace(charge, 'float(charges[j])').replace(cash, 'balance -= net.sum() + charges.sum()')
            .replace(terminal, '        if False:  # no synthetic terminal sale'))
    exec(compile(play, RULE_SOURCE + ':E13 execution adapter', 'exec'), scope)
    return SimpleNamespace(**{name: scope[name] for name in definitions | {'NAMES', 'play'}})


def now_utc():
    return datetime.now(UTC)


def midnight(stamp):
    return stamp.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def iso(stamp):
    return stamp.astimezone(UTC).isoformat()


def clock_at(text):
    return datetime.fromisoformat(text)


def blob(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return sha256(blob(value).encode()).hexdigest()


def pins():
    return {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in PINNED}


def git(*args):
    offline = os.environ | {'GIT_ALLOW_PROTOCOL': '', 'GIT_NO_LAZY_FETCH': '1', 'GIT_TERMINAL_PROMPT': '0'}
    return subprocess.check_output(('git', '-c', 'core.fsmonitor=false', *args), cwd=ROOT, env=offline, stderr=subprocess.DEVNULL)


def ledger_go(ledger, label, value):
    need(label in {'E13_START', 'E13_SCORE_GO'}, 'invalid authorization type')
    need(isinstance(value, str) and re.fullmatch(r'[a-z0-9-]{1,64}', value), 'lead go missing')
    token = rb'`' + label.encode() + rb'=([a-z0-9-]{1,64})`'
    rows = [line for line in ledger.split(b'\n') if line.startswith(b'| 231 |')]
    need(len(rows) == 1 and rows[0].endswith(b' |') and re.findall(token, ledger) == [value.encode()]
         and re.findall(token, rows[0]) == [value.encode()], 'lead go missing')


def committed_go(label, value):
    head = git('rev-parse', 'HEAD').decode().strip()
    ledger_go(git('show', head + ':' + LEDGER), label, value)
    return head


@contextmanager
def private(folder, create=False):
    need(folder.is_absolute() and '..' not in folder.parts and len(folder.parts) > 1, 'direct private folder required')
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY
    fd = os.open('/', flags)
    try:
        for part in folder.parts[1:-1]:
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        if create:
            try:
                os.mkdir(folder.name, mode=0o700, dir_fd=fd)
            except FileExistsError:
                pass
        child = os.open(folder.name, flags, dir_fd=fd)
        os.close(fd)
        fd = child
        info = os.fstat(fd)
        need(stat.S_IMODE(info.st_mode) == 0o700 and info.st_uid == os.geteuid(), 'private folder required')
        yield fd
    finally:
        os.close(fd)


@contextmanager
def private_file(fd, name, flags):
    file = os.open(name, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=fd)
    try:
        info = os.fstat(file)
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.geteuid()
             and stat.S_IMODE(info.st_mode) == 0o600, 'private regular file required')
        yield file
    finally:
        os.close(file)


@contextmanager
def lock(fd, name, blocking=False):
    with private_file(fd, name, os.O_RDWR | os.O_CREAT) as file:
        try:
            fcntl.flock(file, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            raise Refuse('another writer is running') from None
        yield


def read_log(fd):
    try:
        with private_file(fd, 'log.jsonl', os.O_RDONLY) as file, os.fdopen(os.dup(file)) as inp:
            rows, prior = [], None
            for line in inp:
                obj = json.loads(line)
                current = obj.pop('sha256')
                need(line.endswith('\n') and obj['prev'] == prior and digest(obj) == current, 'log chain broken')
                rows.append(obj | {'sha256': current})
                prior = current
            with private_file(fd, 'tip', os.O_RDONLY) as tip:
                need(os.read(tip, 100).decode() == (prior or '') + '\n', 'log tip mismatch')
            return rows
    except FileNotFoundError:
        for name in ('log.jsonl', 'tip', 'tip.tmp'):
            try:
                os.stat(name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise Refuse('log tip mismatch') from None
        return []
    except (KeyError, ValueError, AttributeError, TypeError):
        raise Refuse('log chain broken') from None


def append(fd, rows, row):
    row = row | {'prev': rows[-1]['sha256'] if rows else None}
    row['sha256'] = digest(row)
    with private_file(fd, 'log.jsonl', os.O_WRONLY | os.O_CREAT | os.O_APPEND) as file:
        with os.fdopen(os.dup(file), 'a') as out:
            out.write(blob(row) + '\n')
            out.flush()
            os.fsync(out.fileno())
    with private_file(fd, 'tip.tmp', os.O_WRONLY | os.O_CREAT | os.O_EXCL) as tip:
        os.write(tip, (row['sha256'] + '\n').encode())
        os.fsync(tip)
    os.replace('tip.tmp', 'tip', src_dir_fd=fd, dst_dir_fd=fd)
    os.fsync(fd)
    rows.append(row)
    return row


def checked(rows):
    need(rows and rows[0]['kind'] == 'header', 'log not started')
    need(rows[0]['pins'] == pins(), 'frozen files changed')
    return rows[0]


def start(now, go, folder=OFF):
    need(not git('status', '--porcelain', '--', *PINNED, LEDGER), 'freeze files differ from HEAD')
    commit = committed_go('E13_START', go)
    f, _, _ = settings()
    frozen(f['rule_source_sha256'])
    with private(folder, create=True) as fd, lock(fd, 'writer.lock'):
        rows = read_log(fd)
        need(not rows, 'log already started')
        return append(fd, rows, dict(kind='header', pins=pins(), freeze=commit, authorization=go,
                                     first=iso(midnight(now) + timedelta(days=1)), started=iso(now)))


def positive(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) and number > 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Blocked('public endpoint redirected')


class BinanceUS:
    def __init__(self, f):
        self.f, self.last = f, -math.inf
        self.opener = request.build_opener(request.ProxyHandler({}), NoRedirect())

    def get(self, endpoint, **query):
        need(endpoint in ENDPOINTS, 'invalid public endpoint')
        url = HOST + endpoint + ('?' + parse.urlencode(query) if query else '')
        for attempt in range(self.f['request_attempts']):
            time.sleep(max(0, self.last + self.f['request_gap_s'] - time.monotonic()))
            self.last = time.monotonic()
            delay = 2 ** attempt
            try:
                req = request.Request(url, headers={'User-Agent': 'e13-forward/1', 'Accept': 'application/json'}, method='GET')
                with self.opener.open(req, timeout=self.f['timeout_s']) as inp:
                    data = inp.read(self.f['response_max_bytes'] + 1)
                need(len(data) <= self.f['response_max_bytes'], 'public response too large')
                return json.loads(data)
            except error.HTTPError as exc:
                exc.close()
                if exc.code in (401, 403, 418, 451):
                    raise Blocked(f'venue refused HTTP {exc.code}') from None
                if exc.code == 429:
                    delay = max(delay * self.f['rate_backoff_s'], positive(exc.headers.get('Retry-After')) or 0)
                    need(delay <= self.f['rate_backoff_cap_s'], 'rate limit exceeds observation budget')
                elif not 500 <= exc.code < 600:
                    raise Refuse('public request refused') from None
            except (error.URLError, OSError, ValueError):
                pass
            if attempt + 1 < self.f['request_attempts']:
                time.sleep(delay)
        raise Refuse('public page unavailable')

    def products(self, names):
        raw = self.get('/api/v3/exchangeInfo')
        need(isinstance(raw, dict) and isinstance(raw.get('symbols'), list), 'invalid pair directory')
        out = {}
        for pair in raw['symbols']:
            if not isinstance(pair, dict):
                continue
            coin = pair.get('baseAsset')
            if coin in names and pair.get('quoteAsset') == 'USD' and pair.get('symbol') == coin + 'USD':
                need(coin not in out, 'duplicate USD pair')
                out[coin] = pair
        return out

    def candles(self, coin, first, end):
        start, stop = (int(x.timestamp()) * 1000 for x in (first, end))
        step = self.f['day_s'] * 1000
        limit = (stop - start) // step
        need(0 < limit <= self.f['candle_page_days'], 'invalid candle page')
        raw = self.get('/api/v3/klines', symbol=coin + 'USD', interval='1d', startTime=start, endTime=stop-1, limit=limit)
        need(isinstance(raw, list) and len(raw) <= limit, 'invalid candle page')
        out = {}
        for row in raw:
            need(isinstance(row, list) and len(row) >= 7 and type(row[0]) is int and type(row[6]) is int
                 and start <= row[0] < stop and row[0] % step == 0 and row[6] == row[0] + step - 1,
                 'daily candle outside completed UTC fence')
            day = datetime.fromtimestamp(row[0] // 1000, UTC).date().isoformat()
            price = positive(row[4])
            need(price and day not in out, 'invalid candle close')
            out[day] = price
        return out

    def book(self, coin):
        raw = self.get('/api/v3/depth', symbol=coin + 'USD', limit=self.f['depth_limit'])
        return normalize_book(raw, self.f['depth_limit'])


def pair_state(pair):
    pair = pair or {}
    market = (pair.get('status') == 'TRADING' and pair.get('isSpotTradingAllowed') is True
              and isinstance(pair.get('orderTypes'), list) and 'MARKET' in pair['orderTypes'])
    base, usd, steps, base_cap, usd_cap = [], [], [], [], []
    for field in pair.get('filters') or ():
        if not isinstance(field, dict):
            continue
        kind = field.get('filterType')
        if kind in ('LOT_SIZE', 'MARKET_LOT_SIZE'):
            for key, targets in (('minQty', base), ('maxQty', base_cap), ('stepSize', steps)):
                if n := positive(field.get(key)):
                    targets.append(n)
        if ((kind == 'MIN_NOTIONAL' and field.get('applyToMarket') is True)
                or (kind == 'NOTIONAL' and field.get('applyMinToMarket') is True)):
            if n := positive(field.get('minNotional')):
                usd.append(n)
        if kind == 'NOTIONAL' and field.get('applyMaxToMarket') is True:
            if n := positive(field.get('maxNotional')):
                usd_cap.append(n)
    return dict(market=market, base_min=max(base, default=None), usd_min=max(usd, default=None),
                base_cap=min(base_cap, default=None), usd_cap=min(usd_cap, default=None), steps=sorted(set(steps)))


def normalize_book(raw, limit):
    need(isinstance(raw, dict), 'invalid depth')
    result = {}
    for side in ('bids', 'asks'):
        levels = raw.get(side)
        need(isinstance(levels, list) and 0 < len(levels) <= limit, 'missing or oversized depth side')
        out = []
        for level in levels:
            need(isinstance(level, list) and len(level) == 2, 'invalid depth level')
            price, quantity = map(positive, level)
            need(price and quantity, 'invalid depth level')
            need(not out or (out[-1][0] > price if side == 'bids' else out[-1][0] < price), 'unordered depth')
            out.append([price, quantity])
        result[side] = out
    need(result['bids'][0][0] <= result['asks'][0][0], 'crossed depth')
    return result


def walk(levels, quantity):
    remaining, gross = quantity, 0.
    for price, available in levels:
        take = min(remaining, available)
        remaining -= take
        gross += take * price
        if remaining <= 1e-12 * quantity:
            return gross, True
    return gross, False


def round_qty(quantity, steps):
    if not steps:
        return quantity
    # Intersection of decimal lot grids, not merely the larger step.
    decimals = [Decimal(str(step)) for step in steps]
    scale = 10 ** max(-step.as_tuple().exponent for step in decimals)
    quantum = Decimal(math.lcm(*(int(step * scale) for step in decimals))) / scale
    return float((Decimal(str(quantity)) // quantum) * quantum)


def midpoint(book):
    return (book['asks'][0][0] + book['bids'][0][0]) / 2


def fee_for(fees, coin):
    return fees['taker_overrides_bp'].get(coin, fees['default_taker_bp']) / 10000


MARKET_ROWS = frozenset(('wake', 'void', 'close'))


def make_tape(log, f, rule):
    first = clock_at(log[0]['first']).date()
    prefix = max(rule['vol_days'] + 1, max(rule['lookbacks']))
    origin = first - timedelta(days=prefix)
    visits = [row for row in log if row['kind'] in MARKET_ROWS]
    names = next(row['roster'] for row in visits if row['kind'] == 'wake')
    end = clock_at(visits[-1]['wake']).date()
    days = tuple(origin + timedelta(days=i) for i in range((end - origin).days + 1))
    rows = [{} for _ in days]
    shape = len(days), len(names)
    opens, closes = np.full(shape, np.nan), np.full(shape, np.nan)
    active, sale = np.zeros(shape, bool), np.zeros(shape, bool)
    for row in visits:
        d = (clock_at(row['wake']).date() - origin).days
        rows[d] = row
        for coin, bars in row.get('candles', {}).items():
            j = names.index(coin)
            for day, price in bars.items():
                i = (datetime.fromisoformat(day).date() - origin).days
                need(0 <= i < d and not np.isfinite(closes[i, j]), 'completed close crosses freeze fence')
                closes[i, j] = price
        if row['kind'] != 'wake':
            active[d] = active[d - 1]
            continue
        for j, coin in enumerate(names):
            market = row['states'][coin]['market']
            active[d, j] = market if not row['outage'] else active[d - 1, j]
            if d == prefix:
                active[d - 1, j] = active[d, j]
            snapshot = row['depth'].get(coin)
            # The prior close is only an indicative sizing mark if this wake has no book.
            opens[d, j] = midpoint(snapshot) if snapshot else closes[d - 1, j]
            sale[d, j] = bool(market and snapshot)
    return SimpleNamespace(days=days, names=tuple(names), opens=opens, closes=closes, eligible=active, sell=sale), rows, prefix


def execution(tape, rows, size, f, fees, details):
    names = tape.names

    def execute(d, delta, px, cash, queued):
        row = rows[d]
        result = {'attempts': {}, 'fills': [], 'queued_sells': []}
        details[d] = result
        if row.get('kind') != 'wake':
            return np.zeros_like(delta), np.zeros(len(px)), np.zeros(len(px))
        sells, buys = np.minimum(delta, 0), np.maximum(delta, 0)
        exclude = set()
        depth = row['depth']
        state = row['states']

        def fill_at(j, ref, approximate=False):
            if not ref:
                return 0., 0., 0., None
            coin = names[j]
            market, book = state[coin], depth[coin]
            quantity = round_qty(abs(ref) * size / px[j], market['steps'])
            signed = math.copysign(quantity * px[j] / size, ref)
            gross, complete = walk(book['asks'] if ref > 0 else book['bids'], quantity)
            rate = fee_for(fees, coin)
            if not approximate:
                if not quantity or quantity < (market['base_min'] or 0) or gross < (market['usd_min'] or 0):
                    return 0., 0., 0., 'under_minimum'
                if quantity > (market['base_cap'] or math.inf) or gross > (market['usd_cap'] or math.inf):
                    return 0., 0., 0., 'over_maximum'
                if not complete:
                    return 0., 0., 0., 'insufficient_depth'
            return signed, math.copysign(gross / size, ref), gross * rate / size, None

        def disabled(j, reason):
            result['attempts'].setdefault(names[j], []).append(reason)
            exclude.add(j)

        gross_ref = delta.sum(axis=1)
        for j in range(len(names)):
            if not np.any(delta[j]):
                continue
            coin = names[j]
            book, market = depth.get(coin), state[coin]
            if gross_ref[j] > 1e-14 and (coin in row['candle_failures'] or row['late'] or not book or not book['timely']):
                result['attempts'].setdefault(coin, []).append('void_buy')
                buys[j] = 0  # allow coincident net sales; never force a net buy
            ref = (sells[j] + buys[j]).sum()
            if abs(ref) <= 1e-14:
                continue
            if not market['market']:
                disabled(j, 'pair_unavailable')
            elif not book:
                disabled(j, 'book_missing')
            elif not (market['base_min'] or market['usd_min']):
                disabled(j, 'minimum_unknown')
            else:
                _, _, _, reason = fill_at(j, ref)
                if reason:
                    disabled(j, reason)

        def candidate(scale):
            proposed = sells + scale * buys
            for j in exclude:
                proposed[j] = 0
            return proposed

        def cash_needed(proposed):
            total = 0.
            for j, ref in enumerate(proposed.sum(axis=1)):
                if abs(ref) <= 1e-14:
                    continue
                coin = names[j]
                if not state[coin]['market'] or not depth.get(coin) or not (state[coin]['base_min'] or state[coin]['usd_min']):
                    continue
                _, gross, charge, _ = fill_at(j, ref, approximate=True)
                total += gross + charge
            return total

        while True:
            final = candidate(1.)
            if cash_needed(final) > cash + 1e-12:
                lo, hi = 0., 1.
                for _ in range(48):
                    mid = (lo + hi) / 2
                    if cash_needed(candidate(mid)) <= cash:
                        lo = mid
                    else:
                        hi = mid
                final = candidate(lo)
            net, charges = np.zeros(len(px)), np.zeros(len(px))
            before = len(exclude)
            for j, ref in enumerate(final.sum(axis=1)):
                if abs(ref) <= 1e-14:
                    continue
                coin = names[j]
                if not state[coin]['market'] or not depth.get(coin) or not (state[coin]['base_min'] or state[coin]['usd_min']):
                    disabled(j, 'unplaceable_after_cash_scaling')
                    continue
                if ref > 0 and (row['late'] or not depth[coin]['timely'] or coin in row['candle_failures']):
                    disabled(j, 'void_buy')
                    continue
                adjusted, net[j], charges[j], reason = fill_at(j, ref)
                if reason:
                    disabled(j, reason)
                else:
                    final[j] *= adjusted / ref
            if len(exclude) == before:
                need(net.sum() + charges.sum() <= cash + 1e-12, 'execution would borrow cash')
                break
        for j in np.flatnonzero(net):
            coin = names[j]
            result['attempts'].setdefault(coin, []).append('filled')
            mark = float(final[j].sum() * size)
            gross, charge = float(net[j] * size), float(charges[j] * size)
            cost_bp = ((gross - mark) + charge) / abs(mark) * 10000
            result['fills'].append(dict(coin=coin, side='buy' if gross > 0 else 'sell', gross=gross, fee=charge,
                                        quantity=abs(mark) / px[j], cost_bp=cost_bp))
        result['queued_sells'] = [names[j] for j in np.flatnonzero(queued.any(axis=1) & ~(final < -1e-14).any(axis=1))]
        return final, net, charges

    return execute


def run_book(log, f, rule, fees, label):
    core = frozen(f['rule_source_sha256'])
    tape, rows, prefix = make_tape(log, f, rule)
    inp = core.indicators(tape, rule['lookbacks'], rule, rule['vault_annual_days'])
    roster = core.calendar(tape, inp[2])
    details = {}
    hook = execution(tape, rows, f['bankroll_usd'][label], f, fees, details)
    book = core.play(tape, 0., rule, rule['cap'], inp, roster, execution=hook)
    return tape, prefix, book, details, inp[2]


def page(fetch, failures, key, *args):
    try:
        return fetch(key, *args)
    except Blocked:
        raise
    except (Refuse, OSError, ValueError, KeyError, TypeError):
        failures[key] = 'PAGE_UNAVAILABLE'
        return None


def snapshots(venue, coins, wake, clock, f):
    result, failed = {}, {}
    for coin in coins:
        if midnight(clock()) != wake:
            failed[coin] = 'OUTSIDE_OBSERVATION_DAY'
            continue
        book = page(venue.book, failed, coin)
        received = clock()
        seconds = (received - wake).total_seconds()
        if book and 0 <= seconds < f['day_s']:
            result[coin] = book | {'received': iso(received), 'timely': seconds <= f['quote_offsets_s'][-1]}
        else:
            failed.setdefault(coin, 'DEPTH_UNAVAILABLE')
    return result, failed


def capture(log, wake, observed, venue, clock, f, rule, fees, closing):
    first = clock_at(log[0]['first'])
    before = [row for row in log if row['kind'] == 'wake']
    names = frozen(f['rule_source_sha256']).NAMES
    roster = before[0]['roster'] if before else None
    pairs = venue.products(names)
    if roster is None:
        need(wake == first and 0 <= (clock() - midnight(first)).total_seconds() <= f['quote_offsets_s'][-1] and pairs,
             'first wake roster unavailable')
        roster = [coin for coin in names if coin in pairs]
        need(roster, 'first wake roster unavailable')
    since = (clock_at(before[-1]['wake']) if before else
             first - timedelta(days=max(rule['vol_days'] + 1, max(rule['lookbacks']))))
    states = {coin: pair_state(pairs.get(coin)) for coin in roster}
    row = dict(kind='close' if closing else 'wake', wake=iso(wake), observed=iso(observed), roster=roster,
               states=states, candles={}, candle_failures={}, depth={}, depth_failures={},
               outage=not any(s['market'] for s in states.values()), late=False)
    for coin in roster:
        if coin not in pairs:
            row['candle_failures'][coin] = 'PAIR_MISSING'
            continue
        cursor = since
        while cursor < wake:
            until = min(wake, cursor + timedelta(days=f['candle_page_days']))
            bars = page(venue.candles, row['candle_failures'], coin, cursor, until)
            if bars is not None:
                row['candles'].setdefault(coin, {}).update(bars)
            cursor = until
    if not closing:
        row['depth'], row['depth_failures'] = snapshots(venue, [c for c in roster if states[c]['market']], wake, clock, f)
        row['late'] = not any(q['timely'] for q in row['depth'].values())
        row['books'], follow = {}, set()
        for label in f['bankroll_usd']:
            tape, _, _, details, warm = run_book(log + [row], f, rule, fees, label)
            row['books'][label] = details[len(tape.days) - 1]
            follow.update(row['books'][label]['attempts'])
        row['not_ready'] = [coin for j, coin in enumerate(roster) if not warm[-2, j].any()]
        row['follow'] = [coin for coin in roster if coin in follow and states[coin]['market']]
    return row


def record(now, venue=None, folder=OFF, clock=now_utc, sleep=time.sleep):
    f, rule, fees = settings()
    with private(folder) as fd, lock(fd, 'observer.lock'):
        with lock(fd, 'writer.lock'):
            rows = read_log(fd)
            header = checked(rows)
            need(not any(r['kind'] == 'blocked' for r in rows), 'venue or first wake blocked; recording stopped')
            visits = [r for r in rows if r['kind'] in MARKET_ROWS]
            if visits and visits[-1]['kind'] == 'close':
                return None
            first = clock_at(header['first'])
            end = first + timedelta(days=f['score_days'])
            wake = min(midnight(now), end)
            next_day = clock_at(visits[-1]['wake']) + timedelta(days=1) if visits else first
            if wake < next_day or now < wake + timedelta(seconds=f['wake_delay_s']):
                return None
            if not visits and (wake != first or (now - midnight(first)).total_seconds() > f['quote_offsets_s'][-1]):
                append(fd, rows, {'kind': 'blocked', 'reason': 'FIRST_WAKE_MISSED'})
                raise Blocked('first wake missed; roster not frozen')
            while next_day < wake:
                append(fd, rows, dict(kind='void', wake=iso(next_day), reason='MISSED_WAKE'))
                next_day += timedelta(days=1)
            # Check the original committed authorization again before constructing any client.
            ledger_go(git('show', header['freeze'] + ':' + LEDGER), 'E13_START', header['authorization'])
            frozen(f['rule_source_sha256'])
            venue = venue if venue is not None else BinanceUS(f)
            try:
                row = capture(rows, wake, now, venue, clock, f, rule, fees, closing=wake == end)
            except Blocked:
                append(fd, rows, {'kind': 'blocked', 'reason': 'VENUE_REFUSED'})
                raise
            except (Refuse, OSError, ValueError, TypeError, KeyError):
                if not any(r['kind'] == 'wake' for r in visits):
                    append(fd, rows, {'kind': 'blocked', 'reason': 'FIRST_WAKE_UNAVAILABLE'})
                    raise Blocked('first wake roster not frozen') from None
                if wake == end:
                    raise Refuse('closing observation unavailable') from None
                return append(fd, rows, dict(kind='void', wake=iso(wake), reason='WAKE_UNAVAILABLE'))
            row = append(fd, rows, row)
        for offset in f['quote_offsets_s']:
            if not row.get('follow'):
                break
            target = wake + timedelta(seconds=offset)
            delay = (target - clock()).total_seconds()
            if delay < 0:
                continue
            sleep(delay)
            try:
                books, failures = snapshots(venue, row['follow'], wake, clock, f)
            except Blocked:
                with lock(fd, 'writer.lock', blocking=True):
                    append(fd, rows, {'kind': 'blocked', 'reason': 'VENUE_REFUSED'})
                raise
            with lock(fd, 'writer.lock', blocking=True):
                append(fd, rows, dict(kind='follow', wake=iso(wake), offset=offset, depth=books, depth_failures=failures))
        return row


def stats(values):
    return {'n': len(values), 'median_bp': float(np.median(values)) if values else None,
            'p90_bp': float(np.percentile(values, 90)) if values else None}


def summary(rows, f):
    wakes = [r for r in rows if r['kind'] == 'wake']
    follow = [r for r in rows if r['kind'] == 'follow']
    status = ('STOPPED' if any(r['kind'] == 'blocked' for r in rows) else
              'CLOSED' if any(r['kind'] == 'close' for r in rows) else
              'OBSERVING' if wakes else 'SCHEDULED' if rows else 'REGISTERED')
    result = {'card': 'E13', 'status': status, 'wakes': len(wakes),
              'missed_wakes': sum(r['kind'] == 'void' and r['reason'] == 'MISSED_WAKE' for r in rows),
              'unavailable_wakes': sum(r['kind'] == 'void' and r['reason'] == 'WAKE_UNAVAILABLE' for r in rows),
              'late_wakes': sum(w['late'] for w in wakes), 'roster_count': len(wakes[0]['roster']) if wakes else None,
              'not_ready_coin_wakes': sum(len(w['not_ready']) for w in wakes),
              'candle_page_refusals': sum(len(w['candle_failures']) for w in wakes),
              'book_unavailable_coin_wakes': sum(len(w['depth_failures']) for w in wakes),
              'follow_observations': sum(len(r['depth']) for r in follow), 'lines': {}}
    midcost = [(book['asks'][0][0] - book['bids'][0][0]) / (2 * midpoint(book)) * 10000
               for w in wakes for book in w['depth'].values()]
    result['displayed_half_spread'] = stats(midcost)
    for label in f['bankroll_usd']:
        entries = [w['books'][label] for w in wakes]
        fills = [fill for entry in entries for fill in entry['fills']]
        result['lines'][label] = {'attempts': sum(len(entry['attempts']) for entry in entries), 'fills': len(fills),
                                  'queued_sell_coin_wakes': sum(len(entry['queued_sells']) for entry in entries),
                                  'attempt_flags': {name: sum(name in flags for entry in entries for flags in entry['attempts'].values())
                                                    for name in ('void_buy', 'pair_unavailable', 'book_missing', 'minimum_unknown',
                                                                 'insufficient_depth', 'under_minimum', 'over_maximum',
                                                                 'unplaceable_after_cash_scaling')},
                                  'all_in_cost_by_side': {side: stats([fill['cost_bp'] for fill in fills if fill['side'] == side])
                                                         for side in ('buy', 'sell')}}
    return result


def alive(folder=OFF):
    f, _, _ = settings()
    with private(folder) as fd, lock(fd, 'writer.lock'):
        rows = read_log(fd)
        checked(rows)
        return summary(rows, f)


def publish(folder=OFF, path=PUBLIC):
    # Keep snapshot and replace under one writer lock: public summaries cannot roll back.
    f, _, _ = settings()
    with private(folder) as fd, lock(fd, 'writer.lock', blocking=True):
        rows = read_log(fd)
        checked(rows)
        result = summary(rows, f)
        temporary = None
        try:
            with NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, prefix='.' + path.name, delete=False) as out:
                temporary = out.name
                out.write(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + '\n')
                out.flush()
                os.fchmod(out.fileno(), 0o644)
                os.fsync(out.fileno())
            os.replace(temporary, path)
            temporary = None
        finally:
            if temporary is not None:
                os.unlink(temporary)
        return result


def score_gate(rows, now, days):
    need(not any(r['kind'] == 'score' for r in rows), 'score already read')
    first = next((r for r in rows if r['kind'] == 'wake'), None)
    need(first, 'no first wake')
    need(now >= max(clock_at(first['wake']), clock_at(first['observed'])) + timedelta(days=days), 'forward year incomplete')
    need(any(r['kind'] == 'close' for r in rows) and not any(r['kind'] == 'blocked' for r in rows), 'closing observation missing')
    return first


def benchmark_entry(depth, capital):
    remaining, quantity = capital, 0.
    for price, available in depth['asks']:
        debit = min(remaining, price * available)
        quantity += debit / price
        remaining -= debit
        if remaining <= 1e-12 * capital:
            return capital / quantity
    return None


def private_metrics(rows, first, f, rule, fees, label):
    tape, prefix, book, _, _ = run_book(rows, f, rule, fees, label)
    core = frozen(f['rule_source_sha256'])
    stop = len(tape.days) - 1  # final observation adds the immediately previous close only
    ref = f['reference_coin']
    quote = first['depth'].get(ref)
    gross = None
    if ref in tape.names and quote and quote['timely']:
        history = tape.closes[prefix:stop, tape.names.index(ref)]
        entry = benchmark_entry(quote, f['bankroll_usd'][label])
        if entry and np.isfinite(history).all():
            gross = history / entry

    def read(lo, hi):
        nav = book.nav[lo:hi] / book.nav[lo - 1]
        drawdown = np.max(1 - nav / np.maximum.accumulate(np.maximum(nav, 1.)))
        matched = None
        if gross is not None and len(nav) >= 2:
            before = 1. if lo == prefix else gross[lo - prefix - 1]
            matched, _ = core.matched_btc(gross[lo-prefix:hi-prefix] / before,
                                          [(0, 0, 1., 0.)] if lo == prefix else [], nav, fee_for(fees, ref))
        return dict(net=float(nav[-1] - 1), largest_fall=float(drawdown), matched_btc=matched)

    quarters = {}
    for i in range(prefix, stop):
        day = tape.days[i]
        quarters.setdefault(f'{day.year}-Q{(day.month - 1) // 3 + 1}', []).append(i)
    held = (book.weights[prefix:stop] > 0).any(axis=2)
    stale = int(np.count_nonzero(held & ~np.isfinite(tape.closes[prefix:stop])))
    return dict(whole=read(prefix, stop), calendar_quarters={q: read(ix[0], ix[-1] + 1) for q, ix in quarters.items()},
                stale_held_coin_days=stale)


def score(now, go, folder=OFF):
    f, rule, fees = settings()
    with private(folder) as fd, lock(fd, 'writer.lock'):
        rows = read_log(fd)
        header = checked(rows)
        first = score_gate(rows, now, f['score_days'])
        need(go != header['authorization'], 'score needs its separate lead go')
        authorization = committed_go('E13_SCORE_GO', go)
        result = {'label': 'RECORD_NOT_VERDICT', 'lines': {k: private_metrics(rows, first, f, rule, fees, k) for k in f['bankroll_usd']}}
        append(fd, rows, dict(kind='score', read=iso(now), authorization_commit=authorization, result_sha256=digest(result)))
        return result


def loop(folder=OFF):
    f, _, _ = settings()
    with private(folder) as fd, lock(fd, 'loop.lock'):
        while True:
            try:
                row = record(now_utc(), folder=folder)
            except Blocked:
                publish(folder)
                raise
            if row:
                publish(folder)
            with lock(fd, 'writer.lock', blocking=True):
                rows = read_log(fd)
                checked(rows)
                if any(r['kind'] == 'close' for r in rows):
                    return
            t = now_utc()
            next_wake = midnight(t) + timedelta(seconds=f['wake_delay_s'])
            if t >= next_wake:
                next_wake += timedelta(days=1)
            time.sleep(max(0, (next_wake - t).total_seconds()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('plan', 'start', 'record', 'loop', 'alive', 'publish', 'score'))
    parser.add_argument('--go', help='lead ledger authorization for start or score')
    args = parser.parse_args()
    prior = os.umask(0o077)
    try:
        if args.command == 'plan':
            f, rule, fees = settings()
            out = dict(forward=f, rule=rule['lookbacks'], fees=fees, names=frozen(f['rule_source_sha256']).NAMES)
        elif args.command == 'start':
            row = start(now_utc(), args.go)
            out = {'first': row['first'], 'freeze': row['freeze']}
        elif args.command == 'record':
            row = record(now_utc())
            out = {'status': row['kind'], 'wake': row['wake']} if row else {'status': 'nothing due'}
        elif args.command == 'loop':
            loop()
            return 0
        elif args.command == 'alive':
            out = alive()
        elif args.command == 'publish':
            out = publish()
        else:
            out = score(now_utc(), args.go)
        print(json.dumps(out, sort_keys=True, allow_nan=False))
        return 0
    except (Refuse, OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print('REFUSED ' + (str(exc) if isinstance(exc, Refuse) else type(exc).__name__))
        return 2
    finally:
        os.umask(prior)


if __name__ == '__main__':
    raise SystemExit(main())
