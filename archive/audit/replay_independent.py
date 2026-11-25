"""Independent BTC calculations for audit. Run from any working directory."""
from pathlib import Path
import json
import math
import pandas as pd

RIG = Path(__file__).resolve().parents[2] / 'research_rig'
LAST = '2026-11-24'
FEE = 0.003


def read_daily():
    src = pd.read_csv(RIG / 'data/bitstamp_BTCUSD.csv')
    src.index = pd.DatetimeIndex(src.pop('date'), tz='UTC')
    return src.loc[:LAST]


def read_hourly():
    src = pd.read_csv(RIG / 'data/bitstamp_BTCUSD_1h.csv')
    src.index = pd.to_datetime(src.pop('ts'), unit='s', utc=True)
    src = src.loc[~src.index.duplicated(keep='first')].sort_index()
    cal = pd.date_range(src.index[0].floor('D'), pd.Timestamp(LAST+' 23:00', tz='UTC'), freq='h')
    bars = src.reindex(cal)
    no_print = bars.close.isna() | bars.volume.eq(0)
    rates = no_print.groupby(no_print.index.year).mean()
    for year in rates.index:
        cut = pd.Timestamp(f'{year}-01-01', tz='UTC')
        if cut - src.index[0] >= pd.Timedelta(days=200) and rates.loc[year:].lt(.01).all():
            break
    bars['close'] = bars.close.ffill()
    bars['open'] = bars.open.combine_first(bars.close)
    return bars.loc[cut:]


def daily_orders(prices, name):
    lens = [20, 50, 100, 200] if name == 'P1' else [50]
    past = []
    weights = []
    for close in prices.close:
        past.append(close)
        weights.append(sum(close > (sum(past[-L:]) / L) for L in lens) / len(lens)
                       if len(past) >= max(lens) else None)
    return pd.Series(weights, index=prices.index)


def replay_daily(name):
    prices = read_daily()
    order = daily_orders(prices, name)
    cash, coin, trades, pending = 1., 0., 0, None
    values = []
    prices = prices.loc['2013-01-01':]
    for t, row in prices.iterrows():
        if pending is not None:
            inventory = coin * row.open
            wealth = cash + inventory
            weight = inventory / wealth
            if (abs(weight-pending) > .1 or (pending == 0 and coin > 0)
                    or (pending > 0 and coin == 0)):
                # Find the dollar trade that will reach the desired after-cost weight.
                # Positive value buys, negative value sells. Keep the solution solvent.
                def error(trade):
                    return inventory + trade - pending * (wealth - abs(trade)*FEE)
                low, high = -inventory, cash / (1+FEE)
                for _ in range(52):
                    trial = (low+high)/2
                    if error(trial) >= 0:
                        high = trial
                    else:
                        low = trial
                delta = ((low+high)/2 if 0 < pending < 1 else
                         -inventory if pending == 0 else cash/(1+FEE))
                cash -= delta + abs(delta)*FEE
                coin = 0. if pending == 0 else coin + delta / row.open
                trades += 1
        values.append(cash + coin*row.close)
        pending = order.at[t]
    return pd.Series(values, index=prices.index), trades


def replay_hourly():
    equity, day_open = {}, None
    cash, coin, buys, sells, pending = 1., 0., 0, 0, False
    for t, bar in read_hourly().iterrows():
        if pending and not coin:
            coin, cash = cash / (bar.open*(1+FEE)), 0.
            buys += 1
        if not pending and coin:
            cash, coin = coin*bar.open*(1-FEE), 0.
            sells += 1
        if t.hour == 0:
            day_open = bar.open
        if t.hour == 11:
            pending = bar.close > day_open
        if t.hour == 23:
            equity[t.floor('D')] = cash+coin*bar.close
            pending = False
    return pd.Series(equity), buys, sells


def figures(equity):
    r = equity.pct_change().dropna()
    return [equity.iloc[-1], (equity.iloc[-1]/equity.iloc[0])**(365/len(r))-1,
            math.sqrt(365)*r.mean()/r.std()]


def compare(name, equity, count, hourly=False):
    f = 'results_03.json' if hourly else 'results_01.json'
    saved = json.loads((RIG/f).read_text())['assets']['BTCUSD']['rules'][name]['venues']['Alpaca']['all']
    reported = [1+saved['total'], saved['cagr'], saved['sharpe'],
                saved['trips']['n'] if hourly else saved['trades']]
    own = figures(equity)+[count]
    print(name, 'first EOD', equity.iloc[0])
    for label, a, b in zip(['final equity', 'CAGR', 'Sharpe', 'round trips' if hourly else 'trade sides'], own, reported):
        print(f'{label:14} independent={a:.15g} stored={b:.15g} difference={a-b:.4g}')


if __name__ == '__main__':
    for name in ['P1', 'S50']:
        compare(name, *replay_daily(name))
    equity, buys, sells = replay_hourly()
    compare('H1', equity, sells, hourly=True)
    print('H1 buys', buys, 'sells', sells)
    print('H1 including first day (initial cash baseline)', figures(pd.concat([
        pd.Series([1.], index=[equity.index[0]-pd.Timedelta(days=1)]), equity])))
