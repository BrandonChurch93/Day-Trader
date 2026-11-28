"""E16: one Binance.US USD forward practice venue; no accounts or orders."""
# E13 rebuild: larger directory, fixed roster, void first slots, bounded unsent
# gate retries and named failures. The start go names the audited build itself.
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
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import lru_cache
from hashlib import sha256
from http.client import HTTPException
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import SimpleNamespace
from urllib import error, parse, request

import numpy as np
import yaml

if __package__:
    from . import venue_binance_us as bx
else:
    import venue_binance_us as bx

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'practice/forward/E16_log.json'
CARD = 'practice/traders/E16_coin_trend_ratchet_binance_us.md'
RULE_SOURCE = 'research_rig/score_75.py'
CONFIG = 'config/thresholds.yaml'
LEDGER = 'research_rig/TRIAL_LEDGER.md'
PINNED = (CARD, 'practice/forward_e16.py', RULE_SOURCE, CONFIG, 'practice/venue_binance_us.py')
HOST = 'https://api.binance.us'
ENDPOINTS = frozenset(('/api/v3/exchangeInfo', '/api/v3/klines', '/api/v3/depth'))
UTC = timezone.utc


class Refuse(Exception):
    pass


class Blocked(Refuse):
    pass


class PageRefused(Refuse):
    def __init__(self, reason, message):
        super().__init__(message)
        self.reason = reason


