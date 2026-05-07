# Production Rollout Checklist

**Goal:** move the merged `clinic-ops` and `billing-audit` plugins, the
managed `settings.json`, and the HIPAA policy templates from "code complete"
to "running on real PT clinic data, audited, and binding."

**Realistic timeline:** 4–6 weeks after start, gated by the BAA and legal
review running in parallel.

Update this file as items complete. Don't merge a final "all checked" PR
until everything below is checked off.

---

## Track 1 — Anthropic BAA (longest lead time, start week 0)

| # | Task | Owner | Target | Done |
|---|------|-------|--------|:----:|
| 1.1 | Send the email at `templates/anthropic-baa-email.md` to `sales@anthropic.com`. Replace bracketed personal/company details first. | [Owner / Privacy Officer] | Day 1 | ☐ |
| 1.2 | First Anthropic response received; record AE contact in [secrets manager / CRM]. | [Owner] | Week 1 | ☐ |
| 1.3 | Confirm BAA scope covers Claude Code (Enterprise), Claude.ai (Enterprise), and direct Anthropic API. | [Privacy Officer] | Week 2 | ☐ |
| 1.4 | BAA draft received; routed to healthcare attorney. | [Privacy Officer] | Week 2 | ☐ |
| 1.5 | Counsel redlines complete; final draft executed. | [Owner] | Week 3–4 | ☐ |
| 1.6 | Countersigned BAA filed under `policies/baa/anthropic-<YYYY-MM-DD>.pdf` (create directory at sign time; **do not** add a placeholder file). | [Privacy Officer] | Sign day | ☐ |
| 1.7 | Update `policies/01-acceptable-use-of-ai-coding-tools.md` §2 with the executed BAA date. | [Privacy Officer] | Sign day | ☐ |
| 1.8 | Flip `ANTHROPIC_BAA_SIGNED` to `"true"` in `config/managed-settings.json` and roll out via MDM. | IT | Sign day +1 | ☐ |

> Item 1.8 is the single switch that unlocks every PHI-touching plugin
> (`billing-audit` today, more later). Do not flip it until the executed
> BAA is filed.

---

## Track 2 — Legal review of policy templates (parallel with Track 1)

| # | Task | Owner | Target | Done |
|---|------|-------|--------|:----:|
| 2.1 | Send `policies/01-acceptable-use-of-ai-coding-tools.md` to healthcare attorney. | [Privacy Officer] | Week 0 | ☐ |
| 2.2 | Send `policies/02-plugin-development-standard.md`. | [Engineering Lead] | Week 0 | ☐ |
| 2.3 | Send `policies/03-incident-response-addendum-ai-tools.md`. | [Security Officer] | Week 0 | ☐ |
| 2.4 | Counsel redlines incorporated; policies signed and dated. | [Privacy Officer] | Week 2 | ☐ |
| 2.5 | Acceptable Use acknowledgment circulated to all workforce members with Claude Code or Claude.ai access. | HR / [Privacy Officer] | Week 2–3 | ☐ |
| 2.6 | Acknowledgments collected and filed in HRIS. | HR | Week 3 | ☐ |
| 2.7 | Annual review cadence added to compliance calendar. | [Privacy Officer] | Week 3 | ☐ |

---

## Track 3 — Substitute placeholders across the repo (week 1)

The repo ships with bracketed tokens by design. Until these are real, the
marketplace install snippet won't resolve, CODEOWNERS won't enforce, and
audit attribution will read `unknown`.

### Tokens to replace
- `[Company Name]` — legal practice name
- `[company-name]` — slugified version (used in marketplace name, OTel attrs)
- `[org-name]` — GitHub organization slug
- `[your-emr-vendor]` — EMR vendor's API hostname (after Track 5)
- `[engineering-lead]`, `[privacy-officer]`, `[security-officer]` — real GitHub usernames
- `[engineering@company.com]`, `[security@company.com]` — monitored mailboxes
- `[Date]`, `[YYYY-MM-DD]` — actual dates in policies and skill files
- `$USER@[company-name].com` — verify your MDM's user-scoped substitution

### Files affected
- `MARKETPLACE.md`, `CONTRIBUTING.md`
- `.claude-plugin/marketplace.json`
- `.github/CODEOWNERS`, `.github/pull_request_template.md`
- All `policies/*.md`
- `config/managed-settings.json`, `config/README.md`
- `templates/anthropic-baa-email.md`
- Each plugin's `README.md`, `THREAT-MODEL.md`, `CODEOWNERS`, `plugin.json`,
  and `skills/*/SKILL.md`

