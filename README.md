# TriStar PT — internal Claude Code marketplace

[中文](README.zh.md)

This repository is TriStar PT's private Claude Code plugin marketplace. It is
not published publicly and is restricted to workforce members.

See **[MARKETPLACE.md](MARKETPLACE.md)** for the full repo layout, the list of
available plugins, and how workforce members add this marketplace via managed
`settings.json`. See **[CONTRIBUTING.md](CONTRIBUTING.md)** before opening a
PR that adds or modifies a plugin — HIPAA-relevant review requirements apply.

## Available plugins

| Plugin | Description |
|--------|-------------|
| [`clinic-ops`](plugins/clinic-ops) | Operational KPI rollups across all 8 clinics. Aggregate counts only — no patient-level data. |
| [`billing-audit`](plugins/billing-audit) | Pre-submission claim audit (8-minute rule, plan-of-care signatures). PHI-adjacent — requires a signed Anthropic BAA. |

## Policies

Governing policy documents live under [`policies/`](policies):
- Acceptable use of AI coding tools
- Plugin development standard
- Incident response addendum for AI tools

## Legacy demo web app

This repo also contains a small Next.js app (`pages/`, `components/`,
`config-*.ts`) left over from the template this repository was originally
created from. It streams chat completions from an OpenAI-compatible API and
is unrelated to the plugin marketplace above.

```bash
yarn install
yarn dev
```

Configure it via environment variables (see `.env.example` if present, or
`config-server.ts` / `config-client.ts` for the full list — at minimum
`OPENAI_API_KEY` is required server-side).
