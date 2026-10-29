# 2. Data sets we can work with

Each row is one collector feeding one dashboard tab. ✅ = native to GitHub, so `gh`/Actions can collect it with no other tool.

| Data set | System of record | Native? | ISO 27001:2022 Annex A | What the dashboard shows |
|---|---|---|---|---|
| Control library + assessment ratings | GRC platform (ZenGRC, ServiceNow GRC, Purview Compliance Manager, AuditBoard…) | — | all | Strict vs audit status per control |
| Branch protection / rulesets | GitHub repos | ✅ | 8.4, 8.32 | Repos without required reviews |
| Secret scanning + push protection | GitHub Advanced Security | ✅ | 5.17, 8.12 | Coverage %, open secrets |
| Dependabot & code scanning alerts | GitHub Advanced Security | ✅ | 8.8, 8.28, 8.29 | Open criticals and age vs SLA |
| Pull-request reviews & merge history | GitHub | ✅ | 8.32 | Changes merged without a second reviewer |
| Emergency-change issues + timelines | GitHub Issues | ✅ | 8.32 | Review SLA computed from timeline events |
| Nonconformities / findings board | GitHub Projects | ✅ | 10.2 (clause), 5.35, 5.36 | Open, overdue, by classification |
| Risk register | GitHub Issues (label) | ✅ | 6.1 (clause) | Risks by severity, last-worked date |
| Policy review history | Policy repo (git) | ✅ | 5.1, 5.37 | Overdue policy reviews |
| Org members, outside collaborators, 2FA, teams | GitHub org API | ✅ | 5.15, 5.16, 5.18, 8.2, 8.5 | Access review population |
| Audit log (org/enterprise) | GitHub audit log API / streaming | ✅ | 8.15, 8.16 | Admin actions, setting changes |
| Actions run logs + artifact attestations | GitHub Actions | ✅ | 8.25, 8.29, 8.32 | Signed, verifiable evidence |
| Employee / contractor roster | HRIS (Workday etc.) | — | 6.1, 6.5 | Population for training and access |
| Training completions | LMS | — | 6.3 | Completion by cohort, no-record list |
| Identity groups & access decisions | Entra ID / Okta (Microsoft Graph) | — | 5.15, 5.18 | Campaign completion, revocations |
| Evidence files | SharePoint / OneDrive (Microsoft Graph, metadata only) | — | all | Evidence age, staleness |
| Telemetry (uptime, backups, AI assessments) | Kusto / Log Analytics / SIEM | — | 8.13, 8.16 | Backup success, monitoring coverage |

**Start with the ✅ rows.** They need no new tooling or contracts, and they give the fastest "this control is monitored, not sampled" result.
