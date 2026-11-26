"""Plan 23 tests. Invented prospectus rows, breakpoints and bars only, in temporary folders."""
import subprocess, csv, datetime as dt, gzip, json, math, os, shutil, tempfile, unittest

import common_23 as C
import fetch_23 as F
import score_23 as S
import report_23 as R

P = C.load_config()


def bdays(a, n):
    d, out = dt.date.fromisoformat(a), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def bar(d, c, o=None, v=100, h=None, l=None):
    o = c if o is None else o
    return dict(d=d, o=o, h=h if h is not None else max(o, c) + 1, l=l if l is not None else min(o, c) - 1, c=c, v=v)


def alp(b):
    return dict(t=b["d"] + "T05:00:00Z", o=b["o"], h=b["h"], l=b["l"], c=b["c"], v=b["v"])


def ipo(acc, cik, tk, d, value, us="yes", price="20", filed=None, check="verified"):
    return dict(accession=acc, cik=cik, company=f"Co {acc}", ticker=tk, pricing_date=d, date_filed=filed or d,
                pricing_date_how="prospectus_date", offer_price=price, standin_value_usd=str(value), us_screen_guess=us,
                excluded="", shares_out_after="1000", shares_out_after_classes="common", shares_check=check)


class Config(unittest.TestCase):
    def test_config_ok_and_strict(self):
        C.validate(P)
        self.assertEqual((P["judged_bps"], P["shown_bps"], P["judged_ratio_min"]), (10, 25, 1.5))
        with self.assertRaises(C.Refused):
            C.validate(P | {"extra": 1})
        for bad in ({"bar_end": "2026-11-25"}, {"bar_adjustment": "all"}, {"shown_bps": 5}, {"exit_session": 9},
                    {"no_auction_bps": 20}, {"prior_bar_gap_bdays": 3}):
            with self.subTest(bad=bad), self.assertRaises(C.Refused):
                C.validate(P | bad)


class Events(unittest.TestCase):
    BPS = [("2017-03-06", 1000.0), ("2017-06-05", 2000.0)]

    def test_breakpoint_on_or_before(self):
        self.assertEqual(C.breakpoint_on(self.BPS, "2017-06-05"), ("2017-06-05", 2000.0))
        self.assertEqual(C.breakpoint_on(self.BPS, "2017-06-04"), ("2017-03-06", 1000.0))
        with self.assertRaises(C.Refused):
            C.breakpoint_on(self.BPS, "2017-03-05")

    def test_groups_and_filters(self):
        rows = [ipo("a", "1", "AAA", "2017-03-20", 1500), ipo("b", "2", "BBB", "2017-03-21", 1499),
                ipo("c", "3", "CCC", "2017-03-22", 1000), ipo("d", "4", "DDD", "2017-03-23", 670), ipo("d2", "41", "DDE", "2017-03-23", 669),
                ipo("e", "5", "EEE", "2017-03-17", 9000), ipo("f", "6", "FFF", "2026-10-24", 9000),
                ipo("g", "7", "GGG", "2017-04-03", 9000, us="check"), ipo("h", "8", "HHH", "2017-04-04", ""),
                ipo("i", "9", "III", "2017-06-05", 2999), ipo("j", "10", "JJJ", "2017-06-05", 3000),
                ipo("k", "11", "KKK", "2026-10-23", 2_000_000_000_000)]
        ev = {e["accession"]: e for e in C.select_events(rows, self.BPS, P)}
        self.assertEqual(ev["a"]["group"], "judged")
        self.assertEqual(ev["b"]["group"], "band_1_0_to_1_5")
        self.assertEqual(ev["c"]["group"], "band_1_0_to_1_5")
        self.assertEqual(ev["d"]["group"], "near_0_67_to_1_0")
        self.assertEqual(ev["i"]["group"], "band_1_0_to_1_5")     # the June chart is dated that day: it applies
        self.assertEqual(ev["j"]["group"], "judged")
        self.assertTrue(ev["k"]["mega"])
        self.assertFalse(ev["a"]["mega"])
        for gone in ("e", "f", "g", "h", "d2"):
            self.assertNotIn(gone, ev)

    def test_unverified_share_total_is_listed_and_left_out(self):
        rows = [ipo("a", "1", "AAA", "2017-03-20", 2000), ipo("b", "2", "BBB", "2017-03-20", 2000, check="unverified:no_statement"),
                ipo("c", "3", "CCC", "2017-03-20", 2000, check="verified_manual"), ipo("d", "4", "DDD", "2017-03-20", 2000, check="")]
        ev = {e["accession"]: e for e in C.select_events(rows, self.BPS, P)}
        self.assertEqual([ev[k]["status"] for k in "abcd"], ["", "shares_unverified", "", "shares_unverified"])
        self.assertEqual(ev["b"]["group"], "judged")                   # listed with its group, not silently dropped


