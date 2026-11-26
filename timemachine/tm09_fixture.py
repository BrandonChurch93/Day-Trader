"""Operator-only TM09 fixture compiler. Its output never contains headline text."""
from bisect import bisect_right
from datetime import date, datetime, time, timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
from zoneinfo import ZoneInfo

import yaml

from timemachine.tm09_orders import number

FILES = ('stock_sessions.jsonl', 'stock_bars.jsonl', 'stock_news.jsonl')
EXPORT = Path('/home/user/workspace/rig/data/tm09_stock_export')


def encode(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False)


def fingerprint(obj):
    return sha256(encode(obj).encode()).hexdigest()


def read_private(path):
    """Open exact bytes without following any link, including parent components."""
    target = Path(path)
    if not target.is_absolute() or '..' in target.parts:
        raise ValueError('absolute direct path required')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in target.parts[1:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        entry = os.open(target.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(entry, 'rb') as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
                raise ValueError('input must be a regular file')
            return f.read()
    finally:
        os.close(fd)


def rows(raw):
    for line in raw.splitlines():
        try:
            row = json.loads(line)
        except (ValueError, UnicodeError):
            raise ValueError('invalid export row') from None
        if not isinstance(row, dict):
            raise ValueError('invalid export row')
        yield row


def settings(config_raw):
    cfg = yaml.safe_load(config_raw)
    study = cfg['tm09']['value']
    execution = study['execution']
    parent, child = study['roster_key'].split('.')
    return dict(study=study, symbols=cfg[parent]['value'][child],
                hours=cfg[study['clock']['wake_hours_key']]['value'],
                cash=cfg[execution['starting_cash_key']]['value'],
                spread=str(number(cfg[execution['half_spread_bps_key']]['value']) / 10000),
                cap=str(number(cfg[execution['minute_volume_cap_key']]['value'])))


def mondays(study):
    window = study['window']
    first = date.fromisoformat(window['first_monday'])
    result = [first + timedelta(weeks=i) for i in range(window['weeks'])]
    if first.weekday() != 0 or result[-1].isoformat() != window['last_monday']:
        raise ValueError('inconsistent registered week window')
    return result


def schedule(session_rows, config):
    zone = ZoneInfo(config['study']['clock']['zone'])
    sessions, wakes, last = {}, [], None
    for row in session_rows:
        dt = date.fromisoformat(row['date'])
        op, close = row['open_utc'], row['close_utc']
        if (dt.weekday() >= 5 or (last and dt <= last) or type(op) is not int or type(close) is not int
                or not 0 < close - op <= 86400 or op % 60 or close % 60
                or any(datetime.fromtimestamp(x, zone).date() != dt for x in (op, close))):
            raise ValueError('invalid or unordered recorded session')
        last = dt
        week = (dt - timedelta(days=dt.weekday())).isoformat()
        sessions[dt] = (week, op, close)
        for h in config['hours']:
            minutes = round(h * 60)
            tick = int(datetime.combine(dt, time(*divmod(minutes, 60)), zone).timestamp())
            if op <= tick < close:
                wakes.append((tick, week, close))
    if not wakes or any(a[0] >= b[0] for a, b in zip(wakes, wakes[1:])):
        raise ValueError('invalid wake order')
    return sessions, wakes


def assign_news(source_rows, wakes, config):
    """Project metadata only; first eligibility is computed across all recorded wakes."""
    roster = set(config['symbols'])
    clock = config['study']['clock']
    ticks = [x[0] for x in wakes]
    result, seen = {}, set()
    for row in source_rows:
        src, original, update, edited = (row.get(k) for k in ('source', 'stated_time', 'updated_time', 'edited_later'))
        if src not in config['study']['news_sources'] or type(original) is not int or original <= 0 or (
                type(update) is not int or update != original or edited is not False):
            continue
        tags = row.get('symbols')
        if not isinstance(tags, list) or any(not isinstance(s, str) for s in tags):
            raise ValueError('invalid news tags')
        selected = sorted(roster.intersection(tags))
        if not selected:
            continue
        i = bisect_right(ticks, original + 60 * clock['known_at_lag_minutes'])
        if i == len(ticks):
            continue
        raw_id = row.get('id')
        if type(raw_id) not in (str, int) or not str(raw_id) or len(str(raw_id)) > 256:
            raise ValueError('invalid news identifier')
        ident = fingerprint([src, raw_id])
        if ident in seen:
            raise ValueError('duplicate eligible news item')
        seen.add(ident)
        result.setdefault(ticks[i], []).append({'id': ident, 'source_time': original, 'symbols': selected})
    return result


def compile_weeks(config, session_rows, bar_rows, news_rows):
    sessions, waking = schedule(session_rows, config)
    news = assign_news(news_rows, waking, config)
    weeks = {m.isoformat(): {'week': m.isoformat(), 'wakes': [], 'closes': [], 'news_index': {},
                             'bars': {s: [] for s in config['symbols']}} for m in mondays(config['study'])}
    for tick, week, close in waking:
        if week in weeks:
            weeks[week]['wakes'].append([tick, close])
            weeks[week]['news_index'][str(tick)] = news.get(tick, [])
    for week, _, close in sessions.values():
        if week in weeks:
            weeks[week]['closes'].append(close)
    zone = ZoneInfo(config['study']['clock']['zone'])
    roster = set(config['symbols'])
    for row in bar_rows:
        if row.get('tf') != '1Min' or row.get('symbol') not in roster:
            continue
        tick = row.get('t')
        if type(tick) is not int or tick <= 0 or tick % 60:
            raise ValueError('invalid minute clock')
        session = sessions.get(datetime.fromtimestamp(tick, zone).date())
        if session is None:
            continue
        week, op, cl = session
        if week not in weeks or not op <= tick < cl:
            continue
        o, h, low, c, v = (number(row[k]) for k in ('o', 'h', 'l', 'c', 'v'))
        if not 0 < low <= min(o, c) <= max(o, c) <= h or v < 0:
            raise ValueError('invalid minute values')
        weeks[week]['bars'][row['symbol']].append([tick, *map(str, (o, h, low, c, v))])
    for week in weeks.values():
        if not week['wakes'] or not week['closes']:
            raise ValueError('registered week lacks recorded sessions')
        for bars in week['bars'].values():
            bars.sort()
            if not bars or any(a[0] == b[0] for a, b in zip(bars, bars[1:])):
                raise ValueError('missing or duplicate roster minutes')
    return weeks


def compile_export(config_raw, directory, pins):
    """Operator input only; caller must authorize first. No raw data is emitted."""
    if set(pins) != set(FILES):
        raise ValueError('exact export pins required')
    def verified(name):
        blob = read_private(Path(directory) / name)
        if sha256(blob).hexdigest() != pins[name]:
            raise ValueError('frozen export hash mismatch')
        return rows(blob)
    config = settings(config_raw)
    return compile_weeks(config, verified(FILES[0]), verified(FILES[1]), verified(FILES[2]))


def project_headlines(raw, index):
    """Runtime news-scout projection. Never write or log the returned objects."""
    wanted = {row['id']: row for row in index}
    if not wanted:
        return []
    found = {}
    for row in rows(raw):
        key = fingerprint([row.get('source'), row.get('id')])
        if key not in wanted:
            continue
        headline = row.get('headline')
        if not isinstance(headline, str) or not headline.strip() or key in found:
            raise ValueError('invalid admitted headline')
        item = wanted[key]
        found[key] = {'headline': headline, 'source_time': item['source_time'], 'symbols': item['symbols']}
    if set(found) != set(wanted):
        raise ValueError('admitted item absent from approved source')
    return [found[row['id']] for row in index]
