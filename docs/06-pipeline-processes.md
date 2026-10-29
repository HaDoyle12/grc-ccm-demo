# 6. The processes that feed the dashboard

This is the full inventory of every process that **monitors a system and updates the dashboard**. It follows the same architecture as a production GRC register: collectors per system of record → a builder that joins them → a renderer → scheduled GitHub Actions that refresh, gate, archive and alert.

```
                         systems of record  (each stays authoritative)
 GRC platform  GitHub API  GitHub Project  GitHub Issues  Policy repo  HRIS+LMS  Identity provider  Evidence store
      │            │             │               │             │          │             │                │
  controls   repo_security   findings     risks · changes   policies   training   access_reviews     evidence
      └────────────┴─────────────┴───────────────┴─────────────┴──────────┴─────────────┴────────────────┘
                                       │   data/<dataset>.json  +  data/_freshness.json
                                       ▼
                              build_register.py ──► data/register.db (SQLite) · exports/*.csv · data/history.json
                                       │
                                  gen_html.py ──► site/index.html  (single self-contained file)
                                       │
         ┌─────────────────────────────┼──────────────────────────────────┐
         ▼                             ▼                                  ▼
 check_freshness.py           deploy to GitHub Pages            weekly snapshot Release
 (red run if stale)          (actions/deploy-pages)             (audit trail of what management saw)
         │
         └──► on failure: comment on ONE open "refresh is failing" issue
```

## 1. Orchestration & publishing

| Process | Role | Trigger |
|---|---|---|
| [`refresh.py`](../refresh.py) | **Master orchestrator.** Runs every collector in dependency order (controls before evidence), then the builder, then the renderer. `--live` uses live connectors where they exist and last-good data elsewhere. | Weekly workflow · on demand |
| [`build_register.py`](../build_register.py) | Joins every `data/*.json` into `data/register.db` (one table per dataset + a `control_coverage` view), writes `exports/*.csv` for Excel users, and appends one row of headline stats to `data/history.json` for trend charts. | Called by `refresh.py` |
| [`gen_html.py`](../gen_html.py) | Renders `site/index.html`: one file, no CDN, inline SVG charts, every value HTML-escaped. Because it's one file, the same artefact can be published, attached to a ticket, or archived as evidence. | Called by `refresh.py` |
| [`check_freshness.py`](../check_freshness.py) | **Gate.** Fails the run if any dataset's last success is older than 8 days or its last attempt failed. It also fails if it checked zero datasets, so it can never pass by accident. | Every workflow run |
| Pages deploy | `actions/upload-pages-artifact` + `actions/deploy-pages` publish `site/`. | Weekly workflow |

## 2. Data-source collectors (the "monitors")

Each collector watches **one** system of record, writes **one** dataset and feeds **one** tab. All of them go through [`collectors/_common.py`](../collectors/_common.py), which enforces atomic writes, last-good fallback, freshness recording and "zero rows = failure".

| Collector | Watches | Real-world pull | Feeds tab | Design rule |
|---|---|---|---|---|
| [`controls.py`](../collectors/controls.py) | GRC platform assessments | GRC REST API (`/assessments`) | **ISO Controls**, Overview | Two ratings per control: **strict** (internal bar) and **audit** (external bar), so you can run a tougher program without alarming people. |
| [`evidence.py`](../collectors/evidence.py) | Evidence store + GitHub Releases | Microsoft Graph `/drives/{id}/items/{id}/children` (metadata only) · `gh release list` | **Evidence** | Inventory and links only. Evidence files are never copied into the register. |
| [`findings.py`](../collectors/findings.py) | Nonconformity board (GitHub Project) | `gh project item-list N --owner org --format json` | **Findings** | Overdue is computed from the open date and remediation window, not a hand-set label. |
| [`risks.py`](../collectors/risks.py) | Risk issues (label) | `gh issue list --label "Risk Register" --json …` | **Risk Register** | Last-worked = issue `updatedAt`, so stale risks surface by themselves. |
| [`policies.py`](../collectors/policies.py) | Policy repo git history | `gh pr list --state merged --label annual-review` | **Policies** | Review date = merged PR, so the evidence is the PR and its approvals. |
| [`training.py`](../collectors/training.py) | HRIS roster + LMS | HRIS report export + LMS API | **Training** | Join on employee ID. Roster people with no LMS record are reported, never dropped. |
| [`changes.py`](../collectors/changes.py) | Emergency-change issues | `gh api …/issues/{n}/timeline` | **Change Mgmt** | SLA clock from **timeline events**, because a bot's label threshold can drift from the written policy. |
| [`access_reviews.py`](../collectors/access_reviews.py) | Identity provider + review tool | Graph `/groups/{id}/members` · `gh api orgs/{org}/members` | **Access Reviews** | The population comes from the source, not from the review tool's own list. |
| [`repo_security.py`](../collectors/repo_security.py) | GitHub repos (**runs live**) | `gh api repos/{o}/{r}`, `/rules/branches/main`, `/dependabot/alerts`, `/code-scanning/alerts` | **Repo Security** | A setting the token can't read is recorded as **unknown**, never as a pass. |

