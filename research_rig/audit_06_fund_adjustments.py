"""Compare fund adjustment calibration years with issuer total returns. No rule."""

from decimal import Decimal
import json
from math import sqrt
from statistics import NormalDist

from audit_06_fund_coverage import config, read_bars


# Published calendar 2021 market-price total return in percent, not NAV.
REFERENCES = {
    "SPY": ("28.67", "https://www.sec.gov/Archives/edgar/data/884394/000119312522022720/d284625d497.htm"),
    "IEF": ("-3.33", "https://www.ishares.com/us/products/239456/IEF"),
    "IWM": ("14.54", "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf"),
}
EX_DATES = {
    "SPY": ("2021-12-16", "2021-12-17"),
    "IEF": ("2021-12-15", "2021-12-16"),
    "IWM": ("2021-12-10", "2021-12-13"),
    "EFA": ("2021-12-10", "2021-12-13"),
    "VNQ": ("2021-12-23", "2021-12-27"),
    "QQQ": ("2021-12-17", "2021-12-20"),
    "DBC": ("2022-12-16", "2022-12-19"),
    "BIL": ("2022-11-30", "2022-12-01"),
}
IWM_DISTRIBUTIONS = {"2021-03-25": ".398", "2021-06-10": ".347",
                     "2021-09-24": ".679", "2021-12-13": ".666"}
IWM_DISTRIBUTIONS_URL = "https://www.dividendvision.com/dividends/iwm-dividend-history"
IWM_EXTRA_REFERENCE_PCT = {2024: "11.39"}


def closes(symbol, adjustment, dates):
    return {bar["t"][:10]: Decimal(str(bar["c"])) for bar in read_bars(symbol, adjustment)
            if bar["t"][:10] in dates}


def change(bars, first, last):
    return bars[last] / bars[first] - 1


def year_end_close(symbol, adj, year, first, last):
    lo, hi = f"{year - 1}-12-", f"{year + 1}-01-01"
    selected = [(bar["t"][:10], Decimal(str(bar["c"]))) for bar in read_bars(symbol, adj)
                if lo <= bar["t"][:10] < hi
                and bar["t"][:10] in (first, last)]
    return change(dict(selected), first, last) * 100


def main():
    cfg = config("replay_06_data")
    year = cfg["adjustment_check_year"]
    first, last = f"{year - 1}-12-31", f"{year}-12-31"
    if not cfg["design_start"] <= first <= last < cfg["held_start"]:
        raise ValueError("Check year must be entirely in design dates.")
    ex_checks = {}
    for symbol, (before, ex) in EX_DATES.items():
        if not cfg["design_start"] <= before < ex < cfg["held_start"]:
            raise ValueError("Ex date must fall within design dates.")
        a, s = (closes(symbol, adj, {before, ex}) for adj in ("all", "split"))
        ex_checks[symbol] = dict(ex_date=ex, all_minus_split_return_bps=float(
            (change(a, before, ex) - change(s, before, ex)) * 10_000))
    gld = [{bar["t"]: bar["c"] for bar in read_bars("GLD", a)
            if cfg["design_start"] <= bar["t"][:10] < cfg["held_start"]} for a in ("all", "split")]
    rows = {}
    for symbol, (ref_pct, url) in REFERENCES.items():
        a, s = (closes(symbol, adj, {first, last}) for adj in ("all", "split"))
        adjusted_pct, split_pct = (change(c, first, last) * 100 for c in (a, s))
        diff_bps = (adjusted_pct - Decimal(ref_pct)) * 100
        rows[symbol] = dict(
            issuer_market_total_return_pct=float(ref_pct), reference_url=url,
            alpaca_all_pct=float(adjusted_pct), alpaca_split_only_pct=float(split_pct),
            all_minus_issuer_bps=float(diff_bps),
            within_draft_tolerance=abs(diff_bps) <= cfg["adjustment_max_error_bps"],
        )
    iwm = closes("IWM", "split", {first, last, *IWM_DISTRIBUTIONS})
    units = Decimal(1)
    for ex, amount in IWM_DISTRIBUTIONS.items():
        if not first < ex <= last:
            raise ValueError("IWM distribution must fall in the audit year.")
        units *= 1 + Decimal(amount) / iwm[ex]
    independent_iwm_pct = (units * iwm[last] / iwm[first] - 1) * 100
    # Sole held-period exception: builder explicitly requested an IWM vendor calibration,
    # not any rule, signal, fill, or holding yardstick return for a replay slice.
    extra_year = cfg["iwm_additional_check_year"]
    from exchange_calendars import get_calendar
    calendar = get_calendar("XNYS", start=f"{extra_year - 1}-12-01", end=f"{extra_year}-12-31")
    before, after = [max(d.date().isoformat() for d in calendar.sessions if d.year == y)
                     for y in (extra_year - 1, extra_year)]
    extra_all = year_end_close("IWM", "all", extra_year, before, after)
    extra_split = year_end_close("IWM", "split", extra_year, before, after)
    extra_ref = Decimal(IWM_EXTRA_REFERENCE_PCT[extra_year])
    extra_gap = (extra_all - extra_ref) * 100
    stats = config("replay_06_statistics")
    start = config("replay_06_data")["held_start"]
    stop = config("replay_06_data")["last_bar"]
    # Count completed calendar months, not daily fund observations, as the illustrative N.
    sy, sm = (int(x) for x in start.split("-")[:2])
    ey, em = (int(x) for x in stop.split("-")[:2])
    n = (ey - sy) * 12 + em - sm
    sd = stats["power_annual_active_sd"]
    chance = stats["power_goal"]
    critical = config("replay_min_shuffle_percentile")
    se = sd * sqrt(12 / n)
    detectable = (NormalDist().inv_cdf(critical) + NormalDist().inv_cdf(chance)) * se
    print(json.dumps(dict(
        first_close_date=first, last_close_date=last, check_tolerance_bps=cfg["adjustment_max_error_bps"],
        checks=rows, sampled_ex_date_adjustments=ex_checks,
        gld_design_closes_identical=gld[0] == gld[1],
        iwm_split_prices_with_independent_payouts=dict(
            source_url=IWM_DISTRIBUTIONS_URL, ex_close_reinvest_pct=float(independent_iwm_pct),
            minus_issuer_bps=float((independent_iwm_pct - Decimal(REFERENCES["IWM"][0])) * 100)),
        iwm_additional_year=dict(first_close_date=before, last_close_date=after,
                                 issuer_market_total_return_pct=float(extra_ref),
                                 reference_url=REFERENCES["IWM"][1], alpaca_all_pct=float(extra_all),
                                 alpaca_split_only_pct=float(extra_split), all_minus_issuer_bps=float(extra_gap),
                                 within_draft_tolerance=abs(extra_gap) <= cfg["adjustment_max_error_bps"]),
        indicative_count_if_frozen_now=stats["prior_count_at_draft"] + stats["new_trials"],
        illustrative_power=dict(complete_holdout_months=n, assumed_annual_active_sd=sd,
                                one_sided_percentile=critical, goal=chance, annual_se=se,
                                detectable_annual_edge=detectable),
    ), indent=2))


if __name__ == "__main__":
    main()