class Security(unittest.TestCase):
    COMMON = "Filed Pursuant to Rule 424(b)(4) 20,000,000 Shares Co Inc. Class A Common Stock This is an initial public offering of shares of Class A common stock."
    PREF = "Filed Pursuant to Rule 424(b)(4) 18,000,000 Shares Co Inc. 6.250% Series A Mandatory Convertible Preferred Stock We are offering 18,000,000 shares of our 6.250% Series A Mandatory Convertible Preferred Stock."
    ADS = "10,000,000 American Depositary Shares Co Ltd. Representing 10,000,000 Ordinary Shares This is the initial public offering of American Depositary Shares."
    UNITS = "25,000,000 Units Co Corp. This is an initial public offering of units. Each unit consists of one share of Class A common stock."
    CONCURRENT = COMMON + " Concurrently, we are offering shares of our Mandatory Convertible Preferred Stock by a separate prospectus."

    def test_classes(self):
        self.assertEqual(C.classify_security(self.COMMON), "common")
        self.assertEqual(C.classify_security(self.CONCURRENT), "common")     # the Avantor common prospectus
        self.assertEqual(C.classify_security(self.PREF), "not_common")
        self.assertEqual(C.classify_security(self.ADS), "ads")
        self.assertEqual(C.classify_security(self.UNITS), "not_common")
        self.assertEqual(C.classify_security("TABLE OF CONTENTS Risk Factors 12"), "unknown")
        self.assertEqual(C.classify_security("TABLE OF CONTENTS offer to sell shares of common stock only where"), "common")

    def test_selection_marks_and_refuses(self):
        bps = [("2017-03-06", 1000.0)]
        rows = [ipo("a", "1", "AAA", "2017-03-20", 2000), ipo("b", "1", "AAA", "2017-03-20", 1600)]
        ev = {e["accession"]: e for e in C.select_events(rows, bps, P, security={"a": "common", "b": "not_common"})}
        self.assertEqual((ev["a"]["status"], ev["a"]["security"]), ("", "common"))
        self.assertEqual((ev["b"]["status"], ev["b"]["security"]), ("not_common_security", "not_common"))
        with self.assertRaisesRegex(C.Refused, "P23_SECURITY_UNKNOWN"):
            C.select_events(rows, bps, P, security={"a": "common"})


