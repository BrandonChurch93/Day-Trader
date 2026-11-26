"""TM09 cash-only target orders and the registered fractional benchmark."""
from bisect import bisect_right
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from fractions import Fraction
from itertools import groupby

NO_ELIGIBLE_MINUTE = 'no eligible minute'
NO_SIZING_PRINT = 'no completed sizing print'
SPARSE_REASONS = frozenset((NO_ELIGIBLE_MINUTE, NO_SIZING_PRINT))


def number(value):
    if type(value) not in (int, float, str) or len(str(value)) > 40:
        raise ValueError('invalid number')
    try:
        x = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('invalid number') from None
    if not x.is_finite() or abs(x) > Decimal('1e18') or (x and x.adjusted() < -18):
        raise ValueError('invalid number')
    return x


def floor(x):
    return int(x.to_integral_value(rounding=ROUND_FLOOR))


class Minutes:
    def __init__(self, bars):
        self.bars = bars
        self.times = {s: [r[0] for r in rows] for s, rows in bars.items()}

    def visible(self, symbol, wake, limit):
        i = bisect_right(self.times[symbol], wake - 60)
        return self.bars[symbol][max(0, i - limit):i]

    def next(self, symbol, wake, stop):
        times = self.times[symbol]
        i = bisect_right(times, wake)
        return self.bars[symbol][i] if i < len(times) and times[i] < stop else None

    def close(self, symbol, at):
        rows = self.visible(symbol, at, 1)
        if not rows or rows[0][0] != at - 60:
            raise ValueError('required terminal minute absent')
        return number(rows[0][4])


def value(book, marks):
    return number(book['cash']) + sum(q * marks[s] for s, q in book['shares'].items())


def weights(raw, roster):
    if not isinstance(raw, dict) or raw.keys() - set(roster):
        raise ValueError('use target weights on the roster only')
    parsed = {s: number(w) for s, w in raw.items()}
    if any(w < 0 for w in parsed.values()) or sum(parsed.values()) > 1:
        raise ValueError('long-only target weights must total at most one')
    return parsed


def fill(book, targets, minutes, wake, stop, half_spread, volume_cap, commission=Decimal(0)):
    """Size from the visible book; execute each symbol once at its next minute."""
    if targets is None:
        return []
    cash = number(book['cash'])
    holdings = book['shares']
    active = sorted(holdings.keys() | targets.keys())
    last = {s: minutes.visible(s, wake, 1) for s in active}
    if any(not last[s] for s in holdings):
        raise ValueError('held stock missing a completed valuation print')
    marks = {s: number(rows[-1][4]) for s, rows in last.items() if rows}
    nav = value(book, marks)
    requests, results = [], []
    for symbol in active:
        qty = holdings.get(symbol, 0)
        if symbol not in marks:
            if targets.get(symbol, 0):
                results.append({'symbol': symbol, 'requested': None, 'filled': 0,
                                'canceled': None, 'reason': NO_SIZING_PRINT})
            continue
        delta = floor(nav * targets.get(symbol, 0) / marks[symbol]) - qty
        if delta:
            row = minutes.next(symbol, wake, stop)
            if row is None:
                results.append({'symbol': symbol, 'requested': delta, 'filled': 0,
                                'canceled': abs(delta), 'reason': NO_ELIGIBLE_MINUTE})
                continue
            requests.append((row[0], symbol, delta, row))
    # At each timestamp sell first, then allocate cash pro rata among volume-capped buys.
    for at, group in groupby(sorted(requests, key=lambda r: (r[0], r[2] > 0, r[1])), key=lambda r: r[0]):
        buys = []

        def execute(symbol, delta, price, signed_qty):
            nonlocal cash
            cash -= signed_qty * price + abs(signed_qty) * price * commission
            remain = holdings.get(symbol, 0) + signed_qty
            if remain:
                holdings[symbol] = remain
            else:
                holdings.pop(symbol, None)
            results.append({'symbol': symbol, 'minute': at, 'requested': delta, 'filled': signed_qty,
                            'canceled': abs(delta) - abs(signed_qty), 'price': str(price)})

        for _, symbol, delta, row in group:
            qty = min(abs(delta), floor(number(row[5]) * volume_cap))
            if delta < 0:
                execute(symbol, delta, number(row[1]) * (1 - half_spread), -qty)
            else:
                buys.append((symbol, delta, number(row[1]) * (1 + half_spread), qty))
        required = sum(Fraction(price) * qty * (1 + Fraction(commission)) for _, _, price, qty in buys)
        # Use exact rational division so a rounded factor can never overspend cash.
        scale = min(1, Fraction(cash) / required) if required else 1
        for symbol, delta, price, qty in buys:
            execute(symbol, delta, price, int(qty * scale))
    book['cash'] = str(cash)
    return results


def terminal(book, minutes, close, half_spread):
    return value(book, {s: minutes.close(s, close) * (1 - half_spread) for s in book['shares']})


class BenchmarkUnavailable(ValueError):
    pass


def benchmark(roster, minutes, wake, stop, close, half_spread):
    ratios = []
    for symbol in roster:
        row = minutes.next(symbol, wake, stop)
        if not row:
            raise BenchmarkUnavailable(f'{symbol}: required entry minute absent')
        try:
            final = minutes.close(symbol, close)
        except ValueError:
            raise BenchmarkUnavailable(f'{symbol}: exact terminal minute absent') from None
        ratios.append(final * (1 - half_spread) / (number(row[1]) * (1 + half_spread)))
    return sum(ratios) / len(roster) - 1
