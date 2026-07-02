# Managed Claude Code settings

This directory contains the company-wide managed `settings.json` that IT
deploys to every workforce laptop running Claude Code. Settings here
**cannot be overridden** by users locally — that's the point.

## Deployment paths

| OS | Managed settings path |
|----|----------------------|
| macOS | `/Library/Application Support/ClaudeCode/managed-settings.json` |
| Windows | `%ProgramData%\ClaudeCode\managed-settings.json` |
| Linux | `/etc/claude-code/managed-settings.json` |

Push the file via your MDM (Jamf, Intune, Workspace ONE, etc.). Verify with
`claude config list --managed` on a test workstation before broad rollout.

## What `managed-settings.json` enforces

| Lever | Effect |
|-------|--------|
| `extraKnownMarketplaces` | Adds the private marketplace at `jblack4vols/tt`. |
| `enabledMarketplaces` | **Allowlist.** Only the official Anthropic marketplace and our internal one are usable. Users cannot install plugins from anywhere else. |
| `enabledPlugins` | Pins plugins to specific versions per environment. Bump these in lockstep with `marketplace.json`. |
| `permissions.deny` | Hard-blocks dangerous primitives: outbound HTTP, recursive deletes, reads of secrets / SSH keys / AWS creds. |
| `permissions.ask` | Forces user confirmation for destructive or governance-sensitive writes (policies, marketplace manifest, CODEOWNERS, `git push`). |
| `env.CLAUDE_CODE_ENABLE_TELEMETRY=1` | Exports tool calls, file ops, and Bash invocations via OpenTelemetry to the SIEM. |
| `env.OTEL_EXPORTER_OTLP_ENDPOINT` | Internal collector endpoint. Logs retained 6 years per HIPAA Security Rule §164.316(b)(2)(i). |
| `env.ANTHROPIC_BAA_SIGNED` | **Master gate** for any plugin that touches real PHI. Default `false`. Flip to `true` only after the BAA is countersigned and on file with the Privacy Officer. |
| `env.CLINIC_OPS_ACTOR` / `BILLING_AUDIT_ACTOR` | Per-user audit attribution. MDM injects the user's email at deploy time. |

## Placeholder status

`managed-settings.json` has been substituted with real values: company slug
`tristarpt`, repo `jblack4vols/tt`, OTel collector `otel.tristarpt.internal`,
and email domain `tristarpt.com`. Verify the OTel collector hostname actually
resolves before enabling telemetry export in production.

## Operational runbook

| Action | How |
|--------|-----|
| Add a new plugin to the allowlist | Bump version in `.claude-plugin/marketplace.json`, then add the entry to `enabledPlugins` in `managed-settings.json`. Both PRs must merge before workforce can install. |
| Pin a plugin to a different version | Update the version in `enabledPlugins` and roll out via MDM. Existing installs auto-update on next Claude Code launch. |
| Enable PHI-touching plugins (e.g. `billing-audit`) | After the Anthropic BAA is signed: flip `ANTHROPIC_BAA_SIGNED` to `"true"`. Audit log this change in the security-officer change record. |
| Investigate an unauthorized plugin install | Logs are in the SIEM under `service.namespace=tristarpt`. Search by `tool=plugin_install`. See policies/03-incident-response-addendum-ai-tools.md. |
| Disable a plugin company-wide (incident response) | Remove from `enabledPlugins` and push via MDM. Active sessions terminate the plugin on next request. |

## Schema caveat

The `$schema` URL is illustrative — verify against the current Claude Code
schema before deployment. Some fields may have been renamed in newer
versions. Test on a single workstation first.
