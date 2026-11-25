"""The only code in this repo that talks to a broker. Alpaca practice account only.

What it can do is a short fixed list (ALLOWED below, plus the read-only price addresses in market.READS): read the
account, positions and orders, read prices, and send one order. It has no code to cancel an order, close a position or
change the account, and it refuses any address that is not on the list, so it cannot reach a real-money address
(AGENTS.md, "What the order program always does"). It does not follow redirects. The key is read from the environment
and is never printed or written anywhere (AGENTS.md, "Only the owner"): broker error text is cut down to plain letters and
the key is removed from it before anyone sees it. Standard library only."""
import json, os, re, time, urllib.error, urllib.parse, urllib.request

PAPER = "https://paper-api.alpaca.markets"
DATA = "https://data.alpaca.markets"
ALLOWED = [("GET", PAPER, r"/v2/account"), ("GET", PAPER, r"/v2/positions"), ("GET", PAPER, r"/v2/orders"),
           ("GET", PAPER, r"/v2/orders:by_client_order_id"), ("POST", PAPER, r"/v2/orders")]


class Unclear(Exception):
    """The request may or may not have reached the broker (timeout, network fault, server error)."""


class Refused(Exception):
    """The broker answered clearly with a refusal. Carries the HTTP status and a cleaned, short message."""
    def __init__(self, status, message=""):
        super().__init__(f"HTTP {status}" + (f": {message}" if message else "")); self.status = status; self.message = message


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None  # a redirect becomes an HTTP error, so the key is never sent to another address


_OPENER = urllib.request.build_opener(_NoRedirect)


def allowed(method, base, path, extra_reads=()):
    return any(method == m and base == b and re.fullmatch(p, path) for m, b, p in ALLOWED) or \
        (method == "GET" and any(base == b and re.fullmatch(p, path) for b, p in extra_reads))


def clean(text, secrets=()):
    """Broker text made safe to write down: the key removed, only plain characters, short."""
    for s in secrets:
        if s:
            text = text.replace(s, "[removed]")
    try:
        j = json.loads(text); text = str(j.get("message", "")) if isinstance(j, dict) else ""
    except ValueError:
        text = ""
    for s in secrets:  # again after decoding, in case the key came back written with escapes
        if s:
            text = text.replace(s, "[removed]")
    return re.sub(r"[^A-Za-z0-9 .,:_/%$()\[\]-]", "", text)[:160]


class Broker:
    def __init__(self, key_id=None, secret=None, timeout=20, extra_reads=()):
        self.key_id = key_id or os.environ.get("ALPACA_PAPER_KEY_ID", ""); self.secret = secret or os.environ.get("ALPACA_PAPER_SECRET_KEY", "")
        self.timeout = timeout; self.extra_reads = tuple(extra_reads)

    def has_key(self):
        return bool(self.key_id and self.secret)

    def _call(self, method, base, path, params=None, body=None, tries=1):
        if not allowed(method, base, path, self.extra_reads):
            raise PermissionError(f"not on the allowed list: {method} {base}{path}")
        assert method == "GET" or tries == 1, "a request that changes something is never repeated here"
        url = base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        data = json.dumps(body).encode() if body is not None else None
        last = None
        for i in range(tries):
            req = urllib.request.Request(url, data=data, method=method, headers={"APCA-API-KEY-ID": self.key_id, "APCA-API-SECRET-KEY": self.secret,
                                                                              "Content-Type": "application/json", "Accept": "application/json"})
            try:
                with _OPENER.open(req, timeout=self.timeout) as r:
                    return json.loads(r.read().decode() or "null")
            except urllib.error.HTTPError as e:
                try:
                    text = e.read().decode(errors="replace")
                except Exception:
                    text = ""
                if e.code >= 500 or e.code == 429 or 300 <= e.code < 400:
                    last = Unclear(f"HTTP {e.code}")
                else:
                    raise Refused(e.code, clean(text, (self.key_id, self.secret))) from None
            except Exception as e:  # timeout, connection reset, bad JSON
                last = Unclear(type(e).__name__)
            if i + 1 < tries:
                time.sleep(2 * (i + 1))
        raise last

    # ---- reads (safe to repeat)
    def get(self, base, path, params=None):
        """Read-only call for practice/market.py. Only addresses on the allowed list."""
        return self._call("GET", base, path, params, tries=3)

    def account(self):
        return self._call("GET", PAPER, "/v2/account", tries=3)

    def positions(self):
        """{symbol without a slash: {qty, available}}, read every time (see "What the order program always does")."""
        out = {}
        for p in self._call("GET", PAPER, "/v2/positions", tries=3):
            q = float(p["qty"]); out[p["symbol"].replace("/", "")] = dict(qty=q, available=q if p.get("qty_available") is None else float(p["qty_available"]))
        return out

    def orders(self):
        """Every order the account has, oldest first. The books are worked out from this list on every run."""
        out, seen, cursor = [], set(), None
        for _ in range(400):
            params = {"status": "all", "limit": 500, "direction": "asc", "nested": "false"}
            if cursor:
                params["after_order_id"] = cursor  # the broker's own cursor: orders after this one, oldest first
            page = self._call("GET", PAPER, "/v2/orders", params, tries=3)
            new = [o for o in page if o["id"] not in seen]
            out += new; seen.update(o["id"] for o in new)
            if len(page) < 500:
                return out
            if not new:
                raise Unclear("the order list did not move on")  # a full page with nothing new: the list cannot be trusted as whole
            cursor = page[-1]["id"]
        raise Unclear("too many orders to read")

    def order_by_cid(self, cid):
        """The order with this client id, or None if the broker says it has none."""
        try:
            return self._call("GET", PAPER, "/v2/orders:by_client_order_id", {"client_order_id": cid}, tries=3)
        except Refused as e:
            if e.status == 404:
                return None
            raise

    # ---- the one write. Never repeated here; the caller handles an unclear answer.
    # See AGENTS.md, "What the order program always does".
    def submit(self, symbol, side, tif, cid, qty=None, notional=None):
        assert side in ("buy", "sell") and tif in ("day", "gtc") and (qty is None) != (notional is None)
        body = {"symbol": symbol, "side": side, "type": "market", "time_in_force": tif, "client_order_id": cid}
        if qty is not None:
            assert qty > 0; body["qty"] = f"{qty:.9f}".rstrip("0").rstrip(".")
        else:
            assert notional > 0; body["notional"] = f"{notional:.2f}"
        return self._call("POST", PAPER, "/v2/orders", body=body, tries=1)
