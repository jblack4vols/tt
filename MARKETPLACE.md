# TriStar PT internal Claude Code marketplace

This repository is the private Claude Code plugin marketplace for TriStar PT,
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
    "tristarpt-internal": {
      "source": {
        "type": "github",
        "repo": "jblack4vols/tt"
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

## Placeholder status

Company, org, and role identifiers have been substituted repo-wide:
- `[Company Name]` → TriStar PT
- `[company-name]` → tristarpt
- `[org-name]` → jblack4vols (a personal GitHub account, not a dedicated
  org — there is no separate company org yet)
- `[engineering-lead]` / `[privacy-officer]` / `[security-officer]` →
  jblack4vols (one person currently holds all three roles)
- `[engineering@company.com]` / `[security@company.com]` → jblack@tristarpt.com

Still pending: `api.[your-emr-vendor].com` (EMR vendor hostname), blocked on
vendor selection — see `ROLLOUT.md` Track 5. Policy effective dates and
formal role sign-off (as opposed to the GitHub-username stand-ins above) are
tracked separately in `ROLLOUT.md` Tracks 1–2.
