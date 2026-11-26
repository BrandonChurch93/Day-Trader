"""Plan 35: no-return input validation or one approved IBIT judgment."""
import argparse
import calendar
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING
from hashlib import sha256
import json
from math import isfinite, sqrt
import os
from pathlib import Path
import re
import resource
import stat
from statistics import mean, variance
import subprocess
import sys
from zoneinfo import ZoneInfo, reset_tzpath

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PRIVATE = Path('/home/user/workspace/rig')
INPUTS, RUN = PRIVATE / 'plan35_inputs', PRIVATE / 'replay_35'
PLAN, CONFIG, PINS, APPROVAL = ('PREREG_35_ibit_cme_expiry.md', 'config_35.json',
                                'PINNED_35.json', 'APPROVAL_35.md')
PIN_NAMES = {PLAN, CONFIG, 'score_35.py', 'test_35.py'}
APPROVAL_RE = (rb'Approved by the lead: plan 35, validation and one scored run, freeze commit ([0-9a-f]{40}), '
               rb'freeze SHA-256 ([0-9a-f]{64}), input SHA-256 ([0-9a-f]{64})\.\n')
STAMP = re.compile(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?Z', re.ASCII)
NANO = 1_000_000_000
QUOTE_HEADER = b'{"schema":1,"symbol":"IBIT","feed":"sip","windows":[\n'
QUOTE_CAP = 128 * 1024**2
WINDOW_CAP = 8 * 1024**2


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused('P35_' + code)


def hexpin(value, length=64):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{%d}' % length, value) is not None


def exact_fields(obj, fields):
    return type(obj) is dict and set(obj) == set(fields.split())


def schema1(obj):
    return type(obj['schema']) is int and obj['schema'] == 1


def unique(pairs):
    obj = dict(pairs)
    need(len(obj) == len(pairs), 'JSON_DUPLICATE')
    return obj


def refuse_constant(_):
    raise Refused('P35_JSON_NUMBER')


def parse(data, exact=False):
    return json.loads(data, object_pairs_hook=unique, parse_constant=refuse_constant,
                      parse_float=Decimal if exact else float)


def stamp_ns(stamp):
    match = STAMP.fullmatch(stamp) if type(stamp) is str else None
    need(match is not None, 'TIMESTAMP')
    seconds = calendar.timegm(datetime.fromisoformat(match[1]).timetuple())
    return seconds * NANO + int((match[2] or '').ljust(9, '0'))


def london_ns(day, hour):
    t = datetime(day.year, day.month, day.day, hour, tzinfo=ZoneInfo('Europe/London'))
    return calendar.timegm(t.utctimetuple()) * NANO


def calendar_design(config):
    start, end = (date.fromisoformat(config[key]) for key in ('start', 'end'))
    shift, shifted = map(date.fromisoformat, config['expiry_shift'])
    blocked = set(map(date.fromisoformat, config['non_full_fridays']))
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    fridays = [d for d in days if d.weekday() == 4]
    nominal = [d for d in fridays if (d + timedelta(days=7)).month != d.month]
    need(shift in nominal and shifted in days and shifted.weekday() == 3 and blocked <= set(fridays), 'CALENDAR')
    expiry = sorted(shifted if d == shift else d for d in nominal)
    controls = [d for d in fridays if d not in blocked and d not in expiry]
    return expiry, controls


def amount(value):
    need(type(value) in (int, Decimal), 'PRICE')
    n = Decimal(value)
    need(n.is_finite() and -1_000_000_000 <= n <= 1_000_000_000 and n.as_tuple().exponent >= -12, 'PRICE')
    return n


def quote_packet(data, days, config):
    need(exact_fields(data, 'schema symbol feed windows') and schema1(data) and data['symbol'] == 'IBIT'
         and data['feed'] == 'sip' and type(data['windows']) is list, 'QUOTES')
    return quote_windows(iter(data['windows']), days, config)


def quote_windows(windows, days, config):
    hours = sorted(config['london_hours'].values())
    expected = [(d, h) for d in days for h in hours]
    out = {}
    for day, hour in expected:
        window = next(windows, None)
        need(window is not None, 'QUOTES')
        need(exact_fields(window, 'date hour quotes') and window['date'] == str(day) and type(window['hour']) is int
             and window['hour'] == hour and type(window['quotes']) is list, 'WINDOW')
        start = london_ns(day, hour)
        end = start + config['tolerance_seconds'] * NANO
        previous, first = start, None
        for row in window['quotes']:
            need(type(row) is dict and {'t', 'ap', 'bp', 'as', 'bs'} <= row.keys(), 'QUOTE_ROW')
            stamp = stamp_ns(row['t'])
            need(previous <= stamp < end, 'QUOTE_CLOCK')
            previous = stamp
            ask, bid = amount(row['ap']), amount(row['bp'])
            ask_size, bid_size = row['as'], row['bs']
            need(type(ask_size) is int and type(bid_size) is int and min(ask_size, bid_size) >= 0, 'QUOTE_SIZE')
            if first is None and ask >= bid > 0 and ask_size > 0 and bid_size > 0:
                first = (ask, bid)
        out[day, hour] = first
    need(next(windows, ...) is ..., 'QUOTES')
    return out


def spot_packet(data, days, config):
    hours = config['london_hours']
    expected = {london_ns(d, hours[k]) for d in days for k in ('entry', 'exit')}
    need(exact_fields(data, 'schema venue symbol bars') and schema1(data) and data['venue'] == 'Bitstamp'
         and data['symbol'] == 'BTC/USD' and type(data['bars']) is list, 'SPOT')
    previous, out = -1, {}
    for row in data['bars']:
        need(exact_fields(row, 't open'), 'SPOT_ROW')
        stamp, price = stamp_ns(row['t']), amount(row['open'])
        need(previous < stamp and stamp in expected and price > 0, 'SPOT_CLOCK')
        previous = stamp
        out[stamp] = price
    return out


def fee_on_sale(day, shares, proceeds, config):
    cent = Decimal('0.01')
    sec = next(Decimal(r) for d, r in reversed(config['sec_sell']) if d <= str(day))
    finra, cap = next((Decimal(r), Decimal(c)) for d, r, c in reversed(config['finra_sell']) if d <= str(day))
    return (sec * proceeds).quantize(cent, rounding=ROUND_CEILING) + (
        min(finra * shares, cap)).quantize(cent, rounding=ROUND_CEILING)


def outcomes(days, quotes, config, entry_hour, extra_bps=0):
    capital = Decimal(config['capital_usd'])
    commission = Decimal(config['commission_usd'])
    exit_hour = config['london_hours']['exit']
    placed, missing = {}, {}
    for d in days:
        entry, exit_ = quotes[d, entry_hour], quotes[d, exit_hour]
        if entry is None:
            missing[str(d)] = 'no_entry'
            continue
        shares = int((capital - commission) // entry[0])
        if shares < 1:
            missing[str(d)] = 'unaffordable'
        elif exit_ is None:
            missing[str(d)] = 'no_exit'
        else:
            cost, proceeds = shares * entry[0], shares * exit_[1]
            fees = 2 * commission + fee_on_sale(d, shares, proceeds, config)
            placed[d] = (proceeds - cost - fees - cost * extra_bps / 10_000) / capital
    return placed, missing


def mean_or_none(vals):
    return mean(vals) if vals else None


def t_stat(vals, controls=None):
    if len(vals) < 2 or (controls is not None and len(controls) < 2):
        return None
    se_squared = variance(vals) / len(vals)
    delta = mean(vals)
    if controls is not None:
        se_squared += variance(controls) / len(controls)
        delta -= mean(controls)
    t = float(delta) / sqrt(se_squared) if se_squared > 0 else None
    return t if t is not None and isfinite(t) else None


def positive(n):
    return n is not None and n > 0


def summarize(placed, missing):
    return {'eligible': len(placed) + len(missing), 'placed': len(placed),
            'mean': mean_or_none(list(placed.values())), 'excluded': missing}


def evaluate(expiry, controls, quotes, spot, config):
    hours, rules = config['london_hours'], config['marks']
    ex, ex_missing = outcomes(expiry, quotes, config, hours['entry'])
    co, co_missing = outcomes(controls, quotes, config, hours['entry'])
    primary, prior = list(ex.values()), list(co.values())
    expiry_fridays = [r for d, r in ex.items() if d.weekday() == 4]
    avg, trim, t = mean_or_none(primary), mean_or_none(sorted(primary, reverse=True)[rules['trim_best']:]), t_stat(primary)
    welch = t_stat(expiry_fridays, prior)
    gap = mean(expiry_fridays) - mean(prior) if expiry_fridays and prior else None
    by_year = {}
    for y in sorted({d.year for d in expiry}):
        values = [r for d, r in ex.items() if d.year == y]
        by_year[y] = {'n': len(values), 'mean': mean_or_none(values)}
    marks = {'placed': len(ex) >= rules['placed_floor'], 'mean': positive(avg),
             't': t is not None and t >= rules['one_sample_t_floor'], 'trim': positive(trim),
             'friday_control': positive(gap) and welch is not None and welch >= rules['welch_t_floor'],
             'breadth': sum(positive(y['mean']) for y in by_year.values()) >= rules['positive_years_floor']}
    shown = {}
    for label, entry_hour, friction in [('shorter_window', hours['shown_entry'], 0)] + [
            (f'extra_{b}_bps', hours['entry'], b) for b in config['shown_extra_bps_roundtrip']]:
        shown[label] = {k: summarize(*outcomes(ds, quotes, config, entry_hour, friction))
                        for k, ds in (('expiry', expiry), ('controls', controls))}
    def spot_summary(days):
        returns = []
        for d in days:
            a, b = (spot.get(london_ns(d, hours[k])) for k in ('entry', 'exit'))
            if a is not None and b is not None:
                returns.append(b / a - 1)
        return {'eligible': len(days), 'observed': len(returns), 'mean': mean_or_none(returns)}
    shown['Bitstamp_spot'] = {'expiry': spot_summary(expiry), 'controls': spot_summary(controls)}
    return {'expiry': summarize(ex, ex_missing), 'controls': summarize(co, co_missing),
            'expiry_fridays': {'placed': len(expiry_fridays), 'mean': mean_or_none(expiry_fridays)},
            'score': {'t': t, 'trimmed_mean': trim, 'friday_gap': gap, 'welch_t': welch, 'years': by_year},
            'marks': marks, 'pass': all(marks.values()), 'shown_only': shown}


def encode(data):
    def serialize(value):
        if type(value) is Decimal:
            return float(value)
        raise TypeError('unexpected result type')
    return (json.dumps(data, indent=2, sort_keys=True, allow_nan=False, default=serialize) + '\n').encode()


def private_dir(path):
    s = path.lstat()
    need(path.resolve() == path and stat.S_ISDIR(s.st_mode) and s.st_uid == os.geteuid()
         and s.st_mode & 0o077 == 0, 'PRIVATE')


@contextmanager
def open_pin(path, digest, cap, private=False):
    need(hexpin(digest) and path.resolve() == path, 'PIN')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as f:
        s = os.fstat(f.fileno())
        need(stat.S_ISREG(s.st_mode) and s.st_size <= cap, 'FILE')
        if private:
            need(s.st_uid == os.geteuid() and s.st_mode & 0o077 == 0, 'PRIVATE')
        yield f


def pinned(path, digest, cap, private=False):
    with open_pin(path, digest, cap, private) as f:
        data = f.read(cap + 1)
        need(len(data) <= cap and sha256(data).hexdigest() == digest, 'PIN')
        return data


def quote_stream(path, digest, days, config):
    count = len(days) * len(config['london_hours'])
    with open_pin(path, digest, QUOTE_CAP, private=True) as f:
        hashed, total = sha256(), 0
        while chunk := f.read(256 * 1024):
            total += len(chunk)
            need(total <= QUOTE_CAP, 'QUOTE_FILE')
            hashed.update(chunk)
        need(hashed.hexdigest() == digest, 'PIN')
        f.seek(0)
        reread = sha256()
        def line(cap):
            raw = f.readline(cap + 1)
            need(0 < len(raw) <= cap and raw.endswith(b'\n'), 'QUOTE_LAYOUT')
            reread.update(raw)
            return raw
        need(line(len(QUOTE_HEADER)) == QUOTE_HEADER, 'QUOTE_LAYOUT')
        def rows():
            for i in range(count):
                suffix = b',\n' if i + 1 < count else b'\n'
                raw = line(WINDOW_CAP)
                need(raw.startswith(b'{') and raw.endswith(b'}' + suffix), 'QUOTE_LAYOUT')
                yield parse(raw[:-len(suffix)], True)
            need(line(3) == b']}\n' and not f.read(1), 'QUOTE_LAYOUT')
            need(reread.hexdigest() == digest, 'PIN')
        return quote_windows(rows(), days, config)


def git(*args, allow=False):
    env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
           'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_OPTIONAL_LOCKS': '0'}
    p = subprocess.run(['/usr/bin/git', '--no-replace-objects', '-c', 'core.fsmonitor=false',
                        '-C', str(REPO), *args], env=env, capture_output=True, timeout=15)
    need(allow or p.returncode == 0, 'APPROVAL')
    return p


def authorize(approval, freeze_pin, input_pin):
    need(hexpin(approval, 40) and hexpin(freeze_pin) and hexpin(input_pin), 'PIN')
    need(git('rev-parse', 'HEAD').stdout.strip() == approval.encode(), 'APPROVAL')
    need(not git('status', '--porcelain', '--untracked-files=all').stdout, 'CLEAN')
    def contents(commit, name):
        return git('show', f'{commit}:{name}').stdout
    marker = f'research_rig/{APPROVAL}'
    match = re.fullmatch(APPROVAL_RE, contents(approval, marker))
    need(match is not None, 'APPROVAL')
    freeze, approved_f, approved_i = (x.decode('ascii') for x in match.groups())
    need((freeze_pin, input_pin) == (approved_f, approved_i) and freeze != approval, 'APPROVAL')
    need(git('merge-base', '--is-ancestor', freeze, approval, allow=True).returncode == 0, 'ANCESTRY')
    need(git('cat-file', '-e', f'{freeze}:{marker}', allow=True).returncode != 0, 'APPROVAL')
    disk_pins = pinned(HERE / PINS, freeze_pin, 4096)
    need(disk_pins == contents(freeze, f'research_rig/{PINS}') == contents(approval, f'research_rig/{PINS}'), 'FREEZE')
    pins = parse(disk_pins)
    need(type(pins) is dict and set(pins) == PIN_NAMES and all(hexpin(x) for x in pins.values()), 'FREEZE')
    blobs = {name: pinned(HERE / name, pins[name], 262_144) for name in sorted(pins)}
    for name, blob in blobs.items():
        key = f'research_rig/{name}'
        need(blob == contents(freeze, key) == contents(approval, key), 'FREEZE')
    need([ln for ln in blobs[PLAN].splitlines() if ln.startswith(b'Status ')] == [b'Status FROZEN.'], 'FREEZE')
    for name, row in (('research_rig/TRIAL_LEDGER.md', 170), ('docs/QUEUE.md', 57)):
        prefix = f'| {row} |'.encode()
        frozen = [ln for ln in contents(freeze, name).splitlines() if ln.startswith(prefix)]
        now = [ln for ln in contents(approval, name).splitlines() if ln.startswith(prefix)]
        need(len(frozen) == 1 and frozen == now and PLAN.encode() in frozen[0], 'RECORDS')
    return freeze, parse(blobs[CONFIG])


def load_inputs(folder, digest, config):
    private_dir(folder)
    need({p.name for p in folder.iterdir()} == {'manifest.json', 'quotes.json', 'spot.json'}, 'INPUT_FILES')
    manifest = parse(pinned(folder / 'manifest.json', digest, 4096, True))
    need(exact_fields(manifest, 'schema custodian vendor feed start end collected_utc files') and schema1(manifest)
         and manifest['custodian'] == 'market_feed_builder' and manifest['vendor'] == 'Alpaca'
         and manifest['feed'] == 'sip' and manifest['start'] == config['start'] and manifest['end'] == config['end'], 'MANIFEST')
    need(stamp_ns(manifest['collected_utc']) > stamp_ns(config['end'] + 'T23:59:59Z'), 'MANIFEST_DATE')
    files = manifest['files']
    need(exact_fields(files, 'quotes.json spot.json') and all(hexpin(d) for d in files.values()), 'MANIFEST_PINS')
    expiry, controls = calendar_design(config)
    dates = sorted(expiry + controls)
    quotes = quote_stream(folder / 'quotes.json', files['quotes.json'], dates, config)
    spot = spot_packet(parse(pinned(folder / 'spot.json', files['spot.json'], 256 * 1024, True), True), dates, config)
    return expiry, controls, quotes, spot, config


def validation_report(expiry, controls, quotes, spot, config):
    hours = config['london_hours']
    def paired(days):
        return sum(quotes[d, hours['entry']] is not None and quotes[d, hours['exit']] is not None for d in days)
    return {'eligible_expiry': len(expiry), 'quote_paired_expiry': paired(expiry),
            'eligible_controls': len(controls), 'quote_paired_controls': paired(controls), 'spot_labels': len(spot)}


def unused(folder):
    need(not any(os.path.lexists(folder / s) for s in ('score_35.lock', 'results_35.json')), 'CONSUMED')


def write_exclusive(folder, name, data):
    fd = os.open(folder / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    fd_dir = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd_dir)
    finally:
        os.close(fd_dir)


def once(folder, job, inputs):
    unused(folder)
    job = job | {'claimed_utc': datetime.now(timezone.utc).isoformat()}
    try:
        write_exclusive(folder, 'score_35.lock', encode(job))
    except FileExistsError:
        raise Refused('P35_CONSUMED') from None
    result = evaluate(*inputs)
    write_exclusive(folder, 'results_35.json', encode({'job': job} | result))


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'P35_ARGUMENTS\n')


