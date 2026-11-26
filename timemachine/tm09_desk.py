"""TM09 single-role desk, adapted from the frozen TM07 wake/receipt protocol."""
from contextlib import closing, contextmanager
from datetime import datetime
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
from zoneinfo import ZoneInfo

from timemachine.tm09_fixture import encode, fingerprint as digest, project_headlines, read_private, session_layout, week_pairs
from timemachine.tm09_feed import copied_run, extract_figures
from timemachine.tm09_orders import SPARSE_REASONS, Minutes, benchmark, fill, number, terminal, weights

SID = re.compile(r'TM09-[A-Za-z0-9_-]{1,72}\Z')
PUBLIC_SID = re.compile(r'TM09-[a-f0-9]{32}\Z')
PORTS = frozenset(range(8801, 8807))
ROLES = ('price_scout', 'news_scout', 'boss')
TOKEN = re.compile(r'[A-Za-z0-9_-]{40,100}\Z')


def seal(key, domain, obj):
    if not isinstance(key, str) or len(key) < 32:
        raise ValueError('operator seal key required')
    return hmac.digest(key.encode(), encode([domain, obj]).encode(), 'sha256').hex()


def verify_seal(key, domain, obj, signature):
    if not isinstance(signature, str) or not hmac.compare_digest(seal(key, domain, obj), signature):
        raise ValueError('bad TM09 seal')


def text_words(s):
    return ' '.join(re.findall(r'\w+', s.casefold()))