class Dates(unittest.TestCase):
    def setUp(self):
        self.s = bdays("2020-01-01", 60)

    def ev(self, acc, cik, tk, filed, status=""):
        return dict(accession=acc, cik=cik, ticker=tk, pricing_date=filed, filing_date=filed, group="judged", status=status)

    def test_resolution_on_the_filing_date(self):
        s = self.s
        f = s[20]                                     # the 424B4 filing date
        cases = {
            "day1_after": (self.ev("day1_after", "1", "A", f), s[21:40]),         # usual: filed the evening of pricing
            "same_day": (self.ev("same_day", "2", "B", f), s[20:40]),
            "day2_filing": (self.ev("day2_filing", "3", "C", f), s[19:40]),       # filed on day 2: first bar is F-1
            "day3_filing": (self.ev("day3_filing", "4", "D", f), s[17:40]),       # F-3 is inside the window
            "plus3": (self.ev("plus3", "5", "E", f), s[23:40]),
            "plus4": (self.ev("plus4", "6", "F", f), s[24:40]),                   # outside the window
            "minus4": (self.ev("minus4", "7", "G", f), s[16:40]),                 # F-4: between the window and the cut
            "minus5": (self.ev("minus5", "8", "H", f), [s[15]] + s[21:40]),       # F-5 is not "more than 5" before
            "prior": (self.ev("prior", "9", "I", f), [s[14]] + s[21:40]),         # F-6: a reused ticker
            "none": (self.ev("none", "10", "J", f), []),
            "dup_cik": (self.ev("dup_cik", "1", "Z", f), s[21:40]),
            "dup_tk": (self.ev("dup_tk", "11", "A", f), s[21:40]),
            "refuse": (self.ev("refuse", "12", "K", f), [s[21], s[30]]),
            "no_tk": (self.ev("no_tk", "13", "", f), s[21:40]),
            "entry_flat": (self.ev("entry_flat", "14", "L", f), s[21:40], set(s[22:40])),
            "exit_flat": (self.ev("exit_flat", "15", "M", f), s[21:40], {s[21]} | set(s[29:40])),
            "exit_late_real": (self.ev("exit_late_real", "16", "N", f), s[21:40], {s[21], s[28]}),
            "preset": (self.ev("preset", "17", "O", f, status="shares_unverified"), s[21:40]),
        }
        evs = [v[0] for v in cases.values()]
        dates = {k: (v[1], v[2] if len(v) > 2 else set(v[1])) for k, v in cases.items()}
        out = {e["accession"]: e for e in C.resolve_dates(evs, dates, s, P)}
        st = {k: out[k]["status"] for k in out}
        self.assertEqual(st, dict(day1_after="ok", same_day="ok", day2_filing="ok", day3_filing="ok", plus3="ok",
                                  plus4="late_first_bar", minus4="bars_before_window", minus5="bars_before_window",
                                  prior="prior_bars", none="no_bar", dup_cik="duplicate", dup_tk="duplicate",
                                  refuse="refused_no_exit_bar", no_tk="no_ticker", entry_flat="entry_not_real_bar",
                                  exit_flat="refused_no_exit_bar", exit_late_real="ok", preset="shares_unverified"))
        self.assertEqual(out["day1_after"]["first_trade_date"], s[21])
        self.assertEqual(out["day2_filing"]["first_trade_date"], s[19])
        self.assertEqual(out["day3_filing"]["first_trade_date"], s[17])
        self.assertEqual(out["same_day"]["first_trade_date"], s[20])

    def test_filing_on_a_holiday(self):
        # A filing on a day with no session (Good Friday): the window counts sessions strictly before and after it.
        s = [d for d in self.s if d != self.s[20]]
        hol = self.s[20]
        ev = self.ev("h", "1", "A", hol)
        out = C.resolve_dates([ev], {"h": (self.s[19:40], set(self.s[19:40]))}, s, P)[0]
        self.assertEqual((out["status"], out["first_trade_date"]), ("ok", self.s[19]))
        self.assertEqual(C.around(s, hol, 3), (self.s[17], self.s[23]))


