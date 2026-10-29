"""Collector: policy & standard review dates  (system of record: policy repo in git).

The last review is the most recent merged PR that touched the policy file with
the "annual-review" label. Live pull per policy:

    gh pr list --repo northwind/policies --state merged --label annual-review \
      --search "path:policies/access-control.md" --json mergedAt,url --limit 1
"""
from __future__ import annotations

import sys

from _common import days_ago, rng, run

POLICIES = ["Information Security Policy", "Access Control Standard", "Acceptable Use Policy", "Cryptography Standard",
            "Secure Development Standard", "Vulnerability Management Standard", "Incident Response Plan",
            "Business Continuity Policy", "Supplier Security Standard", "Data Classification Standard",
            "Logging & Monitoring Standard", "Physical Security Policy", "Security Awareness Policy",
            "Change Management Standard", "AI Use Policy", "Data Retention Standard"]


def sample():
    r = rng("policies")
    rows = []
    for p in POLICIES:
        age = r.randint(20, 470)
        rows.append({"policy": p, "last_review": days_ago(age), "age_days": age,
                     "status": "Overdue" if age > 365 else ("Due < 60 days" if age > 305 else "Current"),
                     "owner_team": r.choice(["GRC", "IAM Eng", "SRE", "Legal", "People Ops"]),
                     "link": f"https://github.com/HaDoyle12/grc-ccm-demo/blob/main/docs/06-pipeline-processes.md"})
    return rows


def main(live: bool = False) -> int:
    return run("policies", "Policy repo (git history via gh)", sample, live=live)


if __name__ == "__main__":
    print(main("--live" in sys.argv))
