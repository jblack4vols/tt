# Skills Roadmap

A survey of skills worth installing, building into existing plugins,
shipping as new skill-only plugins, or distributing through Claude.ai for
non-technical staff.

This is a planning document — not a contract. Pull from it when prioritizing
the next quarter's plugin work; revise quarterly.

Last reviewed: [YYYY-MM-DD]
Next review: [YYYY-MM-DD]
Owner: [Engineering Lead]

---

## How to use this doc

- **Categories 1–4** are different surfaces. Pick one based on the audience
  and surface, not on what's "newest" or "easiest."
- Items are **suggestions**, not commitments. Spec sheets become real plugins
  via the intake flow in `CONTRIBUTING.md`.
- Verify Claude Code plugin/marketplace names against the live Anthropic
  marketplace before installing — names and ownership change.

---

## 1 — Claude Code skills to install (developer environment)

For your stack (Python + Next.js + GitHub + healthcare integrations), the
high-value categories from the official + community marketplaces:

| Category | What to look for | Why for you |
|---|---|---|
| Language LSPs | `pyright-lsp` (Python), `typescript-lsp` | Real-time type errors before code touches PHI systems |
| Git / PR workflow | `commit-commands`, `pr-review-toolkit` | Already drafted in `CONTRIBUTING.md` review checklist |
| Issue tracking | `linear`, `asana`, `jira` | Clinic managers file IT requests that flow to your dev's Claude session |
| Comms | `slack` | Front-desk and billing already coordinate there |
| Error tracking | `sentry` | Catches plugin failures with sanitized stack traces |
| Database | `postgres-lsp`, query helpers | Useful when you build internal dashboards |
| Cloud | `aws-cli`, `gcp-cli` helpers | Only if your infra lives there |
| Security | secrets-scanning skills | Belt-and-suspenders against committed credentials |
| Testing | `pytest-runner`, `playwright` | When you have UI tools |

**Caveats**

- The official marketplace will not have healthcare-specific plugins. That
  gap is exactly why your private marketplace exists.
- Anything not on Anthropic's allowlist requires Privacy Officer review per
  `policies/02-plugin-development-standard.md` §6 — install via the managed
  allowlist (`config/managed-settings.json`) only after review.

---

## 2 — Skills to add to existing plugins

Pattern: anything Claude needs to know that you don't want hardcoded in
scripts becomes a `SKILL.md` next to the plugin. Below are skills worth
adding to the two plugins on `main`.

### `clinic-ops`

| Skill | What it captures | Risk |
|---|---|---|
| `report-formatting` | How the rollup looks in email vs Slack vs PDF; company voice; what Owner-Operations wants emphasized | Low |
| `board-deck-style` | Quarterly summary format, level of detail for ownership presentations | Low |
| `anomaly-narrative` | How to write a 2-sentence explanation when a metric drifts ("Cancellations up 27% WoW at C04 — investigating staffing changes") | Low |

### `billing-audit`

| Skill | What it captures | Risk |
|---|---|---|
| `payer-specific-rules` | The per-payer matrix from `billing-rules` — broken out into its own file as it grows | Low |
| `denial-appeal-templates` | Letter templates per CARC code with required attachments | Medium — content needs counsel review |
| `ncci-edits` | NCCI edit pair logic + exception narrative (gating on `flag-modifier-59` v0.2) | Low |
| `annual-rule-updates` | What changed in the 2026 final rule vs 2025; rolled forward each year | Medium — owner is the compliance team |

---

## 3 — New skill-only plugins (highest ROI, lowest engineering effort)

These plugins contain *no scripts* — only skill files. The agent loads
content when relevant. Each captures institutional knowledge that today
lives in someone's head.

