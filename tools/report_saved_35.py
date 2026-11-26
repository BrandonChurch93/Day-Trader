"""Render Replay 35 from the pinned saved aggregate. Never open quotes or score."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

RESULT_SHA = '083580210b0f1ba4fc623d23eefbcc24939b818b4bdc454335a8179288cfa8ac'
DOC = '81_replay_35_cme_bitcoin_expiry_ibit.md'
OUTPUT = Path(__file__).resolve().parents[1] / 'docs' / 'research' / DOC


def pct(value):
    return f'{value:+.4%}'


def stat(value):
    return f'{value:.2f}'


def row(*cells):
    return '| ' + ' | '.join(map(str, cells)) + ' |'


def measured(data):
    e, c, f, s = (data[key] for key in ('expiry', 'controls', 'expiry_fridays', 'score'))
    short = data['shown_only']['shorter_window']['controls']
    years, marks = s['years'], data['marks']
    keys = {'placed', 'mean', 't', 'trim', 'friday_control', 'breadth'}
    if (set(marks) != keys or all(marks.values()) != data['pass']
            or sum(v['n'] for v in years.values()) != e['placed']
            or e['eligible'] - e['placed'] != len(e['excluded'])
            or c['eligible'] - c['placed'] != len(c['excluded'])
            or short['eligible'] - short['placed'] != len(short['excluded'])
            or abs(f['mean'] - c['mean'] - s['friday_gap']) > 1e-12
            or (data['job']['ledger'], data['job']['queue']) != (170, 57)):
        raise ValueError('saved result does not reconcile')
    return e, c, f, s, short, years, marks


def claim(job):
    return datetime.fromisoformat(job['claimed_utc']).astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')


def outcome(data):
    return f"{'Passed' if data['pass'] else 'Did not pass'}, {sum(data['marks'].values())} of {len(data['marks'])} marks"


def render(data):
    e, c, f, s, short, years, marks = measured(data)
    positive = sum(v['mean'] > 0 for v in years.values())
    job = data['job']
    rules = (
        ('placed', 'At least 30 placed expiry round trips', f"{e['placed']} of {e['eligible']}"),
        ('mean', 'Net expiry mean above zero', pct(e['mean'])),
        ('t', 'One-sample t at least 2.0', stat(s['t'])),
        ('trim', 'Net mean above zero after dropping the best two', pct(s['trimmed_mean'])),
        ('friday_control', 'Expiry-Friday gap above zero and Welch t at least 2.0',
         f"{pct(s['friday_gap'])}; Welch t {stat(s['welch_t'])}"),
        ('breadth', 'Positive net mean in at least two of three calendar years', f'{positive} of {len(years)}'),
    )
    lines = [
        '# Replay 35. IBIT at monthly CME Bitcoin expiry', '',
        f"MEASURED. **{outcome(data)}.** Only placement passed. IBIT averaged {pct(e['mean'])} net per expiry "
        f"across {e['placed']} of {e['eligible']} eligible events (t {stat(s['t'])}). "
        f"The mean after dropping the best two was {pct(s['trimmed_mean'])}.", '',
        'STATED. The [frozen rule](../../research_rig/PREREG_35_ibit_cme_expiry.md) bought whole shares at the first '
        'eligible SIP ask at or after 11:00 London and sold at the first eligible bid at or after 16:00, '
        'within one minute of each clock. It assumed a pre-market limit at the ask filled there and charged '
        'zero commission plus historical SEC and FINRA sell fees. The $500 return denominator includes idle cash. '
        'The author had previously held entry and exit quotes for the spread screen; the lead had not seen them when '
        'fixing the marks, and a separate custodian restaged the judged inputs.', '',
        '## Frozen marks', '',
        row('Fixed bar', 'MEASURED', 'Verdict'), row('---', '---:', '---'),
        *(row(label, value, 'Pass' if marks[key] else 'Fail') for key, label, value in rules), '',
        f"MEASURED. The {f['placed']} placed expiry Fridays averaged {pct(f['mean'])}. The other full-session Friday "
        f"controls averaged {pct(c['mean'])} with {c['placed']} of {c['eligible']} placed. The expiry-Friday gap was "
        f"{pct(s['friday_gap'])} (Welch t {stat(s['welch_t'])}); the shifted Thursday is not in that comparison.", '',
        '## By year and shown-only checks', '',
        row('Year', 'Expiry trades', 'MEASURED net mean'), row('---', '---:', '---:'),
        *(row(y, v['n'], pct(v['mean'])) for y, v in sorted(years.items())), '',
        'MEASURED. These checks carry no verdict. The extra friction is per round trip; '
        'the Bitstamp spot cross-check is gross, from hourly open to hourly open.', '',
        row('Shown only', 'Expiry placed or observed', 'Expiry mean', 'Control placed or observed', 'Control mean'),
        row('---', '---:', '---:', '---:', '---:'),
    ]
    for key, label, count in (
        ('extra_2_bps', 'IBIT, +2 bps friction', 'placed'), ('extra_5_bps', 'IBIT, +5 bps friction', 'placed'),
        ('shorter_window', 'IBIT, 14:00 to 16:00 London', 'placed'), ('Bitstamp_spot', 'Bitstamp BTC/USD spot', 'observed'),
    ):
        expiry, controls = (data['shown_only'][key][k] for k in ('expiry', 'controls'))
        lines.append(row(label, f"{expiry[count]}/{expiry['eligible']}", pct(expiry['mean']),
                         f"{controls[count]}/{controls['eligible']}", pct(controls['mean'])))
    dates = ', '.join(sorted(short['excluded']))
    lines.extend([
        '', '## Coverage and reading', '',
        f"MEASURED. All {e['eligible']} expiry windows and all {c['eligible']} primary controls had placed round trips. "
        f"The shorter-window control had {len(short['excluded'])} missing entry ({dates}); STATED. The custodian confirmed "
        'the provider window was empty. It did not affect the judged rule. STATED. IBIT history starts in January 2024 '
        '([Nasdaq listing notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETP2024-04)), so this is not a replay '
        'of all the paper’s post-sample expiries.', '',
        'The cheap route made the clock testable, but the net expiry mean and the Friday gap were both negative. '
        'The earlier Kraken and Robinhood spot routes were stopped on costs; this result does not reopen them. '
        'The Bitstamp check was negative too, but the short IBIT history and assumed SIP fills cannot rule out a smaller '
        'effect on other venues or in other periods. Futures remain forward-log only, with no build.', '',
        '## Run record', '',
        f"MEASURED. The saved result records a claim at {claim(job)}, ledger {job['ledger']}, queue {job['queue']}. "
        'STATED. The lead ran it once after no-return validation. This page reads the saved aggregate only.', '',
        f"- Approval commit `{job['approval_commit']}`",
        f"- Freeze commit `{job['freeze_commit']}`",
        f'- Saved result SHA-256 `{RESULT_SHA}`',
        f"- Freeze manifest SHA-256 `{job['freeze_sha256']}`",
        f"- Input manifest SHA-256 `{job['input_sha256']}`", '',
    ])
    return '\n'.join(lines)


def records(data):
    e, c, _, s, _, _, _ = measured(data)
    common = (f"MEASURED. {outcome(data)}. IBIT averaged {pct(e['mean'])} net on "
              f"{e['placed']} of {e['eligible']} expiry windows (t {stat(s['t'])}); the expiry-Friday gap was "
              f"{pct(s['friday_gap'])} (Welch t {stat(s['welch_t'])}).")
    status = f"- [Replay 35](research/{DOC}), run once {claim(data['job'])}. {common}"
    queue = row(data['job']['queue'], f"Long IBIT at monthly CME Bitcoin expiry (ledger {data['job']['ledger']})",
                f"Done {claim(data['job'])}. {common} Spot remains stopped; futures are forward-log only, no build. "
                f"([Replay 35](research/{DOC}))")
    ledger = (f"{common} All {c['placed']} of {c['eligible']} controls placed. Claim {claim(data['job'])}, "
              f"approval `{data['job']['approval_commit']}`. See `docs/research/{DOC}`.")
    return '\n'.join((status, queue, ledger))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('result', type=Path)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--records', action='store_true')
    args = p.parse_args()
    try:
        blob = args.result.read_bytes()
        if sha256(blob).hexdigest() != RESULT_SHA:
            p.exit(2, 'P35_REPORT_RESULT_PIN\n')
        data = json.loads(blob)
        if args.records:
            print(records(data))
        elif args.write:
            OUTPUT.write_text(render(data), encoding='utf-8')
        else:
            print(render(data), end='')
    except (OSError, KeyError, TypeError, ValueError):
        p.exit(2, 'P35_REPORT_REFUSED\n')


if __name__ == '__main__':
    main()
