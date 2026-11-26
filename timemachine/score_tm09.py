"""TM09 registered week-level marks. The CLI refuses unapproved or repeat scoring."""
import argparse
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from timemachine.tm09_desk import store_new, verify_seal
from timemachine.tm09_fixture import arm_layout, mondays, read_private, settings
from timemachine.tm09_orders import number

DEPS = ('tm09_desk.py', 'tm09_fixture.py', 'tm09_orders.py')


def mean(values):
    return sum(values, Fraction(0)) / len(values) if values else None


def sample(values):
    if len(values) < 2:
        return None, None
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return (m * m * len(values) / variance if variance else None), variance


def decimal(x):
    with localcontext() as ctx:
        ctx.prec = 50
        return Decimal(x.numerator) / Decimal(x.denominator)


def numeric(x):
    return Fraction(number(x))


def score(study, results):
    weeks = [m.isoformat() for m in mondays(study)]
    if set(results) != set(weeks):
        raise ValueError('one status row required for every scheduled week')
    models = study['boss_models']
    controls_in_order, news_arm = arm_layout(study)
    control_weights = [numeric(w) for w in study['scoring']['price_only_weights']]
    news_weight = numeric(study['scoring']['treatment_weight'])
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
            if set(arms) != {*controls_in_order, news_arm}:
                raise ValueError('all arms need statuses')
            if None in arms.values():
                lost[model].append(week)
                continue
            p1, p2 = (numeric(arms[a]) for a in controls_in_order)
            n = numeric(arms[news_arm])
            included.append(model)
            diffs.append(news_weight * n + sum(w * r for w, r in zip(control_weights, (p1, p2))))
            controls.append(p1 - p2)
            n_values.append(n)
        if diffs:
            paired.append(dict(week=week, models=included, by_model=dict(zip(included, diffs)),
                               placebo_by_model=dict(zip(included, controls)), primary=mean(diffs),
                               placebo=mean(controls), n=mean(n_values), benchmark=numeric(row['benchmark'])))
        else:
            missing.append(week)
    primary, placebo = [x['primary'] for x in paired], [x['placebo'] for x in paired]
    t2, _ = sample(primary)
    pt2, pvar = sample(placebo)
    all_zero = bool(placebo) and all(x == 0 for x in placebo)
    placebo_ok = all_zero or pt2 is not None and pt2 < numeric(marks['placebo_abs_t_strict_max']) ** 2
    delivery = Fraction(delivered_total, admitted_total) if admitted_total else None
    delivered = delivery is not None and delivery >= numeric(study['delivery']['min_fraction_eligible_wakes_with_note'])
    complete = len(paired) >= failure['min_weeks_with_primary'] and all(len(w) <= failure['max_lost_weeks_per_boss'] for w in lost.values())
    positive_weeks = sum(x > 0 for x in primary)
    mean_primary = mean(primary)
    trimmed = mean(sorted(primary)[:-1])
    scores = dict(primary_t=t2 is not None and mean_primary > 0 and t2 >= numeric(marks['primary_t_min']) ** 2,
                  positive_weeks=positive_weeks >= marks['positive_weeks_min'],
                  trimmed=trimmed is not None and trimmed > 0,
                  primary_mean=mean_primary is not None and mean_primary * 10000 >= numeric(marks['mean_weekly_bps_min']),
                  placebo=placebo_ok, delivery=delivered, coverage=complete)
    helps = all(scores.values())
    n_mean, baseline = mean([x['n'] for x in paired]), mean([x['benchmark'] for x in paired])
    reasons = []
    if not delivered:
        reasons.append('treatment not delivered')
    if not complete or t2 is None:
        reasons.append('inconclusive')
    if not placebo_ok and placebo:
        reasons.append('harness noise')
    pm = mean(placebo)
    def shown_t(squared, avg):
        if squared is None:
            return None
        with localcontext() as ctx:
            ctx.prec = 50
            return decimal(squared).sqrt() * (-1 if avg < 0 else 1)

    return dict(marks=scores, labels=reasons or (['news helps'] if helps else ['news helps mark not met']),
                news_helps=helps, worth_following_forward=helps and n_mean > baseline,
                weeks_with_primary=len(paired), positive_weeks=positive_weeks, lost_weeks=lost, missing_weeks=missing,
                eligible_wakes=admitted_total, note_wakes=delivered_total, delivery_fraction=delivery,
                primary_t=shown_t(t2, mean_primary), primary_mean=mean_primary, primary_mean_without_best=trimmed,
                placebo_t=shown_t(pt2, pm), placebo_sd=decimal(pvar).sqrt() if pvar is not None else None,
                placebo_all_exact_zero=all_zero, placebo_mean=pm,
                news_mean=n_mean, benchmark_mean=baseline, weekly=paired)


def run_approved(root, approval, key_file, registration, config, sealed_results):
    capsule = json.loads(read_private(approval))
    decision = capsule['body']
    key = read_private(key_file).decode().strip()
    verify_seal(key, 'tm09-score-approval', decision, capsule['seal'])
    cfg, reg = read_private(config), read_private(registration)
    running = Path(__file__).resolve()
    if (decision.get('scope') != 'ledger-222-score-once' or decision.get('root') != str(root)
            or decision.get('release') != str(running.parent.parent)
            or decision.get('scorer_sha256') != sha256(read_private(running)).hexdigest()
            or decision.get('dependency_sha256') != {name: sha256(read_private(running.parent / name)).hexdigest() for name in DEPS}
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
    output = json.loads(json.dumps(result, default=lambda v: str(decimal(v) if isinstance(v, Fraction) else v)))
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
