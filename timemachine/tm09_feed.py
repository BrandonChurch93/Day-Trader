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
MONTH = r'January|February|March|April|May|June|July|August|September|October|November|December'
DATES = re.compile(rf'\b(?:(?:{MONTH})\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,\s*\d{{4}})?|'
                   rf'\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTH})(?:\s+\d{{4}})?)\b', re.I)
CARDINAL = (r'zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|'
            r'fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|'
            r'seventy|eighty|ninety|hundreds?|thousands?|millions?|billions?|trillions?|dozens?')
WRITTEN = re.compile(rf'\b(?:(?:plus|minus|negative) )?(?:{CARDINAL})\b'
                     rf'(?:(?:\s+and\s+|[\s-]+)(?:{CARDINAL})\b)*', re.I)
AMBIGUOUS = re.compile(r'\b(?:(?:a|one)\s+)?(?:half|quarter|third|first|second|fourth|fifth|'
                       r'sixth|seventh|eighth|ninth|tenth)\b', re.I)
JOIN = re.compile(r'\s*(?:[–—-]|to|through)\s*', re.I)


def copied_run(paraphrase, headlines, feed):
    pattern = re.compile(feed['title_token_pattern'])
    submitted = tuple(pattern.findall(normalized(paraphrase)))
    limit = feed['paraphrase_block_run_tokens']
    if type(limit) is not int or not 2 <= limit <= 30:
        raise ValueError('invalid paraphrase bounds')
    for headline in headlines:
        original = tuple(pattern.findall(normalized(headline)))
        width = min(limit, len(original))
        if not width:
            continue
        seen = {original[i:i + width] for i in range(len(original) - width + 1)}
        if any(submitted[i:i + width] in seen for i in range(len(submitted) - width + 1)):
            return True
    return False


def figure_check(title, figures, feed):
    """Require ordered, exact fragments and coverage of mechanically decidable spans.

    Return False for a decided check, True for semantic ambiguity, or raise for a definite error.
    """
    limit, units = feed['figure_max_chars'], feed['figure_units']
    if (type(limit) is not int or not 1 <= limit <= 256 or not units
            or any(not re.fullmatch(r'[A-Za-z]+(?: [A-Za-z]+)*', u) for u in units)):
        raise ValueError('invalid figure bounds or unit settings')
    choices = '|'.join(re.escape(u) for u in sorted(units, key=len, reverse=True))
    suffix = re.compile(rf'(?:[ \t]+(?:{choices})\b){{1,2}}', re.I)
    spans = [(m.start(), m.end()) for m in DATES.finditer(title)]
    for m in NUM.finditer(title):
        if any(lo <= m.start() and m.end() <= hi for lo, hi in spans):
            continue
        unit = suffix.match(title, m.end())
        spans.append((m.start(), unit.end() if unit else m.end()))
    uncertain = []
    for m in AMBIGUOUS.finditer(title):
        if not any(lo <= m.start() and m.end() <= hi for lo, hi in spans):
            unit = suffix.match(title, m.end())
            uncertain.append((m.start(), unit.end() if unit else m.end()))
    for m in WRITTEN.finditer(title):
        if any(lo <= m.start() and m.end() <= hi for lo, hi in (*spans, *uncertain)):
            continue
        unit = suffix.match(title, m.end())
        span = (m.start(), unit.end() if unit else m.end())
        # Capitalized standalone text can be a proper noun, not a quantity.
        if not unit and m.group()[0].isupper() and ' ' not in m.group() and '-' not in m.group():
            uncertain.append(span)
        else:
            spans.append(span)
    reduced = []
    for lo, hi in sorted(spans):
        if reduced and JOIN.fullmatch(title[reduced[-1][1]:lo]):
            reduced[-1] = (reduced[-1][0], hi)
        else:
            reduced.append((lo, hi))
    fragments, start = [], 0
    allowed = sorted(set(reduced + uncertain))
    for fragment in figures:
        if not 0 < len(fragment) <= limit:
            raise ValueError('figure fragment exceeds its bound')
        matches = [(lo, hi) for lo, hi in allowed if lo >= start and title[lo:hi] == fragment]
        if not matches or fragment.strip() == title.strip():
            raise ValueError('figure is not an exact permitted span')
        lo, start = matches[0]
        fragments.append((lo, start))
    if any(span not in fragments for span in reduced):
        raise ValueError('printed figure is incomplete')
    if re.sub(r'\W+', '', ''.join(figures)).casefold() == re.sub(r'\W+', '', title).casefold() and figures:
        raise ValueError('figures cannot reconstruct the headline')
    return bool(uncertain)
