#!/usr/bin/env python3
"""Collect private, read-only market context. Python 3.10+, standard library only."""

import calendar
import concurrent.futures
import datetime as dt
import html
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo


CACHE = Path(os.environ.get("FEEDS_CACHE_DIR", Path(__file__).resolve().parent.parent / "data" / "feeds_cache"))
USER_AGENT = "Day-Trader research modernsoftworks@gmail.com"
TIMEOUT_SECONDS = 15
MAX_RESPONSE_BYTES = 8_000_000
SEC_MIN_PAUSE_SECONDS = 0.25
SEC_FEED_ROWS = 40
SEC_MAX_FORM_FILINGS = 12
POLY_SEARCH_ROWS = 25
POLY_MAX_CONTRACTS = 12
COIN_LOOKBACK_DAYS = 4
STABLECOIN_CHANGE_DAYS = 7

# All flag thresholds below are research placeholders, not owner-set numbers.
BILL_STALE_HOURS = 120
BILL_MONTHLY_STALE_HOURS = 24 * 45
COIN_STALE_HOURS = 72
STABLECOIN_STALE_HOURS = 96
SEC_STALE_HOURS = 120
POLY_STALE_HOURS = 3
FED_CALENDAR_STALE_HOURS = 24 * 180
VIX_BACKWARDATION_RATIO = 1.0
CROWDED_LONG_MIN_FUNDING_RATE = 0.0001  # Fraction per funding interval, not a percent.
CROWDED_LONG_MIN_PREDICTED_FUNDING_RATE = 0.0001
CROWDED_LONG_MIN_OI_USD = 10_000_000

TREASURY = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
TREASURY_AVERAGE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates"
COIN = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
DEFILLAMA = "https://stablecoins.llama.fi/stablecoincharts/all"
SEC = "https://www.sec.gov/cgi-bin/browse-edgar"
FED = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
POLY_US = "https://gateway.polymarket.us/v1"
COIN_UNITS = {
    "CapMVRVCur": "ratio",
    "AdrActCnt": "addresses",
    "TxCnt": "transactions",
    "SplyCur": "native units",
    "FeeTotNtv": "native units",
}
COIN_LABELS = {"CapMVRVCur": "market value to realized value", "AdrActCnt": "active addresses",
               "TxCnt": "transaction count", "SplyCur": "current supply", "FeeTotNtv": "total fees"}
MATURITIES = (4, 6, 8, 13, 17, 26, 52)
EASTERN = ZoneInfo("America/New_York")
UTC = dt.timezone.utc


def utcnow():
    return dt.datetime.now(UTC)


def iso(value):
    return value.isoformat()


def parse_time(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def query(url, **parameters):
    return url + "?" + urllib.parse.urlencode(parameters)


class Fetch:
    """Track each attempt even when parsing or the network fails."""

    def __init__(self):
        self.attempts = []

    def get(self, url):
        attempt = {"source_url": url, "fetch_time_utc": iso(utcnow()), "http_status": None}
        self.attempts.append(attempt)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                attempt["http_status"] = response.status
                attempt["response_url"] = response.geturl()
                data = response.read(MAX_RESPONSE_BYTES + 1)
                if len(data) > MAX_RESPONSE_BYTES:
                    raise ValueError("Response exceeded size limit")
                attempt["fetch_time_utc"] = iso(utcnow())
                return data, attempt
        except urllib.error.HTTPError as exc:
            attempt["http_status"] = exc.code
            raise
        finally:
            attempt["fetch_time_utc"] = iso(utcnow())

    def json(self, url):
        data, attempt = self.get(url)
        return json.loads(data), attempt


def finite(value):
    if value is None or value == "":
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Nonfinite number")
    return number


def field(value, source=None, timestamp=None, max_age_hours=None, *, unit=None,
          date_zone=UTC, note=None, endpoint=None):
    stale = None
    if value is not None and timestamp is not None and max_age_hours is not None:
        observed = parse_time(timestamp)
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=date_zone)
        fetched = parse_time(source["fetch_time_utc"])
        stale = not (dt.timedelta(0) <= fetched - observed <= dt.timedelta(hours=max_age_hours))
    result = {
        "value": value, "source_url": source["source_url"] if source else endpoint,
        "fetch_time_utc": source["fetch_time_utc"] if source else None,
        "data_timestamp": timestamp, "stale": stale,
    }
    if unit:
        result["unit"] = unit
    if note:
        result["note"] = note
    return result


