#!/usr/bin/env python3
"""Plan 69 search only. No order endpoint, vault mode, or individual trade output."""

import argparse
from bisect import bisect_right
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
import fcntl
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time as sleep_clock
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

HERE = Path(__file__).resolve().parent
STORE = Path('/home/user/workspace/rig/data/sweep_69')
CONFIG = HERE.parent / 'config' / 'thresholds.yaml'
BAR_FILE, RECEIPT = 'bars_sip_5min.jsonl.gz', 'collection_receipt.json'
NY, UTC = ZoneInfo('America/New_York'), timezone.utc
ENDPOINT = 'https://data.alpaca.markets/v2/stocks/bars'
FIELDS = ('o', 'h', 'l', 'c', 'v', 'vw')


def open_directory(path):
    """Walk physical directories using anchored directory FDs; never follow symlinks."""
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def read_once(path, directory_fd=None):
    parent = open_directory(path.parent) if directory_fd is None else directory_fd
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, 'rb') as file:
            if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
                raise ValueError('Custody input must be a regular file')
            return file.read()
    finally:
        if directory_fd is None:
            os.close(parent)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verified(raw, expected, label):
    actual = digest(raw)
    if actual != expected:
        raise ValueError(f'Custody SHA-256 mismatch: {label}')
    return actual


CONFIG_RAW = read_once(CONFIG)
P = json.loads(re.search(rb'^replay_69_plan:\n  value: (\{[^\n]+\})$', CONFIG_RAW, re.M).group(1))
FIRST, LAST, SECOND, SETTLE_CHANGE = (date.fromisoformat(P[k]) for k in ('first', 'last', 'half2', 'settle_change'))
# Absolute safety ceiling stays independently fail-closed if the settings file is modified.
if (FIRST.isoformat(), LAST.isoformat()) != ('2016-01-04', '2021-12-31'):
    raise ValueError('Configured search dates do not equal the absolute Plan 69 fence')
MARKS, SYN = P['marks'], P['synthetic']
MINS = P['bar_minutes']
BARS, CASH, YEARS = P['session_minutes'] // MINS, P['capital'], P['years']
SCOPE = f'plan-69-search-only-{FIRST}_{LAST}'


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


def session_list(start=FIRST, end=LAST, *, calendar_raw):
    date_fence(start, end)
    records = json.loads(calendar_raw)['sessions']
    lo, hi = start.isoformat(), end.isoformat()
    return [(date.fromisoformat(d), parse_time(o), parse_time(c))
            for d, o, c in records if lo <= d <= hi]


def offset(clock):
    h, m = map(int, clock.split(':'))
    start = time.fromisoformat(P['session_open'])
    minutes = 60 * (h - start.hour) + m - start.minute
    if not 0 <= minutes <= P['session_minutes'] or minutes % MINS:
        raise ValueError('Not a valid five-minute regular-hours clock')
    return minutes // MINS


def print_spec(spec):
    i = offset(spec['clock_et'])
    mode = spec['print']
    if mode not in ('open', 'close') or not (0 <= i - (mode == 'close') < BARS):
        raise ValueError('Invalid trade print')
    return i, mode


def load_grid(grid_raw):
    grid = json.loads(grid_raw)
    rules = grid['rules']
    if not 1 <= len(rules) <= P['rule_limit'] or len({r['id'] for r in rules}) != len(rules):
        raise ValueError('Bad rule count or duplicate ID')
    for r in rules:
        e, _ = print_spec(r['entry'])
        x, _ = print_spec(r['exit'])
        if r['family'] not in grid['families'] or r['pool'] not in grid['pools']:
            raise ValueError('Rule has an unknown family or pool')
        if type(r['exit']['session_offset']) is not int or r['exit']['session_offset'] not in (0, 1) or (not r['exit']['session_offset'] and x <= e):
            raise ValueError('Rule has an invalid exit clock')
        if r['latest_signal_close_et'] is not None and offset(r['latest_signal_close_et']) >= e:
            raise ValueError('Rule may use a bar not closed strictly before entry')
        if r['side'] not in ('long', 'short') or type(r['cash_500']) is not bool or r['cash_500'] != (r['side'] == 'long'):
            raise ValueError('Only a long position in a listed security can be cash judged')
    return grid


def roster(grid):
    return tuple(sorted({s for symbols in grid['universe'].values() for s in symbols}))


def approval(root_fd):
    """Verify captured buffers before parsing; pass the same buffers to consumers."""
    status = json.loads(read_once(STORE / 'search_approval.json', root_fd))
    bufs = {name: read_once(HERE / name) for name in ('GRID_69.json', 'sweep_69.py', 'calendar_65.json')}
    bufs['identity.json'] = read_once(STORE / 'identity.json', root_fd)
    bufs['thresholds.yaml'] = CONFIG_RAW
    if (status.get('scope') != SCOPE or not isinstance(status.get('approved_by'), str)
            or not status['approved_by'].strip() or set(status.get('sha256', {})) != set(bufs)):
        raise ValueError('Missing or mismatched independent Plan 69 collection approval')
    pins = {name: verified(buf, status['sha256'][name], name) for name, buf in bufs.items()}
    return bufs, pins


