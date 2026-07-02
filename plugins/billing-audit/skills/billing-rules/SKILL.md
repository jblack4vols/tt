---
name: billing-rules
description: Canonical billing rule reference for TriStar PT outpatient PT — Medicare 8-minute rule, plan-of-care signature requirements, modifier 59 guidance, common CARC denial codes. Loaded when any billing-audit command runs.
---

# TriStar PT Billing Rules

Source of truth for what counts as a flag. If a script computes anything
that contradicts this file, the file is right and the script is wrong.

Last reviewed: [YYYY-MM-DD]
Version: 1.0

---

## Medicare 8-minute rule

**Applies to:** Medicare Part B, Medicare Advantage plans that follow CMS,
and most commercial payers that have adopted the rule. **Does not apply** to
some commercial payers, Workers' Comp, and Auto/MVA carriers — see payer
matrix below before flagging.

### Units from documented treatment minutes

| Total documented timed-code minutes | Allowed units |
|-------------------------------------:|--------------:|
| < 8 | 0 |
| 8–22 | 1 |
| 23–37 | 2 |
| 38–52 | 3 |
| 53–67 | 4 |
| 68–82 | 5 |
| 83–97 | 6 |
| 98–112 | 7 |
| 113–127 | 8 |

Closed form: `units = max(0, (minutes - 8) // 15 + 1)` for `minutes >= 8`,
else `0`.

### Timed CPT codes (count toward total minutes)

97110 (therapeutic exercise), 97112 (neuro re-ed), 97116 (gait training),
97140 (manual therapy), 97530 (therapeutic activities), 97532 (cognitive
skills), 97533 (sensory integration), 97535 (self-care training),
97537 (community/work), 97542 (wheelchair management), 97760 (orthotic
training), 97761 (prosthetic training), 97763 (orthotic/prosthetic check).

### Untimed CPT codes (1 unit per visit, do not count toward minutes)

97161, 97162, 97163 (eval, low/mod/high complexity), 97164 (re-eval),
97010 (hot/cold packs), 97014 (electrical stim, unattended),
97150 (group therapy), 97012 (mechanical traction).

### Flag logic

For each visit:
1. Sum documented minutes across all timed CPT lines = `M`.
2. Compute allowed units `U = max(0, (M - 8) // 15 + 1)` for `M >= 8`, else 0.
3. Sum billed units across all timed CPT lines = `B`.
4. Flag if `B > U`. Flag severity:
   - `B - U == 1` → **warn** (likely transcription, fix before submission)
   - `B - U >= 2` → **block** (do not submit until reviewed)

Visits where `B < U` (under-billing) are also surfaced in a separate
"revenue left on table" report — same data, opposite sign.

### Payer matrix

| Payer family | 8-minute rule applies? |
|--------------|-----------------------|
| Medicare Part B | Yes |
| Medicare Advantage | Yes (default; verify per plan) |
| BCBS, Aetna, Cigna, UHC | Yes (most plans) |
| Workers' Comp | **No** — state-specific rules; do not flag |
| Auto / MVA | **No** — state-specific rules; do not flag |
| Self-pay | N/A |

Maintain the per-payer flag in `data/payer_billing_rules.parquet`.

---

## Plan-of-care signature requirement

**Medicare Part B requirement:** the patient's plan of care (POC) must be
signed by the referring physician within 30 calendar days of the initial
evaluation. Claims for treatment visits delivered before signature can be
billed but are at risk of denial / clawback if the signature does not arrive.

### Flag logic

For each claim line on a treatment visit (CPT 97110–97546 family):
1. Look up the patient's active plan of care.
2. Compute `days_since_eval = visit_date - eval_date`.
3. If `days_since_eval > 30` AND POC signature date is null OR
   POC signature date > eval_date + 30: **flag**.
4. Severity:
   - Within 30 days but unsigned: **warn** (chase signature now)
   - Beyond 30 days, unsigned: **block** (do not bill)
   - Beyond 30 days, late signature: **warn** (bill is at clawback risk)

### Special cases

- **Telehealth evals:** same 30-day rule; signature can be electronic.
- **Re-evals (97164):** start a new 30-day window from the re-eval date.
- **Maintenance therapy:** must have updated POC signed every 90 days
  (not enforced in v0.1.0 — track manually).

---

## Modifier 59 guidance (planned for v0.2)

CMS allows modifier 59 to indicate that two services that would normally be
bundled were performed on distinct anatomical sites, in distinct sessions,
or for distinct conditions. It is the most-abused modifier in PT billing.

### Flag logic (preview)

Surface visits where:
- Modifier 59 is appended to a code that has an NCCI edit pair on the visit
- The two paired codes were performed within the same 15-minute timed block
- The patient's documentation does not separately note the distinct service

This requires NCCI edit table lookup (`data/ncci_pairs.parquet`) — implement
in v0.2.

---

## Common denial reason codes (CARC)

Track top-N each week. Most frequent in PT:

| CARC | Description | Common cause |
|------|-------------|--------------|
| 16 | Claim/service lacks information | Missing modifier or NPI |
| 18 | Duplicate claim/service | Already submitted, often a clearinghouse retry |
| 50 | Non-covered services not deemed medically necessary | LCD criteria not met |
| 96 | Non-covered charge(s) | Service excluded under plan |
| 97 | Bundled into payment for another service | NCCI edit not appealed; see modifier 59 above |
| 109 | Claim/service not covered by this payer | Wrong payer on file |
| 119 | Benefit maximum has been reached | Visit cap exhausted; coordinate with patient |
| 197 | Precertification/authorization absent | Auth not obtained or expired |
| 252 | Attachment/documentation required to adjudicate | Send notes |

Mapping CARC → remediation hints lives in `data/carc_remediation.json`.

---

## Reporting conventions

- Dates in claim records are in US Eastern; convert before comparison.
- Visit-level flags are aggregated to the claim before display.
- Billed amounts are pre-adjustment (gross charges).
- Patient identifiers (name, MRN, DOB) are **never** included in any output.
  Use internal `patient_id` (a non-PHI surrogate maintained in the EMR
  reporting view) for any output that needs to identify a record.