def backwardation(vix_close, vix3m_close):
    """Use only same-date, fresh closes; callers must validate dates and freshness."""
    if vix_close is None or vix3m_close is None or vix3m_close <= 0:
        return None
    return vix_close / vix3m_close > VIX_BACKWARDATION_RATIO


def crowded_long(funding, predicted_funding, oi_usd):
    """Use fresh, same-contract funding fractions and USD open interest only."""
    if any(x is None for x in (funding, predicted_funding, oi_usd)):
        return None
    return (funding >= CROWDED_LONG_MIN_FUNDING_RATE
            and predicted_funding >= CROWDED_LONG_MIN_PREDICTED_FUNDING_RATE
            and oi_usd >= CROWDED_LONG_MIN_OI_USD)


def blocked(reason, endpoints):
    return {
        "status": "disabled_terms", "note": reason,
        "fields": {key: field(None, endpoint=url) for key, url in endpoints.items()},
        "attempts": [],
    }


def disabled_feeds():
    cboe = "https://cdn.cboe.com/api/global/us_indices/daily_prices/"
    kraken = "https://futures.kraken.com/derivatives/api/v3/tickers"
    finra = "https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files"
    return {
        "cboe_vix": blocked("Cboe website terms do not clearly allow this automated, retained use.", {
            "vix_close": cboe + "VIX_History.csv", "vix3m_close": cboe + "VIX3M_History.csv",
            "vix_to_vix3m": cboe + "VIX_History.csv", "backwardation": cboe + "VIX_History.csv",
        }),
        "kraken_futures": blocked("Kraken terms prohibit automation on its content; a public ticker API is documented, but no express clearance for this retained use was found.", {
            f"{coin}_{metric}": kraken for coin in ("BTC", "ETH")
            for metric in ("funding_rate", "predicted_funding_rate", "open_interest", "crowded_long")
        }),
        "finra_regsho": blocked("FINRA website terms bar robotic extraction. The separate licensed API requires credentials.", {
            f"{symbol}_{metric}": finra for symbol in ("SPY", "QQQ", "IWM")
            for metric in ("short_volume", "short_exempt_volume", "total_volume", "short_volume_share")
        }),
        "kalshi": blocked("Kalshi limits API use to facilitating a member's own trading on Kalshi.", {
            "next_fed_decision_prices": "https://api.elections.kalshi.com/trade-api/v2/markets",
        }),
        "polymarket_global": blocked("Global Polymarket terms restrict automated data extraction. The separately documented US API is used instead.", {
            "next_fed_decision_prices": "https://gamma-api.polymarket.com/events",
        }),
    }