class Trades(unittest.TestCase):
    def setUp(self):
        self.s = bdays("2021-03-01", 40)
        self.spy = {d: bar(d, 100 + i) for i, d in enumerate(self.s)}

    def ev(self, first, **kw):
        return dict(dict(accession="x", group="judged", pricing_date=self.s[0], first_trade_date=first,
                         offer_price="100", mega=False), **kw)

    def test_clean(self):
        s = self.s
        bars = [bar(s[0], 10), bar(s[1], 11, v=0)] + [dict(d=s[i], o=5, h=5, l=5, c=5, v=9) for i in range(2, 7)] + \
               [dict(d=s[i], o=6, h=6, l=6, c=6, v=9) for i in range(7, 11)]
        g = C.clean(bars, P["flat_run"])
        self.assertEqual(sorted(g), [s[0]] + s[7:11])

    def test_real_dates_respect_bar_end(self):
        # A flat run that crosses bar_end: bars after bar_end are cut before the scan, as the scorer cuts them.
        s = self.s
        raw = json.dumps([alp(bar(s[0], 10))] + [alp(dict(d=s[i], o=5, h=5, l=5, c=5, v=9)) for i in range(1, 6)]).encode()
        dates, real = C.real_dates_from_json(raw, P["flat_run"], s[3])
        self.assertEqual(dates, s[0:4])
        self.assertEqual(real, set(s[0:4]))                 # only three flat bars remain: not a flat run
        dates, real = C.real_dates_from_json(raw, P["flat_run"], s[10])
        self.assertEqual(real, {s[0]})

    def test_exit_rules_and_costs(self):
        s = self.s
        first = s[1]
        full = [bar(s[1 + k], 100 + 2 * k, o=99 + 2 * k) for k in range(8)]
        t = C.trade(self.ev(first), full, self.spy, s, P)
        self.assertEqual((t["exit_date"], t["exit_how"]), (s[5], "fifth_session"))
        self.assertAlmostEqual(t["gross"], 108 / 100 - 1)
        self.assertAlmostEqual(t["net_judged"], 0.08 - 0.001 * (1 + 1.08))
        self.assertAlmostEqual(t["net_shown"], 0.08 - 0.0025 * (1 + 1.08))
        self.assertAlmostEqual(t["net_no_auction"], 0.08 - 0.005 * (1 + 1.08))
        self.assertAlmostEqual(t["spy"], self.spy[s[5]]["c"] / self.spy[s[1]]["c"] - 1)
        self.assertAlmostEqual(t["excess_judged"], t["net_judged"] - t["spy"])
        self.assertAlmostEqual(t["net_second_open"], 108 / 101 - 1 - 0.001 * (1 + 108 / 101))
        self.assertEqual(t["first_close_vs_offer"], "at_or_above")
        no5 = [b for b in full if b["d"] != s[5]]
        t = C.trade(self.ev(first), no5, self.spy, s, P)
        self.assertEqual((t["exit_date"], t["exit_how"]), (s[6], "later_inside_window"))
        only4 = [b for b in full if b["d"] <= s[4]]
        t = C.trade(self.ev(first), only4, self.spy, s, P)
        self.assertEqual((t["exit_date"], t["exit_how"]), (s[4], "last_close_before"))
        late = [full[0], bar(s[9], 1)]            # session 9 is outside the eight-session window
        with self.assertRaisesRegex(C.Refused, "P23_NO_EXIT_AFTER_FREEZE"):     # the freeze refuses these first
            C.trade(self.ev(first), late, self.spy, s, P)
        zero = [dict(full[0], v=0)] + full[1:]
        with self.assertRaisesRegex(C.Refused, "P23_ENTRY_NOT_REAL_AFTER_FREEZE"):  # the freeze leaves these out first
            C.trade(self.ev(first), zero, self.spy, s, P)
        below = C.trade(self.ev(first, offer_price="100.5"), full, self.spy, s, P)
        self.assertEqual(below["first_close_vs_offer"], "below")
        with self.assertRaises(C.Refused):
            C.trade(self.ev(first), full, {}, s, P)


def tr(x, year="2020", pd="2020-05-01", ex=None):
    return dict(net_judged=x, excess_judged=x if ex is None else ex, year=year, pricing_date=pd)


