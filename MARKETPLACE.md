# [Company Name] internal Claude Code marketplace

This repository is the private Claude Code plugin marketplace for [Company Name],
an 8-location outpatient physical therapy group operating as a HIPAA covered
entity.

## What lives here

| Path | Purpose |
|------|---------|
| `.claude-plugin/marketplace.json` | Marketplace manifest enumerating available plugins |
| `plugins/<name>/` | Plugin source (one directory per plugin) |
| `policies/` | HIPAA-aligned governing policies (acceptable use, plugin development standard, AI incident response) |
| `CONTRIBUTING.md` | How to add or modify a plugin |
| `.github/CODEOWNERS` | Required reviewers for top-level changes |
| `.github/workflows/` | Per-plugin CI |

## Available plugins

| Plugin | Description | Status |
|--------|-------------|--------|
| `clinic-ops` | Weekly KPI rollups across all 8 clinics. Aggregate counts only. | v0.1.0 |
| `billing-audit` | Pre-submission claim checks (8-minute rule, modifier 59, POC signatures). | planned |

## Adding this marketplace to Claude Code

Once published, workforce members add the marketplace via managed
`settings.json` (deployed by IT through MDM):

```jsonc
{
  "extraKnownMarketplaces": {
    "[company-name]-internal": {
      "source": {
        "type": "github",
        "repo": "[org-name]/tt"
      }
    }
  }
}
```

Direct user installation is not permitted — managed settings restrict the
allowlist to the official Anthropic marketplace and this one. See the
**Plugin Development Standard** under `policies/` §6 for marketplace controls.

## Governance

- Every plugin MUST follow the Plugin Development Standard (`policies/02-plugin-development-standard.md`).
- PHI-adjacent code requires Privacy Officer review (enforced via per-plugin `CODEOWNERS`).
- Plugin versions are pinned per environment (dev/stage/prod). The marketplace
  manifest is the source of truth for the latest published version.
- The marketplace itself is reviewed monthly by IT for installed plugin
  inventory and audit-log integrity.

## Filling in placeholders

Before this repo goes live, replace every bracketed token:
- `[Company Name]` — the legal name of the practice
- `[company-name]` — slugified name used in identifiers
- `[org-name]` — the GitHub organization slug
- `[engineering-lead]` / `[privacy-officer]` — real GitHub usernames
- `[engineering@company.com]` — a monitored mailbox

Search-and-replace targets: `MARKETPLACE.md`, `CONTRIBUTING.md`,
`.claude-plugin/marketplace.json`, `.github/CODEOWNERS`, every file under
`policies/`, and every plugin's `README.md`, `CODEOWNERS`, and `plugin.json`.