def treasury(client):
    today = utcnow().astimezone(EASTERN).date()
    previous = today.replace(day=1) - dt.timedelta(days=1)
    fields = {}
    reasons = []
    # The previous month can be relevant just after a month boundary.
    for month in ((today, previous) if today.day <= 5 else (today,)):
        url = query(TREASURY, data="daily_treasury_bill_rates", field_tdr_date_value_month=month.strftime("%Y%m"))
        try:
            raw, source = client.get(url)
            root = ET.fromstring(raw)
            for properties in root.findall(".//{*}properties"):
                timestamp = (properties.findtext("{*}INDEX_DATE") or "")[:10]
                if not timestamp or dt.date.fromisoformat(timestamp) > today:
                    continue
                for term in MATURITIES:
                    key = f"{term}wk_coupon_equivalent"
                    rate = finite(properties.findtext(f"{{*}}ROUND_B1_YIELD_{term}WK_2"))
                    if rate is None or (key in fields and fields[key]["data_timestamp"] >= timestamp):
                        continue
                    fields[key] = field(rate, source, timestamp, BILL_STALE_HOURS,
                                        unit="percent", date_zone=EASTERN,
                                        note="US trade date, not a UTC clock time.")
            if fields and all(not x["stale"] for x in fields.values()):
                break
            reasons.append(f"{month:%Y-%m}: no sufficiently recent usable rows.")
        except (ValueError, ET.ParseError, OSError) as exc:
            reasons.append(f"{month:%Y-%m}: {type(exc).__name__}: {exc}")
    daily_source = client.attempts[0]
    for term in MATURITIES:
        fields.setdefault(f"{term}wk_coupon_equivalent", field(None, daily_source))
    daily_complete = all(x["value"] is not None and not x["stale"] for x in fields.values())
    if not daily_complete:
        url = query(TREASURY_AVERAGE, filter="security_desc:eq:Treasury Bills",
                    sort="-record_date", **{"page[size]": 2})
        try:
            data, source = client.json(url)
            row = next(row for row in data["data"] if row["security_desc"] == "Treasury Bills")
            fields["monthly_outstanding_bill_average"] = field(
                finite(row["avg_interest_rate_amt"]), source, row["record_date"],
                BILL_MONTHLY_STALE_HOURS, unit="percent", date_zone=EASTERN,
                note="Monthly average on outstanding bills, not a current yield or a rate for a particular term.")
            reasons.append("Fiscal Data monthly average is a fallback, not a daily bill yield.")
        except (ValueError, OSError, KeyError, StopIteration) as exc:
            reasons.append(f"Fiscal Data: {type(exc).__name__}: {exc}")
            fields["monthly_outstanding_bill_average"] = field(None, client.attempts[-1])
    status = "ok" if daily_complete else (
        "partial" if any(x["value"] is not None for x in fields.values()) else "unavailable")
    return {"status": status, "fields": fields, "note": " ".join(reasons) or None}


def coin_metrics(client):
    start = utcnow().date() - dt.timedelta(days=COIN_LOOKBACK_DAYS)
    url = query(COIN, assets="btc,eth", metrics=",".join(COIN_UNITS), frequency="1d",
                start_time=start, page_size=20)
    data, source = client.json(url)
    fields = {}
    for asset in ("btc", "eth"):
        rows = sorted((row for row in data["data"] if row["asset"] == asset),
                      key=lambda row: parse_time(row["time"]), reverse=True)
        for metric, unit in COIN_UNITS.items():
            row = next((row for row in rows if row.get(metric) not in (None, "")), None)
            fields[f"{asset.upper()}_{metric}"] = (
                field(finite(row[metric]), source, row["time"], COIN_STALE_HOURS, unit=unit) if row
                else field(None, source, unit=unit, note="No nonempty value in the query window."))
    return {"status": "ok" if all(x["value"] is not None and not x["stale"] for x in fields.values()) else "partial",
            "fields": fields}


def stablecoins(client):
    data, source = client.json(DEFILLAMA)
    series = {}
    for row in data:
        # Limit to USD-pegged stablecoins. Do not sum the currency-pegged buckets.
        value = finite(row.get("totalCirculatingUSD", {}).get("peggedUSD"))
        day = dt.datetime.fromtimestamp(int(row["date"]), UTC)
        if value is not None and value > 0 and day.date() < utcnow().date():
            series[day] = value
    latest = max(series)
    baseline = latest - dt.timedelta(days=STABLECOIN_CHANGE_DAYS)
    if baseline not in series:
        return {"status": "unavailable", "fields": {
            "usd_pegged_supply_change_7d": field(None, source, note="Exact baseline date missing.")}}
    note = f"Computed aggregate change, not a raw snapshot. Baseline: {iso(baseline)}."
    change = 100 * (series[latest] / series[baseline] - 1)
    return {"status": "ok", "fields": {
        "usd_pegged_supply_change_7d": field(change, source, iso(latest), STABLECOIN_STALE_HOURS,
                                             unit="percent", note=note)}}


