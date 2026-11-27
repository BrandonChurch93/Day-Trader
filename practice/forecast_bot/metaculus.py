"""The only code that talks to Metaculus. Plain urllib, written from the public API description
(Metaculus/metaculus docs/openapi.yml). Endpoints used:

- GET  /api/posts/?tournaments=<slug>&statuses=open&limit=&offset=   list open posts of one tournament
- GET  /api/questions/bulk-forecast-read/?question_ids=1&question_ids=2   our own forecasts on those questions
  (questions we cannot view are left out of the reply; the pass treats a missing id as "cannot check", not as "none")
- POST /api/questions/bulk-forecast-comment/ {"forecasts": [...], "comments": [...]}   forecast and private comment,
  saved together or not at all

Safety:
- No request at all unless `forecast_bot.network_allowed` is true and the caller has passed the ledger key check
  (bot.arm). The constructor refuses otherwise, so nothing below can run by accident.
- The token is read from the environment variable named by `token_env` at the moment a request is built. It is not
  stored on the object, not logged, not put in an exception, and never reaches a model prompt.
- Only https to the configured host; redirects are refused so the token cannot follow one to another host.
- No automatic retry of a POST: an unknown outcome is settled on the next pass by reading our own forecasts.
"""
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


def read_token(cfg, environ=None):
    env = os.environ if environ is None else environ
    tok = env.get(cfg["token_env"], "")
    if not tok or any(c.isspace() for c in tok) or len(tok) < 16:
        raise Refuse(f"no usable bot token in the environment variable {cfg['token_env']}")
    return tok


class Client:
    def __init__(self, cfg, armed, opener=None, environ=None):
        if not cfg.get("network_allowed"):
            raise Refuse("network_allowed is false in config forecast_bot")
        if armed is not True:
            raise Refuse("not armed: the ledger key check has not passed")
        base = urllib.parse.urlsplit(cfg["api_base"])
        if base.scheme != "https" or not base.hostname or base.path not in ("", "/"):
            raise Refuse("api_base must be a bare https origin")
        self.cfg, self.host = cfg, base.hostname
        self.base = f"https://{base.hostname}"
        self.environ = environ
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        read_token(cfg, environ)                       # fail early, without keeping the value

    def _request(self, method, path, query=None, body=None):
        url = self.base + path + ("?" + urllib.parse.urlencode(query, doseq=True) if query else "")
        if urllib.parse.urlsplit(url).hostname != self.host:
            raise Refuse("request host differs from api_base")
        token = read_token(self.cfg, self.environ)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": "Token " + token, "Accept": "application/json",
            "User-Agent": "B01 forecast bot (Day-Trader repo, practice/forecast_bot)",
            **({"Content-Type": "application/json"} if data is not None else {})})
        where = f"{method} {path}"
        try:
            with self.opener.open(req, timeout=self.cfg["http_timeout_s"]) as resp:
                status, raw = resp.status, resp.read(5_000_000)
        except urllib.error.HTTPError as exc:
            raise ApiError(exc.code, where) from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ApiError(type(exc).__name__, where) from None
        finally:
            token = None
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
