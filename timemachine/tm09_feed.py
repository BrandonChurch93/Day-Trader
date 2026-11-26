"""Amended repeat marks and literal figure checks. Raw titles stay in memory."""
from fractions import Fraction
import re
from unicodedata import normalize


def normalized(title):
    return normalize('NFKC', title).casefold()


def annotate(ordered_by_wake, feed):
    """Inputs already use the fixture's strict signed ordering; state resets per call/week."""
    prior = {}
    token_rx = re.compile(feed['title_token_pattern'])
    figure_rx = re.compile(feed['figure_fingerprint_pattern'])
    min_shared = feed['repeat_min_shared_tokens']
    threshold = Fraction(str(feed['repeat_jaccard_min']))
    result = {}
    for wake, items in ordered_by_wake:
        result[wake] = pairs = []
        for item in items:
            text = normalized(item['headline'])
            tokens = tuple(token_rx.findall(text))
            fingerprint = tuple(figure_rx.findall(text))
            unique = set(tokens)
            for symbol in item['symbols']:
                history = prior.setdefault((symbol, fingerprint), [])
                repeat = False
                for earlier, earlier_set in history:
                    shared = len(unique & earlier_set)
                    if tokens and (tokens == earlier or (
                            shared >= min_shared and Fraction(shared, len(unique | earlier_set)) >= threshold)):
                        repeat = True
                        break
                history.append((tokens, unique))
                pairs.append(dict(headline=item['headline'], source_time=item['source_time'], symbol=symbol, repeat=repeat))
    return result


NUM = re.compile(r'(?<!\d)(?:[+$€£¥₹\-−][ \t]*){0,2}\d+(?:[.,:/–—\-]\d+)*'
                 r'(?:[ \t]?[%‰]|(?:st|nd|rd|th)\b)?')
UNITS = re.compile(r'(?:\s+(?:hundred(?:s)?|thousand(?:s)?|million(?:s)?|billion(?:s)?|trillion(?:s)?|'
                   r'percentage points?|percent|basis points?|points?|shares?|dollars?|euros?|pounds?|yen|rupees?|'
                   r'years?|months?|weeks?|days?|hours?|minutes?|seconds?|barrels?|tonnes?|tons?|'
                   r'kilograms?|kilomet(?:er|re)s?|miles?|gallons?|units?|bps|USD|EUR|GBP|JPY|INR)\b)+', re.I)
MONTH = r'January|February|March|April|May|June|July|August|September|October|November|December'
DATES = re.compile(rf'\b(?:(?:{MONTH})\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,\s*\d{{4}})?|'
                   rf'\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTH})(?:\s+\d{{4}})?)\b', re.I)
WORDS = re.compile(r'\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|'
                   r'fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|'
                   r'seventy|eighty|ninety|hundreds?|thousands?|millions?|billions?|trillions?|first|second|'
                   r'third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|half|quarter|dozens?)\b', re.I)
JOIN = re.compile(r'\s*(?:[–—-]|to|through)\s*', re.I)


def figure_check(title, figures):
    """Require ordered, exact fragments and coverage of mechanically decidable spans.

    Return False for a decided check, True for semantic ambiguity, or raise for a definite error.
    """
    fragments = []
    start = 0
    for fragment in figures:
        at = title.find(fragment, start)
        if not fragment.strip() or at < 0:
            raise ValueError('figure fragment is absent, changed or out of order')
        if fragment.strip() == title.strip():
            raise ValueError('headline is not a figure fragment')
        start = at + len(fragment)
        fragments.append((at, start))
    spans = [(m.start(), m.end()) for m in DATES.finditer(title)]
    for m in NUM.finditer(title):
        if any(lo <= m.start() and m.end() <= hi for lo, hi in spans):
            continue
        unit = UNITS.match(title, m.end())
        spans.append((m.start(), unit.end() if unit else m.end()))
    reduced = []
    for lo, hi in sorted(spans):
        if reduced and JOIN.fullmatch(title[reduced[-1][1]:lo]):
            reduced[-1] = (reduced[-1][0], hi)
        else:
            reduced.append((lo, hi))
    if any(not any(a <= lo and hi <= b for a, b in fragments) for lo, hi in reduced):
        raise ValueError('printed numeric figure is incomplete')
    if re.sub(r'\W+', '', ''.join(figures)).casefold() == re.sub(r'\W+', '', title).casefold() and figures:
        raise ValueError('figures cannot reconstruct the headline')
    words_undecided = any(not any(lo <= m.start() and m.end() <= hi for lo, hi in reduced) for m in WORDS.finditer(title))
    extra_fragment = any(not any(a <= lo and hi <= b for lo, hi in reduced) for a, b in fragments)
    return words_undecided or extra_fragment