def sec_form4(client):
    url = query(SEC, action="getcurrent", type="4", output="atom", count=SEC_FEED_ROWS)
    raw, feed_source = client.get(url)
    root = ET.fromstring(raw)
    # One accession can appear under the issuer and several reporting owners.
    filings = {}
    for entry in root.findall("{*}entry"):
        title = entry.findtext("{*}title", "")
        category = entry.find("{*}category")
        if category is None or category.get("term") != "4":
            continue
        link = entry.find("{*}link")
        accession = entry.findtext("{*}id", "").rsplit("=", 1)[-1]
        if link is None or not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
            continue
        report = (link.get("href", ""), entry.findtext("{*}updated"))
        if accession not in filings or "(Issuer)" in title:
            filings[accession] = report
    entries = sorted(filings.items(), key=lambda item: parse_time(item[1][1]), reverse=True)
    fields = {}
    failures = []
    scanned = 0
    for accession, (index_url, accepted) in entries[:SEC_MAX_FORM_FILINGS]:
        if not re.fullmatch(r"https://www\.sec\.gov/Archives/edgar/data/\d+/\d+/[\d-]+-index\.htm", index_url):
            failures.append(f"{accession}: no usable EDGAR filing path")
            continue
        filing_url = index_url.removesuffix("-index.htm") + ".txt"
        time.sleep(SEC_MIN_PAUSE_SECONDS)
        try:
            submission, source = client.get(filing_url)
            match = re.search(rb"<ownershipDocument\b[^>]*>.*?</ownershipDocument>", submission, re.S)
            if not match:
                raise ValueError("Ownership XML missing")
            ownership = ET.fromstring(match.group())
            purchases = []
            for tx in ownership.findall(".//nonDerivativeTransaction"):
                code = tx.findtext("transactionCoding/transactionCode")
                side = tx.findtext("transactionAmounts/transactionAcquiredDisposedCode/value")
                if code != "P" or side != "A":
                    continue
                purchases.append({
                    "security": tx.findtext("securityTitle/value"),
                    "transaction_date": tx.findtext("transactionDate/value"),
                    "shares": finite(tx.findtext("transactionAmounts/transactionShares/value")),
                    "price_per_share": finite(tx.findtext("transactionAmounts/transactionPricePerShare/value")),
                })
            if purchases:
                fields[f"purchase_{accession}"] = field({
                    "issuer": ownership.findtext("issuer/issuerName"),
                    "symbol": ownership.findtext("issuer/issuerTradingSymbol"),
                    "transactions": purchases,
                }, source, accepted, SEC_STALE_HOURS,
                    note="Time is when EDGAR accepted the filing. Code P includes both open-market and private purchases.")
            scanned += 1
        except (ValueError, ET.ParseError, OSError) as exc:
            failures.append(f"{accession}: {type(exc).__name__}: {exc}")
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (403, 429):
                break
    latest = entries[0][1][1] if entries else None
    fields["filings_scanned"] = field(scanned, feed_source, latest, SEC_STALE_HOURS)
    fields["filings_with_purchase_candidates"] = field(len(fields) - 1, feed_source, latest, SEC_STALE_HOURS)
    note = "Bounded recent sample, not all filings. Code P candidates do not prove open-market buying."
    return {"status": ("unavailable" if not scanned else ("partial" if failures else "ok")),
            "fields": fields, "note": note, "filing_errors": failures}