def store_new(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(encode(value) + '\n')
        f.flush()
        os.fsync(f.fileno())
    directory = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def note_stream(key, stream, fixture, role, wakes):
    body = stream['body']
    verify_seal(key, 'tm09-note-stream', body, stream['seal'])
    if (body['fixture'] != fixture or body['role'] != role
            or list(map(int, sorted(body['wakes'], key=int))) != list(wakes)):
        raise ValueError('note stream not from the completed scout for this fixture')
    return body['wakes']


def check_news_paraphrase_digits(paraphrase):
    if any(char.isdigit() for char in paraphrase):
        raise ValueError('digits in news paraphrase refused')


def check_news_stream_digits(wakes):
    # Also refuse any pre-amendment sealed stream carrying digits in scout prose.
    for notes in wakes.values():
        for note in notes:
            check_news_paraphrase_digits(note['paraphrase'])


def slot(week, role, boss=None, arm=None):
    prefix = 'TM09-' + week
    if role == 'boss' and arm and boss:
        return f'{prefix}-{boss}-{arm}'
    if role in ROLES[:2] and boss is None and arm is None:
        return f'{prefix}-{role}'
    raise ValueError('invalid desk role or arm')


def role_fingerprint(fixture, role):
    # Price input is identical across scout/boss stages even when the later seal adds news.
    return digest(fixture if role == 'news_scout' else {k: v for k, v in fixture.items() if k != 'news_index'})


def persist_options(options):
    return {k: v for k, v in options.items() if k != 'mode'}


def initialize(root, fixture, options, role, key, *, price=None, news=None, boss=None, arm=None, news_reader=None):
    """Operator ceremony only. O_EXCL and fixed slots prevent reruns."""
    sid = slot(fixture['week'], role, boss, arm)
    if not SID.fullmatch(sid) or role not in ROLES:
        raise ValueError('invalid session slot')
    caps = {'notes': 20, 'note_chars': 2000, 'looks': 1000, 'look_rows': 2000,
            'headline_rows': 10000, 'headline_chars': 10000}
    if any(type(options.get(k)) is not int or not 1 <= options[k] <= v for k, v in caps.items()):
        raise ValueError('missing or invalid approved note and look bounds')
    if (number(options['cash']) <= 0 or not 0 <= number(options['spread']) < 1 or not 0 < number(options['cap']) <= 1
            or not 0 <= number(options['commission']) < 1):
        raise ValueError('invalid approved sizing parameters')
    layout = session_layout(options['study'], options.get('mode'))
    if role == 'news_scout' and not layout.news:
        raise ValueError('news scout unavailable in price-only stage')
    if role == 'boss' and (boss not in options['study']['boss_models'] or arm not in layout.arms):
        raise ValueError('unregistered boss')
    fpin = role_fingerprint(fixture, role)
    waking = [t for t, _ in fixture['wakes']]
    price_notes, news_notes = {}, {}
    if role == 'boss':
        if price is None or (arm in layout.news) != (news is not None):
            raise ValueError('wrong scout streams for boss arm')
        price_notes = note_stream(key, price, fpin, 'price_scout', waking)
        if news is not None:
            news_notes = note_stream(key, news, role_fingerprint(fixture, 'news_scout'), 'news_scout', waking)
            if options['study'].get('amendment_1', {}).get('feed'):
                check_news_stream_digits(news_notes)
    elif price is not None or news is not None:
        raise ValueError('a scout cannot receive another worker stream')
    bound = dict(public_id='TM09-' + secrets.token_hex(16), role=role, fixture=fpin, arm=arm, boss=boss, options=persist_options(options),
                 price=price_notes, news=news_notes)
    path = Path(root) / sid
    path.mkdir(mode=0o700)
    token = secrets.token_urlsafe(36)
    book = {'cash': str(options['cash']), 'shares': {}} if role == 'boss' else None
    state = dict(cursor=0, wake_key=None, looks=0, successors=0, token=digest(token), book=book, pending=None)
    with closing(sqlite3.connect(path / 'desk.sqlite')) as con, con:
        os.chmod(path / 'desk.sqlite', 0o600)
        con.executescript('CREATE TABLE state(data TEXT NOT NULL);'
                          'CREATE TABLE journal(wake INTEGER, kind TEXT, data TEXT);'
                          'CREATE TABLE settlement(status TEXT NOT NULL, net TEXT);'
                          'CREATE TABLE receipts(id TEXT PRIMARY KEY, data TEXT NOT NULL);')
        con.execute('INSERT INTO state VALUES(?)', (encode(state),))
    store_new(path / 'manifest.json', {'body': bound, 'seal': seal(key, 'tm09-session', bound)})
    return Desk(path, fixture, key, news_reader=news_reader), token


class Desk:
    def __init__(self, path, fixture, key, *, news_reader=None, approved_options=None):
        self.path = Path(path)
        self.fixture, self.key, self.news_reader = fixture, key, news_reader
        manifest = json.loads(read_private(self.path / 'manifest.json'))
        self.spec = manifest['body']
        verify_seal(key, 'tm09-session', self.spec, manifest['seal'])
        self.role, self.arm = self.spec['role'], self.spec['arm']
        self.public_id = self.spec['public_id']
        self.options = self.spec['options']
        self.feed = self.options['study'].get('amendment_1', {}).get('feed')
        if (self.path.name != slot(fixture['week'], self.role, self.spec['boss'], self.arm)
                or not PUBLIC_SID.fullmatch(self.public_id) or role_fingerprint(fixture, self.role) != self.spec['fixture']
                or approved_options is not None and self.options != persist_options(approved_options)):
            raise ValueError('session fixture changed')
        if self.feed:
            check_news_stream_digits(self.spec['news'])
        self.wakes = fixture['wakes']
        self.minutes = Minutes(fixture['bars'])

    @contextmanager
    def tx(self):
        # Only the dedicated service owns this directory and the journal.
        with closing(sqlite3.connect(self.path / 'desk.sqlite')) as con, con:
            con.execute('BEGIN IMMEDIATE')
            st = json.loads(con.execute('SELECT data FROM state').fetchone()[0])
            yield con, st
            con.execute('UPDATE state SET data=?', (encode(st),))

    @staticmethod
    def log(con, at, kind, record):
        con.execute('INSERT INTO journal VALUES(?,?,?)', (at, kind, encode(record)))

    def _headlines(self, at):
        index = self.fixture['news_index'][str(at)]
        if not index:
            return []
        if self.role != 'news_scout' or self.news_reader is None:
            raise PermissionError('news source unavailable to this role')
        raw = self.news_reader()
        if self.feed:
            items = week_pairs(self.fixture, self.feed, raw=raw, until=at)[at]
            self._headline_bounds(items)
            return items
        return self._project(raw, index)

    def _project(self, raw, index):
        items = project_headlines(raw, index)
        self._headline_bounds(items)
        return items

    def _headline_bounds(self, items):
        if len(items) > self.options['headline_rows'] or any(len(i['headline']) > self.options['headline_chars'] for i in items):
            raise ValueError('news input bounds exceeded; do not truncate')

    def _packet(self, con, st, at):
        self._settle_pending(con, st)
        if st['wake_key'] is None:
            st['wake_key'] = secrets.token_urlsafe(36)
            self.log(con, at, 'packet', {'step': st['cursor']})
        out = {'wake': at, 'wake_key': st['wake_key'], 'step': st['cursor'], 'total': len(self.wakes)}
        if self.role == 'news_scout':
            out['items'] = self._headlines(at)
        else:
            out['symbols'] = self.options['symbols']
            if self.role == 'boss':
                out['book'] = st['book']
                prior = self.wakes[st['cursor'] - 1][0] if st['cursor'] else None
                out['fills'] = [json.loads(raw) for (raw,) in con.execute(
                    "SELECT data FROM journal WHERE wake=? AND kind='immediate' ORDER BY rowid", (prior,))]
                out['price_notes'] = self.spec['price'][str(at)]
                notes = self.spec['news'].get(str(at), [])
                if notes:
                    out['news_notes'] = notes
        return out

    def _note(self, at, body):
        notes = body['notes']
        if not isinstance(notes, list) or len(notes) > self.options['notes']:
            raise ValueError('invalid note bounds')
        if self.role == 'news_scout' and self.feed:
            return self._amended_notes(at, notes)
        if any(not isinstance(n, str) or not n.strip() or len(n) > self.options['note_chars'] for n in notes):
            raise ValueError('invalid note bounds')
        if self.role == 'news_scout':
            if notes and not self.fixture['news_index'][str(at)]:
                raise ValueError('no admitted items at this wake')
            if not notes:
                return notes
            raw = self.news_reader()
            items = [item for wake, _ in self.wakes if wake <= at
                     for item in self._project(raw, self.fixture['news_index'][str(wake)])]
            source = [text_words(row['headline']) for row in items]
            for note in notes:
                clean = text_words(note)
                # Exact token sequence only; human privacy review still required.
                if not clean or any(t and f' {t} ' in f' {clean} ' for t in source):
                    raise ValueError('headline copy refused')
        return notes

    def _amended_notes(self, at, notes):
        if not notes:
            return notes
        raw = self.news_reader()
        items = week_pairs(self.fixture, self.feed, raw=raw, until=at)
        headlines = [pair['headline'] for group in items.values() for pair in group]
        seen, attached = set(), []
        for note in notes:
            if (not isinstance(note, dict) or set(note) != {'symbol', 'source_time', 'repeat', 'paraphrase'}
                    or not isinstance(note['symbol'], str) or type(note['source_time']) is not int
                    or type(note['repeat']) is not bool
                    or not isinstance(note['paraphrase'], str) or len(encode(note)) > self.options['note_chars']):
                raise ValueError('invalid structured news note')
            check_news_paraphrase_digits(note['paraphrase'])
            clean = text_words(note['paraphrase'])
            if not clean or copied_run(note['paraphrase'], headlines, self.feed):
                raise ValueError('headline copy refused')
            matches = []
            for i, pair in enumerate(items[at]):
                if i in seen or any(note[k] != pair[k] for k in ('symbol', 'source_time', 'repeat')):
                    continue
                figures, _ = extract_figures(pair['headline'], self.feed)
                matches.append((i, tuple(figures)))
            if not matches or len({figures for _, figures in matches}) != 1:
                raise ValueError('news note lacks an unambiguous admitted item')
            index, figures = matches[0]
            seen.add(index)
            attached.append({**note, 'figures': list(figures), 'has_number': bool(figures)})
        return attached

    def handle(self, token, action, body=None):
        body = {} if body is None else body
        if not isinstance(token, str) or not TOKEN.fullmatch(token) or not isinstance(body, dict):
            raise PermissionError('invalid request')
        with self.tx() as (con, st):
            if not hmac.compare_digest(st['token'], digest(token)):
                raise PermissionError('bad role token')
            if (action not in ('next', 'status', 'notes', 'pick', 'look')
                    or action == 'notes' and self.role == 'boss'
                    or action == 'pick' and self.role != 'boss'
                    or action == 'look' and self.role == 'news_scout'):
                raise PermissionError('route unavailable for this role')
            done = st['cursor'] == len(self.wakes)
            if action == 'status':
                return dict(done=done, step=st['cursor'], total=len(self.wakes))
            if action in ('notes', 'pick'):
                rid = digest([action, body])
                saved = con.execute('SELECT data FROM receipts WHERE id=?', (rid,)).fetchone()
                if saved:
                    return json.loads(saved[0])
            if action == 'look':
                rid = digest([action, body])
            if done:
                return {'done': True}
            k = st['cursor']
            at, session_close = self.wakes[k]
            if action == 'next':
                return self._packet(con, st, at)
            supplied = body.get('wake_key')
            if not isinstance(supplied, str) or not st['wake_key'] or not hmac.compare_digest(supplied, st['wake_key']):
                raise PermissionError('wrong wake key')
            if action == 'look' and self.role != 'news_scout' and set(body) == {'wake_key', 'symbol', 'rows'}:
                saved = con.execute('SELECT data FROM receipts WHERE id=?', (rid,)).fetchone()
                if saved:
                    return json.loads(saved[0])
                s, limit = body['symbol'], body['rows']
                if s not in self.options['symbols'] or type(limit) is not int or not 1 <= limit <= self.options['look_rows']:
                    raise ValueError('invalid price look')
                if st['looks'] == self.options['looks']:
                    raise ValueError('look limit reached')
                st['looks'] += 1
                answer = {'bars': self.minutes.visible(s, at, limit)}
                self.log(con, at, 'look', {'symbol': s, 'rows': len(answer['bars'])})
            elif action == 'notes' and self.role in ROLES[:2] and set(body) == {'wake_key', 'notes'}:
                notes = self._note(at, body)
                self.log(con, at, 'notes', notes)
                answer = self._advance(st)
            elif action == 'pick' and self.role == 'boss' and set(body) == {'wake_key', 'weights'}:
                if body['weights'] is not None:
                    weights(body['weights'], self.options['symbols'])
                self.log(con, at, 'decision', {'weights': body['weights']})
                st['pending'] = {'step': k, 'weights': body['weights']}
                answer = self._advance(st)
            else:
                raise PermissionError('route or action unavailable for this role')
            con.execute('INSERT INTO receipts VALUES(?,?)', (rid, encode(answer)))
            return answer

    def _advance(self, st):
        st.update(cursor=st['cursor'] + 1, wake_key=None, looks=0)
        return {'accepted': True, 'done': st['cursor'] == len(self.wakes)}

    def _settle_pending(self, con, st):
        pending = st['pending']
        if pending is None:
            return
        k, raw = pending['step'], pending['weights']
        at, close = self.wakes[k]
        stop = min(close, self.wakes[k + 1][0]) if k + 1 < len(self.wakes) else close
        asked = None if raw is None else weights(raw, self.options['symbols'])
        spread, cap, commission = (number(self.options[p]) for p in ('spread', 'cap', 'commission'))
        for report in fill(st['book'], asked, self.minutes, at, stop, spread, cap, commission):
            self.log(con, at, 'immediate', report)
        st['pending'] = None

    def access(self, method, path, session, status):
        with self.tx() as (con, st):
            wake = self.wakes[st['cursor']][0] if st['cursor'] < len(self.wakes) else None
            self.log(con, wake, 'access_attempt' if status is None else 'access',
                     {'method': method, 'path': path, 'session': session, 'status': status})

    def access_checkpoint(self):
        with self.tx() as (con, _):
            return con.execute('SELECT coalesce(max(rowid),0) FROM journal').fetchone()[0]

    def access_records(self, start, end):
        with self.tx() as (con, _):
            return [json.loads(raw) for (raw,) in con.execute(
                "SELECT data FROM journal WHERE kind='access' AND rowid>? AND rowid<=? ORDER BY rowid", (start, end))]

    def work_rows(self):
        kind = 'decision' if self.role == 'boss' else 'notes'
        with self.tx() as (con, _):
            return [rowid for (rowid,) in con.execute('SELECT rowid FROM journal WHERE kind=? ORDER BY rowid', (kind,))]

    def successor(self):
        with self.tx() as (con, st):
            cap = self.options['study']['failures']['max_successors_per_lost_worker']
            if st['cursor'] == len(self.wakes) or st['successors'] >= cap:
                raise ValueError('finished desk or successor already used')
            token = secrets.token_urlsafe(36)
            st.update(token=digest(token), successors=st['successors'] + 1, wake_key=None)
            self.log(con, self.wakes[st['cursor']][0], 'successor', {'number': st['successors']})
            kind = 'decision' if self.role == 'boss' else 'notes'
            handoff = {'step': st['cursor'], 'history': [[w, json.loads(raw)] for w, raw in con.execute(
                'SELECT wake,data FROM journal WHERE kind=? ORDER BY rowid', (kind,))]}
            return token, {'body': handoff, 'seal': seal(self.key, self.path.name + '-successor', handoff)}

    def export_notes(self):
        with self.tx() as (con, st):
            if self.role not in ROLES[:2] or st['cursor'] != len(self.wakes):
                raise ValueError('scout stream incomplete')
            rows = con.execute("SELECT wake,data FROM journal WHERE kind='notes' ORDER BY wake")
            body = {'role': self.role, 'fixture': self.spec['fixture'],
                    'wakes': {str(w): json.loads(n) for w, n in rows}}
            return {'body': body, 'seal': seal(self.key, 'tm09-note-stream', body)}

    def export_boss(self):
        with self.tx() as (con, st):
            if self.role != 'boss' or st['cursor'] != len(self.wakes):
                raise ValueError('boss outcome incomplete')
            cached = con.execute('SELECT status,net FROM settlement').fetchone()
            if cached:
                return cached[1]
            self._settle_pending(con, st)
            spread = number(self.options['spread'])
            try:
                end = terminal(st['book'], self.minutes, self.fixture['closes'][-1], spread)
            except ValueError:
                status, net = 'missing terminal mark', None
            else:
                starting = number(self.options['cash'])
                status, net = 'sealed', str((end - starting) / starting)
            con.execute('INSERT INTO settlement VALUES(?,?)', (status, net))
            self.log(con, self.wakes[-1][0], 'finish', {'status': status})
            return net

    def complete(self):
        with self.tx() as (_, st):
            return st['cursor'] == len(self.wakes)

    def delivery_wakes(self):
        if self.role != 'boss':
            raise ValueError('not a boss desk')
        with self.tx() as (con, _):
            return {wake for (wake,) in con.execute("SELECT DISTINCT wake FROM journal WHERE kind='presented_news'")}

    def confirm_delivery(self, wake):
        if self.role != 'boss' or not self.spec['news'].get(str(wake)):
            raise ValueError('no eligible note to acknowledge')
        with self.tx() as (con, _):
            if not con.execute("SELECT 1 FROM journal WHERE wake=? AND kind='presented_news'", (wake,)).fetchone():
                self.log(con, wake, 'presented_news', {})

    def sparse_counts(self):
        """Operator-only order counts (not share counts), from committed fill receipts."""
        if self.role != 'boss':
            raise ValueError('not a boss desk')
        zone = ZoneInfo(self.options['study']['clock']['zone'])
        by_symbol, by_session = {}, {}
        with self.tx() as (con, st):
            if st['cursor'] == len(self.wakes):
                self._settle_pending(con, st)
            for wake, raw in con.execute("SELECT wake,data FROM journal WHERE kind='immediate'"):
                fill_report = json.loads(raw)
                if fill_report.get('reason') in SPARSE_REASONS:
                    symbol = fill_report['symbol']
                    day = datetime.fromtimestamp(wake, zone).date().isoformat()
                    symbols = by_session.setdefault(day, {})
                    by_symbol[symbol] = by_symbol.get(symbol, 0) + 1
                    symbols[symbol] = symbols.get(symbol, 0) + 1
        return {'session': self.public_id, 'by_symbol': by_symbol, 'by_market_session': by_session}


def weekly_benchmark(fixture, options):
    at, first_close = fixture['wakes'][0]
    return str(benchmark(options['symbols'], Minutes(fixture['bars']), at, first_close,
                         fixture['closes'][-1], number(options['spread'])))
