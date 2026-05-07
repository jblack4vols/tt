<!--
Required for every PR that adds or changes a plugin. Delete sections that
don't apply, but do not delete the security checklist.
-->

## Summary
<!-- 1–3 bullets describing what changed and why. -->

## Plugin(s) affected
<!-- e.g. clinic-ops v0.1.0 → v0.2.0 -->

## Data classes touched
- [ ] None / public / synthetic only
- [ ] Aggregate operational counts (no PHI)
- [ ] Workforce data (therapists, schedules) — confidential, not PHI
- [ ] PHI — Privacy Officer review **required**

## External services contacted
<!-- e.g. EMR reporting API; clearinghouse; nothing new -->

## Security checklist
- [ ] No PHI in source, comments, tests, or fixtures
- [ ] No secrets, API keys, or tokens committed
- [ ] All external endpoints documented in the plugin's `THREAT-MODEL.md`
- [ ] Audit log is emitted **in code** (not in a prompt step) for any PHI access
- [ ] Dependencies pinned; `pip-audit` / `npm audit` clean
- [ ] Tests added or updated; CI green
- [ ] If a new MCP server: explicit allowlist of tools exposed
- [ ] If a new slash command: documented in plugin README
- [ ] Version bumped in `plugin.json` and `.claude-plugin/marketplace.json`

## Test plan
<!--
Bulleted checklist of how this was tested (unit, smoke, manual). Include
the command(s) you ran.
-->

## Out of scope
<!-- What this PR explicitly does NOT do, that someone might expect. -->
