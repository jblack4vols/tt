# clinic-ops

Internal Claude Code plugin that produces operational KPI rollups across all 8 [Company Name] outpatient PT clinics.

## Purpose
Replace the manual Monday-morning spreadsheet that pulls per-clinic productivity, revenue, and visit-volume metrics from the EMR reporting API into a single email/Slack-ready report for ownership.

## Commands
| Command | What it does |
|---------|-------------|
| `/ops:weekly-kpi-rollup` | Full weekly rollup across all 8 clinics |
| `/ops:therapist-productivity` | Per-therapist productivity (by internal ID) |
| `/ops:cancellation-report` | Cancellation + no-show analysis with action thresholds |
| `/ops:referral-source-summary` | Top referrers and conversion by clinic |

## Data accessed
- EMR reporting API (`api.[your-emr-vendor].com`) — aggregate counts only, never patient-level data.
- Internal payer-rate table at `data/payer_rates.parquet` (no PHI).

## External services contacted
- EMR vendor reporting endpoint (TLS 1.2+).
- No other outbound network calls.

## Development
- Default mode pulls from the EMR API. Set `CLINIC_OPS_ENV=dev` to read from `tests/fixtures/synthetic_week.json`.
- All tests run against synthetic data. Real PHI is never used in development.

## Audit
Every command emits an entry to `audit/access.log`. See `audit/sample_audit.log` for format.

## Security
See `THREAT-MODEL.md` and the company Plugin Development Standard.
