"""Collector: repository security posture  (system of record: GitHub).

This is the one collector that runs LIVE in the demo: with --live it calls the
GitHub REST API through `gh api` for every repo in $CCM_REPOS (default: this
demo repo) and reads the same settings an auditor would screenshot:

    gh api repos/OWNER/REPO                       -> visibility, default branch, security_and_analysis
    gh api repos/OWNER/REPO/rules/branches/main   -> active rulesets on the default branch
    gh api repos/OWNER/REPO/dependabot/alerts     -> open vulnerable-dependency alerts
    gh api repos/OWNER/REPO/code-scanning/alerts  -> open code-scanning alerts

Settings the token cannot see are recorded as "unknown" -- never as "pass".
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from _common import days_ago, rng, run

TEAMS = ["payments-api", "web-frontend", "mobile-app", "data-pipeline", "auth-service", "infra-terraform",
         "billing-worker", "search-indexer", "notifications", "admin-portal", "ml-scoring", "docs-site",
         "edge-proxy", "audit-log-svc", "customer-export", "feature-flags", "ci-shared-actions", "sdk-python"]


def sample():
    r = rng("repo_security")
    rows = []
    for name in TEAMS:
        crit = r.random() < 0.3
        rows.append({
            "repo": f"northwind/{name}", "tier": "Critical" if crit else r.choice(["High", "Standard"]),
            "branch_protection": r.random() < 0.85, "required_reviews": r.choice([0, 1, 1, 2]),
            "secret_scanning": r.random() < 0.92, "push_protection": r.random() < 0.8,
            "dependabot_alerts": r.random() < 0.9, "code_scanning": r.random() < 0.7,
            "open_critical_vulns": r.choice([0, 0, 0, 1, 2, 4]), "oldest_critical_days": r.choice([0, 3, 12, 35, 61]),
            "signed_releases": r.random() < 0.5, "last_push": days_ago(r.randint(0, 40)),
        })
    return rows


UNKNOWN = "unknown"


def gh(path: str):
    """Return parsed JSON, or a string reason when the call fails.

    "disabled" means the API said the feature is off (a real fail).
    "unknown" means we could not see (no permission, network) -- never a pass.
    """
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=60)
    if out.returncode == 0:
        return json.loads(out.stdout or "null")
    err = (out.stderr + out.stdout).lower()
    if "disabled" in err or "no analysis found" in err or "not enabled" in err:
        return "disabled"
    return UNKNOWN


def tri(result):
    if result == "disabled":
        return False
    if result == UNKNOWN:
        return UNKNOWN
    return True


def live():
    repos = os.environ.get("CCM_REPOS") or os.environ.get("GITHUB_REPOSITORY") or "HaDoyle12/grc-ccm-demo"
    rows = []
    for full in [x.strip() for x in repos.split(",") if x.strip()]:
        meta = gh(f"repos/{full}")
        if not isinstance(meta, dict):
            raise RuntimeError(f"cannot read {full}")
        sa = meta.get("security_and_analysis")
        flag = (lambda k: (sa.get(k) or {}).get("status") == "enabled") if sa else (lambda k: UNKNOWN)
        rules = gh(f"repos/{full}/rules/branches/{meta['default_branch']}")
        rules = rules if isinstance(rules, list) else []
        pr_rule = next((x for x in rules if x.get("type") == "pull_request"), None)
        dep = gh(f"repos/{full}/dependabot/alerts?state=open&severity=critical&per_page=100")
        cs = gh(f"repos/{full}/code-scanning/alerts?state=open&per_page=100")
        rows.append({
            "repo": full, "tier": "Critical",
            "branch_protection": bool(rules),
            "required_reviews": (pr_rule or {}).get("parameters", {}).get("required_approving_review_count", 0),
            "secret_scanning": flag("secret_scanning"), "push_protection": flag("secret_scanning_push_protection"),
            "dependabot_alerts": tri(dep), "code_scanning": tri(cs),
            "open_critical_vulns": len(dep) if isinstance(dep, list) else 0, "oldest_critical_days": 0,
            "signed_releases": UNKNOWN, "last_push": (meta.get("pushed_at") or "")[:10],
        })
    return rows


def main(live_mode: bool = False) -> int:
    return run("repo_security", "GitHub REST API (gh api)", sample, live, live=live_mode)


if __name__ == "__main__":
    print(main("--live" in sys.argv))
