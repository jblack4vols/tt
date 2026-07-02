---
name: kpi-definitions
description: Canonical KPI formulas for TriStar PT outpatient PT operations. Loaded automatically when any clinic-ops command computes metrics.
---

# TriStar PT KPI Definitions

This is the single source of truth. If a metric is computed anywhere — a
dashboard, a board deck, a clinic manager's spreadsheet — it must match these
formulas. Changes require Owner + Operations Director sign-off and a version
bump in this file.

Last reviewed: [YYYY-MM-DD]
Version: 1.0

---

## Volume

### visits
Count of completed appointments where `appointment_status = "completed"` AND
`appointment_type IN ("eval", "treatment", "re-eval", "progress-note-visit")`.
Excludes administrative visits, no-shows, and cancellations.

### new_patients
Count of unique patients whose first completed `eval` in the rolling 12 months
falls within the reporting window.

### units_billed
Sum of timed-code units (CPT 97110, 97112, 97140, 97530, 97535, 97542, etc.)
plus untimed-code visits (97161–97163, 97164, 97010, etc., counted as 1 unit
each).

---

## Productivity

### visits_per_fte
`visits / sum(therapist_fte)` where `therapist_fte` is each licensed
clinician's contracted FTE (PT, PTA, OT, OTA) for the reporting window.
Excludes admin time and PTO.

**Targets**
- Tier 1 clinics (mature, > 18 months open): ≥ 11.0
- Tier 2 clinics (6–18 months): ≥ 9.0
- Tier 3 clinics (< 6 months): ≥ 7.0

### units_per_visit
`units_billed / visits`.
**Target:** 3.8–4.2. Below 3.5 suggests under-billing or short visits; above
4.5 may flag compliance review.

### eval_to_treat_ratio
`evals / treatment_visits`.
**Target:** 1 : 8 to 1 : 12.

---

## Schedule integrity

### cancellation_pct
`cancellations / scheduled_appointments`.
Same-day cancellations are tracked separately as `same_day_cancel_pct`.
**Target:** < 6%. Action threshold: > 8% same-day.

### no_show_pct
`no_shows / scheduled_appointments`.
**Target:** < 8%. Action threshold: > 15%.

### avg_wait_days
For new patients in the window, mean of `(first_eval_date - referral_date)`
in business days.
**Target:** ≤ 5 business days.

---

## Revenue cycle

### gross_charges
Sum of billed charges at fee-schedule rate, before contractual adjustments.

### expected_reimbursement
`sum(units * payer_contracted_rate)` per CPT/payer combination using the
contracted-rate table in `data/payer_rates.parquet`.

### collection_rate
`payments_received / expected_reimbursement` for claims aged ≥ 90 days.
**Target:** ≥ 96%.

### ar_over_60
`accounts_receivable_balance` aged > 60 days / total AR.
**Target:** < 18%.

### denial_rate
`denied_claim_lines / submitted_claim_lines` for the window. Tracked by
denial reason code (CARC).
**Target:** < 5%. Top 3 CARCs reported each week.

---

## Referrals & growth

### top_referrers
Ranked list of referring NPIs by completed-eval count in the window.

### referral_conversion
`evals_completed / referrals_received` for referrals received in the window.
**Target:** ≥ 70%.

### lapse_rate
`patients_who_canceled_or_no_showed_and_did_not_reschedule_within_14_days /
patients_with_active_plan_of_care`.
**Target:** < 12%.

---

## Compliance

### poc_signed_within_30_days_pct
`plans_of_care_with_physician_signature_within_30_days /
plans_of_care_started`.
**Target:** ≥ 99%. Action threshold: < 97%.

### eight_minute_rule_flags
Count of dated visits where billed timed units exceed what the documented
treatment minutes support per the Medicare 8-minute rule.
**Target:** 0. Each flag triggers chart audit.

### outcome_measure_capture
`patients_with_baseline_and_followup_outcome_measure / patients_eligible`.
Required outcome tools by region: LEFS (lower extremity), DASH (upper
extremity), Oswestry (lumbar), NDI (cervical), NPRS (all).
**Target:** ≥ 90% baseline, ≥ 80% follow-up.

---

## Reporting conventions

- Week = ISO week (Mon–Sun).
- Month = calendar month, US Eastern.
- "All clinics" rollups exclude clinics open < 30 days at start of window.
- Round percentages to 1 decimal; round currency to whole dollars.
- Therapists referenced by `therapist_id` in machine output; names only at
  PDF render time.
