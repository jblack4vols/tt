---
description: Top referring providers and referral conversion by clinic
argument-hint: [--month YYYY-MM]
allowed-tools: Bash(python scripts/*)
---

# Referral source summary

## Steps
1. `python scripts/fetch_emr_report.py --month $1 --include referrals`
2. `python scripts/compute_kpis.py --month $1 --metrics referrals`
3. Render:
   - Top 20 referring providers across all clinics
   - Per-clinic top 10
   - Referral-to-eval conversion rate
   - Eval-to-plan-of-care conversion rate
   - Provider-level trend vs prior month (drop > 30% flagged for liaison
     follow-up)
4. Audit-log entry.

## Guardrails
- Referring provider names are not PHI but may be confidential. Output is
  for internal physician-liaison use only.
- Patient identifiers are excluded from this report.