| # | Task | Owner | Target | Done |
|---|------|-------|--------|:----:|
| 3.1 | Find/replace pass; verify no `[bracket]` tokens remain (`grep -RnE '\[[a-z][a-z-]+\]' .`). | [Engineering Lead] | Week 1 | ☐ |
| 3.2 | Validate `.claude-plugin/marketplace.json` parses and matches current Claude Code schema. | [Engineering Lead] | Week 1 | ☐ |
| 3.3 | Verify all referenced GitHub usernames exist (`gh api users/<name>`). | [Engineering Lead] | Week 1 | ☐ |

---

## Track 4 — GitHub branch protection (week 1)

`CODEOWNERS` enforces nothing without branch protection. Configure in repo
settings under Settings → Branches → Branch protection rules.

| # | Task | Owner | Target | Done |
|---|------|-------|--------|:----:|
| 4.1 | Require pull request reviews before merging on `main`. | IT / [Engineering Lead] | Week 1 | ☐ |
| 4.2 | Require review from Code Owners. | IT | Week 1 | ☐ |
| 4.3 | Require status checks: both `clinic-ops tests` and `billing-audit tests` workflows must pass. | IT | Week 1 | ☐ |
| 4.4 | Require signed commits. | IT | Week 1 | ☐ |
| 4.5 | Block force pushes and direct pushes on `main`. | IT | Week 1 | ☐ |
| 4.6 | Verify by opening a no-op PR from a sandbox account; confirm it cannot be merged without CODEOWNERS approval. | [Engineering Lead] | Week 1 | ☐ |

---

## Track 5 — EMR vendor selection and wiring (weeks 1–3)

Both plugins target a placeholder host (`api.[your-emr-vendor].com`). Until
the real reporting API is wired, neither runs against real data.

| # | Task | Owner | Target | Done |
|---|------|-------|--------|:----:|
| 5.1 | Confirm EMR vendor and obtain reporting API documentation. Common candidates: WebPT, Prompt, Raintree, Net Health, Heno, Jane. | [Owner / Practice Mgr] | Week 1 | ☐ |
| 5.2 | Get a written confirmation from the EMR vendor that the operational-reports endpoint never returns row-level patient data (used by `clinic-ops`). | [Privacy Officer] | Week 2 | ☐ |
| 5.3 | Provision an API key in the company secrets manager under `emr/reporting-api-key`. | IT | Week 2 | ☐ |
| 5.4 | Update `APPROVED_HOSTS` and the URL templates in `plugins/clinic-ops/scripts/fetch_emr_report.py` and `plugins/billing-audit/scripts/fetch_claims.py` to the real host. | [Engineering Lead] | Week 2 | ☐ |
| 5.5 | Map the EMR's response shape into the normalizers (`normalize_clinics.py` for `clinic-ops`; field-name expectations in `check_*.py` for `billing-audit`). Update `is_aggregate` / `_strip_direct_identifiers` if the vendor surfaces additional identifiers. | [Engineering Lead] | Week 2–3 | ☐ |
| 5.6 | Add integration tests against the EMR's sandbox or a captured fixture; tag them so they only run when an explicit env var is set (do not commit captured fixtures that contain PHI). | [Engineering Lead] | Week 3 | ☐ |
| 5.7 | Validate `clinic-ops` rollup against the most recent manually-produced spreadsheet for two historical weeks. Variance should be within rounding. | Operations Director | Week 3 | ☐ |
| 5.8 | Validate `billing-audit` 8-minute rule flag rate against a billing-team manual sample of ~50 claims. Investigate any divergence. | Billing Lead | Week 3–4 | ☐ |

---

## Track 6 — MDM rollout of managed settings (week 3, after Track 4)

| # | Task | Owner | Target | Done |
|---|------|-------|--------|:----:|
| 6.1 | Substitute placeholders in `config/managed-settings.json` (Track 3 must be done). | IT | Week 3 | ☐ |
| 6.2 | Confirm OTel collector (`otel.[company-name].internal`) is running and receiving from a test workstation. | IT | Week 3 | ☐ |
| 6.3 | SIEM ingestion verified; logs retained 6 years per HIPAA Security Rule §164.316(b)(2)(i). | [Security Officer] | Week 3 | ☐ |
| 6.4 | Deploy `managed-settings.json` to a single test workstation. Verify `claude config list --managed` shows the policy. | IT | Week 3 | ☐ |
| 6.5 | On the test workstation, attempt to install a plugin from outside the allowlist; confirm it's blocked. | IT | Week 3 | ☐ |
| 6.6 | On the test workstation, run `/ops:weekly-kpi-rollup` against synthetic data; confirm tool calls appear in the SIEM. | [Engineering Lead] | Week 3 | ☐ |
| 6.7 | Roll out to all developer workstations. | IT | Week 4 | ☐ |
| 6.8 | Roll out to all clinical/admin workstations once Acceptable Use acknowledgments are collected. | IT | Week 4–5 | ☐ |