def next_fed_date(page, today):
    # Parse Treasury/Fed date-only fields as their source dates, not UTC instants.
    months = {name.lower(): n for n, name in enumerate(calendar.month_name) if name}
    months.update({name.lower(): n for n, name in enumerate(calendar.month_abbr) if name})
    decisions = []
    sections = re.split(r"(20\d{2})\s+FOMC Meetings", page, flags=re.I)
    for yeartxt, section in zip(sections[1::2], sections[2::2]):
        for month, days in re.findall(r'fomc-meeting__month[^>]*>(.*?)</div>\s*'
                                      r'<div[^>]+fomc-meeting__date[^>]*>(.*?)</div>', section, re.S):
            month = html.unescape(re.sub(r"<[^>]*>", "", month)).strip().split("/")[-1].lower()
            days = html.unescape(re.sub(r"<[^>]*>", "", days)).strip()
            numbers = re.fullmatch(r"(?:\d{1,2}\s*[-–]\s*)?(\d{1,2})\s*\*?", days)
            if month not in months or not numbers:
                continue
            decision = dt.date(int(yeartxt), months[month], int(numbers[1]))
            if decision >= today:
                decisions.append(decision)
    if not decisions:
        raise ValueError("No upcoming scheduled decision found on the Fed calendar")
    return min(decisions)


def dollar_quote(value):
    if not isinstance(value, dict) or value.get("currency") != "USD":
        return None
    amount = finite(value.get("value"))
    return amount if amount is not None and 0 <= amount <= 1 else None


def polymarket_us(client):
    now = utcnow().astimezone(EASTERN)
    raw, fed_source = client.get(FED)
    page = raw.decode("utf-8")
    decision = next_fed_date(page, now.date())
    date_source = re.search(r"Last Update:\s*((?:</?[^>]+>\s*)*)([A-Z][a-z]+ \d{1,2}, \d{4})", page, re.I)
    try:
        calendar_timestamp = dt.datetime.strptime(date_source[2], "%B %d, %Y").date().isoformat()
    except (TypeError, ValueError):
        calendar_timestamp = None
    fields = {"next_fed_decision_date": field(decision.isoformat(), fed_source, calendar_timestamp,
               FED_CALENDAR_STALE_HOURS, date_zone=EASTERN, note="Last calendar update, when furnished.")}
    url = query(POLY_US + "/search", query="Fed interest rate", limit=POLY_SEARCH_ROWS)
    # The catalog carries both the contract's scheduled time and a date in its event slug.
    catalog, search_source = client.json(url)
    target = f"usfed-fomc-{decision}"
    matches = [e for e in (catalog.get("events") or []) if e.get("slug") == target
               and e.get("active") and not e.get("closed")]
    if len(matches) != 1:
        fields["next_fed_decision_prices"] = field(None, search_source,
                        note="No single active Polymarket US event matched the Fed decision date.")
        return {"status": "unavailable", "fields": fields}
    fields["event"] = field(target, search_source, matches[0].get("updatedAt"), POLY_STALE_HOURS)
    failures = []
    open_markets = [m for m in matches[0].get("markets", []) if m.get("active") and not m.get("closed")]
    for market in open_markets[:POLY_MAX_CONTRACTS]:
        slug = market["slug"]
        contract_url = POLY_US + "/markets/" + urllib.parse.quote(slug, safe="") + "/bbo"
        try:
            payload, source = client.json(contract_url)
            book = payload["marketData"]
            if book.get("state") != "MARKET_STATE_OPEN":
                raise ValueError("Contract not open")
            sample = book.get("lastPriceSample") or {}
            fields[slug + "_yes_sample"] = field(
                dollar_quote(sample.get("longPx")), source, sample.get("ts"), POLY_STALE_HOURS,
                unit="USD per $1 payout", note="Price sample, not an executable quote.")
            for suffix, metric in (("_yes_bid", "bestBid"), ("_yes_ask", "bestAsk")):
                fields[slug + suffix] = field(dollar_quote(book.get(metric)), source,
                    unit="USD per $1 payout", note="No timestamp on the bid or ask itself; freshness is unknown.")
        except (ValueError, KeyError, OSError) as exc:
            failures.append(f"{slug}: {type(exc).__name__}: {exc}")
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (403, 429):
                break
    sample_fields = [value for key, value in fields.items() if key.endswith("_yes_sample")]
    if not any(value["value"] is not None for value in sample_fields):
        fields["next_fed_decision_prices"] = field(None, search_source, note="No usable open contracts.")
        status = "unavailable"
    else:
        status = "partial" if (failures or len(open_markets) > POLY_MAX_CONTRACTS
                              or any(value["stale"] is not False for value in sample_fields)) else "ok"
    return {"status": status, "fields": fields, "contract_errors": failures}


