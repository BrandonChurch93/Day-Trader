"""The only code that talks to Metaculus. Plain urllib, written from the public API description
(Metaculus/metaculus docs/openapi.yml). Endpoints used:

- GET  /api/posts/?tournaments=<slug>&statuses=open&include_descriptions=true&limit=&offset=   open posts of one
  tournament, with description, resolution_criteria and fine_print (openapi.yml line 1409)
- GET  /api/questions/bulk-forecast-read/?question_ids=1&question_ids=2   our own forecasts on those questions
  (questions we cannot view are left out of the reply; the pass treats a missing id as "cannot check", not as "none")
- POST /api/questions/bulk-forecast-comment/ {"forecasts": [...], "comments": [...]}   forecast and private comment,
  saved together or not at all

Safety:
- No request at all unless `forecast_bot.network_allowed` is true and the caller has passed the ledger key check
  (bot.arm). The constructor refuses otherwise, so nothing below can run by accident.
- The token is taken out of the environment variable named by `token_env` the first time it is needed, so no child
  process can inherit it, and is held in this module only. It is not stored on the client, not logged, not put in an
  exception, and never reaches a model prompt.
- Only https to www.metaculus.com; proxies from the environment are ignored and redirects are refused, so the token
  cannot be sent anywhere else.
- No automatic retry of a POST: an unknown outcome is settled on the next pass by reading our own forecasts.
"""
import http.client
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

TOKEN_SHAPE = re.compile(r"(?i)(token\s+)[A-Za-z0-9_\-\.]{8,}")


class Refuse(Exception):
    """A rule stops the bot. The message never holds a secret."""


class ApiError(Exception):
    def __init__(self, status, where):
        super().__init__(f"{where}: HTTP {status}")
        self.status, self.where = status, where


def redact(text, token=None):
    text = str(text)
    if token:
        text = text.replace(token, "[redacted]")
    return TOKEN_SHAPE.sub(r"\1[redacted]", text)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


PINNED_HOST = "www.metaculus.com"
_HELD = {}          # env name -> token, held in this process after it is taken out of the environment


def take_token(cfg, environ=None):
    """The bot token. The first call takes it out of the environment (so no child process can inherit it) and holds it
    in this module; later calls return the held value. Refuses if there is no usable token."""
    env = os.environ if environ is None else environ
    name = cfg["token_env"]
    if name in env:
        tok = env.pop(name)
        if tok and not any(c.isspace() for c in tok) and len(tok) >= 16:
            _HELD[name] = tok
    tok = _HELD.get(name, "")
    if not tok:
        raise Refuse(f"no usable bot token in the environment variable {name}")
    return tok


def forget_token(cfg):
    _HELD.pop(cfg["token_env"], None)


def check_base(api_base):
    """api_base must be exactly https://www.metaculus.com: no userinfo, port, path, query or fragment."""
    try:
        base = urllib.parse.urlsplit(api_base)
        port = base.port
    except ValueError:
        raise Refuse("api_base is not a valid URL") from None
    if (base.scheme != "https" or base.hostname != PINNED_HOST or base.username is not None or base.password is not None
            or port is not None or base.path not in ("", "/") or base.query or base.fragment
            or api_base.rstrip("/") != "https://" + PINNED_HOST):
        raise Refuse(f"api_base must be exactly https://{PINNED_HOST}")
    return base.hostname


def safe_opener():
    """No proxy from the environment (HTTPS_PROXY cannot reroute the token) and no redirects."""
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())


class Client:
    def __init__(self, cfg, armed, opener=None, environ=None):
        if not cfg.get("network_allowed"):
            raise Refuse("network_allowed is false in config forecast_bot")
        if armed is not True:
            raise Refuse("not armed: the ledger key check has not passed")
        self.cfg, self.host = cfg, check_base(cfg["api_base"])
        self.base = f"https://{self.host}"
        self.opener = opener or safe_opener()
        take_token(cfg, environ)                       # fail early; the value stays in the module holder

    def holds_token(self, text):
        """True if `text` holds the bot token or anything shaped like a token header. For the payload check."""
        tok = _HELD.get(self.cfg["token_env"], "")
        return bool(tok and tok in text) or redact(text) != text

    def _request(self, method, path, query=None, body=None):
        url = self.base + path + ("?" + urllib.parse.urlencode(query, doseq=True) if query else "")
        if urllib.parse.urlsplit(url).hostname != self.host:
            raise Refuse("request host differs from api_base")
        token = take_token(self.cfg)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": "Token " + token, "Accept": "application/json",
            "User-Agent": "B01 forecast bot (Day-Trader repo, practice/forecast_bot)",
            **({"Content-Type": "application/json"} if data is not None else {})})
        token = None
        where = f"{method} {path}"
        try:
            with self.opener.open(req, timeout=self.cfg["http_timeout_s"]) as resp:
                status, raw = resp.status, resp.read(5_000_000)
        except urllib.error.HTTPError as exc:
            raise ApiError(exc.code, where) from None
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError, ValueError) as exc:
            raise ApiError(type(exc).__name__, where) from None
        if not 200 <= status < 300:
            raise ApiError(status, where)
        try:
            return status, (json.loads(raw) if raw else None)
        except ValueError:
            raise ApiError("bad_json", where) from None

    def open_posts(self, slug):
        """Every open post of one tournament, following pages up to max_pages."""
        out, offset = [], 0
        for _ in range(self.cfg["max_pages"]):
            _, page = self._request("GET", "/api/posts/", {"tournaments": slug, "statuses": "open",
                                                           "include_descriptions": "true",
                                                           "limit": self.cfg["page_limit"], "offset": offset})
            rows = (page or {}).get("results") or []
            out.extend(r for r in rows if isinstance(r, dict))
            if not (page or {}).get("next") or not rows:
                return out
            offset += len(rows)
        raise ApiError("too_many_pages", "GET /api/posts/")

    def my_forecasts(self, question_ids):
        """{question_id: number of our forecasts} for the questions the site returned."""
        if not question_ids:
            return {}
        _, page = self._request("GET", "/api/questions/bulk-forecast-read/", {"question_ids": sorted(question_ids)})
        return {r["question_id"]: len(r.get("forecasts") or []) for r in (page or {}).get("results") or []
                if isinstance(r, dict) and type(r.get("question_id")) is int}

    def submit(self, payload):
        status, _ = self._request("POST", "/api/questions/bulk-forecast-comment/", body=payload)
        return status
