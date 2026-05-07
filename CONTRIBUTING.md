# Contributing to the [Company Name] internal marketplace

Read this **before** opening a PR that adds or modifies a plugin. The
controls here are how this marketplace stays HIPAA-defensible.

## Required reading

1. `policies/01-acceptable-use-of-ai-coding-tools.md` — what data classes
   you can put into Claude Code at all.
2. `policies/02-plugin-development-standard.md` — the engineering bar every
   plugin must clear.
3. `policies/03-incident-response-addendum-ai-tools.md` — what to do if
   something goes wrong.

If you have not signed the company's Acceptable Use acknowledgment for the
current year, stop and do that first.

## Adding a new plugin

1. **Open an intake issue first.** Do not start coding before the Privacy
   Officer signs off on the data flow. The intake template (under
   `.github/ISSUE_TEMPLATE/new-plugin.md` — TODO) collects:
   - Purpose and target user
   - Data classes touched (none / aggregate / PHI / workforce)
   - External services contacted
   - Authentication / secrets required
2. **Branch from `main`** as `feat/<plugin-name>` or `feat/<plugin-name>-<feature>`.
3. **Scaffold the plugin** at `plugins/<plugin-name>/` with:
   - `plugin.json` — manifest (commands, skills, permissions)
   - `README.md` — purpose, data accessed, external services
   - `THREAT-MODEL.md` — PHI touchpoints, secrets, egress, failure modes
   - `CODEOWNERS` — assign at minimum the engineering lead; assign the
     Privacy Officer for any path under `scripts/` that touches an EMR,
     billing, or PHI-adjacent system
   - `audit/sample_audit.log` — illustrate the audit format
   - `tests/` — unit + smoke tests against synthetic data
4. **Add a CI job** under `.github/workflows/<plugin-name>.yml` that runs the
   plugin's tests on `paths: plugins/<plugin-name>/**`.
5. **Register the plugin** in `.claude-plugin/marketplace.json`.
6. **Open the PR as draft.** Fill in the PR template. CI must be green
   before un-drafting.

## PR review checklist

Every PR (new plugin or change to an existing one) must satisfy:

- [ ] No PHI in source, comments, tests, or fixtures
- [ ] No secrets, API keys, or tokens committed (run `git diff main` and grep)
- [ ] All external endpoints documented in `THREAT-MODEL.md`
- [ ] Audit log emitted in code (not in a prompt step) for any PHI access
- [ ] Dependencies pinned; `pip-audit` / `npm audit` clean
- [ ] If a new MCP server is added: explicit allowlist of tools exposed
- [ ] If a new slash command: documented in plugin README
- [ ] Tests added or updated; CI green
- [ ] Version bumped in both `plugin.json` and `.claude-plugin/marketplace.json`

## Reviewer responsibilities

| Reviewer | Mandatory for |
|----------|---------------|
| Engineering Lead | Every PR |
| Privacy Officer | Any change under `scripts/`, `THREAT-MODEL.md`, or `audit/` of a PHI-adjacent plugin; any change to `policies/` or `.claude-plugin/marketplace.json` |

`CODEOWNERS` enforces these via GitHub branch protection. If you can self-merge,
the protection isn't configured correctly — escalate to IT.

## Decommissioning a plugin

When retiring a plugin:

1. Move the plugin entry in `marketplace.json` to a `retired_plugins` array
   (or remove if no production traffic depended on it).
2. Revoke any associated API keys via the secrets manager within 30 days.
3. Update the company-wide managed `settings.json` to remove the plugin from
   any pinned-version maps.
4. Archive the plugin directory with a `RETIRED.md` explaining when and why,
   so future engineers don't accidentally resurrect it.

## Local development

```bash
cd plugins/<plugin-name>
CLINIC_OPS_ENV=dev python -m unittest discover tests -v
```

Synthetic data is the default. Real PHI access requires Privacy Officer
approval and a documented business need — see the Plugin Development Standard.

## Reporting security issues

Do **not** open a public issue. Email [security@company.com]. See the
Incident Response Addendum for the full procedure.