class Marks(unittest.TestCase):
    def test_all_pass(self):
        ts = [tr(0.02 + 0.01 * ((i % 5) - 2), year=str(2017 + i % 8), pd=f"{2017 + i % 8}-05-01") for i in range(40)]
        j = C.judge(ts, P)
        self.assertTrue(j["passed"], j)

    def test_each_mark_can_fail(self):
        base = [tr(0.02 + 0.01 * ((i % 5) - 2), year=str(2017 + i % 8), pd=f"{2017 + i % 8}-05-01") for i in range(40)]
        self.assertFalse(C.judge(base[:29], P)["marks"]["n_trades"])
        skew = [tr(-0.001, year=str(2017 + i % 8), pd=f"{2017 + i % 8}-05-01") for i in range(37)] + \
               [tr(1.0, year="2024", pd="2024-05-01")] * 3
        j = C.judge(skew, P)["marks"]
        self.assertTrue(j["mean_above_zero"])
        self.assertFalse(j["mean_without_best"])
        self.assertFalse(j["median_above_zero"])
        old = [dict(t, pricing_date="2022-12-31", year="2022") for t in base]
        self.assertFalse(C.judge(old, P)["marks"]["recent_mean"])
        hedge = [dict(t, excess_judged=-0.01) for t in base]
        self.assertFalse(C.judge(hedge, P)["marks"]["excess_vs_spy"])
        flat = [tr(0.01)] * 40
        self.assertFalse(C.judge(flat, P)["marks"]["t_stat"])          # zero spread: t undefined, not a pass

    def test_year_share(self):
        # Five counted years, three positive = 60% passes; a year with two trades is not counted.
        ts = []
        for y, m in (("2017", 1), ("2018", 1), ("2019", 1), ("2020", -1), ("2021", -1)):
            ts += [tr(0.05 * m + 0.001 * k, year=y, pd=f"{y}-05-01") for k in range(3)]
        ts += [tr(-0.5, year="2022", pd="2022-05-01")] * 2
        f = C.judge(ts, P)["figures"]
        self.assertEqual(f["years_counted"], ["2017", "2018", "2019", "2020", "2021"])
        self.assertAlmostEqual(f["year_share_pct"], 60.0)
        self.assertTrue(C.judge(ts, P)["marks"]["year_share"])


