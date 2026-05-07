# billing-audit — Threat Model

This plugin is materially higher-risk than `clinic-ops`. Read carefully.

## PHI touchpoints

- **Reads PHI by design.** Pre-submission claim batches contain at minimum:
  patient internal ID, MRN, DOB, name, primary diagnosis (ICD-10), payer
  member ID, CPT lines with documented treatment minutes, and plan-of-care
  signature dates.
- The plugin **does not export, log, or transmit** any of those identifiers
  outside the EMR. Only internal claim IDs and aggregate flag counts cross
  into Claude's context window.

## Production gating

This plugin must not run against real claim data unless the following are
all true. The launcher script verifies #1 before the first network call.

| # | Gate | How it's enforced |
|---|------|-------------------|
| 1 | `ANTHROPIC_BAA_SIGNED=true` env var set by IT | Checked in `scripts/fetch_claims.py`; refuses to run otherwise. |
| 2 | Managed `settings.json` with marketplace allowlist | Deployed via MDM by IT. |
| 3 | Operator laptop has FDE + EDR | Verified by MDM compliance check. |
| 4 | `BILLING_AUDIT_ACTOR` set | Audit attribution; audit module falls back to `unknown` otherwise. |

Dev mode (`BILLING_AUDIT_ENV=dev` or `CLINIC_OPS_ENV=dev`) bypasses #1 and
reads only the synthetic fixture.

## Secrets

| Secret | Storage | Loaded by |
|--------|---------|-----------|
| EMR API key | `EMR_REPORTING_API_KEY` env var, sourced from the secrets manager | `scripts/fetch_claims.py` |

No secrets are stored in source.

## Egress

- All requests through stdlib `urllib` with TLS 1.2+ context.
- Host check against `APPROVED_HOSTS = {"api.[your-emr-vendor].com"}`. Same
  defense-in-depth caveat as `clinic-ops`: not a sandbox boundary.

## Audit

- Every fetch emits one structured audit line.
- Every check command emits one summary line per run with: actor, action,
  command, claim count, flag count.
- **Per-claim audit:** when a claim is flagged, an additional line is
  emitted recording the internal `claim_id` and rule that fired. **Patient
  names, MRNs, and DOBs are never written to the audit log.**

## Failure modes

| Failure | Behavior |
|---------|----------|
| BAA gate fails | Exit before any network call. Audit `status=err reason=baa-gate`. |
| EMR API 4xx | Fail fast (no retry). Audit `status=err`. |
| EMR API 5xx | Retry 3x with exponential backoff. |
| Claim payload contains an unexpected field that may be PHI | Treat as defect: flag `claim_id` and `unknown_field`, do not persist payload. |
| Audit log write fails | Suppressed (audit must not crash callers); pair with SIEM monitoring on log gaps. |

## Logging guarantees

- No PHI in `audit/access.log`. Only internal `claim_id`s, rule names,
  status, and counts.
- No PHI in script `stdout` / `stderr`. Operators see internal IDs only.
- Stack-trace sanitization for external error reporters: not yet implemented;
  Sentry integration is gated on adding a scrubber.

## Review cadence

- Threat model reviewed at every minor version bump.
- **Privacy Officer + a Security Officer** must sign off on any change that:
  - Adds an external endpoint
  - Adds a secret or auth mechanism
  - Changes what fields land in `audit/access.log`
  - Loosens any production gate above
