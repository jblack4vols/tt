# Plugin Development Standard

**Policy owner:** [Engineering Lead / IT Director]
**Effective date:** [Date]
**Applies to:** All employees and contractors developing software for TriStar PT.

## 1. Scope
This standard governs internal Claude Code plugins, custom skills, MCP servers, and any code that integrates with EMR, billing, scheduling, or PHI-adjacent systems.

## 2. Repository and branch controls
- All internal plugins live under the private GitHub account `jblack4vols` (no dedicated company org exists yet).
- The `main` branch is protected: required PR review, required status checks, signed commits, no force-push, no direct commits.
- A second reviewer is required for any change in the categories `billing/`, `emr/`, or `phi/`.

## 3. Required plugin contents
Every plugin must include:
- `README.md` describing purpose, data accessed, and external services contacted.
- `THREAT-MODEL.md` listing PHI touchpoints, secrets used, and failure modes.
- `audit/` directory with sample log output.
- A `CODEOWNERS` entry assigning a Privacy Officer reviewer for PHI-adjacent code.
- Pinned dependency versions; no floating tags.

## 4. Coding requirements
- **No PHI in source, comments, tests, or fixtures.** Use synthetic data (Synthea or de-identified extracts).
- **No secrets in source.** Use the company secrets manager; reference by name.
- **All outbound network calls** must use TLS 1.2+ and pinned hosts; egress to anything other than approved endpoints requires Privacy Officer review.
- **All PHI access** must emit an application audit log entry: actor, record identifier, action, timestamp, business reason.
- **Logging must not include PHI** beyond minimum-necessary identifiers (typically an internal record ID, never name + DOB + diagnosis together).
- **Error handling** must avoid surfacing PHI in stack traces sent to Sentry or any external service.

## 5. Review checklist (mandatory PR template)
- [ ] No PHI in code, tests, or fixtures
- [ ] No secrets, API keys, or tokens committed
- [ ] All external endpoints documented in `THREAT-MODEL.md`
- [ ] Audit log emitted for any PHI access
- [ ] Dependencies pinned; `npm audit` / `pip-audit` clean
- [ ] If a new MCP server: explicit allowlist of tools exposed
- [ ] If a new slash command: documented in plugin README

## 6. Marketplace controls
- Only the official Anthropic marketplace and `jblack4vols/tt` are permitted via managed `settings.json`.
- Plugin versions are pinned per environment (dev/stage/prod).
- A monthly review of installed plugins is logged by IT.

## 7. Testing
- Unit and integration tests must run against synthetic data.
- Any plugin touching billing must include test cases for the 8-minute rule, modifier 59, and POC signature presence.
- A staging environment with de-identified production-like data is used before any plugin is approved for prod.

## 8. Decommissioning
When a plugin is retired, IT removes it from the managed allowlist and revokes any associated API keys within 30 days.
