"""Collector: risk register  (system of record: labelled GitHub issues).

Live pull:  gh issue list --repo northwind/risk-register --label "Risk Register" \
              --state open --json number,title,labels,updatedAt --limit 500
Severity comes from a label; "last worked" is the issue's updatedAt.
"""
from __future__ import annotations

import sys

from _common import days_ago, rng, run

RISKS = ["Single region for customer database", "Shared admin accounts in legacy CRM", "Unsupported OS on build agents",
         "Third-party SDK with unknown data flows", "Key-person dependency in payments team", "Shadow SaaS adoption",
         "Insufficient DDoS capacity at edge", "AI model outputs not reviewed before release",
         "Long-lived cloud access keys", "Manual offboarding for contractors"]


def sample():
    r = rng("risks")
    return [{
        "id": f"R-{i:03d}", "title": t, "severity": r.choice(["Critical", "High", "Moderate", "Moderate", "Low"]),
        "treatment": r.choice(["Mitigate", "Mitigate", "Accept", "Transfer"]),
        "owner_team": r.choice(["SRE", "IAM Eng", "Platform Eng", "Procurement", "AI Governance"]),
        "last_worked": days_ago(r.randint(1, 120)),
    } for i, t in enumerate(RISKS, start=1)]


def main(live: bool = False) -> int:
    return run("risks", "GitHub Issues (Risk Register label)", sample, live=live)


if __name__ == "__main__":
    print(main("--live" in sys.argv))
