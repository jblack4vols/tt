# billing-audit

Internal Claude Code plugin that runs pre-submission audit checks against PT
claim batches before they reach the clearinghouse. Catches the most common
denial drivers and compliance flags while there is still time to correct them.

## Status: PHI-adjacent

Unlike `clinic-ops`, this plugin operates on **claim-line records that
include patient identifiers** (MRN, DOB, name on the claim). A signed
Anthropic BAA is required before this plugin runs against real data. Until
then, dev mode reads only de-identified or synthetic claim batches.

See `THREAT-MODEL.md`.

## v0.1.0 commands

| Command | What it does |
|---------|--------------|
| `/billing:check-8-minute-rule` | Flag visits where billed timed units exceed what documented treatment minutes support per the Medicare 8-minute rule. |
| `/billing:flag-missing-pocsign` | Flag claims for visits whose plan of care lacks a physician signature within 30 days. |

## Planned (v0.2 / v0.3)

- `/billing:flag-modifier-59` — surface usage patterns of modifier 59 against
  CMS unbundling guidance.
- `/billing:reconcile-clearinghouse` — match 837P submissions against
  999/277CA acknowledgments to catch silent rejections.
- `/billing:denial-summary` — top denials by CARC over a window with
  remediation hints.

## Data accessed

- EMR / practice-management reporting endpoint (`api.[your-emr-vendor].com`):
  claim-line records, treatment-minute notes, plan-of-care signature dates.
- No clearinghouse connection in v0.1.0.

## Audit
Every command emits a structured line via `scripts/audit.py`. Each flagged
claim contributes a `claim_id` (internal) to the audit metadata; **patient
names, DOBs, and MRNs never appear in the audit log**.

## Development

```bash
CLINIC_OPS_ENV=dev python -m unittest discover tests -v
```

Set `BILLING_AUDIT_ENV=dev` (or reuse `CLINIC_OPS_ENV=dev`) to read from
`tests/fixtures/synthetic_claims.json` instead of the EMR API.

## Production gates

Do not run this plugin against real patient data unless **all** of these are
true:

1. Anthropic BAA is signed and on file with Privacy Officer.
2. Managed `settings.json` is deployed (marketplace allowlist + audit logging).
3. Operator's laptop has full-disk encryption + EDR enabled.
4. `BILLING_AUDIT_ACTOR` is set to the operator's company email so audit
   attribution is correct.

The Plugin Development Standard (`policies/02-plugin-development-standard.md`)
covers the rest.
