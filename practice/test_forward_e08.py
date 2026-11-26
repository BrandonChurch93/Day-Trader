"""Checks for the E08 logger with a pretend data source, made-up funds and a temp folder. Makes no requests."""
import json, re, stat, sys, tempfile
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forward_e08 as E

UTC = timezone.utc
N = 0


def check(ok, what):
    global N
    assert ok, what
    N += 1


def refuses(f, what, text=None):
    try:
        f()
    except E.Refuse as e:
        check(text is None or text in str(e), f"{what} (got: {e})"); return
    check(False, what)


def at(d, hh, mm=0):
    return datetime.combine(d, time(hh, mm), E.NY).astimezone(UTC)


FIELDS = E.ROSTER_FIELDS
FILING = "https://www.sec.gov/Archives/edgar/data/1378872/000000000026000001/0000000000-26-000001-index.htm"


def roster_rows(names):
    return [dict(turn_year="2026", holding_id=str(i + 1), ticker=t, cik=f"{1000000000 + i:010d}", holding_name=f"Pretend {t} Income Fund",
                 identity_url=f"https://www.sec.gov/pretend/{t}", series="S000027370", report_period="2026-09-30",
                 public_date="2026-11-25", form="NPORT-P", filing_url=FILING) for i, t in enumerate(names)]


def write_csv(p, rows, fields):
    import csv, io
    b = io.StringIO(); w = csv.DictWriter(b, fieldnames=fields, lineterminator="\n"); w.writeheader(); w.writerows(rows)
    p.write_text(b.getvalue())


FUNDS = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH", "JJJ", "KKK"]
# Year-to-date loss at formation, by fund (larger is worse, so ranked first).
LOSS = dict(AAA="0.30", BBB="0.25", CCC="0.20", DDD="0.15", EEE="0.10", FFF="0.05", GGG="0.02", HHH="0.01", JJJ="0.35", KKK="0.40")
BASE = dict(AAA=10, BBB=12, CCC=14, DDD=16, EEE=18, FFF=20, GGG=22, HHH=24, JJJ=200, KKK=8, PCEF=20)
JAN_UP = dict(AAA="1.05", BBB="1.02", CCC="0.99", DDD="1.01", EEE="1.03", FFF="1.0", GGG="1.0", HHH="1.0", JJJ="1.0", KKK="1.0", PCEF="1.01")


