"""Settings, the frozen build and the ledger key, the same way the forward cards do it (practice/forward_e14.py):
the bot runs only from a clean committed build whose 40-hex hash is written as `B01_START=<hash>` exactly once on its
ledger row (forecast_bot.ledger_row) in research_rig/TRIAL_LEDGER.md as committed on local branch main."""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import yaml

from . import method

ROOT = Path(__file__).resolve().parents[2]
LEDGER = "research_rig/TRIAL_LEDGER.md"
APPROVAL_REF = "refs/heads/main"
PINNED = tuple(f"practice/forecast_bot/{n}" for n in (
    "__init__.py", "bot.py", "cdf.py", "metaculus.py", "method.py", "models.py", "questions.py", "settings.py",
    "state.py")) + ("practice/PLAN_B01_forecast_bot_DRAFT.md",)
KEYS = ("ledger_row", "start_key", "test_key", "network_allowed", "api_base", "token_env", "targets", "testing_target",
        "poll_minutes", "page_limit", "max_pages", "http_timeout_s", "max_attempts_per_post", "min_minutes_left",
        "research_model", "research_web_search", "research_timeout_s", "research_max_tokens", "runs",
        "min_valid_runs", "run_timeout_s", "question_budget_s", "max_model_calls_per_pass", "max_model_calls_per_day", "run_max_tokens", "asknews_enabled", "binary_clip", "mc_floor",
        "cdf_uniform_mix", "cdf_open_bound_mass", "comment_max_chars", "private_dir")


class Refuse(Exception):
    pass


def need(cond, why):
    if not cond:
        raise Refuse(why)


def load(path=None):
    raw = yaml.safe_load(Path(path or ROOT / "config/thresholds.yaml").read_text())
    cfg = json.loads(json.dumps(raw["forecast_bot"]["value"]))
    need(set(cfg) == set(KEYS), "forecast_bot settings differ from the known keys")
    return cfg


def required(cfg):
    need(type(cfg["ledger_row"]) is int and cfg["ledger_row"] > 0, "ledger_row is not set")
    need(isinstance(cfg["targets"], list) and cfg["targets"] and all(isinstance(t, str) and t for t in cfg["targets"]),
         "targets is empty")
    need(len(cfg["runs"]) >= cfg["min_valid_runs"] >= 1, "runs and min_valid_runs do not fit")
    lo, hi = cfg["binary_clip"]
    need(0 < lo < 0.5 < hi < 1, "binary_clip must stay away from 0 and 1")
    need(cfg["asknews_enabled"] is False, "AskNews is not built in this version")
    need(cfg["api_base"] == "https://www.metaculus.com", "api_base must be https://www.metaculus.com")
    need(cfg["question_budget_s"] >= cfg["research_timeout_s"] + cfg["run_timeout_s"],
         "question_budget_s must cover one research call and one run")
    need(cfg["max_attempts_per_post"] * cfg["poll_minutes"] >= 180, "retries must be allowed to last the whole window")
    per_post = (1 if cfg["research_web_search"] else 0) + len(cfg["runs"])
    need(per_post <= cfg["max_model_calls_per_pass"] <= cfg["max_model_calls_per_day"], "model call caps do not fit")
    return cfg


def frozen(cfg):
    """What a run is pinned to: every setting, the prompt hash and the source hashes."""
    return {"config": cfg, "prompt_sha256": method.prompt_hash(),
            "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in PINNED}}


ENV_ALLOW = ("PATH", "HOME", "LANG", "LC_ALL", "TZ")


def child_env():
    """The environment for a child process: an allowlist only, so no token or key variable can reach it."""
    env = {k: os.environ[k] for k in ENV_ALLOW if k in os.environ}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_NO_REPLACE_OBJECTS="1")
    return env


def literal_git(*args, root=None):
    try:
        return subprocess.check_output(("git", "--no-replace-objects", "-c", "core.fsmonitor=false", *args),
                                       cwd=root or ROOT, env=child_env(), text=True, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        raise Refuse("cannot read the committed build or ledger") from None


def checked_build(root=None):
    """The HEAD commit, after checking that every pinned file and the config are tracked, clean and equal to HEAD."""
    root = Path(root or ROOT)
    files = (*PINNED, "config/thresholds.yaml")
    tracked = set(literal_git("ls-files", "-z", "--", *files, root=root).split("\0")) - {""}
    need(tracked == set(files), "frozen inputs are not all tracked")
    need(not literal_git("status", "--porcelain", "--untracked-files=no", "--", *files, root=root),
         "frozen inputs are not clean")
    commit = literal_git("rev-parse", "--verify", "HEAD^{commit}", root=root).strip()
    for p in files:
        need(literal_git("show", f"{commit}:{p}", root=root) == (root / p).read_text(), "a frozen input differs from HEAD")
    return commit


def require_key(row, key, commit, ledger_text=None):
    """Refuse unless ledger row `row` holds `key=<commit>` exactly once (and no other assignment of `key`)."""
    need(re.fullmatch(r"[a-f0-9]{40}", commit or ""), "invalid frozen build")
    body = literal_git("show", f"{APPROVAL_REF}:{LEDGER}") if ledger_text is None else ledger_text
    rows = re.findall(rf"^\|[ \t]*{row}[ \t]*\|[^\r\n]*$", body, re.M)
    need(len(rows) == 1, f"committed ledger row {row} missing or repeated")
    marker = rf"(?<![A-Za-z0-9_]){key}"
    assigned = re.findall(marker + r"[ \t]*=", rows[0])
    good = re.findall(marker + rf"={commit}(?=[\s`|]|$)", rows[0])
    need(len(assigned) == len(good) == 1, f"{key} missing, repeated or mismatched on committed ledger row {row}")
    return True
