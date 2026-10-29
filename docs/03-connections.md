# 3. Connections we can use

| Connection | Use it for | Auth | Notes |
|---|---|---|---|
| **`gh api` (REST)** | Repos, rulesets, alerts, org members, issues, timelines | `gh auth` / `GH_TOKEN` | `--paginate --slurp` returns one JSON array; `--jq` filters inline. |
| **`gh api graphql`** | Projects (v2) fields, multi-object queries in one call | same | Lower call count for board-style data. |
| **First-class `gh` commands** | `gh project item-list`, `gh issue list --json`, `gh ruleset list`, `gh release` | same | Stable JSON output (`--json field,…`), easier than raw API. |
| **GitHub Actions `GITHUB_TOKEN`** | Anything scoped to the workflow's own repo | auto-issued per run, expires at job end | Declare least-privilege `permissions:` per workflow. |
| **GitHub App installation token** | Cross-repo / org-wide collection | App private key in a secret → token per run | Preferred over personal access tokens for org-wide bots. |
| **Actions OIDC → Azure** | Microsoft Graph, Kusto, Key Vault, storage | `azure/login` with federated credential, no stored secret | Same pattern for AWS/GCP. |
| **Microsoft Graph** | SharePoint evidence inventory, Entra groups, Teams/Outlook notifications | OIDC / `az account get-access-token` | Inventory metadata only; never download evidence into the register. |
| **Vendor REST APIs** | GRC tool, LMS, HRIS report export, ticketing | API key from a vault / repo secret | Wrap with a tiny CLI so keys never appear in commands. |
| **Webhooks / audit-log streaming** | Near-real-time events (setting changes, rule bypasses) | Signed webhook secret | `gh webhook forward` (official extension since gh v2.100) for local testing. |
| **Copilot CLI + MCP servers** | Natural-language questions over the register, drafting chases | your session | Point it at `data/register.db` (see [04](04-gh-cli-for-auditors.md)). |

**Least privilege in practice:** each workflow in [`.github/workflows`](../.github/workflows) declares only the scopes it needs. The failure reporter deliberately uses `GITHUB_TOKEN`, not the collector credential, so an alert never depends on the credential whose failure it is reporting.
