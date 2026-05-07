---
description: Flag claim lines for visits whose plan of care lacks a timely physician signature
argument-hint: [--batch BATCH_ID|--week YYYY-WW]
allowed-tools: Bash(python scripts/*), Read
---

# Plan-of-care signature audit

Flag claim lines for treatment visits where the patient's plan of care
either lacks a physician signature or was signed beyond the 30-day window.

## Steps

1. **BAA gate.** `python scripts/fetch_claims.py --gate-only`. Stop on failure.
2. **Fetch claim batch with POC signature dates.**
   `python scripts/fetch_claims.py $1 --include poc_signatures`
3. **Apply rule.** `python scripts/check_poc_signatures.py --batch <label>`
   Output `./.cache/<label>/pocsign_flags.json` with `claim_id`,
   `eval_date`, `signature_date`, `severity`.
4. **Audit log:** one summary line + one per flag (claim IDs only).
5. **Summarize:**
   - Total claim lines audited
   - Unsigned within 30 days (warn — chase signature)
   - Unsigned past 30 days (block — do not submit)
   - Late-signed past 30 days (warn — clawback risk)
   - Patients with multiple flagged claims (by `patient_id`)

## Guardrails

- Internal IDs only in output. No patient names, MRNs, DOBs.
- Re-evals (CPT 97164) restart the 30-day window — handled by the script.
- Maintenance therapy 90-day re-signature is not enforced in v0.1.0.
