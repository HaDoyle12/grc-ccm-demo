"""Comment on ONE open tracking issue when a scheduled run fails.

A new issue every week trains people to close them unread; one issue with a
growing comment history shows how long the problem has lasted.
"""
from __future__ import annotations

import argparse
import json
import subprocess


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--run-url", required=True)
    a = ap.parse_args()
    body = (f"Run failed: {a.run_url}\n\nCollectors keep last-good data, so the dashboard may show stale "
            "figures that look current. Run `python3 check_freshness.py` to see which sources are behind.")
    issues = json.loads(gh("issue", "list", "--state", "open", "--search", f'"{a.title}" in:title', "--json", "number,title"))
    match = next((i["number"] for i in issues if i["title"] == a.title), None)
    if match:
        gh("issue", "comment", str(match), "--body", body)
        print(f"commented on #{match}")
    else:
        print(gh("issue", "create", "--title", a.title, "--body", body).strip())


if __name__ == "__main__":
    main()
