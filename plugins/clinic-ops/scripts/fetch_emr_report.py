"""Fetch aggregate EMR reports for all 8 clinics.

In dev mode (CLINIC_OPS_ENV=dev), reads from synthetic fixtures.
In prod, hits the EMR vendor's reporting API.

Refuses to write any payload that contains row-level patient data.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import pathlib
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from typing import Any

import audit

CLINICS = ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08"]
APPROVED_HOSTS = {"api.[your-emr-vendor].com"}

# Field names that, if present at any nesting level, indicate the payload
# carries patient-level data the rollup must never persist. Defense-in-depth
# — the EMR reporting API is contracted to return aggregates.
PHI_FIELDS = {
    "patient_name", "first_name", "last_name", "full_name",
    "dob", "date_of_birth", "birth_date", "birthdate",
    "ssn", "social_security_number",
    "mrn", "medical_record_number",
    "member_id", "subscriber_id", "policy_number", "account_number",
    "address", "street", "street_address", "home_address",
    "city", "zip", "zipcode", "zip_code", "postal_code",
    "phone", "phone_number", "email", "email_address",
    "diagnosis", "diagnosis_code", "icd10", "icd_10",
}


def is_aggregate(payload: Any) -> bool:
    """Return True iff payload contains no PHI fields at any level."""
    if isinstance(payload, dict):
        if PHI_FIELDS & payload.keys():
            return False
        return all(is_aggregate(v) for v in payload.values())
    if isinstance(payload, list):
        return all(is_aggregate(item) for item in payload)
    return True


def fetch_dev(clinic: str, start: str, end: str) -> dict:
    fixture = pathlib.Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "synthetic_week.json"
    with fixture.open() as fh:
        data = json.load(fh)
    return data["clinics"][clinic]


def _tls_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def fetch_prod(clinic: str, start: str, end: str, include: list[str] | None = None) -> dict:
    api_key = os.environ.get("EMR_REPORTING_API_KEY")
    if not api_key:
        raise RuntimeError("EMR_REPORTING_API_KEY not set; aborting before any network call")

    params = [f"clinic={clinic}", f"start={start}", f"end={end}"]
    if include:
        params.append("include=" + ",".join(include))
    url = "https://api.[your-emr-vendor].com/v1/reports/operational?" + "&".join(params)

    host = re.match(r"https://([^/]+)/", url)
    if not host or host.group(1) not in APPROVED_HOSTS:
        raise RuntimeError(f"refusing to call non-allowlisted host: {host.group(1) if host else url}")

    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    ctx = _tls_context()
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            if 400 <= exc.code < 500:
                raise RuntimeError(f"EMR API client error {exc.code}: {exc.reason}") from exc
            last_err = exc
        except Exception as exc:
            last_err = exc
        time.sleep(2 ** attempt)
    raise RuntimeError(f"EMR API failed after retries: {last_err}")


def fetch_one(clinic: str, start: str, end: str, include: list[str] | None = None) -> dict:
    if os.environ.get("CLINIC_OPS_ENV") == "dev":
        return fetch_dev(clinic, start, end)
    return fetch_prod(clinic, start, end, include=include)


def _resolve_window(args: argparse.Namespace) -> tuple[str, str, str]:
    """Return (start_iso, end_iso, label) from --start/--end, --week, --weeks, or --month."""
    if args.start and args.end:
        return args.start, args.end, args.week or args.start
    if args.week:
        year_str, week_str = args.week.split("-")
        import datetime as dt
        year, week = int(year_str), int(week_str)
        monday = dt.date.fromisocalendar(year, week, 1)
        sunday = dt.date.fromisocalendar(year, week, 7)
        return monday.isoformat(), sunday.isoformat(), args.week
    if args.weeks:
        import datetime as dt
        today = dt.date.today()
        end = today - dt.timedelta(days=today.weekday() + 1)
        start = end - dt.timedelta(weeks=args.weeks - 1, days=6)
        return start.isoformat(), end.isoformat(), f"rolling-{args.weeks}w"
    if args.month:
        import calendar
        import datetime as dt
        year, month = (int(x) for x in args.month.split("-"))
        last_day = calendar.monthrange(year, month)[1]
        return (
            dt.date(year, month, 1).isoformat(),
            dt.date(year, month, last_day).isoformat(),
            args.month,
        )
    raise SystemExit("provide --start/--end, --week, --weeks, or --month")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--week")
    parser.add_argument("--weeks", type=int)
    parser.add_argument("--month")
    parser.add_argument("--include", action="append", default=[],
                        help="repeatable: extra report sections (therapists, schedule_events, referrals)")
    args = parser.parse_args(argv)

    start, end, label = _resolve_window(args)
    cache_dir = pathlib.Path(".cache") / label
    cache_dir.mkdir(parents=True, exist_ok=True)

    errors: list[tuple[str, str]] = []

    def fetch_and_persist(clinic: str) -> None:
        payload = fetch_one(clinic, start, end, include=args.include or None)
        if not is_aggregate(payload):
            errors.append((clinic, "row-level patient data returned"))
            return
        (cache_dir / f"{clinic}.json").write_text(json.dumps(payload, indent=2))

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(fetch_and_persist, CLINICS))

    if errors:
        for clinic, reason in errors:
            sys.stderr.write(f"DEFECT: {clinic}: {reason}\n")
        audit.write(
            "fetch-emr-report", status="err",
            label=label, clinics=len(CLINICS), failed=len(errors),
        )
        return 2

    audit.write(
        "fetch-emr-report", status="ok",
        label=label, clinics=len(CLINICS),
        include=",".join(args.include) if args.include else "",
    )
    print(json.dumps({"cache_dir": str(cache_dir), "clinics": CLINICS, "label": label}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