class Feed:
    """Pretend SIP daily bars, split records and quotes. JJJ costs $140 a share (unaffordable); KKK misses a session;
    HHH has a split in the ranking window; GGG has a one-day jump; options let a test add a held-fund split or a missing exit."""
    def __init__(self, jump=True, held_split=None, missing_exit=None, thin=()):
        self.jump, self.held_split, self.missing_exit, self.thin, self.calls = jump, held_split, missing_exit, set(thin), []

    def close(self, t, d):
        b = Fraction(BASE[t])
        if t == "JJJ":
            b = Fraction(200)
        if d <= E.ENTRY:
            n = len(E.RANK_DAYS) - 1
            k = E.RANK_DAYS.index(d)
            loss = Fraction(LOSS.get(t, "0.05"))
            c = b * (1 - loss * Fraction(min(k, n - 1), n - 1))
            if t == "GGG" and self.jump and d == E.RANK_DAYS[100]:
                c *= Fraction(3, 2)
            return Fraction(str(round(float(c), 4)))
        c = self.close(t, E.ENTRY) * Fraction(JAN_UP[t])
        if self.held_split and t == self.held_split[0] and d >= self.held_split[1]:
            c /= 2
        return Fraction(str(round(float(c), 4)))

    def bars(self, t, a, b, adj):
        out = []
        for d in E.sessions(a, b):
            if t == "KKK" and d == E.RANK_DAYS[50]:
                continue
            if self.missing_exit and t == self.missing_exit and d > E.ENTRY + timedelta(days=10):
                continue
            v = Decimal(str(float(self.close(t, d))))
            if adj == "split":
                if t == "HHH" and d < E.RANK_DAYS[120]:
                    v /= 2
                if self.held_split and t == self.held_split[0] and d < self.held_split[1]:
                    v /= 2
            ts = datetime.combine(d, time(0), E.NY).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            out.append(dict(t=ts, o=v, h=v, l=v, c=v, v=1000, n=5, vw=v))
        return out

    def __call__(self, path, q):
        self.calls.append((path, dict(q)))
        if path == "/v1/corporate-actions":
            t = q["symbols"]; recs = []
            a, b = date.fromisoformat(q["start"]), date.fromisoformat(q["end"])
            if t == "HHH" and a <= E.RANK_DAYS[120] <= b:
                recs.append(dict(symbol="HHH", ex_date=str(E.RANK_DAYS[120]), new_rate=2, old_rate=1))
            if self.held_split and t == self.held_split[0] and a <= self.held_split[1] <= b:
                recs.append(dict(symbol=t, ex_date=str(self.held_split[1]), new_rate=2, old_rate=1))
            return dict(corporate_actions=dict(forward_splits=recs, reverse_splits=[]), next_page_token=None)
        t = path.split("/")[3]
        if path.endswith("/bars"):
            rows = self.bars(t, date.fromisoformat(q["start"]), date.fromisoformat(q["end"]), q["adjustment"])
            if "page_token" not in q and len(rows) > 3:
                return dict(bars=rows[:len(rows) // 2], symbol=t, next_page_token="p2")
            return dict(bars=rows[len(rows) // 2:] if "page_token" in q else rows, symbol=t, next_page_token=None)
        a = datetime.strptime(q["start"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        d = a.astimezone(E.NY).date()
        c = float(self.close(t, d))
        step = 400 if t in self.thin else 10
        qs = [dict(t=(a + timedelta(seconds=k)).strftime("%Y-%m-%dT%H:%M:%S.25Z"), bp=Decimal(str(round(c * 0.999, 4))),
                   ap=Decimal(str(round(c * 1.001, 4))), bs=1, as_=1) for k in range(0, 360, step)]
        return dict(quotes=qs, next_page_token=None, symbol=t)


def half_of(c):
    bp, ap = Fraction(str(round(float(c) * 0.999, 4))), Fraction(str(round(float(c) * 1.001, 4)))
    return (ap - bp) / ((ap + bp) / 2) / 2


def main():
    # pinned numbers agree with config/thresholds.yaml
    import json as J
    y = (E.ROOT / "config" / "thresholds.yaml").read_text()
    p48 = J.loads(re.search(r"^replay_48_plan:\n  value: (.*)$", y, re.M).group(1))
    p53 = J.loads(re.search(r"^replay_53_plan:\n  value: (.*)$", y, re.M).group(1))
    check(p48["cost"] == E.CFG["cost"] and p48["sleeve_usd"] == 100 and p48["capital"] == 500 and p48["picks"] == 5, "cost and sizing = replay_48_plan")
    check(str(p48["split_check_ratio"]) == E.CFG["split_check_ratio"] and p48["shown_exit_session"] == 5, "jump ratio and fifth session")
    check(p53["benchmark"] == "PCEF" and p53["municipal_name_terms"] == E.MUNI_TERMS and set(p53["holdings_forms"]) == E.HOLDINGS_FORMS
          and p53["holdings_series"] == "S000027370" and p53["roster_cutoff"] == "12-01", "scope = replay_53_plan")

    # sessions
    check((E.ANCHOR, E.FORMATION, E.ENTRY, E.EXIT5, E.EXITM) ==
          (date(2026, 1, 2), date(2026, 12, 30), date(2026, 12, 31), date(2027, 1, 8), date(2027, 1, 29)), "pinned sessions")
    cal = J.loads((E.ROOT / "research_rig" / "calendar_25.json").read_text())["sessions"]
    mine = [str(d) for d in E.sessions(date(2026, 1, 1), date(2026, 11, 24))]
    check(mine == [s for s in cal if "2026-01-01" <= s <= "2026-11-24"], "2026 sessions match the pinned Plan 25 calendar")
    check(not ({E.ENTRY, E.EXIT5, E.EXITM, E.FORMATION} & E.EARLY), "no clock on an early close")
    refuses(lambda: E.session(date(2027, 3, 1)), "a date outside the pinned calendar is refused")
    check(E.muni_hit("Pretend Tax-Free Income") and E.muni_hit("X MUNICIPAL FUND") and not E.muni_hit("Communications Income"), "muni name screen")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); off, pub = tmp / "off", tmp / "pub" / "E08_log.json"
        muni = tmp / "muni.csv"
        muni.write_text("turn_year,ticker,cik\r\n2026,MMM,0009999999\r\n2025,AAA,0000000001\r\n")
        rp, xp = tmp / "roster.csv", tmp / "excl.csv"
        rows = roster_rows(FUNDS)
        write_csv(rp, rows, FIELDS)
        write_csv(xp, [dict(roster_rows(["ZZZ"])[0], holding_id=str(len(FUNDS) + 1), holding_name="Pretend Municipal Fund",
                            reason="municipal_name")], FIELDS + ["reason"])
        inside = at(date(2026, 12, 10), 12)
        fz = lambda now=inside, r=rp, x=xp: E.freeze_list(r, x, now, off, pub, commit="0" * 40, muni_path=muni)

        # freeze-list windows and checks
        refuses(lambda: fz(at(date(2026, 11, 30), 23, 59)), "freeze before the roster cutoff", "open from")
        refuses(lambda: fz(at(E.FORMATION, 9, 30)), "freeze at the formation open", "open from")
        bad = tmp / "bad.csv"
        write_csv(bad, [dict(r, holding_name="Pretend Muni Fund") if r["ticker"] == "AAA" else r for r in rows], FIELDS)
        refuses(lambda: fz(r=bad), "a municipal name in the roster", "municipal name")
        write_csv(bad, [dict(r, ticker="MMM") if r["ticker"] == "AAA" else r for r in rows], FIELDS)
        refuses(lambda: fz(r=bad), "a Replay 48 overlap", "Replay 48")
        write_csv(bad, [dict(r, public_date="2026-12-01") for r in rows], FIELDS)
        write_csv(tmp / "x2.csv", [], FIELDS + ["reason"])
        refuses(lambda: fz(r=bad, x=tmp / "x2.csv"), "a filing public on the cutoff", "before 2026-12-01")
        write_csv(tmp / "x3.csv", [dict(roster_rows(["ZZZ"])[0], holding_id=str(len(FUNDS) + 2), reason="duplicate_common")], FIELDS + ["reason"])
        refuses(lambda: fz(x=tmp / "x3.csv"), "a holding_id gap", "without gaps")
        write_csv(bad, rows[:4], FIELDS)
        refuses(lambda: fz(r=bad, x=tmp / "x2.csv"), "fewer than five funds", "fewer than five")
        check(not off.exists() or not (off / "log.jsonl").exists(), "refusals wrote nothing")
        out = fz()
        check(out["roster"] == FUNDS and out["excluded"] == 1, "roster frozen")
        check(stat.S_IMODE(off.stat().st_mode) == 0o700 and stat.S_IMODE((off / "log.jsonl").stat().st_mode) == 0o600, "private modes")
        refuses(lambda: fz(), "a second freeze", "one write only")

        # record-entry
        feed = Feed()
        t_entry = at(E.ENTRY, 16, 25)
        refuses(lambda: E.record_entry(at(E.ENTRY, 16, 10), feed, off=off, pub=pub), "entry before 16:20 New York", "open from")
        refuses(lambda: E.record_entry(at(E.JAN[0], 9, 30), feed, off=off, pub=pub), "entry at the first January open", "open from")
        refuses(lambda: E.record_entry(t_entry, feed, off=off, pub=pub), "an uncleared jump", "GGG")
        g0, g1 = E.RANK_DAYS[99], E.RANK_DAYS[100]; g2 = E.RANK_DAYS[101]
        clr = [f"GGG,{g0},{g1},GENUINE_MOVE,https://example.org/ggg", f"GGG,{g1},{g2},GENUINE_MOVE,https://example.org/ggg"]
        refuses(lambda: E.record_entry(t_entry, feed, clear=clr[:1], off=off, pub=pub), "a missing clearance", "differ")
        refuses(lambda: E.record_entry(t_entry, feed, clear=clr + ["AAA,2026-02-02,2026-02-03,GENUINE_MOVE,https://e.org/a"],
                                       off=off, pub=pub), "an extra clearance", "differ")
        r = E.record_entry(t_entry, feed, clear=clr, off=off, pub=pub)
        log = E.read_log(off); ent = log[-1]["record"]
        check(r == dict(eligible=8, held=5), "8 eligible (KKK missing a session, HHH split), five held")
        check(set(ent["ineligible"]) == {"KKK", "HHH"}, "ineligible reasons recorded")
        check(ent["ranked"][:7] == ["JJJ", "AAA", "BBB", "CCC", "DDD", "EEE", "FFF"], "ranked lowest return first")
        check([p["ticker"] for p in ent["picks"]] == ["AAA", "BBB", "CCC", "DDD", "EEE"] and ent["skipped_unaffordable"] == ["JJJ"],
              "worst five that fit; the $140 fund is skipped")
        for p in ent["picks"]:
            c = feed.close(p["ticker"], E.ENTRY); h = half_of(c)
            check(Fraction(p["entry_half"]) == h and p["shares"] == int(100 // (c * (1 + h + Fraction(5, 10000)))), f"{p['ticker']} sizing")
        b = ent["benchmark"]; c = feed.close("PCEF", E.ENTRY)
        check(b["shares"] == int(500 // (c * (1 + half_of(c) + Fraction(5, 10000)))), "PCEF $500 whole-share sleeve")
        refuses(lambda: E.record_entry(t_entry, feed, clear=clr, off=off, pub=pub), "a second entry", "one write only")

        # record-exit5
        st = [f"{t},none,https://example.org/{t}" for t in ["AAA", "BBB", "CCC", "DDD", "EEE", "PCEF"]]
        t5 = at(E.EXIT5, 16, 30)
        x5 = lambda **k: E.record_exit("exit5", k.pop("now", t5), feed, off=off, pub=pub, **k)
        refuses(lambda: x5(now=at(E.EXIT5, 16, 0), status=st), "exit5 before the close settles", "open from")
        refuses(lambda: x5(now=at(date(2027, 1, 16), 0, 0), status=st), "exit5 after its window", "open from")
        refuses(lambda: x5(status=st[:-1]), "a missing PCEF status", "exactly one cash status")
        refuses(lambda: x5(status=st[:-1] + ["PCEF,partial,https://e.org/p"]), "PCEF partial", "documented or none")
        refuses(lambda: x5(status=st, cash=["AAA,2027-01-11,0.05,https://e.org/a,issuer_site"]), "cash after the exit", "outside")
        refuses(lambda: x5(status=st, cash=["AAA,2026-12-31,0.05,https://e.org/a,issuer_site"]), "cash on the entry day", "outside")
        refuses(lambda: x5(status=st, cash=["AAA,2027-01-06,0.05,https://e.org/a,issuer_site"]), "status none with cash", "does not match")
        refuses(lambda: x5(status=st, cash=["AAA,2027-01-06,0.05,https://e.org/a,vendor"]), "a vendor cash source", "https issuer")
        st5 = ["AAA,documented,https://e.org/a"] + st[1:]
        cash5 = ["AAA,2027-01-06,0.05,https://e.org/a,issuer_site"]
        res = x5(status=st5, cash=cash5)
        # independent arithmetic
        def net(t, X, pk, cash=Fraction(0)):
            ce, cx = feed.close(t, E.ENTRY), feed.close(t, X)
            eh, xh = half_of(ce), half_of(cx)
            fee = max(eh, xh) + Fraction(5, 10000)
            return pk * cx * (1 - fee) + cash * pk - pk * ce * (1 + eh + Fraction(5, 10000))
        sh = {p["ticker"]: p["shares"] for p in ent["picks"]}
        port = sum(net(t, E.EXIT5, sh[t], Fraction("0.05") if t == "AAA" else 0) for t in sh) / 500
        bench = net("PCEF", E.EXIT5, b["shares"]) / 500
        check(res["portfolio_pct"] == round(float(port) * 100, 4) and res["pcef_pct"] == round(float(bench) * 100, 4)
              and res["portfolio_minus_pcef_pct"] == round(float(port - bench) * 100, 4), "fifth-session returns match the hand sum")
        port_p = sum(net(t, E.EXIT5, sh[t]) for t in sh) / 500
        check(res["portfolio_price_only_pct"] == round(float(port_p) * 100, 4), "price-only diagnostic")
        refuses(lambda: x5(status=st5, cash=cash5), "a second exit5", "one write only")

        # record-exit-month: missing exit bar for BBB, thin quotes for CCC (proxy side)
        feed.missing_exit, feed.thin = "BBB", {"CCC"}
        tm = at(E.EXITM, 17, 0)
        xm = lambda **k: E.record_exit("exit_month", k.pop("now", tm), feed, off=off, pub=pub, **k)
        refuses(lambda: xm(status=st), "the month exit must repeat exit5 cash", "repeat every cash event")
        resm = xm(status=st5 + [], cash=cash5)
        pubtxt = pub.read_text(); pe = json.loads(pubtxt)["entries"]
        check([x["kind"] for x in pe] == ["header", "freeze", "entry", "exit5", "exit_month"], "public log has one line per record")
        check(pe[-1]["missing_exits"] == 1 and pe[-1]["exit_proxy_sides"] == 1, "missing exit and proxy side counted")
        fm = E.read_log(off)[-1]["record"]["funds"]
        ceB = feed.close("BBB", E.ENTRY)
        check(fm["BBB"]["missing_exit"] and Fraction(fm["BBB"]["exit_fee"]) == max(half_of(ceB), E.PROXY) + Fraction(5, 10000),
              "missing exit valued at the last close with max(entry half, proxy) + 5 bp")
        check(Fraction(fm["CCC"]["exit_fee"]) == max(half_of(feed.close("CCC", E.ENTRY)), E.PROXY) + Fraction(5, 10000), "thin quotes use the proxy")
        refuses(lambda: xm(status=st5, cash=cash5), "a second month exit", "one write only")
        # no prices, share counts or tickers of picks in the public log
        for t in ["AAA", "BBB", "CCC", "DDD", "EEE"]:
            check(f'"{t}"' not in pubtxt, f"pick {t} not in the public log")
        check("entry_close" not in pubtxt and "shares" not in pubtxt and "last_close" not in pubtxt, "no closes or share counts public")
        check(E.read_public(pub) and E.alive(tm, off)["records"] == ["header", "freeze", "entry", "exit5", "exit_month"], "chains hold")

    # a held-fund split must be documented, and PCEF may not split
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); off, pub = tmp / "off", tmp / "pub.json"
        muni = tmp / "muni.csv"; muni.write_text("turn_year,ticker,cik\n2026,MMM,0009999999\n")
        rp, xp = tmp / "r.csv", tmp / "x.csv"
        write_csv(rp, roster_rows(FUNDS), FIELDS); write_csv(xp, [], FIELDS + ["reason"])
        E.freeze_list(rp, xp, at(date(2026, 12, 10), 12), off, pub, commit="0" * 40, muni_path=muni)
        sd = E.JAN[2]
        feed = Feed(jump=False, held_split=("AAA", sd))
        E.record_entry(at(E.ENTRY, 16, 25), feed, off=off, pub=pub)
        st = [f"{t},none,https://example.org/{t}" for t in ["AAA", "BBB", "CCC", "DDD", "EEE", "PCEF"]]
        t5 = at(E.EXIT5, 16, 30)
        refuses(lambda: E.record_exit("exit5", t5, feed, status=st, off=off, pub=pub), "an undocumented held split", "vendor split dates")
        refuses(lambda: E.record_exit("exit5", t5, feed, status=st, splits=[f"PCEF,{sd},2/1,https://e.org/p"], off=off, pub=pub),
                "a PCEF split", "PCEF")
        res = E.record_exit("exit5", t5, feed, status=st, splits=[f"AAA,{sd},2/1,https://www.sec.gov/pretend"], off=off, pub=pub)
        sh = E.read_log(off)[-2]["record"]["picks"][0]
        check(sh["ticker"] == "AAA", "AAA held")
        f = E.read_log(off)[-1]["record"]["funds"]["AAA"]
        ce, cx = feed.close("AAA", E.ENTRY), feed.close("AAA", E.EXIT5)
        fee = max(half_of(ce), half_of(cx)) + Fraction(5, 10000)
        want = 2 * sh["shares"] * cx * (1 - fee) - sh["shares"] * ce * (1 + half_of(ce) + Fraction(5, 10000))
        check(Fraction(f["net"]) == want, "a documented split doubles the share count from its ex-date")
    print(f"E08 logger checks: {N} passed")


if __name__ == "__main__":
    main()