def check_environment():
    need(sys.flags.isolated and sys.dont_write_bytecode and set(os.environ) <= {'PATH', 'LC_ALL'}, 'ENVIRONMENT')


def set_limits():
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    cap = min(n for n in (288 * 1024**2, soft, hard) if n != resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS, (cap, hard))
    priority = os.nice(0)
    if priority < 10:
        os.nice(10 - priority)


def main():
    parser = Parser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--validate-inputs', action='store_true')
    mode.add_argument('--go', action='store_true')
    for arg in ('approval-commit', 'freeze-sha256', 'input-sha256'):
        parser.add_argument('--' + arg, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        check_environment()
        reset_tzpath(('/usr/share/zoneinfo',))
        set_limits()
        freeze, config = authorize(args.approval_commit, args.freeze_sha256, args.input_sha256)
        private_dir(RUN)
        unused(RUN)
        inputs = load_inputs(INPUTS, args.input_sha256, config)
        if args.validate_inputs:
            report = validation_report(*inputs) | {'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
            print('P35_INPUTS_OK', json.dumps(report, sort_keys=True))
            return
        rechecked, checked_config = authorize(args.approval_commit, args.freeze_sha256, args.input_sha256)
        need(rechecked == freeze and checked_config == config, 'FREEZE')
        once(RUN, {'schema': 1, 'ledger': 170, 'queue': 57, 'approval_commit': args.approval_commit,
                   'freeze_commit': freeze, 'freeze_sha256': args.freeze_sha256, 'input_sha256': args.input_sha256}, inputs)
    except Refused as exc:
        parser.exit(2, f'{exc}\n')
    except Exception:
        parser.exit(2, 'P35_REFUSED\n')
    print('P35_RESULT_WRITTEN')


if __name__ == '__main__':
    main()
