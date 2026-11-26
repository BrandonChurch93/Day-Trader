"""Read the static dashboard findings and counted results from Markdown."""

import posixpath
import re
from urllib.parse import urlsplit


FINDINGS = {"Where things stand", "What is believed now"}
HEADING = re.compile(r"^ {0,3}##[ \t]+(.+?)\s*#*\s*$")
BULLET = re.compile(r"^ {0,3}[-*+]\s+(.+)")
STAMP = re.compile(r"\b(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}(?::\d{2})?) UTC\b")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
RUN = re.compile(r"\brun once\b", re.I)
REPLAY = re.compile(r"\bReplay\s+(\d+)\b", re.I)
MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\(([^()\s]+(?:\([^()]*\)[^()\s]*)*)\)")
CODE_PATH = re.compile(r"(?<!\w)\x60((?:docs/|research/)[^\x60\s]+\.md(?:#[\w-]+)?)\x60")
SCORECARD_PATH = "docs/research/95_where_we_stand_after_32_tests.md"


def sections(markdown):
    active = None
    for n, line in enumerate(markdown.splitlines(), 1):
        heading = HEADING.match(line)
        if heading:
            active = heading[1]
        elif re.match(r"^ {0,3}#\s", line):
            active = None
        else:
            yield active, n, line


def url(target, gh):
    parsed = urlsplit(target)
    if parsed.scheme in {"https", "http"} and parsed.netloc:
        return target
    if parsed.scheme or parsed.netloc:
        return None
    path = target.lstrip("/")
    if not target.startswith(("/", "docs/")):
        path = posixpath.join("docs", path) if path else "docs/STATUS.md"
    return gh + posixpath.normpath(path)


def validate_status_runs(markdown, findings):
    """Check independently for every run-once marker in the findings sections."""
    exported = {n for item in findings if RUN.search(item["lead"] + " " + item["body"])
                for n in item["source_lines"]}
    for section, n, line in sections(markdown):
        if section in FINDINGS and RUN.search(line) and n not in exported:
            raise ValueError(f"STATUS.md:{n}: 'run once' entry was not exported: {line.strip()}")


def parse_status(markdown, gh):
    items = []
    current = None
    for section, n, line in sections(markdown):
        bullet = BULLET.match(line)
        if section not in FINDINGS:
            current = None
        elif bullet:
            current = (section, [n], [bullet[1].strip()])
            items.append(current)
        elif current and current[0] == section and line.startswith((" ", "\t")) and line.strip():
            current[1].append(n)
            current[2].append(line.strip())
        else:
            current = None

    def render(section, numbers, lines):
        raw = " ".join(lines)
        links = []

        def add(label, target):
            href = url(target, gh)
            if href and all(existing != href for _, existing in links):
                links.append([label, href])
            return label

        lead_link = MARKDOWN_LINK.match(raw)
        plain = MARKDOWN_LINK.sub(lambda m: add(m[1], m[2]), raw)
        def code_link(match):
            add(posixpath.basename(match[1]), match[1])
            return ""

        plain = CODE_PATH.sub(code_link, plain).replace("\x60", "")
        plain = re.sub(r"\(\s*,?\s*\)|\s+([.,;:])", lambda m: m[1] or "", plain).strip()
        if lead_link:
            lead = lead_link[1]
            body = plain[len(lead):].lstrip(" ,.:")
        else:
            split = re.search(r"(?<!\d):|:(?!\d)|\.(?=\s|$)", plain)
            # Keep a dotted domain or decimal together; stop at a real sentence break.
            lead, body = (plain[:split.start()], plain[split.end():].strip()) if split else (plain, "")
        if not links:
            links.append(["Status notes", gh + "docs/STATUS.md#" + section.lower().replace(" ", "-")])
        run = RUN.search(raw)
        stamp = STAMP.search(raw, run.end()) if run else None
        stamp = stamp or STAMP.search(raw)
        utc = " ".join(stamp.groups()) if stamp else None
        date_only = DATE.search(raw)
        date = utc + (":00" if len(stamp[2]) == 5 else "") if utc else (date_only[0] if date_only else "")
        return dict(lead=lead, body=body[:1].upper() + body[1:], links=links, utc=utc,
                    date=date, raw=raw, source_lines=numbers)

    result = [render(*item) for item in items]
    return sorted(result, key=lambda item: item["date"], reverse=True)


def scoreboard(markdown, findings, gh):
    base = []
    total = None
    for section, _, line in sections(markdown):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if section and section.startswith("1. ") and cells[0].isdigit() and len(cells) == 7:
            _, label, name, _, reachable, verdict, details = cells
            match = CODE_PATH.search(details)
            base.append(dict(label=label, name=name, verdict=verdict,
                             passed=bool(re.match(r"^passed\b", verdict, re.I)),
                             url=url(match[1], gh) if match else gh + SCORECARD_PATH,
                             scope="US $500 reachable" if reachable == "Yes" else "Not US-reachable"))
        elif section and section.startswith("2. ") and cells[0] == "Total":
            total = int(cells[1]), int(cells[2])
    if total != (len(base), sum(row["passed"] for row in base)):
        raise ValueError("Dashboard scoreboard: test inventory and family totals disagree")

    # A previously reported design result does not use up a later held-back verdict.
    recorded = {int(match[1]): row for row in base if (match := REPLAY.match(row["label"]))
                and not row["verdict"].lower().startswith("design only")}
    latest_baseline = max(
        (item["date"] for item in findings
         if (m := REPLAY.search(item["lead"])) and int(m[1]) in recorded and RUN.search(item["raw"])),
        default="",
    )
    matched, later = set(), set()
    dated = []
    for item in findings:
        replay = REPLAY.search(item["lead"])
        if not (replay and item["utc"] and RUN.search(item["raw"])):
            continue
        number = int(replay[1])
        if number in recorded:
            if number not in matched:
                dated.append(recorded[number])
                matched.add(number)
            continue
        if number in later or item["date"] <= latest_baseline:
            continue
        verdict = re.search(r"(?<![\w-])(?:did not pass|failed|passed|met all)\b(?:[, ]+(\d+\s+of\s+\d+\s+marks))?",
                            item["raw"], re.I)
        if not verdict:
            raise ValueError(f"Dashboard scoreboard: cannot read the verdict for {item['lead']!r}")
        passed = verdict[0].lower().startswith(("passed", "met all"))
        label = f"Replay {number:02}"
        report = next((href for text, href in item["links"] if text == item["lead"]), item["links"][0][1])
        outcome = "Passed" if passed else "Did not pass"
        if verdict[1]:
            outcome += f" ({verdict[1]})"
        dated.append(dict(label=label, name="", verdict=outcome, passed=passed, url=report, scope=""))
        later.add(number)

    passes = [row for row in base if row["passed"]] + [row for row in dated if row["passed"] and row not in base]
    tests = total[0] + len(later)
    # The status timestamps determine the latest run order; untimed inventory entries are the fallback.
    latest = dated + [row for row in reversed(base) if row not in dated]
    return dict(tests=tests, passed=len(passes), did_not_pass=tests - len(passes),
                passes=passes, latest=latest[:5])
