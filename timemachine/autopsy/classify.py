"""Text rules for the decision autopsy. Categories fixed in categories.md (2026-11-25 21:27 UTC).
Imported by autopsy.py. No outcome is read here."""
import re

BUY_GROUPS = [
    ("B_HEADLINE", [r"^\s*headline", r"^\s*catalyst", r"^\s*re-entering .* as .* (merger|completed)", r"^\s*buy the hold above .* after the .*headline",
                    r"^\s*(ether|eth) products gained", r"^\s*headlines? '", r"^\s*flows-led", r"supply is leaving exchanges", r"^\s*post-fomc", r"^\s*trigger: "]),
    ("B_REVERSAL", [r"flush", r"capitulat", r"v-reversal", r"\bv-shaped", r"\bsweep", r"\bswept", r"hammer", r"\brebound", r"false breakdown",
                    r"washout", r"\bspring\b", r"\breversal\b", r"bounce off", r"bouncing off", r"recover(ed|y)"]),
    ("B_SUPPORT", [r"support", r"range[- ]low", r"range floor", r"\bfloor\b", r"double[- ]bottom", r"double low", r"held twice", r"two tests",
                   r"twice-tested", r"tests? of", r"lower third", r"lower part of the range", r"bottom of the range", r"double-defended"]),
    ("B_PULLBACK", [r"retest", r"pullback", r"pulled back", r"held (its|the) first pullback", r"consolidat", r"\bbase\b", r"shelf", r"coil",
                    r"bull flag", r"\bflag\b", r"higher-low retest", r"hold above", r"holding above", r"held above", r"buy the consolidation"]),
    ("B_BREAKOUT", [r"breakout", r"break(s|ing)? (out|above|up)", r"broke (out|above|up|through)", r"new high", r"higher highs?", r"continuation",
                    r"pressing", r"cleared", r"closed above", r"above .* (high|ceiling|resistance)", r"two-week high", r"2-week high", r"uptrend",
                    r"green hourly", r"momentum"]),
    ("B_RELSTRENGTH", [r"relative strength", r"\bleader\b", r"strongest", r"outperform", r"leads? the", r"laggard"]),
    ("B_INDICATOR", [r"\bsmas?\b", r"\bsma\d", r"\bema\b", r"\bma ?\d", r"\bma5", r"\brsi\b", r"moving average", r"hourly mas", r"20-day average", r"50-week"]),
    ("B_OTHER", [r"top(ping)? up", r"under-filled", r"^\s*adding"]),
]

def _groups(text, groups):
    t = (text or "").lower()
    hit = []
    for name, pats in groups:
        if any(re.search(p, t) for p in pats):
            hit.append(name)
    return hit

def classify_buy(reason, thesis):
    """Return (label or None, how). None means hand label needed."""
    h = _groups(reason, BUY_GROUPS)
    if len(h) == 1:
        return h[0], "rule"
    if len(h) == 0:
        h2 = _groups(thesis, BUY_GROUPS)
        if len(h2) == 1:
            return h2[0], "rule_thesis"
    return None, "hand"

SELL_GROUPS = [
    ("S_TIME", [r"time limit", r"one day left", r"final day", r"out of reach in the time left", r"time stop", r"session end"]),
    ("S_EARLY_GAIN", [r"taking profit", r"take (a quarter|half|profit)", r"bank the", r"take the small gain", r"booking"]),
    ("S_ROTATE", [r"laggard", r"rotat", r"concentrat", r"better to own"]),
    ("S_HEADLINE", [r"headline", r"fed\b", r"macro", r"\d{4}-\d\d-\d\dt\d\d", r"caveat", r"etf"]),
    ("S_VIEW_PRICE", [r"broken", r"broke", r"invalid", r"thesis", r"premise", r"momentum (gone|dead)", r"failed", r"lower highs", r"rejection"]),
]

def classify_sell(reason):
    r = reason or ""
    if r.startswith("Exit set in pick"):
        if "stop price" in r: return "S_STOP", "rule"
        if "target price" in r: return "S_TARGET", "rule"
        if "exit time" in r: return "S_TIME", "rule"
        return None, "hand"
    h = _groups(r, SELL_GROUPS)
    if len(h) == 1:
        return h[0], "rule"
    return None, "hand"

