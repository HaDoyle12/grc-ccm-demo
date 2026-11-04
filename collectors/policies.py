"""Collector: policy & standard review dates  (system of record: policy repo in git).

The last review is the most recent merged PR that touched the policy file with
the "annual-review" label. Live pull per policy:

    gh pr list --repo northwind/policies --state merged --label annual-review \
      --search "path:policies/access-control.md" --json mergedAt,url --limit 1

Policy vs standard check: every standard names a parent policy, and both carry
their measurable requirements in YAML front matter. Live, read both files at the
same ref and compare:

    gh repo read-file standards/access-control.md --repo northwind/policies

A standard is flagged when it
  * Conflict -- sets a weaker value than its parent policy for the same requirement
  * Drift    -- was last reviewed before its parent policy, so it may not reflect it
"""
from __future__ import annotations

import sys

from _common import days_ago, rng, run

POLICIES = ["Information Security Policy", "Access Control Standard", "Acceptable Use Policy", "Cryptography Standard",
            "Secure Development Standard", "Vulnerability Management Standard", "Incident Response Plan",
            "Business Continuity Policy", "Supplier Security Standard", "Data Classification Standard",
            "Logging & Monitoring Standard", "Physical Security Policy", "Security Awareness Policy",
            "Change Management Standard", "AI Use Policy", "Data Retention Standard"]


# Each standard implements one parent policy.
PARENT = {p: "Information Security Policy" for p in POLICIES if p.endswith("Standard")}

# (requirement, unit, stricter-direction, policy value, standard, standard value)
# "max" = smaller is stricter (e.g. days to fix); "min" = larger is stricter.
REQUIREMENTS = [
    ("Minimum password length", "chars", "min", 14, "Access Control Standard", 12),
    ("Privileged access review cadence", "days", "max", 90, "Access Control Standard", 90),
    ("Minimum TLS version", "", "min", 1.2, "Cryptography Standard", 1.2),
    ("Critical vulnerability remediation", "days", "max", 30, "Vulnerability Management Standard", 45),
    ("Security log retention", "days", "min", 365, "Logging & Monitoring Standard", 365),
    ("Supplier reassessment cadence", "months", "max", 12, "Supplier Security Standard", 12),
]


def conflicts(requirements=REQUIREMENTS):
    """Return {standard: [detail, ...]} where the standard is weaker than its policy."""
    out: dict[str, list[str]] = {}
    for req, unit, direction, pol_v, std, std_v in requirements:
        weaker = std_v > pol_v if direction == "max" else std_v < pol_v
        if weaker:
            u = f" {unit}" if unit else ""
            out.setdefault(std, []).append(f"{req}: standard says {std_v}{u}, {PARENT[std]} requires "
                                           f"{'≤' if direction == 'max' else '≥'} {pol_v}{u}")
    return out


def alignment(rows):
    """Add doc_type / parent_policy / alignment / alignment_detail to each row."""
    by_name = {r["policy"]: r for r in rows}
    bad = conflicts()
    for r in rows:
        parent = PARENT.get(r["policy"])
        r["doc_type"] = "Standard" if parent else "Policy"
        r["parent_policy"] = parent or ""
        if not parent:
            r["alignment"], r["alignment_detail"] = "n/a", ""
        elif r["policy"] in bad:
            r["alignment"], r["alignment_detail"] = "Conflict", "; ".join(bad[r["policy"]])
        elif r["last_review"] < by_name[parent]["last_review"]:
            r["alignment"] = "Drift"
            r["alignment_detail"] = (f"Last reviewed {r['last_review']}, before {parent} was revised on "
                                     f"{by_name[parent]['last_review']}; re-review against the current policy")
        else:
            r["alignment"], r["alignment_detail"] = "Aligned", ""
    return rows


def sample():
    r = rng("policies")
    rows = []
    for p in POLICIES:
        age = r.randint(20, 470)
        rows.append({"policy": p, "last_review": days_ago(age), "age_days": age,
                     "status": "Overdue" if age > 365 else ("Due < 60 days" if age > 305 else "Current"),
                     "owner_team": r.choice(["GRC", "IAM Eng", "SRE", "Legal", "People Ops"]),
                     "link": f"https://github.com/HaDoyle12/grc-ccm-demo/blob/main/docs/06-pipeline-processes.md"})
    return alignment(rows)


def main(live: bool = False) -> int:
    return run("policies", "Policy repo (git history via gh)", sample, live=live)


if __name__ == "__main__":
    print(main("--live" in sys.argv))
