"""Where the autopsy reads from and writes to. The one place these paths are set.

Order: command-line flags of autopsy.py (--runs, --tape, --out), then the environment variables
DT_AUTOPSY_RUNS, DT_AUTOPSY_TAPE, DT_AUTOPSY_OUT, then the defaults below (the off-repo working area used on 2026-11-25).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.environ.get("DT_AUTOPSY_RUNS", "/home/user/workspace/rig/tm_runs")
TAPE = os.environ.get("DT_AUTOPSY_TAPE", "/home/user/workspace/rig/tm_store/tape.sqlite")
OUT = os.environ.get("DT_AUTOPSY_OUT", os.path.join(HERE, "autopsy_results.json"))


def tape_uri():
    """Read-only sqlite URI for the tape."""
    return f"file:{TAPE}?mode=ro"