def run_feed(function):
    client = Fetch()
    try:
        result = function(client)
    except Exception as exc:
        result = {"status": "error", "fields": {}, "note": f"{type(exc).__name__}: {exc}"}
    result["attempts"] = client.attempts
    return result


def summary(report):
    lines = ["# Market context", "", f"Run at {report['run_at_utc']}. This is private research context.",
             "A missing flag is not a negative signal. Source dates and links are in the JSON.", "",
             "| Feed | Result |", "|---|---|"]
    for name, result in report["feeds"].items():
        label = name.replace("_", " ")
        note = result.get("note") or ""
        lines.append(f"| {label} | {result['status'].replace('_', ' ')}. {note.replace('|', '/')} |")
    lines += ["", "## Readings", ""]
    for name, result in report["feeds"].items():
        if result["status"] in ("disabled_terms", "error", "unavailable"):
            continue
        for key, record in result["fields"].items():
            value = record["value"]
            if value is None or isinstance(value, dict):
                continue
            if name in ("treasury_bills", "coin_metrics", "stablecoins", "polymarket_us", "sec_form4"):
                if name == "polymarket_us" and (key == "event" or key.endswith(("_yes_ask", "_yes_bid"))):
                    continue
                value = (f"{value:,.0f}" if abs(value) >= 100 else f"{value:.4g}") if isinstance(value, float) else str(value)
                timestamp = record["data_timestamp"] or "no timestamp supplied"
                freshness = {None: "freshness unknown", False: "not stale", True: "stale"}[record["stale"]]
                label = key.replace("_", " ")
                if name == "coin_metrics":
                    asset, metric = key.split("_", 1)
                    label = f"{asset} {COIN_LABELS[metric]}"
                if key.endswith("_yes_sample"):
                    outcome = key.removesuffix("_yes_sample").rsplit("-", 1)[-1]
                    label = {"hike25": "25 bp increase", "hike50": "50+ bp increase",
                             "nochng": "no change", "cut25": "25 bp cut",
                             "cut50": "50+ bp cut"}.get(outcome, outcome) + " Yes sample"
                unit = " " + record["unit"] if "unit" in record else ""
                title = name.replace("_", " ")
                lines.append(f"- {label}: {value}{unit} ({timestamp}; {freshness}) "
                             f"([{title}]({record['source_url']})).")
    lines += ["", "SEC code P includes both open-market and private purchases "
               "([Form 4 instructions](https://www.sec.gov/divisions/corpfin/topic-topics/forms/form4.pdf)). "
               "Prediction prices describe event contracts, not stock price forecasts.", ""]
    return "\n".join(lines)


def write_atomic(path, data):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as file:
        pending = Path(file.name)
        try:
            file.write(data)
            file.flush()
            os.replace(pending, path)
        finally:
            pending.unlink(missing_ok=True)


def main():
    run_time = utcnow()
    work = {"treasury_bills": treasury, "coin_metrics": coin_metrics, "stablecoins": stablecoins,
            "sec_form4": sec_form4, "polymarket_us": polymarket_us}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(work)) as executor:
        tasks = {name: executor.submit(run_feed, fn) for name, fn in work.items()}
        feeds = {name: task.result() for name, task in tasks.items()}
    feeds.update(disabled_feeds())
    report = {"run_at_utc": iso(run_time), "feeds": feeds}
    CACHE.mkdir(parents=True, exist_ok=True, mode=0o700)
    dated = CACHE / f"context_{run_time.date()}.json"
    latest = CACHE / "context_latest.md"
    write_atomic(dated, json.dumps(report, allow_nan=False, indent=2) + "\n")
    write_atomic(latest, summary(report))
    print(dated)
    print(latest)
    for name, result in feeds.items():
        print(f"{name}: {result['status']}")


if __name__ == "__main__":
    main()
