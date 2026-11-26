"""Checks for the E07 logger with a pretend quote source and made-up funds. Makes no requests."""
import csv, io, json, stat, sys, tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forward_e07 as E

UTC = timezone.utc
N = 0


def check(ok, what):
    global N
    assert ok, what
    N += 1


def refuses(f, what):
    try:
        f()
    except E.Refuse:
        check(True, what); return
    check(False, what)


def t(day, hms, frac=""):
    """A New York wall time on day as an Alpaca-style UTC stamp."""
    h, m, s = map(int, hms.split(":"))
    u = datetime(day.year, day.month, day.day, h, m, s, tzinfo=E.NY).astimezone(UTC)
    return u.strftime("%Y-%m-%dT%H:%M:%S") + (("." + frac) if frac else "") + "Z"


def ny(day, hms):
    h, m, s = map(int, hms.split(":"))
    return datetime(day.year, day.month, day.day, h, m, s, tzinfo=E.NY).astimezone(UTC)


def row(tk, ltd, pay, acc="2026-11-20T15:00:00Z", tm="false", cash="pre_last_trade", url=None, exch="NASDAQ"):
    return dict(ticker=tk, fund_name=f"Pretend {tk} Fund", exchange=exch, cik="1234567", accession="0001234567-26-000001", form="497",
                edgar_acceptance_utc=acc, stated_last_trading_day=ltd, stated_liquidation_or_payout_date=pay, target_maturity_etf=tm,
                cash_before_last_trade=cash, cash_disclosure_quote="The fund will hold cash before the last day of trading.",
                filing_url=url or f"https://www.sec.gov/Archives/edgar/data/1234567/{tk.lower()}.htm")


def write_csv(path, rows):
    b = io.StringIO(); w = csv.DictWriter(b, fieldnames=E.FIELDS); w.writeheader(); w.writerows(rows)
    path.write_text(b.getvalue())


