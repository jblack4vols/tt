# clinic-ops — Threat Model

## PHI touchpoints
- **Aggregate-only by contract.** All EMR queries are scoped to operational
  reports that return counts (visits, units, charges) grouped by clinic,
  therapist, payer, or CPT code. The plugin does not request patient-level
  records.
- Therapist-level data is workforce data, not PHI.

## Defense-in-depth: row-level data refusal
`fetch_emr_report.py` calls `is_aggregate()` on every payload before
persisting. The check rejects any object whose keys (at any nesting depth)
match a list of PHI field names (`mrn`, `dob`, `ssn`, `address`, etc.). On
match, the script writes an audit line with `status=err` and exits non-zero
without writing the payload to disk.

This is a backstop against an EMR API change, not a primary control. Field-
name detection cannot catch every possible PHI shape (e.g. PHI smuggled into
opaque string values). Treat the EMR-side report contract as the primary
guarantee.

## Secrets
| Secret | Storage | Loaded by |
|--------|---------|-----------|
| EMR API key | `EMR_REPORTING_API_KEY` env var, sourced from the company secrets manager | `scripts/fetch_emr_report.py` |

No secrets are stored in source, in `plugin.json`, or in any committed file.

## Egress
- All outbound HTTPS requests go through Python's stdlib `urllib` with an
  explicit TLS 1.2+ context (`ssl.create_default_context()` +
  `ssl.TLSVersion.TLSv1_2`).
- Before each request, the URL host is parsed and compared against
  `APPROVED_HOSTS = {"api.[your-emr-vendor].com"}`. The check defends against
  accidental URL construction errors; it is not a sandbox boundary. Hardening
  to a per-process egress allowlist (e.g. proxy or `iptables`) is a follow-up.

## Audit
- `scripts/audit.py` writes one structured line per PHI-adjacent action to
  `audit/access.log`. Every `fetch_emr_report.py` invocation emits one line
  (success or failure). Audit writes are best-effort and never raise.
- Actor resolves from `CLINIC_OPS_ACTOR`, then `git config user.email`,
  then `unknown`.
- The log file is `.gitignore`d and intended to ship to the company SIEM via
  OTel collector / log shipper.

## Failure modes
| Failure | Behavior |
|---------|----------|
| EMR API 4xx | Fail fast, no retry, audit line `status=err`. |
| EMR API 5xx / network | Retry up to 3x with exponential backoff, then audit and exit non-zero. |
| EMR API returns row-level patient data | Audit `status=err`, exit non-zero, no payload written. |
| `EMR_REPORTING_API_KEY` unset | Exit before any network call. |
| Audit-log write fails | Suppressed; the operational call still proceeds (audit must not crash callers). Pair with SIEM monitoring on log-shipping gaps. |

## Logging guarantees
- No PHI is written to `audit/access.log` — only `actor`, `action`, `status`,
  and aggregate metadata (week label, clinic count, optional include sections).
- Stack traces are not currently sanitized for external error reporters.
  When/if Sentry or similar is integrated, add a scrubber and document here.

## Review cadence
- Threat model reviewed each minor version bump.
- Privacy Officer sign-off required for any change that adds an external
  endpoint, secret, or new data class.
