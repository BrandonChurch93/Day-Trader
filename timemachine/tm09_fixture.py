"""Operator-only TM09 fixture compiler. Its output never contains headline text."""
from bisect import bisect_right
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
from zoneinfo import ZoneInfo

from timemachine.tm09_orders import number
from timemachine.tm09_feed import annotate, extract_figures

FILES = ('stock_sessions.jsonl', 'stock_bars.jsonl', 'stock_news.jsonl')


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


TOKEN = re.compile(r'''\s*("(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[{}\[\]:,]|[A-Za-z0-9_./+\-]+)''')


def flow(text):
    """Parse only the pinned config's single-line flow values; refuse other YAML syntax."""
    tokens, pos = [], 0
    while pos < len(text):
        match = TOKEN.match(text, pos)
        if not match:
            raise ValueError('unsupported TM09 config value')
        tokens.append(match[1]); pos = match.end()
    tokens.reverse()

    def parse():
        token = tokens.pop()
        if token in ('[', '{'):
            mapping = token == '{'
            end = '}' if mapping else ']'
            out = {} if mapping else []
            while tokens[-1] != end:
                if mapping:
                    key = tokens.pop()
                    if not re.fullmatch(r'[a-z][a-z0-9_]*', key) or key in out or tokens.pop() != ':':
                        raise ValueError('invalid TM09 config key')
                    out[key] = parse()
                else:
                    out.append(parse())
                if tokens[-1] == end:
                    break
                if tokens.pop() != ',' or tokens[-1] == end:
                    raise ValueError('invalid TM09 config separator')
            tokens.pop()
            return out
        if token in ('}', ']', ':', ','):
            raise ValueError('invalid TM09 config token')
        if token.startswith("'"):
            return token[1:-1].replace("''", "'")
        try:
            return json.loads(token)
        except ValueError:
            if token[0].isalpha():
                return token
            raise ValueError('invalid TM09 config scalar') from None

    try:
        result = parse()
    except (IndexError, RecursionError):
        raise ValueError('invalid TM09 config structure') from None
    if tokens:
        raise ValueError('extra TM09 config tokens')
    return result


def settings(config_raw):
    text = config_raw.decode()

    def value(key, submap=False):
        if not isinstance(key, str) or not re.fullmatch(r'[a-z][a-z0-9_]*', key):
            raise ValueError('unsupported TM09 config reference')
        section, = re.findall(r'^' + key + r':\n((?:[ \t][^\n]*\n)+)', text, re.M)
        if submap:
            block, = re.findall(r'^  value:\n((?: {4}[^\n]+\n)+)', section, re.M)
            result, level = {}, {4: None}
            level[4] = result
            for line in block.splitlines():
                matched = re.fullmatch(r'( +)([a-z][a-z0-9_]*):(?: +(.*))?', line)
                if not matched:
                    raise ValueError('unsupported TM09 config block')
                indent, item, raw = matched.groups()
                indent = len(indent)
                level = {k: v for k, v in level.items() if k <= indent}
                if indent not in level or item in level[indent]:
                    raise ValueError('invalid TM09 config nesting or duplicate')
                entry = flow(raw.strip()) if raw else {}
                level[indent][item] = entry
                if not raw:
                    level[indent + 2] = entry
            if not result:
                raise ValueError('unsupported TM09 config block')
            return result
        raw, = re.findall(r'^  value: +([^\n]+)$', section, re.M)
        return flow(raw.strip())

    study = value('tm09', submap=True)
    execution = study['execution']
    arm_layout(study)
    parent, child = study['roster_key'].split('.')
    return dict(study=study, symbols=value(parent)[child], hours=value(study['clock']['wake_hours_key']),
                cash=value(execution['starting_cash_key']),
                spread=str(number(value(execution['half_spread_bps_key'])) / 10000),
                cap=str(number(value(execution['minute_volume_cap_key']))),
                commission=str(number(execution['stock_commission_bps']) / 10000))


def arm_layout(study):
    controls = tuple(study['arms']['price_only'])
    news = study['arms']['price_plus_news']
    arms = (*controls, news)
    if (len(controls) != 2 or len(set(arms)) != 3 or study['scoring']['unit'] != 'week'
            or study['session_counts_per_arm'] != {arm.lower(): 1 for arm in arms}
            or len(study['scoring']['price_only_weights']) != len(controls)):
        raise ValueError('unimplemented TM09 registration layout')
    return controls, news


@dataclass(frozen=True)
class Layout:
    price: tuple
    news: tuple
    placebo: tuple

    @property
    def arms(self):
        return self.price + self.news


