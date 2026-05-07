---
description: Cancellation and no-show analysis with action threshold flags
argument-hint: [--clinic CODE|all] [--weeks N]
allowed-tools: Bash(python scripts/*)
---

# Cancellation report

## Steps
1. Default `--weeks` to 4 (rolling).
2. `python scripts/fetch_emr_report.py --weeks $2 --include schedule_events`
3. `python scripts/compute_kpis.py --window rolling-$2 --metrics cancellations`
4. Render trend chart per clinic.
5. Flag clinics where:
   - Same-day cancellation rate > 8%
   - No-show rate > 15%
   - Either metric increased > 25% week-over-week
6. Audit-log entry.

## Output
Markdown table + PNG trend chart embedded. PDF optional.