def read_identity(grid, identity_raw):
    """Dated, non-price identity and split data. No substitution for delisted securities."""
    obj = json.loads(identity_raw)
    if obj.get('coverage_start') != FIRST.isoformat() or obj.get('coverage_end') != LAST.isoformat():
        raise ValueError('The identity register must cover exactly the search dates')
    members = obj['members']
    if set(members) != set(roster(grid)):
        raise ValueError('The identity register must retain every original member')
    spans, splits, actions = [], {}, set()
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
            day = date.fromisoformat(p['effective_date'])
            if type(p['new_per_old']) not in (int, float):
                raise ValueError('Split ratios must be numeric, not boolean')
            factor = float(p['new_per_old'])
            date_fence(day, day)
            if (not math.isfinite(factor) or factor <= 0 or (member, day) in splits
                    or not any(m == member and lo <= day <= hi for m, _, lo, hi in spans)):
                raise ValueError('Invalid split register row')
            splits[member, day] = factor
            actions.add((member, day))
        for p in rec.get('other_actions', []):
            day = date.fromisoformat(p['effective_date'])
            date_fence(day, day)
            if (p['kind'] not in ('cash_distribution', 'spin_off', 'reorganization')
                    or not p['source'].startswith('https://')
                    or not any(m == member and lo <= day <= hi for m, _, lo, hi in spans)):
                raise ValueError('Invalid non-price corporate-action row')
            actions.add((member, day))
    for periods in by_alias.values():
        periods.sort()
        if any(later[0] <= earlier[1] for earlier, later in zip(periods, periods[1:])):
            raise ValueError('A ticker cannot represent two original members at once')
    return spans, splits, actions


class BarsTransportFailure(ValueError):
    pass


