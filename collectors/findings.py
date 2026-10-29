"""Collector: nonconformities & findings  (system of record: a GitHub Project board).

Real-world equivalent: an issue-backed Project where each nonconformity is an
issue with custom fields (Classification, Control, Due, Status). Live pull:

    gh project item-list 12 --owner northwind --format json --limit 500

Since gh v2.97 project fields can be addressed by name, so the collector does
not need to resolve field IDs first.
"""
from __future__ import annotations

import sys

from _common import days_ago, days_ahead, rng, run

TITLES = [
    ("Quarterly access review missed for finance app", "A.5.18"),
    ("Two production repos without required reviews", "A.8.32"),
    ("Backup restore test older than 12 months", "A.8.13"),
    ("Supplier SOC report not collected for log vendor", "A.5.22"),
    ("Contractor training overdue past 30-day window", "A.6.3"),
    ("Critical vulnerability open beyond 30-day SLA", "A.8.8"),
    ("Incident post-mortems missing lessons-learned owner", "A.5.27"),
    ("Encryption standard references retired cipher", "A.8.24"),
    ("Visitor log retention shorter than policy", "A.7.2"),
    ("Firewall rule review not evidenced for Q3", "A.8.20"),
    ("Data classification labels missing on shared drive", "A.5.13"),
    ("Change approvals bypassed for emergency deploys", "A.8.32"),
    ("Policy owner departed; review not reassigned", "A.5.1"),
    ("Logging gap on admin portal authentication", "A.8.15"),
]


def sample():
    r = rng("findings")
    rows = []
    for n, (title, ctl) in enumerate(TITLES, start=101):
        cls = r.choices(["Major NC", "Minor NC", "OFI"], weights=[1, 4, 4])[0]
        opened = r.randint(10, 200)
        window = {"Major NC": 30, "Minor NC": 90, "OFI": 180}[cls]
        due_in = window - opened
        status = r.choice(["Open", "In remediation", "Open", "Closed"]) if n != 113 else "Open"
        rows.append({
            "id": f"NC-{n}", "title": title, "control_id": ctl, "classification": cls,
            "source": r.choice(["Internal audit", "External audit", "Self-identified", "Continuous monitoring"]),
            "opened": days_ago(opened), "due": days_ahead(due_in) if due_in >= 0 else days_ago(-due_in),
            "overdue": status != "Closed" and due_in < 0, "status": status,
            "owner_team": r.choice(["IAM Eng", "SRE", "Platform Eng", "GRC", "People Ops", "Product Security"]),
            "link": f"https://github.com/HaDoyle12/grc-ccm-demo/issues?q=NC-{n}",
        })
    return rows


def main(live: bool = False) -> int:
    return run("findings", "GitHub Project (nonconformity board)", sample, live=live)


if __name__ == "__main__":
    print(main("--live" in sys.argv))
