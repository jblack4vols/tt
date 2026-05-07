---
description: Per-therapist productivity report for a clinic or all clinics
argument-hint: [--clinic CODE|all] [--week YYYY-WW]
allowed-tools: Bash(python scripts/*), Read
---

# Therapist productivity

Generate a productivity report by therapist using internal IDs only.

## Steps
1. `python scripts/resolve_week.py $2`
2. `python scripts/fetch_emr_report.py --start <week_start> --end <week_end> --include therapists`
3. `python scripts/compute_kpis.py --week <week> --by therapist`
4. `python scripts/render_report.py --week <week> --view therapist --clinic $1`
5. Audit-log: `actor=<user> action=therapist-productivity scope=$1 week=<week>`
6. Summarize:
   - Median visits/day per therapist
   - Therapists below 80% of company median (flag for manager review, by ID)
   - Therapists above 120% of company median (flag for burnout check, by ID)

## Guardrails
- Therapist names are workforce data, not PHI, but treat them as confidential.
  Do not export to anything outside the company.
- Output uses therapist internal IDs by default. Names are looked up only at
  render time and only in PDFs sent through company email.
