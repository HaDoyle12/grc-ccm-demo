"""Collector: user access reviews  (systems of record: identity provider + review tool).

Live pull: identity provider groups via Microsoft Graph
(GET /groups/{id}/members) for the population, plus the review campaign API for
decisions. For GitHub orgs the same population comes from:

    gh api orgs/northwind/members --paginate --jq '.[].login'
    gh api orgs/northwind/outside_collaborators --paginate
"""
from __future__ import annotations

import sys

from _common import days_ago, rng, run

APPS = ["GitHub org", "Cloud console (prod)", "Customer database", "Finance ERP", "HR system",
        "Admin portal", "SIEM", "Payment processor dashboard"]


def sample():
    r = rng("access")
    rows = []
    for a in APPS:
        users = r.randint(15, 400)
        reviewed = users if r.random() < 0.7 else int(users * r.uniform(0.6, 0.95))
        rows.append({"application": a, "users_in_scope": users, "reviewed": reviewed,
                     "revoked": int(reviewed * r.uniform(0.01, 0.08)), "last_campaign": days_ago(r.randint(10, 140)),
                     "complete": reviewed == users})
    return rows


def main(live: bool = False) -> int:
    return run("access_reviews", "Identity provider + review campaigns", sample, live=live)


if __name__ == "__main__":
    print(main("--live" in sys.argv))
