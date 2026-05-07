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
Every EMR fetch emits a structured line to `audit/access.log` via `scripts/audit.py`.
The audit write happens in code, not in the command prompt — it cannot be
silently skipped. See `audit/sample_audit.log` for the format.

### Actor resolution
Audit lines record the actor in this order of preference:
1. `CLINIC_OPS_ACTOR` env var
2. `git config user.email`
3. `unknown`

**Production deployments must set `CLINIC_OPS_ACTOR`** in the wrapper that
launches the rollup (cron, systemd unit, GitHub Actions workflow, etc.) —
otherwise audits attribute every action to whichever service-account email
happens to be configured for git on that host. Example:

```bash
CLINIC_OPS_ACTOR=clinic-ops@company.com python scripts/fetch_emr_report.py --week 2026-18
```

## Window flags
`fetch_emr_report.py` accepts any of:
- `--start YYYY-MM-DD --end YYYY-MM-DD` — explicit range
- `--week YYYY-WW` — single ISO week
- `--weeks N` — rolling N weeks ending on the most recent Sunday
- `--month YYYY-MM` — calendar month
- `--include <section>` (repeatable) — extra report sections (`therapists`,
  `schedule_events`, `referrals`)

## Security
See `THREAT-MODEL.md` and the company Plugin Development Standard.