class OneShot(unittest.TestCase):
    """Fetch-free pipeline in a temporary RUN: select, freeze on dates, score once, refuse a second time."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src, self.run = os.path.join(self.tmp, "src"), os.path.join(self.tmp, "run")
        os.makedirs(self.src); os.makedirs(os.path.join(self.run, "bars"))
        self.old = (F.RUN, F.SRC)
        F.RUN, F.SRC = self.run, self.src
        s = bdays("2022-12-12", 100)
        self.s = s
        with open(os.path.join(self.src, "breakpoints.csv"), "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["ranking_date", "bp98_usd", "bp85_usd", "source", "how"])
            w.writerow(["2022-12-05", "1000", "9000", "x", "y"])
        rows = [ipo(f"e{i}", str(i), f"T{i}", s[15 + 2 * i], 2000) for i in range(30)]
        with open(os.path.join(self.src, "ipos.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        self.covers({f"e{i}": Security.COMMON for i in range(30)})
        json.dump([alp(bar(d, 100 + i)) for i, d in enumerate(s)], open(os.path.join(self.run, "bars", "SPY.json"), "w"))
        for i in range(30):
            first = s[15 + 2 * i + 1]
            k0 = s.index(first)
            b = [alp(bar(s[k0 + k], 20 + k + 0.01 * i)) for k in range(8)]
            json.dump(b, open(os.path.join(self.run, "bars", f"e{i}.json"), "w"))

    def covers(self, m):
        os.makedirs(os.path.join(self.src, "src"), exist_ok=True)
        with gzip.open(os.path.join(self.src, "src", "snips.jsonl.gz"), "wt") as fh:
            for a, c in m.items():
                fh.write(json.dumps({"accession": a, "_cover": c, "_snips": []}) + "\n")

    def tearDown(self):
        F.RUN, F.SRC = self.old
        shutil.rmtree(self.tmp)

    def freeze(self):
        F.cmd_events(P)
        F.cmd_freeze(P)
        return C.sha256_file(os.path.join(self.run, "freeze.json"))

    def test_once_and_refusals(self):
        sha = self.freeze()
        with self.assertRaises(C.Refused):
            S.run("0" * 64)
        self.assertFalse(os.path.exists(os.path.join(self.run, S.LOCK)))
        S.run(sha)
        res = json.load(open(os.path.join(self.run, S.RESULT)))
        self.assertEqual(res["judgment"]["figures"]["n"], 30)
        self.assertTrue(res["judgment"]["marks"]["n_trades"])
        with self.assertRaisesRegex(C.Refused, "P23_ALREADY_USED"):
            S.run(sha)
        page = R.page(res, res["parameters"])
        self.assertIn("| trades | 30 |", page)

    def test_changed_bar_refuses_before_lock(self):
        sha = self.freeze()
        f = os.path.join(self.run, "bars", "e3.json")
        b = json.load(open(f)); b[2]["c"] += 1; json.dump(b, open(f, "w"))
        with self.assertRaisesRegex(C.Refused, "P23_BARS_CHANGED"):
            S.run(sha)
        self.assertFalse(os.path.exists(os.path.join(self.run, S.LOCK)))

    def test_missing_exit_window_refuses_freeze(self):
        f = os.path.join(self.run, "bars", "e5.json")
        json.dump(json.load(open(f))[:1], open(f, "w"))
        with self.assertRaises(SystemExit) as cm:
            self.freeze()
        self.assertIn("P23_REFUSED_NO_EXIT_BAR", str(cm.exception))
        self.assertFalse(os.path.exists(os.path.join(self.run, "freeze.json")))

    def test_freeze_reads_no_price_as_a_number(self):
        # Open, high, low and close become distinct words that cannot be used as numbers; volume stays. A freeze that
        # succeeds compared prices for equality at most and computed no return.
        for i in range(30):
            f = os.path.join(self.run, "bars", f"e{i}.json")
            b = json.load(open(f))
            for k, x in enumerate(b):
                x.update(o=f"o{k}", h=f"h{k}", l=f"l{k}", c=f"c{k}")
            json.dump(b, open(f, "w"))
        self.freeze()
        ev = C.parse_events(open(os.path.join(self.run, "events_frozen.csv"), "rb").read())
        self.assertEqual(sum(e["status"] == "ok" for e in ev), 30)

    def test_entry_not_real_left_out_before_lock(self):
        f = os.path.join(self.run, "bars", "e7.json")
        b = json.load(open(f)); b[0]["v"] = 0; json.dump(b, open(f, "w"))
        sha = self.freeze()
        ev = {e["accession"]: e for e in C.parse_events(open(os.path.join(self.run, "events_frozen.csv"), "rb").read())}
        self.assertEqual(ev["e7"]["status"], "entry_not_real_bar")
        S.run(sha)
        res = json.load(open(os.path.join(self.run, S.RESULT)))
        self.assertEqual(res["judgment"]["figures"]["n"], 29)

    def test_flat_exit_window_refuses_freeze(self):
        # Real first bar, then sessions 2 to 8 all one identical bar: no real close, so the freeze refuses.
        f = os.path.join(self.run, "bars", "e9.json")
        b = json.load(open(f))
        for x in b[1:]:
            x.update(o=b[1]["o"], h=b[1]["h"], l=b[1]["l"], c=b[1]["c"])
        json.dump(b, open(f, "w"))
        with self.assertRaises(SystemExit) as cm:
            self.freeze()
        self.assertIn("P23_REFUSED_NO_EXIT_BAR e9", str(cm.exception))
        self.assertFalse(os.path.exists(os.path.join(self.run, "freeze.json")))

    def test_not_common_listed_and_unknown_refuses(self):
        self.covers({**{f"e{i}": Security.COMMON for i in range(30)}, "e4": Security.PREF})
        F.cmd_events(P)
        ev = {e["accession"]: e for e in C.parse_events(open(os.path.join(self.run, "events_selected.csv"), "rb").read())}
        self.assertEqual(ev["e4"]["status"], "not_common_security")
        self.covers({f"e{i}": Security.COMMON for i in range(29)})
        with self.assertRaisesRegex(C.Refused, "P23_SECURITY_UNKNOWN e29"):
            F.cmd_events(P)

    def test_day2_filing_end_to_end(self):
        # e3 priced on s[21] and first traded s[22]; its 424B4 was filed on day 2 (s[23]), and the prospectus date
        # was not read, so pricing_date fell back to the filing date. The bar window on the filing date still finds
        # day 1, and day 1's bar is not taken for a reused ticker.
        s = self.s
        rows = list(csv.DictReader(open(os.path.join(self.src, "ipos.csv"))))
        rows[3].update(date_filed=s[23], pricing_date=s[23], pricing_date_how="filing_date_fallback")
        with open(os.path.join(self.src, "ipos.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        self.freeze()
        ev = {e["accession"]: e for e in C.parse_events(open(os.path.join(self.run, "events_frozen.csv"), "rb").read())}
        self.assertEqual((ev["e3"]["status"], ev["e3"]["first_trade_date"], ev["e3"]["prospectus_date"]), ("ok", s[22], ""))

    def test_changed_covers_refuse_before_lock(self):
        sha = self.freeze()
        self.covers({f"e{i}": Security.COMMON + " " for i in range(30)})
        with self.assertRaisesRegex(C.Refused, "P23_INPUT_CHANGED"):
            S.run(sha)
        self.assertFalse(os.path.exists(os.path.join(self.run, S.LOCK)))


class FetchPlan(unittest.TestCase):
    """Every row is checked before the first network call (gate audit S1)."""

    def row(self, **k):
        e = dict(accession="0001193125-21-000001", ticker="ABCD", filing_date="2021-06-10", status="")
        e.update(k)
        return e

    def test_good_rows_and_skips(self):
        plan = F.fetch_plan([self.row(), self.row(accession="0001193125-21-000002", status="duplicate"),
                             self.row(accession="0001193125-21-000003", ticker="")], P)
        self.assertEqual(plan, [("0001193125-21-000001", "ABCD", "2021-05-11", "2021-07-20", "2021-06-15")])

    def test_any_bad_row_refuses_before_a_request(self):
        for bad in (dict(filing_date="2021-13-01"), dict(filing_date=""), dict(ticker="AB/CD"), dict(ticker="abc"),
                    dict(ticker="ABCDEFG"), dict(filing_date="2026-11-25"), dict(accession="../x")):
            with self.assertRaises(C.Refused) as cm:
                F.fetch_plan([self.row(), self.row(**dict(dict(accession="0001193125-21-000009"), **bad))], P)
            self.assertIn("P23_EVENT_ROW_BAD", str(cm.exception))

    def test_fetch_refuses_without_any_network_call(self):
        calls = []
        old = F.bars
        F.bars = lambda *a: calls.append(a) or []
        tmp = tempfile.TemporaryDirectory()
        try:
            P2 = F.paths(run=tmp.name)
            with open(P2["selected"], "wb") as fh:
                fh.write(C.events_csv_bytes([dict({k: "" for k in C.EVENT_FIELDS}, **self.row(ticker="A B"))]))
            old_paths = F.paths
            F.paths = lambda run=None, src=None: P2
            try:
                with self.assertRaises(C.Refused):
                    F.cmd_fetch(P)
            finally:
                F.paths = old_paths
            self.assertEqual(calls, [])
            self.assertFalse(os.path.exists(P2["bars"]))
        finally:
            F.bars = old
            tmp.cleanup()


class Approval(unittest.TestCase):
    """The gate: collection, freeze and scoring need the lead's approval commit (invented repo, no bars)."""

    def git(self, *a):
        subprocess.run(["git", "-C", self.root, *a], check=True, capture_output=True)

    def head(self):
        return subprocess.run(["git", "-C", self.root, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    def put(self, path, body):
        full = os.path.join(self.root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as fh:
            fh.write(body)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        pins = {}
        for n in C.PINNED_NAMES:
            body = (b"Status FROZEN.\n" if n == C.PLAN_NAME else b"") + n.encode()
            self.put("research_rig/" + n, body)
            pins[n] = C.sha256_bytes(body)
        cfg = b"replay_23_plan:\n  value: {judged_bps: 10}\nother: {value: 1}\n"
        self.put("config/thresholds.yaml", cfg)
        pins[C.CONFIG_PIN] = C.config_block_sha256(cfg)
        self.put("research_rig/PINNED_23.json", json.dumps(pins).encode())
        self.put("research_rig/TRIAL_LEDGER.md", b"| 160 | x | `research_rig/PREREG_23_ipo_fast_track.md` | y |\n")
        self.git("add", "-A"); self.git("commit", "-qm", "freeze")
        self.frozen = self.head()

    def tearDown(self):
        self.tmp.cleanup()

    def approve(self, line=None):
        line = line or f"Approved by the lead: plan 23, one collection and one scored run, freeze commit {self.frozen}."
        self.put(C.APPROVAL, (line + "\n").encode())
        self.git("add", "-A"); self.git("commit", "-qm", "approve")
        return self.head()

    def refuses(self, commit, why):
        with self.assertRaises(C.Refused) as cm:
            C.authorize(commit, root=self.root, config=os.path.join(self.root, "config", "thresholds.yaml"))
        self.assertIn(why, str(cm.exception))

    def test_freeze_commit_alone_refuses(self):
        self.refuses(None, "no approval commit")
        self.refuses(self.frozen, "APPROVAL_23.md")

    def test_approval_passes_and_names_the_freeze(self):
        c = self.approve()
        self.assertEqual(C.authorize(c, root=self.root, config=os.path.join(self.root, "config", "thresholds.yaml")), self.frozen)

    def test_wrong_line_or_head_or_dirty_refuses(self):
        c = self.approve("Approved: plan 23")
        self.refuses(c, "APPROVAL_23.md")
        c = self.approve()
        self.put("research_rig/common_23.py", b"changed")
        self.refuses(c, "tracked files changed")
        self.git("checkout", "-q", "--", "research_rig/common_23.py")
        self.put("x.txt", b"1"); self.git("add", "x.txt"); self.git("commit", "-qm", "later")
        self.refuses(c, "HEAD is not")

    def test_changed_code_or_config_refuses(self):
        self.put("research_rig/score_23.py", b"edited after the freeze")
        c = self.approve()
        self.refuses(c, "pin score_23.py")
        self.setUp()
        self.put("config/thresholds.yaml", b"replay_23_plan:\n  value: {judged_bps: 5}\nother: {value: 1}\n")
        c = self.approve()
        self.refuses(c, "pin " + C.CONFIG_PIN)

    def test_environment_or_other_config_refuses(self):
        c = self.approve()
        for k in ("P23_CONFIG", "P23_PLAN", "P23_RUN", "P23_ALLOW_DRAFT"):
            os.environ[k] = "/tmp/x"
            try:
                self.refuses(c, "environment " + k)
            finally:
                del os.environ[k]
        other = os.path.join(self.root, "elsewhere", "thresholds.yaml")
        os.makedirs(os.path.dirname(other))
        shutil.copy(os.path.join(self.root, "config", "thresholds.yaml"), other)
        with self.assertRaises(C.Refused) as cm:
            C.authorize(c, root=self.root, config=other)
        self.assertIn("config path", str(cm.exception))
        with self.assertRaises(C.Refused) as cm:
            C.authorize(c, root=self.root)                       # the repo's own config is not this root's
        self.assertIn("config path", str(cm.exception))
        self.assertEqual(C.CONFIG, os.path.join(C.ROOT, "config", "thresholds.yaml"))
        self.assertEqual(F.PLAN, C.PLAN_NAME)

    def test_other_config_keys_may_change(self):
        self.put("config/thresholds.yaml", b"replay_23_plan:\n  value: {judged_bps: 10}\nother: {value: 2}\n")
        c = self.approve()
        self.assertEqual(C.authorize(c, root=self.root, config=os.path.join(self.root, "config", "thresholds.yaml")), self.frozen)

if __name__ == "__main__":
    unittest.main()