## 3. Scheduled bots (GitHub Actions)

| Workflow | What it does | Trigger | Permissions |
|---|---|---|---|
| [`weekly-dashboard.yml`](../.github/workflows/weekly-dashboard.yml) | **1)** Archives *last week's* live dashboard as a Release **before** refreshing, giving an unbroken weekly history of what management saw. **2)** Runs `refresh.py --live`. **3)** Runs the freshness gate. **4)** Commits refreshed data (diffable week to week). **5)** Deploys Pages. **6)** On failure, comments on one tracking issue. | Mon 12:00 UTC · manual | `contents: write`, `pages: write`, `id-token: write`, `issues: write` |
| [`evidence-collection.yml`](../.github/workflows/evidence-collection.yml) | Runs live collectors, writes a `MANIFEST.md` (command, run URL, actor, time, SHA-256s), **signs every file** with `actions/attest-build-provenance`, and publishes a dated `evidence-YYYY-MM-DD` Release. | 1st of month · manual | `contents: write`, `id-token: write`, `attestations: write` |
| [`quarterly-policy-review.yml`](../.github/workflows/quarterly-policy-review.yml) | Lists policies past 365 days (or due within 60) and opens or updates **one** idempotent quarterly tracking issue. | 1st of Jan/Apr/Jul/Oct · manual | `contents: read`, `issues: write` |
| [`ci.yml`](../.github/workflows/ci.yml) | Unit tests for the gate and the HTML escaping, plus a full pipeline run on every PR. | PR · push | `contents: read` |

## 4. Design rules baked into every process

1. **Link, never duplicate.** The register holds IDs, states and URLs. The system of record stays authoritative, and the register can be rebuilt from scratch at any time.
2. **Keep last-good, but make staleness loud.** A failed pull never blanks the dashboard, and it never goes unnoticed: the freshness gate turns it into a red run.
3. **A red run must reach a person.** The failure step comments on a single open tracking issue (no new issue each week, which trains people to close them unread). It uses `GITHUB_TOKEN`, not the collector credential, so the alert path never depends on the credential that may have just failed.
4. **A gate that checked nothing has not passed.** Collectors fail on zero rows, and the freshness gate fails on zero datasets checked.
5. **Unknown ≠ pass.** Anything a token can't see is shown as `?`.
6. **Compute from events, not labels.** SLAs come from issue timelines and dates, not from labels a bot or person sets.
7. **Version everything.** Data is committed each week, so `git diff` between weeks *is* the change log for the control environment.
8. **Strict internally, honest externally.** The same data, two thresholds, one toggle.

## 5. Build your own (swap the connectors, keep the model)

| Slice | This demo | Swap in your tool |
|---|---|---|
| Control ratings | `controls.py` (sample) | ZenGRC / ServiceNow GRC / AuditBoard / Purview Compliance Manager API |
| Evidence inventory | `evidence.py` | SharePoint via Graph · S3 / Blob listing · your DMS |
| Findings | GitHub Project | Jira / Azure DevOps / ServiceNow |
| Training | HRIS + LMS | Workday + Cornerstone / Docebo / Viva Learning |
| Access | IdP + review tool | Entra ID Access Reviews / Okta / SailPoint |
| Repo security | **GitHub API (live)** | the same, on your org |

Only the collector changes. The JSON schema, builder, renderer, gate and workflows stay as they are.