---

## Track 7 — Endpoint posture (parallel, week 1–4)

Per `policies/01-acceptable-use-of-ai-coding-tools.md` §4. Most are likely
already in place; verify and document.

| # | Task | Owner | Target | Done |
|---|------|-------|--------|:----:|
| 7.1 | Full-disk encryption (FileVault / BitLocker) enforced via MDM on every workstation that runs Claude Code. | IT | Week 1 | ☐ |
| 7.2 | Auto-lock under 5 minutes; OS account password + MFA. | IT | Week 1 | ☐ |
| 7.3 | EDR (CrowdStrike / SentinelOne / Defender for Business) deployed and reporting. | IT | Week 1 | ☐ |
| 7.4 | Personal-device policy enforced — no Claude Code on BYOD. | IT / HR | Week 2 | ☐ |
| 7.5 | Workforce training on Acceptable Use Policy (30-minute session). | [Privacy Officer] / HR | Week 3 | ☐ |

---

## Track 8 — Cutover (week 4–6)

| # | Task | Owner | Target | Done |
|---|------|-------|--------|:----:|
| 8.1 | All Tracks 1–7 complete and checked off. | [Privacy Officer] | Week 5 | ☐ |
| 8.2 | First production `/ops:weekly-kpi-rollup` against real EMR data. Compare to manual spreadsheet. | Operations Director | Week 5 | ☐ |
| 8.3 | First production `/billing:check-8-minute-rule` against a real claim batch. **Do not auto-act on flags** — review with billing team for first 4 weeks. | Billing Lead | Week 5 | ☐ |
| 8.4 | Retire the manual KPI spreadsheet workflow. | Operations Director | Week 6 | ☐ |
| 8.5 | Schedule the first quarterly access review (audit logs, plugin inventory, BAA still active). | [Privacy Officer] | Week 6 | ☐ |
| 8.6 | Schedule the first annual tabletop exercise per `policies/03-incident-response-addendum-ai-tools.md` §7. | [Security Officer] | Within Year 1 | ☐ |

---

## Track 9 — Sustainment (ongoing, after cutover)

| # | Cadence | Task | Owner |
|---|---------|------|-------|
| 9.1 | Weekly | Review `audit/access.log` shipping to SIEM; alert on gaps > 24h. | [Security Officer] |
| 9.2 | Monthly | Plugin inventory review per `policies/02-plugin-development-standard.md` §6. | IT |
| 9.3 | Quarterly | Information-system activity review per HIPAA Security Rule §164.308(a)(1)(ii)(D). | [Privacy Officer] |
| 9.4 | Quarterly | KPI definitions sign-off (`plugins/clinic-ops/skills/kpi-definitions/SKILL.md`) by Owner + Operations Director. | Operations Director |
| 9.5 | Quarterly | Billing rules sign-off (`plugins/billing-audit/skills/billing-rules/SKILL.md`) by Billing Lead + Compliance. | Billing Lead |
| 9.6 | Annually | Acceptable Use Policy acknowledgment refresh. | HR |
| 9.7 | Annually | Threat-model and policy review cycle. | [Privacy Officer] / [Security Officer] |
| 9.8 | Annually | Tabletop exercise (one of the three scenarios in the IR addendum). | [Security Officer] |

---

## Don't ship without

These are the conditions for go-live. If any of these is `☐`, the rollout
is **not** ready, regardless of what else is checked.

- ☐ **1.6** Countersigned Anthropic BAA on file.
- ☐ **2.4** Policies signed by counsel and the Privacy Officer.
- ☐ **3.1** No `[bracket]` placeholders remain in `policies/`, `config/`, or `.claude-plugin/`.
- ☐ **4.1–4.5** GitHub branch protection on `main` is fully configured.
- ☐ **5.7** `clinic-ops` validated against historical manual spreadsheet.
- ☐ **5.8** `billing-audit` validated against billing-team manual sample.
- ☐ **6.5** Marketplace allowlist verified to actually block out-of-list plugins.
- ☐ **7.1–7.3** All workstations have FDE + auto-lock + EDR.

---

## Status board

Edit this section as you go. Keep it short.

```
Track 1 (BAA):                 not started
Track 2 (Legal review):        not started
Track 3 (Placeholders):        not started
Track 4 (Branch protection):   not started
Track 5 (EMR wiring):          not started
Track 6 (MDM rollout):         not started
Track 7 (Endpoint posture):    not started
Track 8 (Cutover):             blocked on 1–7
Track 9 (Sustainment):         starts after cutover
```

Last updated: [YYYY-MM-DD]
By: [Name]
