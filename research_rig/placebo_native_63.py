"""Price-free, strict offset index for native Alpaca daily SIP bar pages."""
from datetime import datetime, time
from hashlib import sha256
import json
import re

from count_63 import NY
from placebo_run_63 import need


TOKEN = re.compile(rb'[-+]?[0-9][0-9.eE+-]*|null|true|false')
FIELDS = {"t", "o", "h", "l", "c", "v", "n", "vw"}
REQUIRED = {"t", "o", "h", "l", "c", "v"}


class Cursor:
    def __init__(self, raw):
        self.raw, self.i = raw, 0

    def at(self):
        while self.i < len(self.raw) and self.raw[self.i] in b" \r\n\t":
            self.i += 1
        return self.raw[self.i:self.i + 1]

    def take(self, b):
        need(self.at() == b, "NATIVE_JSON_SHAPE")
        self.i += 1

    def string_indices(self):
        self.take(b'"')
        start = self.i - 1
        while self.i < len(self.raw):
            token = self.raw[self.i:self.i + 1]
            self.i += 1
            if token == b'"':
                return start, self.i
            if token == b"\\":
                need(self.i < len(self.raw), "NATIVE_JSON_SHAPE")
                self.i += 1
        need(False, "NATIVE_JSON_SHAPE")

    def key(self):
        a, b = self.string_indices()
        return json.loads(self.raw[a:b])

    def value_indices(self):
        if self.at() == b'"':
            return self.string_indices()
        found = TOKEN.match(self.raw, self.i)
        need(found is not None, "NATIVE_JSON_SHAPE")
        a, b = found.span()
        self.i = b
        return a, b

    def pairs(self):
        self.take(b"{")
        names = set()
        while self.at() != b"}":
            name = self.key()
            need(name not in names, "NATIVE_DUPLICATE_FIELD")
            names.add(name)
            self.take(b":")
            yield name
            if self.at() == b"}":
                break
            self.take(b",")
            need(self.at() != b"}", "NATIVE_JSON_SHAPE")
        self.take(b"}")

    def array(self):
        self.take(b"[")
        while self.at() != b"]":
            yield None
            if self.at() == b"]":
                break
            self.take(b",")
            need(self.at() != b"]", "NATIVE_JSON_SHAPE")
        self.take(b"]")


def scan_page(raw, wanted, bounds=None):
    """Read structure and metadata; locate opaque close tokens for wanted keys.

    Inputs are an exact native SIP/raw daily page and an independently
    approved set of (dated alias, session date). Provider/feed/view are
    authenticated by the capture metadata, not guessed from a bar object.
    No JSON parse on a full body/bar and no price token conversion.
    """
    cursor, out, observed = Cursor(raw), {}, set()
    digest = sha256(raw).hexdigest()
    outer = set()
    next_page = None
    for top in cursor.pairs():
        outer.add(top)
        if top == "next_page_token":
            a, b = cursor.value_indices()
            need(raw[a:a + 1] == b'"' or raw[a:b] == b"null", "NATIVE_JSON_SHAPE")
            next_page = json.loads(raw[a:b])
            continue
        need(top == "bars", "NATIVE_JSON_SHAPE")
        for alias in cursor.pairs():
            for _ in cursor.array():
                fields = {}
                for name in cursor.pairs():
                    need(name in FIELDS, "NATIVE_BAR_SHAPE")
                    fields[name] = cursor.value_indices()
                need(REQUIRED <= fields.keys(), "NATIVE_BAR_SHAPE")
                a, b = fields["t"]
                t = datetime.fromisoformat(json.loads(raw[a:b]).replace("Z", "+00:00"))
                need(t.tzinfo is not None, "NATIVE_BAR_CLOCK")
                local = t.astimezone(NY)
                need(local.time() == time(0), "NATIVE_BAR_CLOCK")
                key = alias, local.date()
                if bounds is not None:
                    sym, first, last = bounds
                    need(alias == sym and first <= key[1] <= last, "NATIVE_BAR_WINDOW")
                need(key not in observed, "NATIVE_DUPLICATE_BAR")
                observed.add(key)
                if key not in wanted:
                    continue
                a, b = fields["v"]
                v = json.loads(raw[a:b])
                need(type(v) is int and v >= 0, "NATIVE_BAR_VOLUME")
                a, b = fields["c"]
                out[key] = {"session": str(key[1]), "alias": alias, "feed": "sip", "view": "raw", "volume": v,
                            "close_ref": {"body_sha256": digest, "offset": a, "length": b - a}}
    need(outer == {"bars", "next_page_token"} and cursor.at() == b"", "NATIVE_JSON_SHAPE")
    return out, next_page


def approved_bar_leaves(raw, wanted):
    return scan_page(raw, wanted)[0]