def session_layout(study, mode=None):
    controls, news = arm_layout(study)
    if mode in (None, 'A'):
        return Layout(controls, (news,), controls)
    amendment = study['amendment_1']
    if mode == 'stage1':
        return Layout(controls, (), controls)
    if mode != 'B':
        raise ValueError('unknown TM09 study mode')
    design = amendment['design_b']
    layout = Layout(tuple(design['price_only']), tuple(design['price_plus_news']), tuple(design['placebo']))
    if (not layout.price or not layout.news or len(set(layout.arms)) != len(layout.arms)
            or len(set(layout.placebo)) != 2 or not set(layout.placebo) <= set(layout.price)
            or not set(controls) <= set(layout.price)):
        raise ValueError('invalid amended arm layout')
    return layout


def stage1_weeks(study):
    weeks = mondays(study)
    take = study['amendment_1']['stage1_weeks']
    if type(take) is not int or not 2 <= take < len(weeks):
        raise ValueError('invalid Stage 1 window')
    return weeks[:take]


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


def assign_news(source_rows, wakes, config, counts=None):
    """Project metadata only; first eligibility is computed across all recorded wakes."""
    roster = set(config['symbols'])
    clock = config['study']['clock']
    ticks = [x[0] for x in wakes]
    result, seen = {}, set()
    for row in source_rows:
        src, original, update, edited = (row.get(k) for k in ('source', 'stated_time', 'updated_time', 'edited_later'))
        if counts is not None and src in config['study']['news_sources'] and (edited is True or update != original):
            counts['skipped_edited_or_changed_clock'] += 1
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
        row = {'id': ident, 'source_time': original, 'symbols': selected}
        result.setdefault(ticks[i], []).append(((original, src, str(raw_id)), row))
    return {wake: [row for _, row in sorted(items, key=lambda pair: pair[0])] for wake, items in result.items()}


def compile_weeks(config, session_rows, bar_rows, news_rows, counts=None, week_dates=None):
    sessions, waking = schedule(session_rows, config)
    news = assign_news(news_rows, waking, config, counts)
    weeks = {m.isoformat(): {'week': m.isoformat(), 'wakes': [], 'closes': [], 'news_index': {},
                             'bars': {s: [] for s in config['symbols']}}
             for m in (mondays(config['study']) if week_dates is None else week_dates)}
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


def compile_export(config, directory, pins, counts=None, *, stage1=False):
    """Operator input only; caller must authorize first. No raw data is emitted."""
    required = FILES[:2] if stage1 else FILES
    if set(pins) != set(required):
        raise ValueError('exact export pins required')
    def verified(name):
        blob = read_private(Path(directory) / name)
        if sha256(blob).hexdigest() != pins[name]:
            raise ValueError('frozen export hash mismatch')
        return blob
    raw = None if stage1 else verified(FILES[2])
    weeks = compile_weeks(config, rows(verified(FILES[0])), rows(verified(FILES[1])), () if stage1 else rows(raw), counts,
                          stage1_weeks(config['study']) if stage1 else None)
    feed = config['study'].get('amendment_1', {}).get('feed')
    if raw is not None and feed and counts is not None:
        index = [item for fixture in weeks.values() for wake, _ in fixture['wakes']
                 for item in fixture['news_index'][str(wake)]]
        lookup = {i['id']: p for i, p in zip(index, project_headlines(raw, index))}
        for week, fixture in weeks.items():
            pairs = [pair for group in week_pairs(fixture, feed, lookup=lookup).values() for pair in group]
            # assign_news admits each source item once, even when it has several roster tags.
            weekly = counts.setdefault('by_week', {})[week] = {
                'admitted_pairs': len(pairs), 'repeat_pairs': sum(p['repeat'] for p in pairs),
                'items_with_extracted_figure': 0, 'items_without_extracted_figure': 0,
                'possible_figure_missed': 0,
            }
            for group in fixture['news_index'].values():
                for row in group:
                    spans, missed = extract_figures(lookup[row['id']]['headline'], feed)
                    weekly['items_with_extracted_figure' if spans else 'items_without_extracted_figure'] += 1
                    weekly['possible_figure_missed'] += missed
    return weeks


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


def week_pairs(fixture, feed, *, raw=None, until=None, lookup=None):
    waking = [wake for wake, _ in fixture['wakes'] if until is None or wake <= until]
    if lookup is None:
        index = [item for wake in waking for item in fixture['news_index'][str(wake)]]
        lookup = {i['id']: p for i, p in zip(index, project_headlines(raw, index))}
    return annotate(((w, [lookup[i['id']] for i in fixture['news_index'][str(w)]]) for w in waking), feed)
