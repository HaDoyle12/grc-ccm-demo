# 1. How we connect to the data

> Northwind Cloud is fictional. This page describes the connection *pattern*. It works the same way with real systems.

## The core idea

Audit knowledge is relational, but it lives in five to eight different tools. Continuous control monitoring (CCM) does **not** add another system of record. It adds a thin layer that consolidates data and answers questions:

```
system of record ──► collector ──► data/<dataset>.json ──► builder ──► SQLite register ──► dashboard / CLI / AI
   (stays the source       (one per         (fixed schema,          (joins on IDs)     (one file,
    of truth)               system)          thin slice)                                queryable)
```

## The collector contract (every connection follows it)

| Step | Rule | Why |
|---|---|---|
| 1. Authenticate | Short-lived credentials only: `GITHUB_TOKEN`, a GitHub App token, Azure **OIDC** workload identity, or a vault/Keychain secret. | Nothing long-lived sits in code or in a prompt. |
| 2. Pull a thin slice | IDs, states, dates, owners and **links**. Never the raw evidence file. | *Link, never duplicate*: the source stays authoritative and the register can always be rebuilt. |
| 3. Emit a fixed schema | Write `data/<dataset>.json` in the same shape whether the data is live or sample. | Everything downstream is tool-agnostic. To swap a GRC tool you rewrite one collector. |
| 4. Fail loudly, keep last-good | On error, keep the previous file and record the failed attempt in `data/_freshness.json`. | The dashboard stays up, and the freshness gate turns staleness into a red run. |
| 5. Zero rows = failure | A collector that returns nothing raises an error instead of reporting "all clear". | An empty result looks the same as a passing control. |

See [`collectors/_common.py`](../collectors/_common.py) for the ~80 lines that enforce rules 3–5 for every collector.

## Join keys (the part that usually goes wrong)

| Join | Key | Don't use |
|---|---|---|
| Control ↔ evidence | Control ID (`A.8.8`) | Free-text control names |
| Person ↔ training ↔ access | Employee ID / immutable directory ID | Display name or email (people have several) |
| Finding ↔ control | Control ID field on the issue | Title parsing |
| Repo ↔ owner | Repo custom property or CODEOWNERS | Repo naming conventions |

Records that don't match are **reported** (for example "no LMS record"), never dropped. Unmatched people are exactly the population an auditor samples from.

## Live vs sample in this demo

`python3 refresh.py --live` runs the **Repo Security** collector against the real GitHub API, scoped to this demo repo by default (`CCM_REPOS=owner/repo,...` to widen it). The other collectors use deterministic sample data because Northwind's systems don't exist. Each one has the real-world pull command in its docstring.