class PublicStatus(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def need(ok, reason):
    if not ok:
        raise Refuse(reason)


def card_settings(raw):
    spec = raw['forward_e16']['value']
    prior = raw[spec['prior_ref']]['value']
    inherited = raw[prior['operations_ref']]['value']
    used = ('bankroll_usd', 'day_s', 'wake_delay_s', 'quote_offsets_s', 'score_days', 'request_gap_s',
            'timeout_s', 'request_attempts', 'candle_page_days', 'reference_coin')
    busy_wait = raw[spec['busy_ref']]['value']['busy_wait_s']
    return ({k: inherited[k] for k in used} | prior | spec | {'busy_wait_s': busy_wait},
            raw[inherited['rule_key']]['value'], raw[inherited['second_fee_key']]['value'])


def settings():
    return card_settings(yaml.safe_load((ROOT / CONFIG).read_text()))


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
    play = play[:lo] + '        delta, net, charges = execution(d, delta, px, balance, queued, wanted, goal)\n' + play[hi:]
    play = (play.replace(signature, '*, execution, mode="trend", override=None, shift=0):')
            .replace(charge, 'float(charges[j])').replace(cash, 'balance -= net.sum() + charges.sum()')
            .replace(terminal, '        if False:  # no synthetic terminal sale'))
    exec(compile(play, RULE_SOURCE + ':E16 execution adapter', 'exec'), scope)
    return SimpleNamespace(**{name: scope[name] for name in definitions | {'NAMES', 'play'}})


def now_utc():
    return datetime.now(UTC)


def midnight(stamp):
    return stamp.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def iso(stamp):
    return stamp.astimezone(UTC).isoformat()


def clock_at(text):
    return datetime.fromisoformat(text)


def check_not_early(stamp, not_before):
    if not_before is not None and stamp < not_before:
        raise bx.Failure('clock_before_window')


def blob(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return sha256(blob(value).encode()).hexdigest()


def pins(commit=None):
    result = {}
    for path in PINNED:
        raw = git('show', commit + ':' + path) if commit else (ROOT / path).read_bytes()
        if path == CONFIG:
            cfg = yaml.safe_load(raw)
            raw = blob((card_settings(cfg), cfg['binance_us_gate'])).encode()
        result[path] = sha256(raw).hexdigest()
    return result


def git(*args):
    offline = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    offline.update(GIT_ALLOW_PROTOCOL='', GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0',
                   GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
    try:
        return subprocess.check_output(('git', '--no-replace-objects', '-c', 'core.fsmonitor=false', *args),
                                       cwd=ROOT, env=offline, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        raise Refuse('local Git approval or release unavailable') from None


def ledger_value(ledger, label, pattern, row):
    token = rb'`' + label.encode() + rb'=(' + pattern + rb')`'
    rows = [line for line in ledger.split(b'\n') if line.startswith(f'| {row} |'.encode())]
    found = re.findall(token, ledger)
    need(len(rows) == 1 and rows[0].endswith(b' |') and ledger.count(label.encode() + b'=') == 1 and len(found) == 1
         and re.findall(token, rows[0]) == found, 'lead go missing')
    return found[0].decode()


def ledger_go(ledger, label, value, row):
    need(label in {'E16_START', 'E16_SCORE_GO'}, 'invalid authorization type')
    pattern = rb'[0-9a-f]{40}' if label == 'E16_START' else rb'[a-z0-9-]{1,64}'
    need(value is not None and ledger_value(ledger, label, pattern, row) == value, 'lead go missing')


def committed_go(label, value, expected_release=None, expected_generation=None):
    need(Path(os.fsdecode(git('rev-parse', '--show-toplevel').strip())).resolve() == ROOT, 'unexpected Git checkout')
    main = git('rev-parse', '--verify', 'refs/heads/main^{commit}').decode().strip()
    ledger = git('show', main + ':' + LEDGER)
    row = settings()[0]['ledger_row']
    ledger_go(ledger, label, value, row)
    release = ledger_value(ledger, 'E16_START', rb'[0-9a-f]{40}', row)
    if label == 'E16_START' and expected_generation:
        generation = ledger_value(ledger, 'E16_START_GENERATION', rb'[0-9]+', row)
        need(generation == str(expected_generation), 'lead go is for a different venue generation')
    if expected_release is not None:
        need(release == expected_release, 'audited release changed')
    git('merge-base', '--is-ancestor', release, main)
    need(not git('status', '--porcelain', '--', LEDGER, *PINNED), 'freeze files differ from HEAD')
    need(pins() == pins(release) == pins(main) == pins('HEAD'), 'audited release pins differ')
    need(git('rev-parse', '--verify', 'refs/heads/main^{commit}').decode().strip() == main, 'committed main moved')
    return main, release


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
            else:
                os.fsync(fd)
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


def read_log(fd, recover=False):
    try:
        with private_file(fd, 'tip', os.O_RDONLY) as tip:
            expected = os.read(tip, 100).decode()
        with private_file(fd, 'log.jsonl', os.O_RDWR if recover else os.O_RDONLY) as file, os.fdopen(os.dup(file), 'rb') as inp:
            rows, prior = [], None
            while line := inp.readline():
                obj = json.loads(line)
                current = obj.pop('sha256')
                need(line.endswith(b'\n') and obj['prev'] == prior and digest(obj) == current, 'log chain broken')
                rows.append(obj | {'sha256': current})
                prior = current
                if current + '\n' == expected:
                    offset = inp.tell()
                    if offset != os.fstat(file).st_size:
                        need(recover, 'uncommitted log tail')
                        os.ftruncate(file, offset)
                        os.fsync(file)
                    if recover:
                        try:
                            os.unlink('tip.tmp', dir_fd=fd)
                        except FileNotFoundError:
                            pass
                        os.fsync(fd)
                    return rows
            raise Refuse('log tip mismatch')
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
    gen = rows[0].get('venue_generation')
    need(type(gen) is int and gen >= 0, 'invalid private venue generation')
    return rows[0]


def claim_start_id(custody, go):
    name = 'start-' + sha256(go.encode()).hexdigest()
    with private(custody, create=True) as fd, lock(fd, 'writer.lock', blocking=True):
        try:
            with private_file(fd, name, os.O_WRONLY | os.O_CREAT | os.O_EXCL) as file:
                os.fsync(file)
            os.fsync(fd)
        except FileExistsError:
            raise Refuse('start ID was already used') from None


def start(now, go, folder=None, gate=None):
    commit, release = committed_go('E16_START', go)
    generation = venue_gate(gate).check_start(reject_cooldown=True)
    need(type(generation) is int and generation >= 0, 'invalid shared venue generation')
    if generation:
        commit, release = committed_go('E16_START', go, release, generation)
    f, _, _ = settings()
    custody = Path(f['authorization_dir']) if folder is None else folder.with_name(folder.name + '_authorizations')
    folder = Path(f['private_dir']) if folder is None else folder
    frozen(f['rule_source_sha256'])
    with private(folder, create=True) as fd, lock(fd, 'writer.lock'):
        rows = read_log(fd)
        need(not rows, 'log already started')
        claim_start_id(custody, go)
        return append(fd, rows, dict(kind='header', pins=pins(), freeze=commit, release=release, authorization=go,
                                     venue_generation=generation,
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
        return None  # Let urllib report the known 3xx without following it.


def venue_gate(gate=None, clock=now_utc):
    if gate is not None:
        return gate
    spec = yaml.safe_load((ROOT / CONFIG).read_bytes())['binance_us_gate']['value']
    return bx.Gate(cooldown_path=Path(spec['cooldown_path']), clock=clock)


class BinanceUS:
    def __init__(self, f, gate=None, clock=now_utc, generation=0, sleep=None):
        self.f, self.last = f, -math.inf
        self.gate, self.clock, self.deadline = venue_gate(gate, clock), clock, None
        self.not_before = None
        self.generation = generation
        self.sleep = sleep if sleep is not None else time.sleep
        self.retry_delay_s = 0.
        self.retry_sink = None
        self.opener = request.build_opener(request.ProxyHandler({}), NoRedirect())

    def log_retry(self, event):
        try:
            need(self.retry_sink is not None, 'no durable retry journal')
            return self.retry_sink(event)
        except (OSError, Refuse, ValueError, TypeError) as exc:
            raise Blocked('could not durably record venue retry') from exc

    @contextmanager
    def send_slot(self):
        """A busy lock can retry only before its context has granted permission to send."""
        begun, monotonic = self.clock(), time.monotonic()
        check_not_early(begun, self.not_before)
        wait = self.f['busy_wait_s']

        def retry_deadline(now):
            left = wait - (time.monotonic() - monotonic)
            return min(self.deadline, begun + timedelta(seconds=wait), now + timedelta(seconds=left))

        busy = False
        while True:
            deadline = self.deadline
            if busy:
                now = self.clock()
                check_not_early(now, self.not_before)
                deadline = retry_deadline(now)
                if now >= deadline:
                    raise bx.Failure('shared_gate_busy')
            entered = False
            try:
                with self.gate.attempt(deadline, generation=self.generation):
                    entered = True
                    if busy and (self.clock() >= deadline or time.monotonic() - monotonic >= wait):
                        self.gate.cancel_unsent()
                        raise bx.Failure('shared_gate_busy')
                    yield
                    return
            except bx.Failure as exc:
                if entered or self.deadline is None:
                    raise
                if busy and exc.reason == 'wake_window_elapsed':
                    raise bx.Failure('shared_gate_busy') from None
                if exc.reason != 'shared_gate_busy':
                    raise
                busy = True
                now = self.clock()
                left = (retry_deadline(now) - now).total_seconds()
                if left > 0:
                    self.sleep(min(self.f['busy_poll_s'], left))

    def get(self, endpoint, *, coin=None, validate=None, **query):
        self.retry_delay_s = 0.
        need(endpoint in ENDPOINTS, 'invalid public endpoint')
        url = HOST + endpoint + ('?' + parse.urlencode(query) if query else '')
        req = request.Request(url, headers={'User-Agent': 'e16-forward/1', 'Accept': 'application/json'}, method='GET')
        max_bytes = self.f['directory_max_bytes'] if endpoint == '/api/v3/exchangeInfo' else self.f['response_max_bytes']
        prior_no_status_at = None
        last_page_failure = 'INVALID_PAGE'
        for attempt in range(self.f['request_attempts']):
            pause = max(0, self.last + self.f['request_gap_s'] - time.monotonic())
            if self.deadline is not None and self.clock() + timedelta(seconds=pause) >= self.deadline:
                raise bx.Failure('wake_window_elapsed')
            if pause:
                self.sleep(pause)
            delay = 2 ** attempt
            no_status = False
            retry, retry_at, wait_until, attempted = None, None, None, None
            status, body_error, outcome = None, None, 'INTERRUPTED'
            received_early = False
            try:
                with self.send_slot():
                    self.last = time.monotonic()
                    timeout = self.f['timeout_s']
                    if self.deadline is not None:
                        timeout = min(timeout, (self.deadline - self.clock()).total_seconds())
                    if timeout <= 0:
                        self.gate.cancel_unsent()
                        raise bx.Failure('wake_window_elapsed')
                    if prior_no_status_at is not None:
                        retry_at = self.clock()
                        try:
                            retry = self.log_retry(dict(kind='retry', endpoint=endpoint, coin=coin,
                                                        first_attempt_at=iso(prior_no_status_at), retry_at=iso(retry_at),
                                                        delay_s=(retry_at - prior_no_status_at).total_seconds(),
                                                        outcome='PENDING'))
                        except Blocked:
                            self.gate.cancel_unsent()
                            raise
                        timeout = min(timeout, (self.deadline - self.clock()).total_seconds())
                        if timeout <= 0:
                            self.gate.cancel_unsent()
                            outcome = 'NOT_SENT_WINDOW_ELAPSED'
                            raise bx.Failure('wake_window_elapsed')
                    prior_no_status_at = None
                    replied = False
                    retry_after = None
                    try:
                        with bx.wall_budget(timeout, timeout < self.f['timeout_s']):
                            attempted = self.clock()
                            if self.not_before is not None and attempted < self.not_before:
                                self.gate.cancel_unsent()
                                check_not_early(attempted, self.not_before)
                            if self.deadline is not None and attempted >= self.deadline:
                                self.gate.cancel_unsent()
                                outcome = 'NOT_SENT_WINDOW_ELAPSED'
                                raise bx.Failure('wake_window_elapsed')
                            inp = self.opener.open(req, timeout=timeout)
                            replied = True
                            try:
                                if self.not_before is not None:
                                    received_early = self.clock() < self.not_before
                                status = getattr(inp, 'status', None)
                                if status is None and callable(getattr(inp, 'getcode', None)):
                                    status = inp.getcode()
                                if status == 429:
                                    headers = getattr(inp, 'headers', None)
                                    retry_after = headers.get('Retry-After') if headers is not None else None
                                if not received_early and (status is None or (type(status) is int and 200 <= status < 300)):
                                    data = inp.read(max_bytes + 1)
                            finally:
                                if self.not_before is not None:
                                    received_early |= self.clock() < self.not_before
                                inp.close()
                    except Exception as exc:
                        if replied:
                            body_error = exc
                        elif isinstance(exc, error.HTTPError):
                            status = exc.code
                            if self.not_before is not None:
                                received_early = self.clock() < self.not_before
                            with suppress(Exception):
                                retry_after = exc.headers.get('Retry-After') if exc.headers is not None else None
                            with suppress(Exception):
                                exc.close()
                        elif isinstance(exc, (OSError, HTTPException)):
                            no_status = True
                            self.gate.no_status()
                        else:
                            raise
                    if type(status) is int and not 200 <= status < 300:
                        self.gate.http_error(status, retry_after)
                        raise PublicStatus(status)
                    self.gate.reply_received()
                    if received_early:
                        raise bx.Failure('clock_before_window')
                    if status is not None and type(status) is not int:
                        raise Refuse('invalid public HTTP status')
                    if body_error is not None:
                        if self.deadline is not None and self.clock() >= self.deadline:
                            raise bx.Failure('wake_window_elapsed') from None
                        raise PageRefused('BODY_UNAVAILABLE', 'public response body unavailable') from body_error
                if self.deadline is not None and self.clock() >= self.deadline:
                    raise bx.Failure('wake_window_elapsed')
                if len(data) > max_bytes:
                    raise PageRefused('RESPONSE_TOO_LARGE', 'public response too large')
                decoded = json.loads(data)
                value = decoded if validate is None else validate(decoded)
                outcome = 'SUCCESS'
                return value
            except bx.Cooldown as exc:
                outcome = 'NO_HTTP_STATUS' if no_status else f'HTTP_{status}' if status else 'SHARED_COOLDOWN'
                if received_early:
                    outcome = 'CLOCK_BEFORE_WINDOW'
                    raise bx.Failure('clock_before_window') from None
                if not no_status or self.deadline is None or exc.not_before >= self.deadline or attempt + 1 >= self.f['request_attempts']:
                    raise
                prior_no_status_at, wait_until = attempted, exc.not_before
            except bx.Blocked as exc:
                outcome = f'HTTP_{status}' if status else 'SHARED_STOP'
                raise
            except bx.GateTerminal as exc:
                outcome = exc.reason.upper()
                raise
            except bx.Failure as exc:
                if outcome != 'NOT_SENT_WINDOW_ELAPSED':
                    outcome = exc.reason.upper()
                raise
            except PublicStatus as exc:
                outcome = f'HTTP_{exc.code}'
                if 300 <= exc.code < 400:
                    raise Blocked('public endpoint redirected') from None
                if received_early:
                    outcome = 'CLOCK_BEFORE_WINDOW'
                    raise bx.Failure('clock_before_window') from None
                if not 500 <= exc.code < 600:
                    raise PageRefused(outcome, 'public request refused') from None
                last_page_failure = outcome
            except Blocked:
                outcome = 'RETRY_JOURNAL_UNAVAILABLE'
                raise
            except PageRefused as exc:
                outcome = exc.reason
                raise
            except Refuse as exc:
                outcome = 'INVALID_PAGE'
                raise PageRefused(outcome, str(exc)) from None
            except ValueError:
                outcome = last_page_failure = 'INVALID_PAGE'
            except OSError:
                outcome = 'GATE_STORAGE'
                raise Blocked('shared venue gate I/O failed; refusing further requests') from None
            except (KeyError, TypeError):
                outcome = 'INVALID_PAGE'
                raise
            except Exception:
                outcome = 'FAILED'
                raise
            finally:
                if retry is not None:
                    actual = attempted or retry_at
                    self.log_retry(dict(kind='retry_outcome', endpoint=endpoint, coin=coin,
                                        first_attempt_at=retry['first_attempt_at'], retry_at=iso(actual),
                                        delay_s=(actual - clock_at(retry['first_attempt_at'])).total_seconds(),
                                        outcome=outcome, http_status=status if type(status) is int else None,
                                        retry_sha256=retry['sha256']))
            if wait_until is not None:
                began = self.clock()
                self.sleep(max(0., (wait_until - began).total_seconds()))
                self.retry_delay_s += max(0., (self.clock() - began).total_seconds())
                continue
            if attempt + 1 < self.f['request_attempts']:
                if self.deadline is not None and self.clock() + timedelta(seconds=delay) >= self.deadline:
                    raise bx.Failure('wake_window_elapsed')
                self.sleep(delay)
        raise PageRefused(last_page_failure, 'public page unavailable')

    def products(self, names):
        return self.get('/api/v3/exchangeInfo', validate=lambda raw: self.parse_products(raw, names))

    @staticmethod
    def parse_products(raw, names):
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
        return self.get('/api/v3/klines', coin=coin, symbol=coin + 'USD', interval='1d', startTime=start, endTime=stop-1,
                        limit=limit, validate=lambda raw: self.parse_candles(raw, start, stop, step, limit))

    @staticmethod
    def parse_candles(raw, start, stop, step, limit):
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
        limit = self.f['depth_limit']
        return self.get('/api/v3/depth', coin=coin, symbol=coin + 'USD', limit=limit,
                        validate=lambda raw: normalize_book(raw, limit))


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


def first_wake(rows):
    return next((row for row in rows if row['kind'] == 'wake'), None)


def closing_wake(first, days):
    return clock_at(first['wake']) + timedelta(days=days) if first else None


def warmup_days(rule):
    return max(rule['vol_days'] + 1, max(rule['lookbacks']))


def make_tape(log, f, rule):
    opening = first_wake(log)
    need(opening, 'no first wake')
    first = clock_at(opening['wake']).date()
    prefix = warmup_days(rule)
    origin = first - timedelta(days=prefix)
    # Pre-opening voids are counted in the journal but are not scored or traded.
    visits = [row for row in log if row['kind'] in MARKET_ROWS and row['wake'] >= opening['wake']]
    names = frozen(f['rule_source_sha256']).NAMES
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
            # Fix the decision on closed prices as known at this wake. An older
            # mark lets a queued exit be sized; the core still requires d-1 for buys.
            known = closes[:d, j]
            finite = known[np.isfinite(known)]
            opens[d, j] = finite[-1] if finite.size else np.nan
            sale[d, j] = market
    return SimpleNamespace(days=days, names=tuple(names), opens=opens, closes=closes, eligible=active, sell=sale), rows, prefix


def execution(tape, rows, size, fees, details, label, decision_only):
    names = tape.names

    def execute(d, delta, px, cash, queued, wanted, goal):
        row = rows[d]
        result = {'attempts': {}, 'fills': [], 'queued_sells': [], 'intent': {}}
        details[d] = result
        if row.get('kind') != 'wake':
            return np.zeros_like(delta), np.zeros(len(px)), np.zeros(len(px))
        fixed = delta.copy()
        for j, coin in enumerate(names):
            if not np.any(fixed[j]):
                continue
            ref = float(fixed[j].sum())
            side = 'buy' if ref > 1e-14 else 'sell' if ref < -1e-14 else 'internal'
            result['intent'][coin] = {'side': side, 'sleeve_target_weights': wanted[j].tolist(),
                                      'sleeve_target_units': (goal[j] * size).tolist(),
                                      'sleeve_targets_delta': fixed[j].tolist(),
                                      'closed_mark': float(px[j]), 'units': abs(ref) * size / float(px[j])}
            if side == 'buy' and coin in row['candle_failures']:
                result['intent'][coin]['side'] = 'void_buy'
                fixed[j] = 0
        if decision_only == d:
            return np.zeros_like(delta), np.zeros(len(px)), np.zeros(len(px))
        need(row['intent'][label] == result['intent'], 'closed-bar intent changed on replay')
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

        gross_ref = fixed.sum(axis=1)
        for j in range(len(names)):
            coin = names[j]
            planned = result['intent'].get(coin)
            if planned and planned['side'] == 'void_buy':
                disabled(j, 'void_buy')
            ref = gross_ref[j]
            if abs(ref) <= 1e-14:
                continue
            book, market = depth.get(coin), state[coin]
            if not market['market']:
                disabled(j, 'pair_unavailable')
            elif not book:
                disabled(j, 'book_late' if row['depth_failures'].get(coin) == 'WINDOW_ELAPSED' else 'book_missing')
            elif not book['timely']:
                disabled(j, 'book_late')
            elif not (market['base_min'] or market['usd_min']):
                disabled(j, 'minimum_unknown')
            else:
                _, _, _, reason = fill_at(j, ref)
                if reason:
                    disabled(j, reason)

        def candidate(scale):
            proposed = fixed * np.where(gross_ref > 1e-14, scale, 1.)[:, None]
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
            units = abs(float(final[j].sum() * size / px[j]))
            mark = math.copysign(units * midpoint(depth[coin]), net[j])
            gross, charge = float(net[j] * size), float(charges[j] * size)
            cost_bp = ((gross - mark) + charge) / abs(mark) * 10000
            result['fills'].append(dict(coin=coin, side='buy' if gross > 0 else 'sell', gross=gross, fee=charge,
                                        quantity=units, cost_bp=cost_bp, delay_s=depth[coin].get('retry_delay_s', 0.)))
        result['queued_sells'] = [names[j] for j in np.flatnonzero(queued.any(axis=1) & ~(final < -1e-14).any(axis=1))]
        return final, net, charges

    return execute


def run_book(log, f, rule, fees, label, decision_only=False):
    core = frozen(f['rule_source_sha256'])
    tape, rows, prefix = make_tape(log, f, rule)
    inp = core.indicators(tape, rule['lookbacks'], rule, rule['vault_annual_days'])
    roster = core.calendar(tape, inp[2])
    details = {}
    hook = execution(tape, rows, f['bankroll_usd'][label], fees, details, label,
                     len(rows) - 1 if decision_only else None)
    book = core.play(tape, 0., rule, rule['cap'], inp, roster, execution=hook)
    return tape, prefix, book, details, inp[2]


def page(fetch, failures, key, *args):
    try:
        return fetch(key, *args)
    except (Blocked, bx.Blocked, bx.GateTerminal, bx.Failure, bx.Refuse):
        raise
    except (Refuse, OSError, ValueError, KeyError, TypeError):
        failures[key] = 'PAGE_UNAVAILABLE'
        return None


def snapshots(venue, coins, wake, clock, deadline, not_before=None):
    result, failed = {}, {}
    for coin in coins:
        dispatch = clock()
        check_not_early(dispatch, not_before)
        if dispatch >= deadline:
            failed[coin] = 'WINDOW_ELAPSED'
            continue
        book = page(venue.book, failed, coin)
        received = clock()
        check_not_early(received, not_before)
        if book and wake <= received < deadline:
            result[coin] = book | {'received': iso(received), 'timely': True,
                                   'retry_delay_s': getattr(venue, 'retry_delay_s', 0.)}
        else:
            failed.setdefault(coin, 'WINDOW_ELAPSED' if received >= deadline else 'DEPTH_UNAVAILABLE')
    return result, failed


def capture(fd, log, wake, observed, venue, clock, f, rule, fees, closing, deadline):
    before = [row for row in log if row['kind'] == 'wake']
    roster = list(frozen(f['rule_source_sha256']).NAMES)
    not_before = wake + timedelta(seconds=f['wake_delay_s'])
    check_not_early(clock(), not_before)
    pairs = venue.products(roster)
    received = clock()
    check_not_early(received, not_before)
    if received >= deadline:
        raise bx.Failure('wake_window_elapsed')
    since = (clock_at(before[-1]['wake']) if before else
             wake - timedelta(days=warmup_days(rule)))
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
            dispatch = clock()
            check_not_early(dispatch, not_before)
            if dispatch >= deadline:
                raise bx.Failure('wake_window_elapsed')
            until = min(wake, cursor + timedelta(days=f['candle_page_days']))
            bars = page(venue.candles, row['candle_failures'], coin, cursor, until)
            received = clock()
            check_not_early(received, not_before)
            if received >= deadline:
                raise bx.Failure('wake_window_elapsed')
            if bars is not None:
                row['candles'].setdefault(coin, {}).update(bars)
            cursor = until
    if not closing:
        intents, selected = {}, set()
        for label in f['bankroll_usd']:
            tape, _, _, details, warm = run_book(log + [row], f, rule, fees, label, decision_only=True)
            intents[label] = details[len(tape.days) - 1]['intent']
            selected.update(c for c, intent in intents[label].items() if intent['side'] in ('buy', 'sell'))
        if not before and f['reference_coin'] in roster:
            selected.add(f['reference_coin'])  # first-wake benchmark only; cannot create a trade
        order_coins = [c for c in roster if c in selected and states[c]['market']]
        decision = append(fd, log, dict(kind='decision', wake=iso(wake), fixed=iso(clock()), intent=intents,
                                        roster=roster, order_coins=order_coins, candle_sha256=digest(row['candles'])))
        row['intent'] = decision['intent']
        row['decision_sha256'] = decision['sha256']
        row['depth'], row['depth_failures'] = snapshots(venue, order_coins, wake, clock, deadline, not_before)
        row['late'] = any(reason == 'WINDOW_ELAPSED' for reason in row['depth_failures'].values())
        row['books'], follow = {}, set()
        for label in f['bankroll_usd']:
            tape, _, _, details, warm = run_book(log + [row], f, rule, fees, label)
            row['books'][label] = details[len(tape.days) - 1]
            follow.update(row['books'][label]['attempts'])
        row['not_ready'] = [coin for j, coin in enumerate(roster) if not warm[-2, j].any()]
        row['follow'] = [coin for coin in roster if coin in follow and states[coin]['market']]
    return row


@contextmanager
def retry_journal(venue, fd, rows, wake, phase, offset=None):
    # The caller holds writer.lock for all writes made through this callback.
    if not isinstance(venue, BinanceUS):
        yield
        return
    prior = venue.retry_sink
    context = dict(wake=iso(wake), phase=phase)
    if offset is not None:
        context['offset'] = offset
    venue.retry_sink = lambda event: append(fd, rows, context | event)
    try:
        yield
    finally:
        venue.retry_sink = prior


def unfinished_claim(rows, last_visit):
    claim = next((r for r in reversed(rows) if r['kind'] == 'claim'), None)
    return claim if claim and (last_visit is None or claim['wake'] > last_visit['wake']) else None


def record(now, venue=None, folder=None, clock=now_utc, sleep=time.sleep):
    f, rule, fees = settings()
    folder = Path(f['private_dir']) if folder is None else folder
    with private(folder) as fd, lock(fd, 'observer.lock'):
        with lock(fd, 'writer.lock'):
            rows = read_log(fd, recover=True)
            header = checked(rows)
            need(not any(r['kind'] == 'blocked' for r in rows), 'venue blocked; recording stopped')
            visits = [r for r in rows if r['kind'] in MARKET_ROWS]
            first = clock_at(header['first'])
            end = closing_wake(first_wake(visits), f['score_days'])
            claim = unfinished_claim(rows, visits[-1] if visits else None)
            if claim:
                return append(fd, rows, dict(kind='void', wake=claim['wake'], reason='WAKE_INTERRUPTED'))
            if end is not None and clock_at(visits[-1]['wake']) >= end:
                return None
            wake = midnight(now) if end is None else min(midnight(now), end)
            deadline = midnight(wake) + timedelta(seconds=f['quote_offsets_s'][-1])
            next_day = clock_at(visits[-1]['wake']) + timedelta(days=1) if visits else first
            if wake < next_day or now < wake + timedelta(seconds=f['wake_delay_s']):
                return None
            while next_day < wake:
                append(fd, rows, dict(kind='void', wake=iso(next_day), reason='MISSED_WAKE'))
                next_day += timedelta(days=1)
            if now >= deadline:
                return append(fd, rows, dict(kind='void', wake=iso(wake), reason='LATE_WAKE'))
            venue = venue if venue is not None else BinanceUS(f, clock=clock, sleep=sleep)
            if isinstance(venue, BinanceUS):
                venue.deadline = deadline
                venue.generation = header['venue_generation']
                try:
                    preflight(venue.gate, venue.generation)
                except (bx.GateTerminal, bx.Blocked, bx.Refuse) as exc:
                    append(fd, rows, {'kind': 'blocked', 'wake': iso(wake), 'reason': terminal_reason(exc)})
                    raise Blocked(str(exc)) from None
            committed_go('E16_START', header['authorization'], header['release'], header['venue_generation'])
            frozen(f['rule_source_sha256'])
            append(fd, rows, dict(kind='claim', wake=iso(wake), claimed=iso(clock())))
            try:
                if isinstance(venue, BinanceUS):
                    venue.not_before = wake + timedelta(seconds=f['wake_delay_s'])
                with retry_journal(venue, fd, rows, wake, 'CLOSE' if wake == end else 'PRIMARY'):
                    row = capture(fd, rows, wake, now, venue, clock, f, rule, fees, closing=wake == end, deadline=deadline)
            except (Blocked, bx.Blocked, bx.GateTerminal, bx.Refuse) as exc:
                append(fd, rows, {'kind': 'blocked', 'wake': iso(wake), 'reason': terminal_reason(exc)})
                raise Blocked(str(exc)) from None
            except (Refuse, bx.Failure, OSError, ValueError, TypeError, KeyError) as exc:
                return append(fd, rows, dict(kind='void', wake=iso(wake), reason=wake_reason(exc)))
            finally:
                if isinstance(venue, BinanceUS):
                    venue.not_before = None
            row = append(fd, rows, row)
        for offset in f['quote_offsets_s']:
            if not row.get('follow'):
                break
            target = wake + timedelta(seconds=offset)
            delay = (target - clock()).total_seconds()
            if delay < 0:
                continue
            sleep(delay)
            diagnostic_end = target + timedelta(seconds=f['timeout_s'])
            if isinstance(venue, BinanceUS):
                venue.deadline = diagnostic_end
            with lock(fd, 'writer.lock', blocking=True):
                try:
                    with retry_journal(venue, fd, rows, wake, 'DIAGNOSTIC', offset):
                        books, failures = snapshots(venue, row['follow'], wake, clock, diagnostic_end)
                except (Blocked, bx.Blocked, bx.GateTerminal, bx.Refuse) as exc:
                    append(fd, rows, {'kind': 'blocked', 'reason': terminal_reason(exc)})
                    raise Blocked('venue stopped during diagnostics') from None
                except bx.Failure as exc:
                    books, failures = {}, {c: str(exc.reason).upper() for c in row['follow']}
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
    result = {'card': 'E16', 'status': status, 'wakes': len(wakes),
              'missed_wakes': sum(r['kind'] == 'void' and r['reason'] == 'MISSED_WAKE' for r in rows),
              'unavailable_wakes': sum(r['kind'] == 'void' and r['reason'] not in {
                  'MISSED_WAKE', 'WAKE_INTERRUPTED', 'LATE_WAKE', 'SHARED_COOLDOWN',
                  'SHARED_GATE_BUSY', 'WAKE_WINDOW_ELAPSED'} for r in rows),
              'interrupted_wakes': sum(r.get('reason') == 'WAKE_INTERRUPTED' for r in rows),
              'cooldown_void_wakes': sum(r.get('reason') == 'SHARED_COOLDOWN' for r in rows),
              'other_gate_void_wakes': sum(r.get('reason') in ('SHARED_GATE_BUSY', 'WAKE_WINDOW_ELAPSED') for r in rows),
              'late_wakes': sum(w['late'] for w in wakes) + sum(r.get('reason') == 'LATE_WAKE' for r in rows),
              'roster_count': len(wakes[0]['roster']) if wakes else None,
              'not_ready_coin_wakes': sum(len(w['not_ready']) for w in wakes),
              'candle_page_refusals': sum(len(w['candle_failures']) for w in wakes),
              'book_unavailable_coin_wakes': sum(len(w['depth_failures']) for w in wakes),
              'follow_observations': sum(len(r['depth']) for r in follow),
              'cooldown_void_follow_coin_slots': sum(reason == 'SHARED_COOLDOWN' for r in follow
                                                    for reason in r['depth_failures'].values()), 'lines': {}}
    midcost = [(book['asks'][0][0] - book['bids'][0][0]) / (2 * midpoint(book)) * 10000
               for w in wakes for book in w['depth'].values()]
    result['displayed_half_spread'] = stats(midcost)
    for label in f['bankroll_usd']:
        entries = [w['books'][label] for w in wakes]
        fills = [fill for entry in entries for fill in entry['fills']]
        result['lines'][label] = {'attempts': sum(len(entry['attempts']) for entry in entries), 'fills': len(fills),
                                  'queued_sell_coin_wakes': sum(len(entry['queued_sells']) for entry in entries),
                                  'attempt_flags': {name: sum(name in flags for entry in entries for flags in entry['attempts'].values())
                                                    for name in ('void_buy', 'pair_unavailable', 'book_missing', 'book_late', 'minimum_unknown',
                                                                 'insufficient_depth', 'under_minimum', 'over_maximum',
                                                                 'unplaceable_after_cash_scaling')},
                                  'all_in_cost_by_side': {side: stats([fill['cost_bp'] for fill in fills if fill['side'] == side])
                                                         for side in ('buy', 'sell')}}
    return result


def alive(folder=None):
    f, _, _ = settings()
    folder = Path(f['private_dir']) if folder is None else folder
    with private(folder) as fd, lock(fd, 'writer.lock'):
        rows = read_log(fd)
        checked(rows)
        return summary(rows, f)


def publish(folder=None, path=PUBLIC):
    # Keep snapshot and replace under one writer lock: public summaries cannot roll back.
    f, _, _ = settings()
    folder = Path(f['private_dir']) if folder is None else folder
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
    first = first_wake(rows)
    need(first, 'no first wake')
    need(now >= max(clock_at(first['wake']), clock_at(first['observed'])) + timedelta(days=days), 'forward year incomplete')
    end = closing_wake(first, days)
    need(any(r['kind'] == 'close' and clock_at(r['wake']) == end for r in rows)
         and not any(r['kind'] == 'blocked' for r in rows), 'closing observation missing')
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


def score(now, go, folder=None):
    f, rule, fees = settings()
    folder = Path(f['private_dir']) if folder is None else folder
    with private(folder) as fd, lock(fd, 'writer.lock'):
        rows = read_log(fd)
        header = checked(rows)
        first = score_gate(rows, now, f['score_days'])
        need(go != header['authorization'], 'score needs its separate lead go')
        authorization, _ = committed_go('E16_SCORE_GO', go, header['release'])
        result = {'label': 'RECORD_NOT_VERDICT', 'lines': {k: private_metrics(rows, first, f, rule, fees, k) for k in f['bankroll_usd']}}
        append(fd, rows, dict(kind='score', read=iso(now), authorization_commit=authorization, result_sha256=digest(result)))
        return result


def wake_reason(exc):
    if isinstance(exc, (PageRefused, bx.Failure, bx.GateTerminal)):
        return exc.reason.upper()
    if isinstance(exc, (ValueError, KeyError, TypeError)):
        return 'INVALID_PAGE'
    return 'WAKE_IO_FAILED' if isinstance(exc, OSError) else 'WAKE_REFUSED'


def terminal_reason(exc):
    if isinstance(exc, bx.Blocked):
        return f'HTTP_{exc.status}'
    if isinstance(exc, bx.GateTerminal):
        return exc.reason.upper()
    return {
        'public endpoint redirected': 'ENDPOINT_REDIRECTED',
        'could not durably record venue retry': 'RETRY_JOURNAL_UNAVAILABLE',
        'shared venue gate I/O failed; refusing further requests': 'GATE_STORAGE',
    }.get(str(exc), 'VENUE_REFUSED')


def preflight(gate, generation):
    try:
        gate.check_start(generation=generation)
    except bx.Blocked:
        raise
    except bx.Failure as exc:
        if exc.reason != 'shared_gate_busy':
            raise
        # No request in this check; the actual attempt still enforces the gate
        # and books the slot as void if it cannot acquire the lock in time.


def resume(folder=None, gate=None):
    folder = Path(settings()[0]['private_dir']) if folder is None else folder
    with private(folder) as fd, lock(fd, 'writer.lock'):
        rows = read_log(fd, recover=True)
        header = checked(rows)
        need(not any(r['kind'] == 'blocked' for r in rows), 'venue blocked; recording stopped')
        try:
            preflight(venue_gate(gate), header['venue_generation'])
        except (bx.GateTerminal, bx.Blocked, bx.Refuse) as exc:
            # Count an abandoned local attempt even when shared safety forbids resuming.
            last_visit = next((r for r in reversed(rows) if r['kind'] in MARKET_ROWS), None)
            claim = unfinished_claim(rows, last_visit)
            if claim:
                append(fd, rows, dict(kind='void', wake=claim['wake'], reason='WAKE_INTERRUPTED'))
            append(fd, rows, {'kind': 'blocked', 'reason': terminal_reason(exc)})
            raise Blocked(str(exc)) from None


def loop(folder=None):
    f, _, _ = settings()
    folder = Path(f['private_dir']) if folder is None else folder
    with private(folder) as fd, lock(fd, 'loop.lock'):
        try:
            resume(folder)
        except Blocked:
            publish(folder)
            raise
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
                end = closing_wake(first_wake(rows), f['score_days'])
                if end is not None and any(r['kind'] in MARKET_ROWS and clock_at(r['wake']) >= end for r in rows):
                    return
            t = now_utc()
            if row and clock_at(row['wake']) < midnight(t):
                continue
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
    except (Refuse, bx.Blocked, bx.GateTerminal, bx.Failure, bx.Refuse, OSError, ValueError, KeyError, TypeError) as exc:
        print('REFUSED ' + (str(exc) if isinstance(exc, Refuse) else type(exc).__name__))
        return 2
    finally:
        os.umask(prior)


if __name__ == '__main__':
    raise SystemExit(main())
