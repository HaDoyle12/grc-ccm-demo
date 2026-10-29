# 5. Examples: CLI and Actions generating audit evidence

Each recipe produces evidence that is **timestamped, reproducible and attributable**: who ran it, when, with what command, and the raw output. The Actions versions also **sign** the output.

## A. One-liners (`gh` CLI)

```bash
# A.8.32 change management: merged PRs on main in the period, with reviewers (population for sampling)
gh pr list --repo northwind/payments-api --state merged --base main \
  --search "merged:2026-07-01..2026-09-30" --limit 1000 \
  --json number,title,author,mergedAt,mergedBy,reviews,url > prs_q3.json

# ...and the exceptions: merged with no approving review
jq '[.[] | select([.reviews[] | select(.state=="APPROVED")] | length == 0)]' prs_q3.json

# A.8.4 / A.8.32: branch rules actually enforced on main
gh ruleset check main --repo northwind/payments-api

# A.5.18 access review population: members + outside collaborators
gh api orgs/northwind/members --paginate --slurp > members.json
gh api orgs/northwind/outside_collaborators --paginate --slurp > outside.json

# A.8.8 vulnerability SLA: open critical Dependabot alerts with age
gh api "repos/northwind/payments-api/dependabot/alerts?state=open&severity=critical" --paginate \
  --jq '.[] | [.number, .security_advisory.ghsa_id, .created_at] | @tsv'

# A.8.12 secrets: open secret-scanning alerts (no secret values are returned by default)
gh api "repos/northwind/payments-api/secret-scanning/alerts?state=open" --paginate \
  --jq '.[] | {number, secret_type, created_at, push_protection_bypassed}'

# A.8.15 logging: admin actions from the org audit log (Enterprise Cloud)
gh api "orgs/northwind/audit-log?phrase=action:repo.update_member+created:>=2026-10-01" --paginate

# A.5.1 policy review: last annual-review merge for a policy
gh pr list --repo northwind/policies --state merged --label annual-review \
  --search "access-control" --json mergedAt,url,mergedBy --limit 1

# Change SLA from the timeline (not a label): when was "needs-review" removed?
gh api repos/northwind/deploys/issues/2412/timeline --paginate \
  --jq '.[] | select(.event=="unlabeled" and .label.name=="needs-review") | .created_at'
```

## B. GitHub Actions that generate signed evidence

[`.github/workflows/evidence-collection.yml`](../.github/workflows/evidence-collection.yml) runs on a schedule and on demand:

1. Runs the collectors live and writes the output JSON plus a `MANIFEST.md` (command, run URL, actor, UTC time, SHA-256 of every file).
2. **Signs** the bundle with `actions/attest-build-provenance`. Each file gets a Sigstore-backed attestation linked to this repo, workflow and commit.
3. Publishes the bundle as a **GitHub Release** (`evidence-YYYY-MM-DD`). Releases are permanent, dated and linkable from a PBC response.

The auditor verifies independently:

```bash
gh release download evidence-2026-10-26 --repo HaDoyle12/grc-ccm-demo
gh attestation verify repo_security.json --repo HaDoyle12/grc-ccm-demo
```

## C. Other evidence patterns worth copying

| Pattern | How | Control |
|---|---|---|
| **Snapshot before refresh** | Weekly job archives *last week's* dashboard as a Release **before** pulling new data. You keep an unbroken weekly record of what management saw. | 9.1 / 9.3 (clauses) |
| **Quarterly policy review report** | Scheduled workflow lists policies past 365 days and opens (or updates) one tracking issue. | 5.1 |
| **Failure → tracking issue** | A failed refresh comments on one open "refresh is failing" issue, so a red run always reaches a person. | 8.16 |
| **Required status check as a control** | Make a compliance check a required check in a ruleset. The PR record then proves it ran on every change. | 8.25, 8.32 |
| **Issue-form intake** | Findings/exceptions submitted through an issue form, so every record has the same fields and an audit trail. | 5.24, 10.2 |
| **Attach walkthroughs** | `gh issue comment N --attach walkthrough.mp4` puts process-walkthrough evidence directly on the control issue. | any |
