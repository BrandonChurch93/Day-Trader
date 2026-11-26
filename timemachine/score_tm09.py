"""TM09 registered week-level marks. The CLI refuses unapproved or repeat scoring."""
import argparse
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from timemachine.tm09_desk import store_new, verify_seal
from timemachine.tm09_fixture import mondays, read_private, settings
from timemachine.tm09_orders import number


def mean(values):
    return sum(values, Decimal(0)) / len(values) if values else None


def sample(values):
    m = mean(values)
    if len(values) < 2:
        return None, None
    sd = (sum((x - m) ** 2 for x in values) / (len(values) - 1)).sqrt()
    return (m * Decimal(len(values)).sqrt() / sd if sd else None), sd


def score(study, results):
    weeks = [m.isoformat() for m in mondays(study)]
    if set(results) != set(weeks):
        raise ValueError('one status row required for every scheduled week')
    models = study['boss_models']
    marks, failure = study['marks'], study['failures']
    lost = {model: [] for model in models}
    missing, paired = [], []
    admitted_total = delivered_total = 0
    for week in weeks:
        row = results[week]
        if set(row) != {'eligible_wakes', 'note_wakes', 'models', 'benchmark'} or set(row['models']) != set(models):
            raise ValueError('invalid sealed week row')
        admitted, delivered = row['eligible_wakes'], row['note_wakes']
        if type(admitted) is not int or type(delivered) is not int or not 0 <= delivered <= admitted:
            raise ValueError('invalid delivery counts')
        admitted_total += admitted
        delivered_total += delivered
        diffs, controls, n_values = [], [], []
        included = []
        for model in models:
            arms = row['models'][model]
            if set(arms) != {'P1', 'P2', 'N'}:
                raise ValueError('all arms need statuses')
            if None in arms.values():
                lost[model].append(week)
                continue
            p1, p2, n = (number(arms[a]) for a in ('P1', 'P2', 'N'))
            included.append(model)
            diffs.append(n - (p1 + p2) / 2)
            controls.append(p1 - p2)
            n_values.append(n)
        if diffs:
            paired.append(dict(week=week, models=included, by_model=dict(zip(included, diffs)),
                               placebo_by_model=dict(zip(included, controls)), primary=mean(diffs),
                               placebo=mean(controls), n=mean(n_values), benchmark=number(row['benchmark'])))
        else:
            missing.append(week)
    primary, placebo = [x['primary'] for x in paired], [x['placebo'] for x in paired]
    t, _ = sample(primary)
    pt, psd = sample(placebo)
    all_zero = bool(placebo) and all(x == 0 for x in placebo)
    placebo_ok = all_zero or pt is not None and abs(pt) < number(marks['placebo_abs_t_strict_max'])
    delivery = Decimal(delivered_total) / admitted_total if admitted_total else None
    delivered = delivery is not None and delivery >= number(study['delivery']['min_fraction_eligible_wakes_with_note'])
    complete = len(paired) >= failure['min_weeks_with_primary'] and all(len(w) <= failure['max_lost_weeks_per_boss'] for w in lost.values())
    positive_weeks = sum(x > 0 for x in primary)
    mean_primary = mean(primary)
    trimmed = mean(sorted(primary)[:-1])
    scores = dict(primary_t=t is not None and t >= number(marks['primary_t_min']),
                  positive_weeks=positive_weeks >= marks['positive_weeks_min'],
                  trimmed=trimmed is not None and trimmed > 0,
                  primary_mean=mean_primary is not None and mean_primary * 10000 >= number(marks['mean_weekly_bps_min']),
                  placebo=placebo_ok, delivery=delivered, coverage=complete)
    helps = all(scores.values())
    n_mean, baseline = mean([x['n'] for x in paired]), mean([x['benchmark'] for x in paired])
    reasons = []
    if not delivered:
        reasons.append('treatment not delivered')
    if not complete or t is None:
        reasons.append('inconclusive')
    if not placebo_ok and placebo:
        reasons.append('harness noise')
    return dict(marks=scores, labels=reasons or (['news helps'] if helps else ['news helps mark not met']),
                news_helps=helps, worth_following_forward=helps and n_mean > baseline,
                weeks_with_primary=len(paired), positive_weeks=positive_weeks, lost_weeks=lost, missing_weeks=missing,
                eligible_wakes=admitted_total, note_wakes=delivered_total, delivery_fraction=delivery,
                primary_t=t, primary_mean=mean_primary, primary_mean_without_best=trimmed,
                placebo_t=pt, placebo_sd=psd, placebo_all_exact_zero=all_zero, placebo_mean=mean(placebo),
                news_mean=n_mean, benchmark_mean=baseline, weekly=paired)


def run_approved(root, approval, key_file, registration, config, sealed_results):
    capsule = json.loads(read_private(approval))
    decision = capsule['body']
    key = read_private(key_file).decode().strip()
    verify_seal(key, 'tm09-score-approval', decision, capsule['seal'])
    cfg, reg = read_private(config), read_private(registration)
    if (decision.get('scope') != 'ledger-222-score-once' or decision.get('root') != str(root)
            or decision.get('registration_sha256') != sha256(reg).hexdigest()
            or decision.get('config_sha256') != sha256(cfg).hexdigest()
            or decision.get('results_path') != str(sealed_results)
            or not isinstance(decision.get('approved_by'), str) or not decision['approved_by'].strip()):
        raise ValueError('lead scoring approval required')
    # A claim is not removed after a failure; confirm with the lead before any recovery.
    store_new(root / 'score.claim.json', {'approval': sha256(json.dumps(capsule, sort_keys=True).encode()).hexdigest()})
    result_raw = read_private(sealed_results)
    if sha256(result_raw).hexdigest() != decision.get('results_sha256'):
        raise ValueError('sealed results changed')
    result = score(settings(cfg)['study'], json.loads(result_raw))
    output = json.loads(json.dumps(result, default=str))
    store_new(root / 'scored.json', output)
    return output


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for field in ('root', 'approval', 'key-file', 'registration', 'config', 'sealed-results'):
        p.add_argument('--' + field, type=Path, required=True)
    a = p.parse_args()
    try:
        run_approved(a.root, a.approval, a.key_file, a.registration, a.config, a.sealed_results)
    except (KeyError, TypeError, ValueError, OSError):
        p.exit(1, 'TM09 scoring refused; consult the lead and sealed custody log.\n')
