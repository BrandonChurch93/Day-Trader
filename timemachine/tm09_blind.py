"""One-shot, blinded TM09 Stage 1 gate. Only the signed weekly contrasts are read."""
import argparse
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from timemachine.tm09_desk import store_new, verify_seal
from timemachine.tm09_fixture import read_private, session_layout, settings, stage1_weeks

DEPS = ('tm09_desk.py', 'tm09_fixture.py', 'tm09_orders.py', 'tm09_feed.py')


def exact(x):
    if type(x) not in (int, str, Decimal) or len(str(x)) > 150:
        raise ValueError('invalid blinded number')
    value = Decimal(x)
    if not value.is_finite() or abs(value.as_tuple().exponent) > 1000:
        raise ValueError('invalid blinded number')
    return Fraction(value)


def calculate(study, weekly):
    if not isinstance(weekly, list) or len(weekly) != len(stage1_weeks(study)):
        raise ValueError('blinded weekly input is incomplete')
    xs = [exact(v) for v in weekly]
    n = len(xs)
    mean = sum(xs, Fraction(0)) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1)
    gate = study['amendment_1']['blind']
    max_edge = exact(str(gate['max_edge_bps']))
    k = exact(str(gate['edge_per_primary_sd']))
    if k <= 0 or max_edge < 0 or not 0 < exact(str(gate['target_power'])) < 1:
        raise ValueError('invalid registered blind settings')
    out = {}

    def display(square):
        with localcontext() as ctx:
            ctx.prec = 34
            return str((Decimal(square.numerator) / Decimal(square.denominator)).sqrt())

    out['placebo_sd_bps'] = display(var)
    selected = 'C'
    for mode in ('A', 'B'):
        layout = session_layout(study, mode)
        v = var * (Fraction(1, len(layout.price)) + Fraction(1, len(layout.news))) / 2
        edge2 = k * k * v
        suffix = mode.lower()
        out[f'primary_sd_{suffix}_bps'] = display(v)
        out[f'edge_{suffix}_bps'] = display(edge2)
        if selected == 'C' and edge2 <= max_edge * max_edge:
            selected = mode
    out['decision'] = selected
    return out


def run_approved(root, approval, key_file, registration, config, contrasts):
    capsule = json.loads(read_private(approval))
    decision = capsule['body']
    key = read_private(key_file).decode().strip()
    verify_seal(key, 'tm09-stage1-check-approval', decision, capsule['seal'])
    running = Path(__file__).resolve()
    cfg = read_private(config)
    study = settings(cfg)['study']
    if (decision['scope'] != 'ledger-222-check-stage1-once' or decision['root'] != str(root)
            or decision['release'] != str(running.parent.parent)
            or decision['checker_sha256'] != sha256(read_private(running)).hexdigest()
            or decision['dependency_sha256'] != {name: sha256(read_private(running.parent / name)).hexdigest() for name in DEPS}
            or decision['config_sha256'] != sha256(cfg).hexdigest()
            or decision['registration_sha256'] != sha256(read_private(registration)).hexdigest()
            or decision['contrasts_path'] != str(contrasts)
            or contrasts != root / 'stage1-contrasts.json'
            or not isinstance(decision['approved_by'], str) or not decision['approved_by'].strip()):
        raise ValueError('lead blinded-check approval required')
    store_new(root / 'stage1-check.claim.json', {'approval_sha256': sha256(json.dumps(capsule, sort_keys=True).encode()).hexdigest()})
    raw = read_private(contrasts)
    if sha256(raw).hexdigest() != decision['contrasts_sha256']:
        raise ValueError('sealed blinded input changed')
    report = calculate(study, json.loads(raw, parse_float=Decimal))
    store_new(root / 'stage1-checked.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for field in ('root', 'approval', 'key-file', 'registration', 'config', 'contrasts'):
        p.add_argument('--' + field, required=True, type=Path)
    a = p.parse_args()
    try:
        report = run_approved(a.root, a.approval, a.key_file, a.registration, a.config, a.contrasts)
    except (TypeError, ValueError, KeyError, OSError, InvalidOperation):
        p.exit(1, 'TM09 blinded Stage 1 input or approval refused.\n')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
