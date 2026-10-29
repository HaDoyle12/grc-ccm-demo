"""Collector: control library + assessment state  (system of record: GRC platform).

Real-world equivalent: a GRC tool's REST API (e.g. /api/v2/controls and
/api/v2/assessments on ZenGRC, the Table API on ServiceNow GRC, or a Purview
Compliance Manager export). The live pull would be:

    curl -su "$GRC_KEY_ID:$GRC_KEY_SECRET" "$GRC_BASE/api/v2/assessments?limit=500"

Each control carries TWO ratings:
  * strict_status -- our internal bar (any stale evidence or open finding = red)
  * audit_status  -- what an external auditor would conclude today
The dashboard toggles between them, so a team can run a stricter-than-audit
program without alarming stakeholders who only need the audit view.
"""
from __future__ import annotations

import sys

from _common import days_ago, rng, run

# ISO/IEC 27001:2022 Annex A clause IDs with short paraphrased descriptions.
ANNEX_A = {
    "5": ("Organizational", [
        "Security policy set", "Security roles defined", "Duties kept separate", "Leadership accountability",
        "Authority contacts", "Special-interest group contacts", "Threat intelligence", "Security in project work",
        "Asset inventory", "Acceptable use of assets", "Asset return on exit", "Information classification",
        "Information labelling", "Information transfer rules", "Access control rules", "Identity lifecycle",
        "Authentication secrets", "Access rights reviews", "Supplier security", "Security in supplier contracts",
        "ICT supply chain", "Supplier monitoring", "Cloud service security", "Incident planning",
        "Event triage", "Incident response", "Learning from incidents", "Evidence handling",
        "Security during disruption", "ICT continuity readiness", "Legal and contractual requirements",
        "Intellectual property", "Records protection", "Privacy of personal data",
        "Independent security review", "Policy compliance checks", "Documented procedures"]),
    "6": ("People", [
        "Pre-hire screening", "Employment terms", "Security awareness training", "Disciplinary process",
        "Duties after termination", "Confidentiality agreements", "Remote working", "Event reporting"]),
    "7": ("Physical", [
        "Physical perimeters", "Physical entry", "Securing offices", "Physical monitoring",
        "Environmental threats", "Secure areas", "Clear desk and screen", "Equipment siting",
        "Off-site assets", "Storage media", "Supporting utilities", "Cabling security",
        "Equipment maintenance", "Secure disposal"]),
    "8": ("Technological", [
        "Endpoint devices", "Privileged access", "Information access restriction", "Source code access",
        "Secure authentication", "Capacity management", "Malware protection", "Technical vulnerabilities",
        "Configuration management", "Information deletion", "Data masking", "Data leakage prevention",
        "Backups", "Redundancy", "Logging", "Monitoring", "Clock synchronisation", "Privileged utilities",
        "Software installation", "Network security", "Network services", "Network segregation",
        "Web filtering", "Cryptography", "Secure development lifecycle", "Application security requirements",
        "Secure architecture", "Secure coding", "Security testing", "Outsourced development",
        "Environment separation", "Change management", "Test information", "Audit testing protection"]),
}

# Which fictional team owns which clause, and which system produces its evidence.
DOMAIN_RULES = [
    (("5.1", "5.2", "5.3", "5.4", "5.31", "5.32", "5.35", "5.36", "5.37"), "Governance", "GRC", "Policy repo"),
    (("5.15", "5.16", "5.17", "5.18", "8.2", "8.3", "8.5", "8.18"), "Identity & Access", "IAM Eng", "Identity provider"),
    (("5.19", "5.20", "5.21", "5.22", "5.23", "8.30"), "Vendor Management", "Procurement", "Vendor tracker"),
    (("5.24", "5.25", "5.26", "5.27", "5.28", "6.8"), "Incident Response", "SIRT", "Incident tracker"),
    (("5.29", "5.30", "8.13", "8.14", "8.6"), "Resilience & Backups", "SRE", "Cloud monitoring"),
    (("6.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "5.11"), "People & HR", "People Ops", "HRIS + LMS"),
    (("8.4", "8.25", "8.26", "8.27", "8.28", "8.29", "8.31", "8.32", "8.33", "8.9"), "Secure SDLC", "Platform Eng", "GitHub"),
    (("8.8", "8.7", "8.1", "8.19", "5.7"), "Vulnerability Mgmt", "Product Security", "GitHub + EDR"),
    (("8.15", "8.16", "8.17", "8.34"), "Logging & Monitoring", "Detection Eng", "SIEM"),
    (("8.20", "8.21", "8.22", "8.23"), "Network", "NetOps", "Cloud config"),
]


def _domain(cid: str):
    for ids, domain, owner, system in DOMAIN_RULES:
        if cid in ids:
            return domain, owner, system
    if cid.startswith("7."):
        return "Physical Security", "Workplace", "Badge system"
    return "Data Protection", "Privacy Eng", "Data catalog"


def sample():
    r = rng("controls")
    rows = []
    for theme_no, (theme, names) in ANNEX_A.items():
        for i, name in enumerate(names, start=1):
            cid = f"{theme_no}.{i}"
            domain, owner, system = _domain(cid)
            automated = system in ("GitHub", "Identity provider", "Cloud config", "SIEM", "GitHub + EDR", "Cloud monitoring")
            automation = "Automated" if automated and r.random() < 0.8 else ("Semi-automated" if r.random() < 0.5 else "Manual")
            last_tested = r.randint(1, 30) if automation == "Automated" else r.choice([r.randint(10, 85), r.randint(10, 85), r.randint(60, 200), r.randint(300, 420)])
            open_findings = r.choices([0, 0, 0, 0, 0, 0, 1, 2], k=1)[0]
            evidence = r.choice([0, 1, 2, 3, 4, 5, 6]) if automation == "Manual" else r.randint(2, 14)
            # Strict internal bar: evidence < 90 days old, no open finding, at least 2 artefacts.
            if evidence == 0 or last_tested > 365:
                strict = "Not effective"
            elif open_findings or last_tested > 90 or evidence < 2:
                strict = "Needs attention"
            else:
                strict = "Effective"
            # Audit bar: tested within the 12-month period and not missing evidence entirely.
            audit = "Effective" if evidence > 0 and last_tested <= 365 else "Exception"
            rows.append({
                "control_id": f"A.{cid}", "clause": cid, "theme": theme, "title": name,
                "domain": domain, "owner_team": owner, "evidence_system": system,
                "automation": automation, "last_tested": days_ago(last_tested),
                "open_findings": open_findings, "evidence_count": evidence,
                "strict_status": strict, "audit_status": audit,
                "grc_link": f"https://grc.example.com/controls/A.{cid}",
            })
    return rows


def main(live: bool = False) -> int:
    return run("controls", "GRC platform (assessments API)", sample, live=live)


if __name__ == "__main__":
    print(main("--live" in sys.argv))
