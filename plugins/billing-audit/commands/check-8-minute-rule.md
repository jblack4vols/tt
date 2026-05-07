---
description: Pre-submission audit of timed-code unit billing against the Medicare 8-minute rule
argument-hint: [--batch BATCH_ID|--week YYYY-WW]
allowed-tools: Bash(python scripts/*), Read
---

# 8-minute rule audit

Audit a pre-submission claim batch for visits where billed timed-code units
exceed what the documented treatment minutes support per the Medicare
8-minute rule.

## Inputs
- `$1` = `--batch BATCH_ID` (preferred, what the user submits to clearinghouse) or `--week YYYY-WW` (audit a window of completed visits).

## Steps

1. **BAA gate.**
   Run: `python scripts/fetch_claims.py --gate-only`
   This refuses to proceed unless `ANTHROPIC_BAA_SIGNED=true` (or
   `BILLING_AUDIT_ENV=dev`). If the gate fails, STOP and surface the
   message — do not retry.

2. **Fetch the claim batch.**
   Run: `python scripts/fetch_claims.py $1`
   Writes `./.cache/<batch-or-week>/claims.json`. Each record carries
   visit-level CPT lines, billed units, and documented treatment minutes.
   Patient identifiers are stripped before persistence — only internal
   `patient_id` and `claim_id` are retained.

3. **Apply the 8-minute rule.**
   Run: `python scripts/check_8min_rule.py --batch <label>`
   Output: `./.cache/<label>/eight_min_flags.json`. Each flagged visit
   carries `claim_id`, `visit_date`, `cpt`, `documented_minutes`,
   `billed_units`, `allowed_units`, `delta`, `severity`.

4. **Audit log.**
   The check script writes one summary audit line and one line per flag
   (with `claim_id` only — no patient identifiers).

5. **Summarize for the user.**
   Print:
   - Total visits audited
   - Count of `warn` flags (off-by-one, fix before submission)
   - Count of `block` flags (off-by-two-or-more, requires review before submission)
   - Top 5 offenders by `claim_id` (internal IDs only; never patient names)
   - Estimated revenue impact (sum of over-billed-unit dollar value)

## Guardrails

- This command is for use by the billing team or compliance reviewer.
- Output must NEVER include patient names, MRNs, DOBs, or any other
  Safe Harbor identifier — internal `claim_id` and `patient_id` only.
- Modifier 59 patterns and CCI edit pairs are out of scope — see
  `/billing:flag-modifier-59` (planned, v0.2).

## Synthetic-data dev mode
Set `BILLING_AUDIT_ENV=dev` (or `CLINIC_OPS_ENV=dev`) to read from
`tests/fixtures/synthetic_claims.json` and bypass the BAA gate.