DIAL_GROUPS = [
    ("D_STRETCHED", [r"stretched", r"bank part", r"squeeze fuel", r"extended", r"overbought"]),
    ("D_MACRO_EVENT", [r"\bfed\b", r"fomc", r"rate[- ]hike", r"tariff", r"\biran\b", r"cpi\b", r"payroll", r"yields?", r"dollar", r"war\b",
                       r"geopolit", r"senate", r"clarity", r"macro", r"inflation", r"jobs", r"ceasefire", r"boj\b", r"japan", r"pce\b", r"powell", r"warsh"]),
    ("D_FLOWS_NEWS", [r"etf", r"outflow", r"inflow", r"selling more than", r"strategy", r"riot", r"miner", r"whale", r"liquidation", r"mt\.? gox",
                      r"treasury sales", r"headline"]),
    ("D_PRICE_BREAK", [r"broke", r"break", r"below", r"under ", r"lower low", r"lower close", r"lowest", r"failed", r"fell", r"slide", r"drop",
                       r"plunge", r"new .*low", r"down \d", r"lost"]),
    ("D_PRICE_RECOVER", [r"reclaim", r"rebound", r"recover", r"rall(y|ied)", r"bounce", r"up day", r"higher", r"advanced", r"rose", r"green",
                         r"back above", r"breakout", r"momentum", r"firm"]),
]

def classify_dial(why):
    h = _groups(why, DIAL_GROUPS)
    if len(h) == 1:
        return h[0], "rule"
    # price words plus exactly one of flows or macro: the price words are the trigger in this card's texts only when nothing else is named.
    return None, "hand"

BASKET_GROUPS = [
    ("K_BAD_NEWS", [r"downgrad", r"\bmiss", r"lawsuit", r"probe", r"investigat", r"security", r"sale\b", r"sold", r"loss of", r"contract loss",
                    r"delayed", r"cut (its|the) (guidance|outlook)", r"started at hold", r"warning", r"recall", r"sued", r"\bfine\b", r"injunction", r"target cuts", r"price-target cuts"]),
    ("K_WEAKNESS", [r"fallen", r"declin", r"trend broke", r"broken", r"turned negative", r"stall", r"down about", r"faded", r"weak", r"lower",
                    r"lagg", r"red\b", r"slid", r"slide", r"drawdown", r"-\d", r"\bdown\b", r"negative", r"reversed", r"rolled over", r"bleed", r"drift"]),
    ("K_DIVERSIFY", [r"exposure", r"defensive", r"diversif", r"complement", r"balance", r"hedge"]),
    ("K_NEWS", [r"upgrad", r"target", r"beat", r"raised", r"approv", r"phase 3", r"deal", r"acqui", r"contract", r"partnership", r"launch",
                r"buyback", r"results", r"earnings", r"guidance", r"fda", r"agreement", r"order", r"talks", r"expansion", r"initiation", r"discovery",
                r"licen[cs]e", r"record", r"stress", r"outlook", r"settlement", r"win\b"]),
    ("K_MOMENTUM", [r"\+\d", r"momentum", r"uptrend", r"trend", r"strongest", r"riser", r"gains? (across|over)", r"positive", r"relative strength",
                    r"7d", r"30d", r"91d", r"rising", r"breakout", r"high"]),
]

def classify_basket(text, kind):
    h = _groups(text, BASKET_GROUPS)
    if kind == "added" or kind == "kept":
        h = [x for x in h if x not in ("K_BAD_NEWS", "K_WEAKNESS")] or h
        s = set(h)
        if s == {"K_MOMENTUM", "K_NEWS"} or s == {"K_MOMENTUM", "K_NEWS", "K_DIVERSIFY"}:
            return "K_MOM_NEWS", "rule"
    else:
        # added 2026-11-25 21:32 UTC after the first rule check: a dropped stock whose text only names trailing returns is a falling-price drop.
        hb = [x for x in h if x in ("K_BAD_NEWS", "K_WEAKNESS")]
        h = hb if hb else (["K_WEAKNESS"] if "K_MOMENTUM" in h else h)
    if len(h) == 1:
        return h[0], "rule"
    return None, "hand"

def _quoted_title(text):
    """A quoted string of 20+ characters with at least three capitalised words, as headlines are written. Fixed 2026-11-25 21:40 UTC: the first
    version also matched text between two apostrophes (Bitcoin's ... it's) and flagged price-only buys in TM01."""
    for q in re.findall(r"['\"\u201c\u2018]([^'\"\u201d\u2019]{20,})['\"\u201d\u2019]", text or ""):
        if sum(1 for w in q.split() if w[:1].isupper()) >= 3:
            return True
    return False

def flags_buy(reason, thesis):
    t = ((reason or "") + " " + (thesis or "")).lower()
    return dict(
        states_target=bool(re.search(r"target|aim(ing)? (for|at)?|toward \d|objective|room to", t)),
        states_stop_in_text=bool(re.search(r"stop|invalidat|exit if|failure", t)),
        cites_headline=bool(re.search(r"headline|\d{4}-\d\d-\d\dt\d\d", t)) or _quoted_title(reason) or _quoted_title(thesis),
        size_or_confidence=bool(re.search(r"small|starter|half[- ]size|half the|modest|two-thirds|conviction|confiden|moderate|reduce size|low end", t)),
    )
