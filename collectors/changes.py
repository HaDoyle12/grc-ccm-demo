"""Collector: emergency changes & review SLA  (system of record: change issues in GitHub).

The SLA clock is computed from the issue TIMELINE (when the "needs-review" label
was removed), not from a label a bot applies -- labels can be configured with a
different threshold than the written policy. Live pull per issue:

    gh api repos/northwind/deploys/issues/{n}/timeline --paginate
"""
from __future__ import annotations

import sys

from _common import days_ago, rng, run


def sample():
    r = rng("changes")
    rows = []
    for n in range(1, 41):
        hrs = round(r.lognormvariate(3.0, 0.8), 1)
        rows.append({"id": f"CHG-{2400 + n}", "opened": days_ago(r.randint(0, 90)),
                     "service": r.choice(["payments-api", "auth-service", "edge-proxy", "web-frontend", "data-pipeline"]),
                     "review_hours": hrs, "within_sla": hrs <= 48, "approved_by_second_person": r.random() < 0.95})
    return rows


def main(live: bool = False) -> int:
    return run("changes", "GitHub issue timelines (gh api)", sample, live=live)


if __name__ == "__main__":
    print(main("--live" in sys.argv))