class Feed:
    """Pretend SIP quotes for the window, in two pages, steady at a made-up bid and ask."""
    def __init__(self, bid=9.98, ask=10.02, gap=False):
        self.bid, self.ask, self.gap, self.calls = bid, ask, gap, []

    def __call__(self, path, q):
        self.calls.append((path, dict(q)))
        a = datetime.strptime(q["start"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        step = 400 if self.gap else 10
        qs = [dict(t=(a + timedelta(seconds=k)).strftime("%Y-%m-%dT%H:%M:%S.5Z"), bp=self.bid, ap=self.ask) for k in range(0, 360, step)]
        if "page_token" not in q:
            return dict(quotes=qs[:len(qs) // 2], next_page_token="p2")
        return dict(quotes=qs[len(qs) // 2:], next_page_token=None)


def main():
    p = E.plan()
    check(p["window_ny"] == ["15:54:00", "15:59:00"] and p["min_cover_s"] == 180 and p["stop_count"] == 40, "pinned clock and stop rule")
    check(p["decision"]["mean_gt"] == 0.0025 and p["decision"]["share_positive_ge"] == 0.6, "pinned decision rule")

    # calendar and windows
    check(not E.session(date(2026, 11, 26)) and E.session(date(2026, 11, 27)) and not E.session(date(2027, 5, 31)), "holidays")
    a, b, s = E.window(date(2026, 11, 27))
    check((a.hour, a.minute, b.minute, s.minute) == (17, 54, 59, 55), "early close moves the window to 12:54 to 12:59 New York")
    a, b, s = E.window(date(2026, 12, 1))
    check((a.hour, a.minute, b.hour, b.minute) == (20, 54, 20, 59), "normal window 15:54 to 15:59 New York")
    check(E.add_sessions(date(2027, 6, 1), 15) == date(2027, 6, 23) and E.sessions_between(date(2026, 12, 24), date(2026, 12, 28)) == 1, "session counting")
    refuses(lambda: E.session(date(2028, 1, 3)), "a date outside the pinned calendar is refused")

    # the quote summary
    d = date(2026, 12, 1)
    qs = [dict(t=t(d, "15:53:30"), bp=10.0, ap=10.1),          # carry-in, holds 15:54:00 to 15:54:30 (expiry)
          dict(t=t(d, "15:55:00"), bp=10.0, ap=10.2),          # 60 s
          dict(t=t(d, "15:56:00"), bp=10.3, ap=10.2),          # crossed, 60 s not counted
          dict(t=t(d, "15:57:00", "25"), bp=10.1, ap=10.3),    # 15:57:00.25 to 15:58:00.25 (expiry)
          dict(t=t(d, "15:58:30"), bp=0, ap=10.3),             # one-sided, not counted
          dict(t=t(d, "15:58:40"), bp=10.1, ap=10.1)]          # locked, valid, 20 s to the window end
    sm = E.summarize(qs, d)
    check(sm["valid_seconds"] == 170.0 and sm["quote_status"] == "missing_or_insufficient" and sm["closing_ask"] is None, "below 180 s is refused")
    qs.append(dict(t=t(d, "15:58:00", "25"), bp=10.1, ap=10.4))  # fills 15:58:00.25 to 15:58:30
    sm = E.summarize(qs, d)
    check(abs(sm["valid_seconds"] - 199.75) < 1e-9 and sm["quote_status"] == "ok", "coverage counts expiry, crossed and one-sided states")
    check(sm["closing_bid"] == 10.1 and sm["closing_ask"] == 10.2, "duration-weighted medians")
    check(sm["snapshot"] == dict(valid=True, bid=10.0, ask=10.2), "the 15:55:00 snapshot takes the quote in force at that time")
    check(E.summarize([dict(t=t(d, "15:53:00"), bp=1, ap=2)], d)["snapshot"]["valid"] is False, "an expired quote is no snapshot")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); off, pub = tmp / "e07", tmp / "E07_log.json"; wl = tmp / "watch.csv"
        write_csv(wl, [row("AAAA", "2026-12-01", "2026-12-04"), row("BBBB", "2026-12-01", "2026-12-04", tm="true"),
                       row("CCCC", "2026-12-02", "2026-12-07", cash="post_last_trade_only"),
                       row("DDDD", "2026-11-20", "2026-11-25"), row("EEEE", "2026-12-03", "2026-12-08", url="https://example.com/x.htm"),
                       row("FFFF", "2026-12-03", "2026-12-08", exch="OTC")])
        now = datetime(2026, 11, 26, 18, 0, tzinfo=UTC)
        refuses(lambda: E.add_funds(wl, ["DDDD"], now, off, pub, commit="abc"), "a last trading day not after acceptance is refused")
        check(E.read_log(off)[0]["kind"] == "header", "the header is written first")
        refuses(lambda: E.add_funds(wl, ["EEEE"], now, off, pub), "a filing link off sec.gov is refused")
        refuses(lambda: E.add_funds(wl, ["FFFF"], now, off, pub), "an exchange off the list is refused")
        check(E.add_funds(wl, ["AAAA", "BBBB", "CCCC"], now, off, pub) == ["AAAA", "BBBB", "CCCC"], "three funds admitted")
        refuses(lambda: E.add_funds(wl, ["AAAA"], now, off, pub), "a fund is admitted once")
        write_csv(wl, [row("GGGG", "2026-12-01", "2026-12-04")])
        refuses(lambda: E.add_funds(wl, ["GGGG"], ny(d, "15:54:00"), off, pub), "no admission once the window has started")
        check(stat.S_IMODE(off.stat().st_mode) == 0o700 and stat.S_IMODE((off / "log.jsonl").stat().st_mode) == 0o600, "private modes")
        E.amend("CCCC", None, "2026-12-08", "https://www.sec.gov/Archives/edgar/data/1234567/supp.htm", now, off, pub)
        check(E.state(E.read_log(off))[0]["CCCC"]["fund"]["stated_liquidation_or_payout_date"] == "2026-12-08", "a supplement moves the payout date")

        f = Feed()
        check(E.record_quote(ny(d, "15:58:00"), f, off=off, pub=pub) == [] and not f.calls, "nothing is read before the window closes")
        r = E.record_quote(ny(d, "16:05:00"), f, off=off, pub=pub)
        check(sorted(r) == [("AAAA", "ok"), ("BBBB", "ok")] and len(f.calls) == 4, "both funds of the day are recorded, two pages each")
        check(f.calls[0][1]["feed"] == "sip" and f.calls[0][1]["start"] == "2026-12-01T20:53:00Z" and f.calls[0][1]["end"] == "2026-12-01T20:59:00Z",
              "reads the window plus 60 s carry-in from the SIP feed")
        check(E.record_quote(ny(d, "16:30:00"), Feed(), off=off, pub=pub) == [], "a recorded fund is not recorded again")
        check(E.record_quote(ny(date(2026, 12, 3), "16:05:00"), Feed(), off=off, pub=pub) == [], "a missed day is not back-filled")
        pk = sorted((off / "packets").iterdir())
        check(len(pk) == 2 and all(stat.S_IMODE(x.stat().st_mode) == 0o600 for x in pk), "quote packets off repo, 0600")

        al = E.alive(ny(date(2026, 12, 3), "17:00:00"), off)
        check((al["funds"], al["quote_ok"], al["quote_missed"], al["completed"]) == (3, 2, 1, 0), "alive counts")
        check(not any(k in json.dumps(al) for k in ("bid", "ask", "payout_per", "over_")), "alive shows counts only")

        later = ny(date(2026, 12, 5), "12:00:00")
        src = "https://www.ishares.com/us/closed-funds/aaaa-notice.pdf"
        refuses(lambda: E.record_payout("AAAA", 10.05, "2026-12-04", src, "robinhood", "2026-12-04", later, off=off, pub=pub), "a broker tracker is not primary")
        E.record_payout("AAAA", 10.03, "2026-12-04", "https://robinhood.com/x", "tracker", "2026-12-04", later, secondary=True, off=off, pub=pub)
        check(E.alive(later, off)["completed"] == 0, "a secondary payout does not complete a fund")
        E.record_payout("AAAA", 10.05, "2026-12-04", src, "issuer_notice", "2026-12-04", later, off=off, pub=pub)
        refuses(lambda: E.record_payout("AAAA", 10.05, "2026-12-04", src, "issuer_notice", "2026-12-04", later, off=off, pub=pub), "one primary payout per fund")
        late = ny(E.payout_deadline(E.state(E.read_log(off))[0]["BBBB"]["fund"]) + timedelta(days=1), "12:00:00")
        refuses(lambda: E.record_payout("BBBB", 10.0, "2026-12-04", src, "issuer_notice", "2026-12-04", late, off=off, pub=pub), "past the deadline is refused")
        al = E.alive(late, off)
        check((al["completed"], al["primary_missing"]) == (1, 1), "the late fund counts as primary_missing")

        refuses(lambda: E.score(late, off, pub), "score refuses before the stop rule")
        pubtxt = pub.read_text()
        check(not any(k in pubtxt for k in ("closing_bid", "closing_ask", "payout_per_share", "payout_total", "10.05", "9.98", "10.02")),
              "the public log holds no prices or payouts")
        ent = E.read_public(pub)
        check([e["kind"] for e in ent][:4] == ["header", "fund", "fund", "fund"] and all("private_line_sha256" in e for e in ent), "public log entries")

        E.STOP_COUNT = 1
        try:
            refuses(lambda: E.record_quote(ny(date(2026, 12, 2), "16:05:00"), Feed(), off=off, pub=pub), "no new observations after the count stop")
            res = E.score(late, off, pub)
            check(res["stopped_by"] == "count" and res["completed_used"] == 1, "score after the count stop")
            check(abs(res["slices"]["all"]["mean_over_ask_pct"] - round(100 * (10.05 / 10.02 - 1), 4)) < 1e-9, "payout over the closing ask")
            check(res["conditions"]["mean"] and res["conditions"]["discretionary"] is None and res["verdict"] == "write_follow_on", "decision rule")
            refuses(lambda: E.score(late, off, pub), "score runs once")
            check(E.read_public(pub)[-1]["kind"] == "final", "the aggregate goes to the public log at stop")
        finally:
            E.STOP_COUNT = 40

        lines = (off / "log.jsonl").read_text().splitlines()
        (off / "log.jsonl").write_text("\n".join(lines[:1] + [lines[2], lines[1]] + lines[3:]) + "\n")
        refuses(lambda: E.read_log(off), "a reordered private log is refused")
        j = json.loads(pub.read_text()); j["entries"][1]["ticker"] = "ZZZZ"; pub.write_text(json.dumps(j))
        refuses(lambda: E.read_public(pub), "an edited public log is refused")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); off, pub = tmp / "e07", tmp / "E07_log.json"; wl = tmp / "w.csv"
        write_csv(wl, [row("HHHH", "2026-12-01", "2026-12-04")])
        E.add_funds(wl, [], datetime(2026, 11, 26, tzinfo=UTC), off, pub, commit="abc")
        r = E.record_quote(ny(d, "16:01:00"), Feed(gap=True), off=off, pub=pub)
        check(r == [("HHHH", "missing_or_insufficient")], "a thin window is logged as a quote refusal")
        x = E.read_log(off)[-1]
        check(x["summary"]["closing_ask"] is None, "no trade print, midpoint or prior close is substituted")
        res_dir = E.alive(datetime(2027, 6, 22, 12, tzinfo=UTC), off)
        check(res_dir["stop_met"] and res_dir["completed"] == 0, "the date stop")
        res = E.score(datetime(2027, 6, 22, 12, tzinfo=UTC), off, pub)
        check(res["stopped_by"] == "date" and res["verdict"] == "inconclusive_on_data_availability", "below 20 completed by date is inconclusive")
        off2 = tmp / "open"; off2.mkdir(mode=0o755); off2.chmod(0o755)
        refuses(lambda: E.add_funds(wl, [], datetime(2026, 11, 26, tzinfo=UTC), off2, tmp / "p2.json", commit="abc"), "a shared record folder is refused")
    print(f"{N} checks passed")


if __name__ == "__main__":
    main()
