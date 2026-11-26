"""One-shot, blinded TM09 Stage 1 gate. Only the signed weekly contrasts are read."""
import argparse
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from timemachine.tm09_desk import seal, store_new, verify_seal
from timemachine.tm09_fixture import encode, read_private, session_layout, settings, stage1_weeks

DEPS = ('tm09_desk.py', 'tm09_fixture.py', 'tm09_orders.py', 'tm09_feed.py', 'tm09_operator.py',
        'tm09_isolation_probe.py', 'score_tm09.py', 'TM09_WORKER_BRIEFS.md')
OUTPUT = frozenset(('placebo_sd_bps', 'primary_sd_a_bps', 'primary_sd_b_bps', 'edge_a_bps', 'edge_b_bps', 'decision'))


def sha(raw):
    return sha256(raw).hexdigest()


def release_identity(config_sha256, registration_sha256):
    running = Path(__file__).resolve()
    return dict(release=str(running.parent.parent), checker_sha256=sha(read_private(running)),
                dependency_sha256={name: sha(read_private(running.parent / name)) for name in DEPS},
                config_sha256=config_sha256, registration_sha256=registration_sha256)


def input_receipt(root, key, release, config_sha256, registration_sha256, input_sha256, count):
    body = dict(root=str(root), release=release, config_sha256=config_sha256, registration_sha256=registration_sha256,
                contrasts_sha256=input_sha256, weeks=count, mode='stage1')
    store_new(root / 'stage1-input.receipt.json', {'body': body, 'seal': seal(key, 'tm09-stage1-input', body)})


def verify_input_receipt(root, key, identity, input_sha256, count):
    raw = read_private(root / 'stage1-input.receipt.json')
    signed = json.loads(raw)
    body = signed['body']
    verify_seal(key, 'tm09-stage1-input', body, signed['seal'])
    if body != dict(root=str(root), release=identity['release'], config_sha256=identity['config_sha256'],
                    registration_sha256=identity['registration_sha256'], contrasts_sha256=input_sha256,
                    weeks=count, mode='stage1'):
        raise ValueError('Stage 1 contrast provenance refused')
    return sha(raw)


def verify_stage2(root, key, mode, report_pin, config_sha256, registration_sha256, count):
    if mode not in ('A', 'B'):
        raise ValueError('invalid Stage 2 branch')
    signed = json.loads(read_private(root / 'stage1-check.receipt.json'))
    body = signed['body']
    verify_seal(key, 'tm09-stage1-check-provenance', body, signed['seal'])
    identity = release_identity(config_sha256, registration_sha256)
    report_raw = read_private(root / 'stage1-checked.json')
    report = json.loads(report_raw)
    claim_raw = read_private(root / 'stage1-check.claim.json')
    claim = json.loads(claim_raw)
    if (body['root'] != str(root) or body['checker_sha256'] != identity['checker_sha256']
            or body['release_sha256'] != sha(encode(identity).encode())
            or body['report_sha256'] != report_pin or sha(report_raw) != report_pin
            or set(report) != OUTPUT or body['decision'] != mode or report['decision'] != mode
            or body['claim_sha256'] != sha(claim_raw) or claim.get('approval_sha256') != body['approval_sha256']
            or body['input_receipt_sha256'] != verify_input_receipt(root, key, identity, body['contrasts_sha256'], count)):
        raise ValueError('Stage 2 checker provenance refused')


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
    cfg = read_private(config)
    study = settings(cfg)['study']
    identity = release_identity(sha(cfg), sha(read_private(registration)))
    if (decision['scope'] != 'ledger-222-check-stage1-once' or decision['root'] != str(root)
            or any(decision[k] != v for k, v in identity.items())
            or decision['contrasts_path'] != str(contrasts)
            or contrasts != root / 'stage1-contrasts.json'
            or not isinstance(decision['approved_by'], str) or not decision['approved_by'].strip()):
        raise ValueError('lead blinded-check approval required')
    input_pin = decision['contrasts_sha256']
    source_proof = verify_input_receipt(root, key, identity, input_pin, len(stage1_weeks(study)))
    approval_pin = sha(encode(capsule).encode())
    claim_path = root / 'stage1-check.claim.json'
    store_new(claim_path, {'approval_sha256': approval_pin})
    raw = read_private(contrasts)
    if sha(raw) != input_pin:
        raise ValueError('sealed blinded input changed')
    report = calculate(study, json.loads(raw, parse_float=Decimal))
    report_path = root / 'stage1-checked.json'
    store_new(report_path, report)
    proof = dict(root=str(root), decision=report['decision'], contrasts_sha256=input_pin, approval_sha256=approval_pin,
                 checker_sha256=identity['checker_sha256'], release_sha256=sha(encode(identity).encode()),
                 claim_sha256=sha(read_private(claim_path)), report_sha256=sha(read_private(report_path)),
                 input_receipt_sha256=source_proof)
    store_new(root / 'stage1-check.receipt.json', {'body': proof, 'seal': seal(key, 'tm09-stage1-check-provenance', proof)})
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
