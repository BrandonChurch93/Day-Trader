"""Check screen card verdicts, tones, required plain lines, and figures against their source pages."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replay_cards as RC


def test_cards():
    c = {x["id"]: x for x in RC.cards("GH/")}
    assert (c["replay48"]["verdict"], c["replay48"]["tone"]) == ("Passed, 7 of 7 marks", "mixed")
    assert (c["replay52"]["verdict"], c["replay52"]["tone"]) == ("Did not pass, 0 of 6 marks", "fail")
    assert (c["replay53"]["verdict"], c["replay53"]["tone"]) == ("Did not pass, 5 of 7 marks", "fail")
    assert (c["replay60"]["verdict"], c["replay60"]["tone"]) == ("Did not pass, 6 of 7 marks", "fail")
    assert (c["replay62"]["verdict"], c["replay62"]["tone"]) == ("Did not pass, 1 of 5 marks", "fail")
    assert "MUI" in c["replay48"]["summary"] and "pass stands" in c["replay48"]["summary"]
    s53 = c["replay53"]["summary"]
    assert "fifth January session is shown only" in s53 and "cannot count" in s53 and "+0.802" in s53
    s60 = c["replay60"]["summary"]
    assert "Missed: Paired IWM." in s60 and "339 matched pairs from 443 filing events" in s60
    assert "refused 24 events" in s60 and "shown only and cannot count" in s60
    rows60 = dict(c["replay60"]["numbers"])
    assert rows60["Stock minus SPY, shown only"] == "+1.06% on 281 pairs"
    assert rows60["Settled sleeves on $500, shown only"] == "$422.82 net, +84.56% of starting cash"
    assert c["replay60"]["links"][0] == ["Replay 60", "GH/" + RC.P60]
    s62 = c["replay62"]["summary"]
    assert "316 matched pairs from 443 filing events" in s62 and "cannot count" in s62 and "The row closes." in s62
    rows62 = dict(c["replay62"]["numbers"])
    assert rows62["Raw paired mean: Above zero"] == "−0.0607 pp, not met"
    assert rows62["Earlier entry, shown only"] == "+0.2915 pp on 316 pairs"
    assert rows62["Vendor exact match, shown only"] == "−0.0375 pp on 230 pairs"
    assert rows62["Vendor Class A, shown only"] == "−0.1229 pp on 86 pairs"
    assert c["replay62"]["links"][0] == ["Replay 62", "GH/" + RC.P62]
    assert (c["replay22"]["title"], c["replay22"]["verdict"], c["replay22"]["tone"]) == ("Fable rule A, no AI", "Did not pass, 1 of 5 marks", "fail")
    s22 = c["replay22"]["summary"]
    assert "Missed: Daily Sharpe; Largest fall; Random twins; Positive years." in s22 and "57% of random-entry twins" in s22
    assert "+275.40% against +274.25%" in s22 and "cannot count toward a mark" in s22 and "The row closes." in s22
    rows22 = dict(c["replay22"]["numbers"])
    assert rows22["Beats holding: End value above holding the same list in equal weights, same costs"] == "+275.40% against +274.25%, met"
    assert rows22["Largest fall: 40% or less"] == "79.40%, not met"
    assert rows22["Without the best 3 trades, shown only"] == "\u221211.14%"
    assert c["replay22"]["links"][0] == ["Replay 22", "GH/" + RC.P22]
    assert (c["replay65"]["title"], c["replay65"]["verdict"], c["replay65"]["tone"]) == ("Stock-bond rebalancing", "Did not pass, 3 of 5 marks", "fail")
    s65 = c["replay65"]["summary"]
    assert "Missed: Evidence; Trim." in s65 and "not shown, not refuted" in s65 and "cannot count toward a mark" in s65
    assert "2,614 sessions, mean +1.01 bp a session net, t 1.04" in s65 and "the row closes." in s65
    rows65 = dict(c["replay65"]["numbers"])
    assert rows65["Evidence: t at least 2, clustered by calendar week of the exit session"] == "1.04, not met"
    assert rows65["Trim: Mean above zero after dropping the best 1% of sessions, rounded up"] == "\u22121.76 bp; dropped 27, not met"
    assert rows65["Net yearly Sharpe"] == "0.35"
    assert rows65["Without March 2020, shown only"] == "\u22120.07 bp a session"
    assert rows65["Cash account a $500 account could hold, shown only"] == "\u22120.73 bp a session"
    assert c["replay65"]["links"][0] == ["Replay 65", "GH/" + RC.P65]
    pages = {"replay48": RC.read(RC.P48) + RC.read(RC.R48), "replay52": RC.read(RC.P52),
             "replay53": RC.read(RC.P53), "replay60": RC.read(RC.P60), "replay62": RC.read(RC.P62), "replay22": RC.read(RC.P22), "replay65": RC.read(RC.P65)}
    for k, card in c.items():
        shown = " ".join([card["summary"]] + [v for _, v in card["numbers"]]).replace("\u2212", "-")
        for fig in re.findall(r"[+-]?\$?\d[\d,]*\.\d+%?", shown):
            assert fig in pages[k] or fig.lstrip("+-") in pages[k], (k, fig)
    for card in c.values():
        text = card["summary"] + card["basis"] + "".join(a + b for a, b in card["numbers"])
        assert "\u2014" not in text and "!" not in text


if __name__ == "__main__":
    test_cards(); print("replay cards ok")
