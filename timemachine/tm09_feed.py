"""Amended repeat marks and literal figure extraction. Raw titles stay in memory."""
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


MONTHS = 'January|February|March|April|May|June|July|August|September|October|November|December'


def copied_run(paraphrase, headlines, feed):
    pattern = re.compile(feed['title_token_pattern'])
    submitted = tuple(pattern.findall(normalized(paraphrase)))
    limit, minimum = feed['paraphrase_block_run_tokens'], feed['paraphrase_min_title_tokens']
    if type(limit) is not int or type(minimum) is not int or not 2 <= minimum <= limit <= 30:
        raise ValueError('invalid paraphrase bounds')
    for headline in headlines:
        original = tuple(pattern.findall(normalized(headline)))
        if len(original) < minimum:
            continue
        width = min(limit, len(original))
        seen = {original[i:i + width] for i in range(len(original) - width + 1)}
        if any(submitted[i:i + width] in seen for i in range(len(submitted) - width + 1)):
            return True
    return False


def extract_figures(title, feed):
    """Copy exact source slices. The missed-figure flag is diagnostic and never blocks a note."""
    limit, units = feed['figure_max_chars'], feed['figure_units']
    if (type(limit) is not int or not 1 <= limit <= 256 or not units
            or any(not re.fullmatch(r'[A-Za-z]+(?: [A-Za-z]+)*', u) for u in units)):
        raise ValueError('invalid figure bounds or unit settings')
    choices = '|'.join(re.escape(u) for u in sorted(units, key=len, reverse=True))
    pattern = feed['figure_extract_pattern'].replace('{{units}}', choices).replace('{{months}}', MONTHS)
    spans = [m.span() for m in re.finditer(pattern, title) if 0 < m.end() - m.start() <= limit]
    missed = any(not any(lo <= m.start() and m.end() <= hi for lo, hi in spans)
                 for m in re.finditer(feed['figure_possible_miss_pattern'], title))
    return [title[lo:hi] for lo, hi in spans], missed
