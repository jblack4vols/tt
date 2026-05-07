"""Fetch a pre-submission claim batch from the EMR / practice-management API.

Production gating: this script refuses to make any network call unless the
ANTHROPIC_BAA_SIGNED env var is set to "true" — to be set by IT only after
the Anthropic BAA is countersigned and on file with the Privacy Officer.
Dev mode (BILLING_AUDIT_ENV=dev or CLINIC_OPS_ENV=dev) bypasses the gate
and reads from synthetic fixtures.

Persisted payloads carry only internal identifiers: claim_id, patient_id,
visit_date, CPT lines, billed units, documented minutes, POC signature
dates. Direct identifiers (name, MRN, DOB) are stripped at the EMR
reporting view, not in this script.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import ssl
import sys
import time
import urllib.error
import urllib.request

import audit

APPROVED_HOSTS = {"api.[your-emr-vendor].com"}
DIRECT_IDENTIFIER_FIELDS = {
    "patient_name", "first_name", "last_name", "full_name",
    "dob", "date_of_birth", "birth_date", "birthdate",
    "ssn", "mrn", "medical_record_number",
    "address", "street", "phone", "phone_number", "email",
}


def _is_dev() -> bool:
    return os.environ.get("BILLING_AUDIT_ENV") == "dev" or os.environ.get("CLINIC_OPS_ENV") == "dev"


def _baa_gate() -> None:
    if _is_dev():
        return
    if os.environ.get("ANTHROPIC_BAA_SIGNED") != "true":
        audit.write("billing-audit-fetch", status="err", reason="baa-gate")
        raise SystemExit(
            "BAA gate failed: ANTHROPIC_BAA_SIGNED is not 'true'. "
            "Refusing to access PHI. Contact the Privacy Officer if this is unexpected."
        )


def _strip_direct_identifiers(claim: dict) -> dict:
    """Belt-and-suspenders: even if the EMR view leaks an identifier, drop it here."""
    return {k: v for k, v in claim.items() if k not in DIRECT_IDENTIFIER_FIELDS}


def _tls_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def fetch_dev(label: str) -> list[dict]:
    fixture = pathlib.Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "synthetic_claims.json"
    with fixture.open() as fh:
        return json.load(fh)["claims"]


def fetch_prod(label: str, include: list[str]) -> list[dict]:
    api_key = os.environ.get("EMR_REPORTING_API_KEY")
    if not api_key:
        raise RuntimeError("EMR_REPORTING_API_KEY not set; aborting before any network call")

    params = [f"label={label}"]
    for s in include:
        params.append(f"include={s}")
    url = "https://api.[your-emr-vendor].com/v1/billing/claims?" + "&".join(params)
    host_match = re.match(r"https://([^/]+)/", url)
    if not host_match or host_match.group(1) not in APPROVED_HOSTS:
        raise RuntimeError(f"refusing to call non-allowlisted host: {host_match.group(1) if host_match else url}")

    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    ctx = _tls_context()
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                return json.loads(resp.read())["claims"]
        except urllib.error.HTTPError as exc:
            if 400 <= exc.code < 500:
                raise RuntimeError(f"EMR API client error {exc.code}: {exc.reason}") from exc
            last_err = exc
        except Exception as exc:
            last_err = exc
        time.sleep(2 ** attempt)
    raise RuntimeError(f"EMR API failed after retries: {last_err}")


def _resolve_label(args: argparse.Namespace) -> str:
    if args.batch:
        return args.batch
    if args.week:
        return args.week
    raise SystemExit("provide --batch BATCH_ID or --week YYYY-WW")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", help="Submission batch ID")
    parser.add_argument("--week", help="ISO week YYYY-WW")
    parser.add_argument("--include", action="append", default=[],
                        help="repeatable: extra report sections (poc_signatures, modifier_59)")
    parser.add_argument("--gate-only", action="store_true",
                        help="Exit 0 if the BAA gate passes; do not fetch")
    args = parser.parse_args(argv)

    _baa_gate()
    if args.gate_only:
        print(json.dumps({"baa_gate": "ok", "dev_mode": _is_dev()}))
        return 0

    label = _resolve_label(args)
    cache_dir = pathlib.Path(".cache") / label
    cache_dir.mkdir(parents=True, exist_ok=True)

    raw = fetch_dev(label) if _is_dev() else fetch_prod(label, args.include)
    cleaned = [_strip_direct_identifiers(c) for c in raw]

    out = cache_dir / "claims.json"
    out.write_text(json.dumps({"label": label, "claims": cleaned}, indent=2))

    audit.write(
        "billing-audit-fetch", status="ok",
        label=label, claim_count=len(cleaned),
        include=",".join(args.include) if args.include else "",
    )
    print(json.dumps({"output": str(out), "claim_count": len(cleaned), "label": label}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
