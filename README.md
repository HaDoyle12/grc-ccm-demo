# Continuous Control Monitoring with GitHub CLI + Actions — demo

**Live dashboard:** https://hadoyle12.github.io/grc-ccm-demo/

> ⚠️ **Everything here is fictional.** *Northwind Cloud* is a made-up company and every number is synthetic sample data. The one exception is the **Repo Security** tab, which can run live against *this demo repository only*.

This repo is a working miniature of a continuous control monitoring (CCM) program for **ISO/IEC 27001:2022**. Collectors pull a thin slice from each system of record. A builder joins the slices into one queryable SQLite register. A renderer publishes a single-file dashboard to GitHub Pages. Scheduled GitHub Actions refresh it, gate it for freshness, archive it, and produce **signed, verifiable audit evidence**.

## What to read

| # | Doc | Answers |
|---|---|---|
| 1 | [How we connect to the data](docs/01-data-connections.md) | The collector contract, auth, join keys, failure handling |
| 2 | [Data sets we can work with](docs/02-datasets.md) | Every source, mapped to Annex A controls and dashboard tabs |
| 3 | [Connections we can use](docs/03-connections.md) | `gh api`, GraphQL, Actions tokens, GitHub Apps, OIDC, Microsoft Graph, webhooks |
| 4 | [New GitHub CLI features for auditors](docs/04-gh-cli-for-auditors.md) | Attestations, release verification, rulesets, semantic search, attachments, Copilot |
| 5 | [Examples: CLI and Actions generating audit evidence](docs/05-audit-evidence-examples.md) | Copy-paste one-liners and the signed-evidence workflow |
| 6 | [The processes that feed the dashboard](docs/06-pipeline-processes.md) | Every collector, builder, gate and bot, and the design rules behind them |

## Run it locally (Python 3.10+, no dependencies)

```bash
python3 refresh.py                 # sample data -> data/register.db -> site/index.html
python3 refresh.py --live          # Repo Security tab pulls live from the GitHub API (needs `gh auth login`)
python3 check_freshness.py         # the gate that CI runs
open site/index.html

# query the register directly, or ask Copilot CLI to
sqlite3 data/register.db "SELECT control_id,title,strict_status FROM controls WHERE strict_status='Not effective'"
sqlite3 data/register.db "SELECT * FROM control_coverage WHERE linked_evidence = 0"
```

## Layout

```
collectors/         one file per system of record -> data/<dataset>.json
build_register.py   joins data/ -> data/register.db + exports/*.csv + history
gen_html.py         register -> site/index.html (self-contained, GitHub Pages)
refresh.py          runs the whole pipeline
check_freshness.py  fails if any source is stale (and if it checked nothing)
quarterly_policy_review.py, report_failure.py, evidence/make_bundle.py   bots used by the workflows
.github/workflows/  weekly refresh + deploy · signed evidence · quarterly policy review · CI
```

## Verify the evidence yourself

```bash
gh release list --repo HaDoyle12/grc-ccm-demo
gh release download <evidence-tag> --repo HaDoyle12/grc-ccm-demo
gh attestation verify repo_security.json --repo HaDoyle12/grc-ccm-demo
```

ISO/IEC 27001 control titles in this repo are short paraphrases written for the demo, not the standard's text.
