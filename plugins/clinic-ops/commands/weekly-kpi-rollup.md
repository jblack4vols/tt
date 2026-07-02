---
description: Generate the weekly KPI rollup across all 8 clinics
argument-hint: [--week YYYY-WW] [--format md|pdf|both]
allowed-tools: Bash(python scripts/*), Read, Write
---

# Weekly KPI rollup

You are generating the Monday-morning operational report for TriStar PT.
Follow these steps in order. Do not skip steps. Do not infer numbers — every
metric must come from a script output, never from memory.

## Inputs
- `$1` = week argument (e.g. `--week 2026-18`). If absent, default to the most
  recently completed ISO week.
- `$2` = format flag. Default `both`.

## Steps

1. **Resolve the target week.**
   Run: `python scripts/resolve_week.py $1`
   Capture `week_start` and `week_end` (ISO dates) from the JSON output.

2. **Fetch raw EMR reports for all 8 clinics in parallel.**
   Run: `python scripts/fetch_emr_report.py --start <week_start> --end <week_end>`
   This writes one JSON file per clinic to `./.cache/<week>/<clinic_code>.json`.
   If any clinic fails, STOP and report the failure — do not produce a partial
   report.

3. **Normalize.**
   Run: `python scripts/normalize_clinics.py --week <week>`
   This produces `./.cache/<week>/normalized.parquet`.

4. **Compute KPIs using the definitions in the `kpi-definitions` skill.**
   Run: `python scripts/compute_kpis.py --week <week>`
   Output: `./.cache/<week>/kpis.json`.

   Verify the output contains every metric listed in
   `skills/kpi-definitions/SKILL.md`. If any are missing, surface the gap and
   stop.

5. **Render.**
   Run: `python scripts/render_report.py --week <week> --format $2`
   Outputs:
   - `reports/<week>/rollup.md`
   - `reports/<week>/rollup.pdf` (if format includes pdf)

6. **Audit log.**
   Append one line to `audit/access.log`:
   `<ISO timestamp> actor=<git user.email> action=weekly-rollup week=<week> clinics=8 status=ok`

7. **Summarize for the user.**
   Print: report path, top 3 clinics by visits-per-FTE, bottom 3 clinics by
   cancellation %, and any clinic with > 15% no-show rate (the action
   threshold). Do NOT include patient names or therapist names beyond
   internal IDs.

## Failure handling
- EMR API 4xx/5xx: retry up to 3 times with exponential backoff (already in
  `fetch_emr_report.py`). If still failing, surface the HTTP error and stop.
- Synthetic-data mode: if `CLINIC_OPS_ENV=dev`, fetch reads from
  `tests/fixtures/synthetic_week.json` instead of the EMR API.

## Guardrails
- Never paste raw clinical notes, patient names, DOBs, or diagnoses into the
  conversation. Aggregates only.
- If a script ever returns row-level patient data, treat that as a defect and
  stop the run.
