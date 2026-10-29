# 4. New GitHub CLI features that help an auditor

Version numbers come from the [cli/cli release notes](https://github.com/cli/cli/releases). Check yours with `gh --version`; upgrade with `brew upgrade gh` or `winget upgrade GitHub.cli`.

## Verify evidence wasn't tampered with

| Feature | Since | Auditor use | Example |
|---|---|---|---|
| **Artifact attestations** | v2.49 | Prove an evidence file was produced by a specific workflow in a specific repo, unmodified. | `gh attestation verify evidence.json --repo HaDoyle12/grc-ccm-demo` |
| **Release attestations** | v2.81 | Verify a whole evidence release, or one downloaded asset, against its signed attestation. | `gh release verify evidence-2026-10-26` · `gh release verify-asset evidence-2026-10-26 ./repo-security.json` |
| **`gh auth status --json`** | v2.81 | Record *which identity and scopes* collected the evidence, as part of the evidence. | `gh auth status --json hosts` |
| **Expiring, auto-refreshing tokens** (preview) | v2.103 | Collection jobs run on short-lived credentials, which answers the auditor's "long-lived key" question. | `gh auth login --expiring` |

## Pull populations and samples

| Feature | Since | Auditor use | Example |
|---|---|---|---|
| **Rulesets** | v2.32 | Show the branch rules actually enforced on a branch, including inherited org rules. | `gh ruleset check main --repo org/repo` |
| **Projects by field name** | v2.97 | Export a findings board without looking up field IDs. | `gh project item-list 12 --owner northwind --format json` |
| **Issue types, sub-issues, blocked-by** | v2.94 | Model finding → corrective action → task as real relationships, then query them. | `gh issue create --type Finding --parent 100` |
| **Advanced + semantic issue search** | v2.79 / v2.98 | Find every issue *about* a topic ("access review exceptions") even when titles differ. | `gh search issues "access review exception" --search-type semantic --owner northwind` |
| **Read files at a point in time** (preview) | v2.95 | Pull the policy text *as it was* on the audit date, with no clone. | `gh repo read-file policies/access.md --ref 2026-06-30-tag --repo northwind/policies` |
| **`gh api --paginate --slurp`** | v2.48 | One JSON array for an entire population (all members, all alerts). | `gh api orgs/northwind/members --paginate --slurp` |

## Document and close the loop

| Feature | Since | Auditor use | Example |
|---|---|---|---|
| **Attach screenshots/video to issues & PRs** | v2.99 | Attach walkthrough evidence straight to the finding or control issue. | `gh issue comment 123 --attach ./walkthrough.mp4` |
| **Close as duplicate** | v2.88 | Clean finding de-duplication with a traceable link. | `gh issue close 123 --duplicate-of 456` |
| **`gh workflow run` returns the run URL** | v2.87 | Kick off an on-demand evidence pull and cite its run link immediately. | `gh workflow run evidence-collection.yml` |
| **Discussions** | v2.94 | Run audit Q&A or management-review threads from the CLI. | `gh discussion list` |
| **Issue artifacts** (private preview) | v2.103 | Store versioned artefacts on an issue. A natural fit for "evidence attached to a request". | `gh issue artifact list 123` |

## AI on top of the register

| Feature | Since | Auditor use |
|---|---|---|
| **`gh copilot`** (runs GitHub Copilot CLI) | v2.86 | Ask the register questions in plain English: *"Which Annex A 8.x controls have no evidence newer than 90 days?"* Copilot runs the `sqlite3` query against `data/register.db` and shows its work. |
| **Copilot code review from the CLI** | v2.88 | `gh pr create --reviewer @copilot`. An automated second reviewer on policy/control-as-code PRs. Not a substitute for the required human approval. |
| **Agent tasks** | v2.80 (JSON v2.88) | `gh agent-task create "Refresh the evidence README for Q4"` delegates routine documentation upkeep. |
| **Agent skills** (preview) | v2.90 | `gh skill install` packages a repeatable audit procedure (e.g. "build the PBC package") so every team runs it the same way. |

> **Guardrail:** AI output is a draft. Evidence is the underlying query result or signed artifact, not the model's summary of it.