| Plugin | Skills inside | Primary user | Dependencies |
|---|---|---|---|
| `pt-compliance-knowledge` | Medicare therapy cap, KX modifier, MIPS reporting, functional reporting G-codes, state PT practice acts, telehealth coverage | Billing + compliance | None |
| `documentation-templates` | POC, initial eval, progress note, discharge note, re-eval — clinically reviewed and formatted | Clinical staff (also via Claude.ai) | None |
| `denial-playbook` | Top 20 CARC codes with appeal-letter templates, evidence checklists, deadlines per payer | Billing | counsel review of templates |
| `clinical-outcome-measures` | LEFS, DASH, Oswestry, NDI, NPRS — scoring, MCID, when to readminister, ICF mapping | Clinical staff and billing-audit plugin | None |
| `intake-standardization` | Standard intake question set; outcome-measure selection by body part; red-flag screening for direct-access states | Front-desk + new-patient eval | None |
| `physician-liaison-playbook` | Talking points by specialty (ortho, neuro, PCP, OB/GYN for pelvic floor); openers; leave-behind handouts | Liaisons + marketing | None |

### Recommended build order

1. **`pt-compliance-knowledge`** — supports `billing-audit` immediately and
   gives the compliance team a Claude-native reference.
2. **`denial-playbook`** — turns billing-team appeal letters from 20 minutes
   to 3.
3. **`clinical-outcome-measures`** — bridges clinical + billing; readable by
   `billing-audit` for outcome-tool capture flags.

The remaining three are valuable but have less direct overlap with current
plugins; they're stronger as Claude.ai skills (see §4) than as Claude Code
plugins.

---

## 4 — Skills for Claude.ai (non-technical staff)

Different surface from Claude Code plugins. Claude.ai (Team/Enterprise)
supports skills at the project level — upload a skill folder and the chat
references it automatically. These are the highest-ROI use cases for the 8
clinics' non-developer staff.

| Audience | Skill pack | Saves time on |
|---|---|---|
| Front desk | Phone scripts (new-patient intake, scheduling, insurance verification, no-show outreach) | Inconsistent first impressions across clinics |
| Billing | Appeal-letter drafting, prior-auth phone scripts, ABN explanation in plain English | Bespoke writing every time |
| Clinical | Patient education handouts (back pain, ACL recovery, balance training for elderly, post-surgical protocols) | Reinventing patient handouts |
| Marketing | Social media post templates by clinic; Google Business Profile review responses (positive + negative); referral-source thank-yous | Voice consistency across clinics |
| HR | PT / PTA / front-desk job descriptions; interview rubrics; reference-check scripts | Hiring drag |
| Compliance | Incident response triage checklist; breach notification letter templates per state; OSHA + HIPAA training quiz banks | Reactive scrambling |
| Owner / Ops | Weekly board-update format; monthly KPI narrative voice; quarterly investor memo structure | Format-from-scratch every cycle |

### Distribution

- Claude.ai supports **organization-level skills** under Team/Enterprise.
  IT publishes the pack once; every workspace member sees it.
- Skill content must follow the Acceptable Use Policy. PHI in skill content
  is prohibited — these are templates and reference, not patient records.
- Maintain skills in this same repo under `claude-ai-skills/<pack>/` so
  versioning, review, and CODEOWNERS extend to them.

### Recommended order

1. **Front-desk + clinical patient education** — visible to patients,
   highest immediate impact on patient experience.
2. **Billing appeal letters** — direct dollars-recovered impact.
3. **Marketing social/GBP responses** — brand consistency.

---

## Picking the next build

If you're choosing one thing to ship next quarter, the highest-leverage move
is **`pt-compliance-knowledge`** + a **front-desk Claude.ai skill pack**
together:

- They cover both surfaces (Claude Code plugin + Claude.ai workspace).
- Together they touch all four audiences: developers, billing, clinical,
  front-desk.
- Neither requires the EMR vendor wiring (Track 5 of `ROLLOUT.md`), so they
  can ship in parallel with the rollout.

If you're choosing two things, add **`denial-playbook`** — same engineering
shape as `pt-compliance-knowledge` and arguably higher dollar impact.

---

## Out of scope for this roadmap

- Generic developer plugins (Docker, Kubernetes, etc.) — install on demand,
  not roadmap-worthy.
- Anything that touches a third-party API not already on the data-flow
  diagram. New endpoints require Privacy Officer review per the Plugin
  Development Standard.
- AI-tool replacements for clinical decision-making. PT clinical reasoning
  is out of scope for these plugins; assistive workflows (documentation,
  education handouts) are in scope.
