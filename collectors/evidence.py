"""Collector: evidence inventory  (system of record: evidence store + GitHub Releases).

Inventory only -- the register stores filename, date, hash and a LINK, never
the file itself. Two stores are shown:
  * SharePoint / OneDrive via Microsoft Graph:
      GET /drives/{drive}/items/{folder}/children   (recursive, metadata only)
  * GitHub Releases, where the Actions evidence jobs publish signed bundles:
      gh release list --repo HaDoyle12/grc-ccm-demo --json tagName,publishedAt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import DATA, days_ago, rng, run

KINDS = [("Branch protection snapshot", "GitHub Actions", "A.8.32"), ("Org member export", "GitHub Actions", "A.5.18"),
         ("Dependabot alert export", "GitHub Actions", "A.8.8"), ("Secret scanning summary", "GitHub Actions", "A.8.12"),
         ("Workflow run log", "GitHub Actions", "A.8.25"), ("Signed build attestation", "GitHub Actions", "A.8.29"),
         ("Training completion report", "LMS export", "A.6.3"), ("Access review sign-off", "Review tool", "A.5.18"),
         ("Backup restore test", "SharePoint", "A.8.13"), ("Supplier SOC 2 report", "SharePoint", "A.5.22"),
         ("Incident post-mortem", "SharePoint", "A.5.27"), ("Firewall rule review", "SharePoint", "A.8.20")]


def sample():
    r = rng("evidence")
    rows = []
    controls = json.loads((DATA / "controls.json").read_text())["rows"] if (DATA / "controls.json").exists() else []
    for i in range(1, 121):
        kind, store, ctl = r.choice(KINDS)
        if controls and r.random() < 0.5:
            ctl = r.choice(controls)["control_id"]
        age = r.randint(0, 35) if store == "GitHub Actions" else r.choice([r.randint(10, 80), r.randint(10, 80), r.randint(90, 400)])
        rows.append({"evidence_id": f"EV-{i:04d}", "name": kind, "store": store, "control_id": ctl,
                     "collected": days_ago(age), "age_days": age, "stale": age > 90,
                     "sha256": f"{r.getrandbits(256):064x}"[:16] + "…",
                     "link": "https://github.com/HaDoyle12/grc-ccm-demo/releases" if store == "GitHub Actions"
                             else "https://evidence.example.com/" + kind.lower().replace(" ", "-")})
    return rows


def main(live: bool = False) -> int:
    return run("evidence", "Evidence store (Graph) + GitHub Releases", sample, live=live)


if __name__ == "__main__":
    print(main("--live" in sys.argv))
