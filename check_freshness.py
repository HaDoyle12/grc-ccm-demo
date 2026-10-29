"""Freshness gate: fail the run if any dataset is stale or missing.

A dashboard that silently serves last-good data looks exactly like a healthy
one. This gate turns staleness into a red workflow run that reaches a person.
It also fails if it checked zero datasets, so it can never pass by accident.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

DATA = Path(__file__).parent / "data"
EXPECTED = ["controls", "evidence", "findings", "risks", "policies", "training", "changes", "access_reviews", "repo_security"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-days", type=int, default=8)
    a = ap.parse_args(argv)
    state = json.loads((DATA / "_freshness.json").read_text()) if (DATA / "_freshness.json").exists() else {}
    now = dt.datetime.now(dt.timezone.utc)
    problems, checked = [], 0
    for name in EXPECTED:
        s = state.get(name)
        if not s or not s.get("last_success"):
            problems.append(f"{name}: never collected")
            continue
        checked += 1
        age = (now - dt.datetime.fromisoformat(s["last_success"])).days
        if s["status"] != "ok":
            problems.append(f"{name}: last attempt failed ({s.get('error', '')[:80]})")
        if age > a.max_age_days:
            problems.append(f"{name}: last success {age} days ago (limit {a.max_age_days})")
    print(f"freshness gate checked {checked}/{len(EXPECTED)} datasets")
    if checked == 0:
        print("FAIL: checked nothing")
        return 1
    for p in problems:
        print("FAIL:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