def bars_transport():
    REQUEST_PAUSE_SECONDS = 0.25
    env = {k: os.environ[k] for k in ('HTTPS_PROXY', 'CURL_CA_BUNDLE', 'SSL_CERT_FILE') if k in os.environ}
    if not env.get('HTTPS_PROXY'):
        raise ValueError('Alpaca collection requires the credential HTTPS proxy')
    argv = ['/usr/bin/curl', '--disable', '--silent', '--show-error', '--compressed', '--proto', '=https',
            '--connect-timeout', '20', '--max-time', '60', '--write-out', '\n%{http_code}', '--config', '-']

    def get(query):
        # urlencode escapes curl-config metacharacters; the fixed URL is never in argv.
        stdin = f'url = "{ENDPOINT}?{urlencode(query)}"\n'.encode('ascii')
        for delay in (0, 2, 4, 8, 16, 32, 64, 128):
            if delay:
                sleep_clock.sleep(delay)
            sleep_clock.sleep(REQUEST_PAUSE_SECONDS)
            response = subprocess.run(argv, input=stdin, capture_output=True, env=env, check=False)
            body, separator, status = response.stdout.rpartition(b'\n')
            if not separator or len(status) != 3 or not status.isdigit() or status == b'000':
                continue
            code = int(status)
            if code != 200 and code not in (429, 500, 502, 503, 504):
                raise ValueError(f'Alpaca bars HTTP {code}; no response body logged')
            if response.returncode:
                continue
            if code == 200:
                try:
                    return json.loads(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
            if delay >= 16:
                raise ValueError(f'Alpaca bars HTTP {code}; no response body logged')
        raise BarsTransportFailure('Alpaca bars transport failed; no response body logged')

    return get


def bars_pages(ticker, start, end, get):
    date_fence(start, end)
    window = {'symbols': ticker, 'timeframe': f'{MINS}Min', 'feed': 'sip', 'adjustment': 'raw',
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


def collection_header(start, end, pins):
    return {'feed': 'sip', 'timeframe': f'{MINS}Min', 'adjustment': 'raw', 'asof': '-',
            'start': start.isoformat(), 'end': end.isoformat(), 'input_sha256': pins}


def new_private(root_fd, name):
    fd = os.open(name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=root_fd)
    try:
        os.fchmod(fd, 0o600)
        return os.fdopen(fd, 'w+b')
    except BaseException:
        os.close(fd)
        raise


def publish(root_fd, staging, destination, *, dest_fd=None):
    target = root_fd if dest_fd is None else dest_fd
    os.link(staging, destination, src_dir_fd=root_fd, dst_dir_fd=target, follow_symlinks=False)
    os.fsync(target)
    os.unlink(staging, dir_fd=root_fd)
    os.fsync(root_fd)


def chunk_metadata(span, pins):
    member, alias, start, end = span
    return {'span': [member, alias, start.isoformat(), end.isoformat()], 'input_sha256': pins}


def chunk_name(index, metadata):
    return f'{index:04d}-{digest(json.dumps(metadata, sort_keys=True).encode())}.jsonl'


def chunk_header(metadata, rows, pin, width):
    return json.dumps({**metadata, 'rows': rows, 'rows_sha256': pin}, sort_keys=True).encode().ljust(width) + b'\n'


def store_chunk(chunks_fd, name, span, metadata, get):
    member, alias, start, end = span
    temp = name + '.tmp'
    sha, rows = hashlib.sha256(), 0
    # Reserve first-line space for the final row count and payload digest.
    width = len(chunk_header(metadata, 0, '0' * 64, 0)) + 24
    with new_private(chunks_fd, temp) as file:
        file.write(chunk_header(metadata, 0, '0' * 64, width))
        for row in bars_pages(alias, start, end, get):
            line = (json.dumps([member, alias, row['t'], *(row.get(k) for k in FIELDS)],
                               allow_nan=False, separators=(',', ':')) + '\n').encode()
            file.write(line)
            sha.update(line)
            rows += 1
        file.seek(0)
        file.write(chunk_header(metadata, rows, sha.hexdigest(), width))
        file.flush()
        os.fsync(file.fileno())
    publish(chunks_fd, temp, name)
    return rows


def read_chunk(chunks_fd, name, metadata, out=None):
    problem = f'Invalid collection chunk {name}; inspect and delete it before re-collecting this span'
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=chunks_fd)
    with os.fdopen(fd, 'rb') as file:
        mode = os.fstat(file.fileno()).st_mode
        if not stat.S_ISREG(mode) or stat.S_IMODE(mode) != 0o600:
            raise ValueError(problem)
        raw = file.readline(len(chunk_header(metadata, 0, '0' * 64, 0)) + 25)
        try:
            header = json.loads(raw)
        except (ValueError, UnicodeError):
            raise ValueError(problem) from None
        if (not raw.endswith(b'\n') or not isinstance(header, dict)
                or {k: v for k, v in header.items() if k not in ('rows', 'rows_sha256')} != metadata
                or type(header.get('rows')) is not int or header['rows'] < 0):
            raise ValueError(problem)
        sha, rows = hashlib.sha256(), 0
        for line in file:
            if not line.endswith(b'\n'):
                raise ValueError(problem)
            sha.update(line)
            rows += 1
            if out is not None:
                out.write(line)
        if rows != header['rows'] or sha.hexdigest() != header.get('rows_sha256'):
            raise ValueError(problem)
        return rows


def consolidate_chunks(root_fd, chunks_fd, chunks, start, end, pins):
    temp, temp_receipt = 'archive.tmp', 'receipt.tmp'
    count = 0
    with new_private(chunks_fd, temp) as file:
        with gzip.GzipFile(fileobj=file, mode='wb', filename='', mtime=0) as out:
            out.write((json.dumps(collection_header(start, end, pins)) + '\n').encode())
            for name, metadata, _ in chunks:
                count += read_chunk(chunks_fd, name, metadata, out)
        file.flush()
        os.fsync(file.fileno())
        file.seek(0)
        bar_pin = hashlib.file_digest(file, 'sha256').hexdigest()
    if not count:
        raise ValueError('Vendor returned no bars; chunks retained for audit')
    with new_private(chunks_fd, temp_receipt) as file:
        file.write((json.dumps({'scope': SCOPE, 'bars_sha256': bar_pin, 'input_sha256': pins,
                                'archive_records': count}, sort_keys=True) + '\n').encode())
        file.flush()
        os.fsync(file.fileno())
    publish(chunks_fd, temp, BAR_FILE, dest_fd=root_fd)
    publish(chunks_fd, temp_receipt, RECEIPT, dest_fd=root_fd)
    return {'bars_sha256': bar_pin, 'archive_records': count}


def collect(grid, start, end, root_fd, bufs, pins):
    date_fence(start, end)
    if (start, end) != (FIRST, LAST):
        raise ValueError('The persisted collection must cover the entire frozen search')
    spans, _, _ = read_identity(grid, bufs['identity.json'])
    session_list(start, end, calendar_raw=bufs['calendar_65.json'])
    fcntl.flock(root_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        for name in (BAR_FILE, RECEIPT, BAR_FILE + '.partial', RECEIPT + '.partial'):
            try:
                os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise ValueError('Existing search data, receipt or partial collection; do not overwrite')
        try:
            os.mkdir('chunks', 0o700, dir_fd=root_fd)
            os.fsync(root_fd)
        except FileExistsError:
            pass
        chunks_fd = os.open('chunks', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd)
        try:
            if stat.S_IMODE(os.fstat(chunks_fd).st_mode) != 0o700:
                raise ValueError('Collection chunks directory must have mode 0700')
            chunks = []
            for i, span in enumerate(spans, 1):
                metadata = chunk_metadata(span, pins)
                chunks.append((chunk_name(i, metadata), metadata, span))
            expected = {name for name, _, _ in chunks}
            completed = set()
            for name in sorted(os.listdir(chunks_fd)):
                if name.endswith('.tmp'):
                    os.unlink(name, dir_fd=chunks_fd)
                elif name not in expected:
                    raise ValueError(f'Unexpected collection chunk {name}; inspect approval pins before re-collecting')
                else:
                    completed.add(name)
            os.fsync(chunks_fd)
            counts = {name: read_chunk(chunks_fd, name, metadata)
                      for name, metadata, _ in chunks if name in completed}
            get = None  # Finished chunks can be consolidated without a transport.
            for i, (name, metadata, span) in enumerate(chunks, 1):
                if name not in counts:
                    if get is None:
                        get = bars_transport()
                    try:
                        counts[name] = store_chunk(chunks_fd, name, span, metadata, get)
                    except BarsTransportFailure as error:
                        print(f'{error}; spans done {len(counts)}, remaining {len(chunks) - len(counts)}', file=sys.stderr)
                        raise SystemExit(75) from None
                    print(f'Collection span {i} of {len(chunks)}: {counts[name]} rows', file=sys.stderr, flush=True)
            result = consolidate_chunks(root_fd, chunks_fd, chunks, start, end, pins)
            for name, _, _ in chunks:
                os.unlink(name, dir_fd=chunks_fd)
            os.fsync(chunks_fd)
        finally:
            os.close(chunks_fd)
        os.rmdir('chunks', dir_fd=root_fd)
        os.fsync(root_fd)
        print(json.dumps(result, sort_keys=True))
    finally:
        fcntl.flock(root_fd, fcntl.LOCK_UN)


# Ledger 217 pre-return ruling: accept only the completed, audited legacy collection.
LEGACY_COLLECTOR_SHA256 = 'f79efee37eefdc2c27d2a8ef51f10435169e87852e6becbd209f9141fe8ec43b'
LEGACY_ARCHIVE_SHA256 = '29abd63c9b371cb61e7e21ff65197bdedbd8b96451f8adcad847003c5985cd9e'
LEGACY_RECEIPT_SHA256 = '5dee5c67aa865a12a22937e1c4255751b8195285e3ffa0581a941df83e82c01a'
# Ledger 217 pre-return ruling: at most 0.1% overall and 10 masked days per member.
MASKED_DAY_LIMIT_DENOMINATOR, MASKED_DAYS_PER_MEMBER_LIMIT = 1000, 10


def archive_input(root_fd, pins, *, score):
    receipt_raw = read_once(STORE / RECEIPT, root_fd)
    receipt = json.loads(receipt_raw)
    receipt_pin = digest(receipt_raw)
    recorded = receipt.get('input_sha256')
    legacy = (receipt_pin == LEGACY_RECEIPT_SHA256 and receipt.get('bars_sha256') == LEGACY_ARCHIVE_SHA256
              and 'sweep_69.py' in pins and recorded == dict(pins, **{'sweep_69.py': LEGACY_COLLECTOR_SHA256}))
    if (receipt.get('scope') != SCOPE or (recorded != pins and not legacy)
            or type(receipt.get('archive_records')) is not int or receipt['archive_records'] <= 0):
        raise ValueError('Invalid Plan 69 collection receipt')
    if score:
        permit = json.loads(read_once(STORE / 'score_approval.json', root_fd))
        if (permit.get('scope') != SCOPE + '-score' or not isinstance(permit.get('approved_by'), str)
                or not permit['approved_by'].strip() or permit.get('collection_receipt_sha256') != receipt_pin
                or permit.get('bars_sha256') != receipt.get('bars_sha256')):
            raise ValueError('Missing or mismatched independent Plan 69 scoring approval')
    raw = read_once(STORE / BAR_FILE, root_fd)
    pin = verified(raw, receipt.get('bars_sha256'), BAR_FILE)
    return raw, pin, receipt['archive_records'], recorded


def is_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def jump_mask(a, dates, names, actions):
    """Screen the observed tape before mutating it; local bad days cannot seed overnight jumps."""
    limits = P['jump_ratio']
    outside = lambda v: (v < limits['lower']) | (v > limits['upper'])
    masked = np.zeros((len(dates), len(names)), dtype=bool)
    for i, name in enumerate(names):
        o, c = a[0, :, i].ravel(), a[3, :, i].ravel()
        seen = np.flatnonzero(np.isfinite(o) & np.isfinite(c))
        if not seen.size:
            continue
        days = seen // BARS
        earlier, later = days[:-1], days[1:]
        change = (outside(o[seen[1:]].astype(np.float64) / c[seen[:-1]])
                  | outside(c[seen[1:]].astype(np.float64) / c[seen[:-1]]))
        allowed = np.array([(name, day) in actions for day in dates])
        local = np.zeros(len(dates), dtype=bool)
        local[days[outside(c[seen].astype(np.float64) / o[seen])]] = True
        local[later[change & (earlier == later)]] = True
        local &= ~allowed
        masked[:, i] = local
        # Attribute a boundary jump to the later session, unless either endpoint
        # was already locally bad. Do not bridge over a masked session or rescan.
        overnight = change & (earlier != later) & ~local[earlier] & ~local[later] & ~allowed[later]
        masked[later[overnight], i] = True
    return masked


def mask_report(mask, dates, names, active_days):
    pairs = [(names[n], dates[d].isoformat()) for d, n in zip(*np.nonzero(mask))]
    years, members = defaultdict(int), defaultdict(int)
    for member, day in pairs:
        years[day[:4]] += 1
        members[member] += 1
    exceeded = (len(pairs) * MASKED_DAY_LIMIT_DENOMINATOR > active_days
                or any(total > MASKED_DAYS_PER_MEMBER_LIMIT for total in members.values()))
    return {'active_member_days': active_days, 'masked_member_days': len(pairs),
            'masked_member_day_pairs': pairs, 'masked_member_days_by_year': dict(years),
            'masked_member_days_by_member': dict(members), 'masked_member_day_limit_exceeded': exceeded}


def enforce_mask_limit(counts):
    if counts['masked_member_day_limit_exceeded']:
        raise ValueError('Masked member-day limit exceeded; stop for lead review')


def load_collection(grid, start, end, root_fd, bufs, pins, *, score):
    date_fence(start, end)
    if (start, end) != (FIRST, LAST):
        raise ValueError('The registered search uses the whole search period')
    raw, bar_pin, expected_count, collection_pins = archive_input(root_fd, pins, score=score)
    spans, splits, actions = read_identity(grid, bufs['identity.json'])
    sessions, names = session_list(start, end, calendar_raw=bufs['calendar_65.json']), roster(grid)
    dates = [x[0] for x in sessions]
    di, si = {d: i for i, d in enumerate(dates)}, {s: i for i, s in enumerate(names)}
    active = {(m, d): a for m, a, lo, hi in spans for d in dates if lo <= d <= hi}
    a = np.full((len(FIELDS), len(dates), len(names), BARS), np.nan, dtype=np.float32)
    count, kept = 0, 0
    with gzip.GzipFile(fileobj=io.BytesIO(raw), mode='rb') as f:
        header = json.loads(next(f))
        expected = collection_header(start, end, collection_pins)
        if header != expected:
            raise ValueError('Collection header does not match the registered inputs')
        for line in f:
            count += 1
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
            if seconds % (60 * MINS) or len(vals) != len(FIELDS):
                raise ValueError('Off-grid or malformed regular-hours bar')
            i = int(seconds / (60 * MINS))
            o, h, low, c, v, vw = vals
            if (not all(is_number(x) and x > 0 for x in vals[:5])
                    or low > min(o, c) or h < max(o, c)
                    or (vw is not None and (not is_number(vw) or vw <= 0))
                    or np.isfinite(a[0, d, n, i])):
                raise ValueError('Invalid or duplicate regular-hours bar')
            a[:, d, n, i] = vals
            kept += 1
    if count != expected_count:
        raise ValueError('Archive record count does not match collection receipt')
    for member, _, lo, hi in spans:
        span_days = [di[day] for day in dates if lo <= day <= hi]
        if span_days and not np.any(np.isfinite(a[0, span_days, si[member]])):
            raise ValueError('A documented active symbol span has no regular SIP bars; audit coverage first')
    split_array = np.ones((len(dates), len(names)))
    for (member, day), factor in splits.items():
        if day not in di:
            raise ValueError('Split date must be its first effective search session')
        split_array[di[day], si[member]] = factor
    if any(day not in di for _, day in actions):
        raise ValueError('Corporate-action date must be its first effective search session')
    mask = jump_mask(a, dates, names, actions)
    counts = {'archive_rows': count, 'regular_rows': kept, 'sessions': len(dates),
              'registered_instruments': len(names), 'active_alias_spans': len(spans),
              'instruments_with_regular_rows': int(np.any(np.isfinite(a[0]), axis=(0, 2)).sum()),
              'registered_splits': len(splits), 'registered_action_dates': len(actions)}
    counts.update(mask_report(mask, dates, names, len(active)))
    a[:, mask, :] = np.nan
    return dates, names, a, [int((c - o).total_seconds() / (60 * MINS)) for _, o, c in sessions], split_array, mask, counts, bar_pin


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
    def __init__(self, dates, names, a, lengths, splits, masked=None):
        if not dates or any(a >= b for a, b in zip(dates, dates[1:])):
            raise ValueError('Search session dates must be strictly ordered')
        date_fence(dates[0], dates[-1])
        if tuple(names) != tuple(sorted(set(names))):
            raise ValueError('Stable symbols must be unique and sorted')
        self.dates, self.names, self.a, self.splits = dates, names, a, splits
        self.masked = masked if masked is not None and masked.any() else None
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

    def masked_signal_windows(self, r, grid):
        """Identify candidates with an unknowable signal; never calculate one on bad bars."""
        if self.masked is None:
            return None
        fam, p = r['family'], r['signal']
        if fam == 'TEST':
            return None
        prior = p.get('volume_days', 0)
        current = fam != 'S8' and not (fam == 'S10' and p['type'] == 'low_vol')
        if fam == 'S6':
            prior = p['range_days']
        elif fam == 'S8':
            prior = p['past_days']
        elif fam == 'S10':
            prior = (p['vol_days'] if p['type'] == 'low_vol' else p['past_days']) + 1
        elif fam == 'S11':
            prior = max(prior, p['risk_days'] + p['risk_median_days'] + 1)
        elif fam == 'S4':
            prior = max(prior, 1)
        blocked = self.masked.copy() if current else np.zeros_like(self.masked)
        if prior:
            def history():
                prefix = np.vstack((np.zeros((1, len(self.names)), dtype=np.int64),
                                    np.cumsum(self.masked, axis=0)))
                idx = self.prior_indices
                return prefix[idx] > prefix[np.maximum(0, idx - prior)]
            blocked |= self.cached(('masked-history', prior), history)
        if fam == 'S5':
            blocked |= self.masked[:, self.names.index(p['benchmark']), None]
        if fam == 'S10':
            friday_monday = [d.weekday() == 4 and n.weekday() == 0
                             for d, n in zip(self.dates[:-1], self.dates[1:])] + [False]
            blocked &= np.array(friday_monday)[:, None]
        allowed = frozenset(grid['pools'][r['pool']])
        return blocked & np.array([name in allowed for name in self.names])

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
        elif fam in ('S2', 'S3', 'S7'):
            val = -self.period_return(earliest(), cut)
            test = val >= limit
            if 'volume_multiple' in p:
                test &= self.volume_multiple(offset(p['volume_from_et']), cut, p['volume_days']) >= p['volume_multiple']
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
            mult = self.cached(('range', earliest(), range_end, p['range_days']),
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
    width = P['cost_window_minutes'] // MINS
    bucket = 0 if i < width else 2 if i >= BARS - width else 1
    model = P['cost_bps_per_side']
    group = next((g for g, symbols in grid['measured_cost_symbols'].items() if symbol in symbols), 'cautious')
    if mode == 'close' and e == BARS:
        group = 'cautious'
    return model[group][bucket]


def settlement_delay(day):
    return P['settlement_delays'][day >= SETTLE_CHANGE]


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


def execute(tape, grid, r, scores, *, mask_counts=None):
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
        # A known masked fill or sizing print is a dropped candidate, not a
        # normal missing input and not a reason to try the next-ranked member.
        if tape.masked is not None and (tape.masked[d, n] or (e < 2 and d and tape.masked[d - 1, n])):
            if mask_counts is not None:
                mask_counts['masked_trade_drops'] += 1
            continue
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
        if tape.masked is not None and tape.masked[d + over, n]:
            if mask_counts is not None:
                mask_counts['masked_trade_drops'] += 1
            continue  # no P&L, settlement, fallback or repricing for this candidate
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
    k = math.ceil(n * MARKS['trim'])
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
    ok = (plain > 0 and all(v > 0 for v in half_plain) and t >= MARKS['t']
          and h1 >= MARKS['half_t'] and h2 >= MARKS['half_t'] and trim > 0 and annual >= MARKS['annual'])
    status = ('unpriced_exit' if missing_exit else 'too_thin' if n < MARKS['trades'] or days[0] < MARKS['days'] or min(days[1:]) < MARKS['half_days']
              else 'eligible' if ok else 'miss')
    return {'id': r['id'], 'family': r['family'], 'status': status, 'trades': n, 'days': days[0],
            'days_h1': days[1], 'days_h2': days[2], 'net_mean': plain, 'net_mean_h1': half_plain[0],
            'net_mean_h2': half_plain[1], 'annual_net_500': annual, 't': t, 't_h1': h1, 't_h2': h2,
            'trimmed_net': trim, 'missed_entry_prints': missing_entries, 'duplicate_of': None}


def overlap_corr(a, b):
    common = sorted(a.keys() & b.keys())
    if len(common) < MARKS['duplicate_days'] or len(common) < MARKS['duplicate_share'] * min(len(a), len(b)):
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
        blocked = tape.masked_signal_windows(r, grid)
        scores = tape.signals(r, grid)
        mask_counts = {'masked_signal_candidates': int(blocked.sum()) if blocked is not None else 0,
                       'masked_trade_drops': 0}
        if blocked is not None:
            scores[blocked] = -np.inf
        trades, blocks, absent, no_exit = execute(tape, grid, r, scores, mask_counts=mask_counts)
        row = summarize(r, trades, blocks, absent, no_exit)
        row.update(mask_counts)
        summaries.append(row)
        if row['status'] == 'eligible':
            eligible.append((row, {d: n for d, n, _ in trades}))
    finalists = []
    for row, pnl in sorted(eligible, key=lambda item: (-item[0]['t'], item[0]['id'])):
        dup = next((prior['id'] for prior, p in finalists if overlap_corr(pnl, p) > MARKS['duplicate_r']), None)
        if dup is not None:
            row['status'], row['duplicate_of'] = 'duplicate', dup
        elif len(finalists) < MARKS['finalists']:
            row['status'] = 'finalist'
            finalists.append((row, pnl))
        else:
            row['status'] = 'cap'
    return summaries


def synthetic_tape(grid, seed, case='noise', *, calendar_raw, inject_plant=True):
    rng = np.random.default_rng(seed)
    sessions = session_list(calendar_raw=calendar_raw)
    # Small fake cross-section exercises the same families, clocks and scoring. Real names are never used here.
    source_pools = ['stocks'] * 7 + ['sector'] * 4 + ['broad'] * 2 + ['bond'] * 2 + ['bull', 'inverse']
    names = tuple('FAKE%02d' % i for i in range(len(source_pools)))
    n, d = len(names), len(sessions)
    early_lengths = [int((c - o).total_seconds() / (60 * MINS)) for _, o, c in sessions]
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
        # Fix two isolated, causal positive blocks for fake sector member 07.
        # The signal ends at 15:25 and a reward starts strictly after 15:30.
        known = np.arange(d) % 4 == 0
        shock[:, 7, :] *= .05
        # Distribute the balancing log move across the next three sessions.
        # Keep it in the no-plant control too, so it cannot explain a finalist.
        shock[~known, 7, :] -= (.042 + .030) / (3 * np.array(early_lengths)[~known, None])
        if inject_plant:
            shock[known, 7, 9:70] += .042 / 61
            shock[known, 7, 74:78] += .030 / 4
    if case == 'drift':
        # Offset the deliberately constant log gap intraday, preserving both
        # positive overnight drift and a whole-share-affordable control price.
        shock[:, 0, 20:68] -= .018 / 48
    # Every open carries the previous close forward plus its own gap. With
    # a daily reset, the next gap would undo the prior day's intraday move.
    shock *= full[:, None, :]  # injected moves outside an early close cannot carry forward
    gap += np.vstack((np.zeros((1, n)), shock[:-1].sum(axis=2)))
    start = np.cumsum(gap, axis=0)
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


def internal_tests(grid, calendar_raw):
    poison = date(2022, 1, 3)
    assert_raises(lambda: date_fence(FIRST, poison))
    assert_raises(lambda: session_list(FIRST, poison, calendar_raw=calendar_raw))
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
    assert math.isnan(overlap_corr({i: i for i in range(20)}, {i: i for i in range(1, 21)}))
    assert math.isnan(overlap_corr({i: i for i in range(101)}, {i: i for i in range(81, 182)}))
    assert overlap_corr({i: i for i in range(100)}, {i: i for i in range(80, 180)}) > MARKS['duplicate_r']
    assert overlap_corr({i: i for i in range(100)}, {i: -i for i in range(80, 180)}) < -MARKS['duplicate_r']
    assert not is_number(True) and is_number(1.0)
    jump = np.full((len(FIELDS), 2, 1, BARS), 20.)
    second = FIRST + timedelta(days=1)
    jump[:, 1, 0] *= 4
    assert jump_mask(jump, [FIRST, second], ['FAKE'], set()).ravel().tolist() == [False, True]
    assert not jump_mask(jump, [FIRST, second], ['FAKE'], {('FAKE', second)}).any()

    tape, fake = synthetic_tape(grid, SYN['plant_seed'], 'plant', calendar_raw=calendar_raw)
    res = search(tape, fake)
    clears_mark = {'finalist', 'duplicate', 'cap'}
    planted = next(r for r in res if r['id'] == 'S1-04')
    if planted['status'] not in clears_mark:
        raise AssertionError(f'Planted S1-04 did not clear every statistical mark: {planted}')
    rank = lambda r: (-r['t'], r['id'])
    ahead = sorted((r for r in res if r['status'] == 'finalist' and rank(r) < rank(planted)), key=rank)
    control_tape, control_grid = synthetic_tape(grid, SYN['plant_seed'], 'plant',
                                                calendar_raw=calendar_raw, inject_plant=False)
    control = {r['id']: r for r in search(control_tape, control_grid)}
    surviving_ahead = [r['id'] for r in ahead if control[r['id']]['status'] in clears_mark]
    control_finalists = [r['id'] for r in control.values() if r['status'] == 'finalist']
    if surviving_ahead or control_finalists:
        raise AssertionError(f'Plant-free control failed: higher-ranked rules still clearing marks '
                             f'{surviving_ahead}; finalists {control_finalists}')
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
    print(json.dumps({'test': 'plant_and_no_lookahead', 'plant_rule': planted['id'],
                      'plant_status': planted['status'], 'plant_t': planted['t'],
                      'higher_finalists': [{'id': r['id'], 't': r['t'],
                                            'control_status': control[r['id']]['status']} for r in ahead],
                      'control_finalists': control_finalists,
                      'prospective_rules_tested': sum(r['cash_500'] for r in fake['rules']),
                      'date_fence_mocked_pages': True}), flush=True)

    tape, fake = synthetic_tape(grid, SYN['drift_seed'], 'drift', calendar_raw=calendar_raw)
    r = {'id': 'always-long-overnight-control', 'family': 'TEST', 'signal': {}, 'pool': 'drift_control',
         'cash_500': True, 'side': 'long', 'latest_signal_close_et': None,
         'entry': {'clock_et': '16:00', 'print': 'close'},
         'exit': {'clock_et': '09:35', 'print': 'open', 'session_offset': 1}}
    fake['pools']['drift_control'] = [tape.names[0]]
    row = search(tape, dict(fake, rules=[r]))[0]
    if not (row['annual_net_500'] >= MARKS['annual'] and row['net_mean'] > 0 and row['trades'] >= MARKS['trades']
            and row['t'] < MARKS['t'] and row['status'] == 'miss'):
        raise AssertionError(f'Positive upward drift did not demonstrate the matched-baseline guard: {row}')
    print(json.dumps(row | {'test': 'upward_drift'}), flush=True)


def power():
    # Whole mark, conditional one true rule with zero gross clock baseline, one trade per day,
    # equal halves, no duplicate competitor, fixed 90% deployed, fixed trade counts.
    rng = np.random.default_rng(SYN['power_seed'])
    for n in SYN['power_counts']:
        for sd in SYN['power_sd']:
            simulations = SYN['power_draws']
            x = rng.normal(0, sd, (simulations, n))
            avg = x.mean(axis=1)
            se = x.std(axis=1, ddof=1) / np.sqrt(n)
            h = x.reshape(simulations, 2, n // 2)
            ha = h.mean(axis=2)
            hs = h.std(axis=2, ddof=1) / np.sqrt(n // 2)
            trim = np.sort(x, axis=1)[:, :-math.ceil(n * MARKS['trim'])].mean(axis=1)
            min_edge = np.maximum.reduce([MARKS['t'] * se - avg,
                                         np.max(MARKS['half_t'] * hs - ha, axis=1),
                                         MARKS['annual'] * YEARS / (n * SYN['deployed_share']) - avg, -trim])
            p50, p80 = np.quantile(min_edge, [.50, .80])
            print(json.dumps({'test': 'power', 'trades': n, 'days': n, 'sd_bp': sd * 1e4,
                              'simulations': simulations, 'net_edge_bp_50': round(p50 * 1e4, 2),
                              'net_edge_bp_80': round(p80 * 1e4, 2)}))


def synthetic(grid, calendar_raw):
    internal_tests(grid, calendar_raw)
    failures, max_t = [], -np.inf
    reached_floors = set()
    max_eligible_by_seed = 0
    seeds = range(SYN['first_seed'], SYN['first_seed'] + SYN['worlds'])
    for seed in seeds:
        tape, fake = synthetic_tape(grid, seed, calendar_raw=calendar_raw)
        rows = search(tape, fake)
        hits = [r['id'] for r in rows if r['status'] == 'finalist']
        eligible = [r for r in rows if r['status'] in {'finalist', 'duplicate', 'cap', 'miss'}]
        max_eligible_by_seed = max(max_eligible_by_seed, len(eligible))
        for r in eligible:
            max_t = max(max_t, r['t'])
            reached_floors.add(r['family'])
        if hits:
            failures.append({'seed': seed, 'rules': hits})
    print(json.dumps({'test': 'whole_mark_pure_noise', 'clean_seeds': len(seeds) - len(failures),
                      'first_seed': seeds[0], 'last_seed': seeds[-1], 'all_registered_rules': len(grid['rules']),
                      'families_with_any_rule_at_floors': sorted(reached_floors),
                      'max_rules_reaching_floors_in_seed': max_eligible_by_seed,
                      'largest_t_among_rules_at_floors': round(max_t, 6), 'failures': failures}), flush=True)
    if len(seeds) - len(failures) < SYN['min_clean']:
        raise ValueError('Synthetic luck gate failed: stop. No rule, cost, seed or mark was retuned.')
    power()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    for name in ('collect', 'search', 'synthetic', 'validate-inputs'):
        mode.add_argument('--' + name, action='store_true')
    p.add_argument('--start', type=date.fromisoformat, default=FIRST)
    p.add_argument('--end', type=date.fromisoformat, default=LAST)
    args = p.parse_args()
    date_fence(args.start, args.end)
    if (args.start, args.end) != (FIRST, LAST):
        raise ValueError('All modes use the exact frozen search calendar')
    if args.synthetic:
        with np.errstate(invalid='ignore', divide='ignore'):
            synthetic(load_grid(read_once(HERE / 'GRID_69.json')), read_once(HERE / 'calendar_65.json'))
        return
    root_fd = open_directory(STORE)
    try:
        bufs, pins = approval(root_fd)
        grid = load_grid(bufs['GRID_69.json'])
        if args.collect:
            collect(grid, args.start, args.end, root_fd, bufs, pins)
            return
        *data, counts, bar_pin = load_collection(grid, args.start, args.end, root_fd, bufs, pins, score=args.search)
        if args.validate_inputs:
            print(json.dumps(counts, sort_keys=True))
        enforce_mask_limit(counts)
        if args.validate_inputs:
            return
        with np.errstate(invalid='ignore', divide='ignore'):
            for row in search(Tape(*data), grid):
                row['bars_sha256'] = bar_pin
                print(json.dumps({k: (None if isinstance(v, float) and not math.isfinite(v) else v)
                                  for k, v in row.items()}, allow_nan=False))
    finally:
        os.close(root_fd)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as e:
        sys.exit(str(e))
