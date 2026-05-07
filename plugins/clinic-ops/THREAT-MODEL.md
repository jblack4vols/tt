# clinic-ops — Threat Model

## PHI touchpoints
- **None at the patient level.** All EMR queries return aggregate counts (visits, units, charges) grouped by clinic, therapist, payer, or CPT code.
- Therapist-level data is workforce data, not PHI.

## Secrets used
| Secret | Storage | Loaded by |
|--------|---------|-----------|
| EMR API key | Company secrets manager (`emr/reporting-api-key`) | `scripts/fetch_emr_report.py` |

No secrets are stored in source, in `plugin.json`, or in any committed file.

## Egress endpoints
- `https://api.[your-emr-vendor].com/v1/reports/*` — TLS 1.2+, host pinned via allowlist.
- No other outbound calls. Plugin will refuse to run if any other host is contacted.

## Failure modes
| Failure | Behavior |
|---------|----------|
| EMR API 5xx | Retry 3x with exponential backoff, then exit non-zero with clear error. No partial report produced. |
| EMR API returns row-level patient data | Treated as defect: command exits, audit log entry written, ticket auto-filed. |
| Secrets manager unavailable | Command exits before any network call. |
| Audit log write fails | Command exits before producing report. |

## Logging guarantees
- No PHI in logs.
- Every PHI-adjacent action (any EMR API call) emits one structured audit line: timestamp, actor email, command, week, clinic count, status.
- Stack traces are sanitized before any external error reporter (Sentry) is contacted.

## Review cadence
- Threat model reviewed each minor version bump.
- Privacy Officer sign-off required for any change that adds an external endpoint or new data class.
