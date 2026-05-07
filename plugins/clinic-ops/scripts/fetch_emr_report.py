"""Fetch aggregate EMR reports for all 8 clinics.

In dev mode (CLINIC_OPS_ENV=dev), reads from synthetic fixtures.
In prod, hits the EMR vendor's reporting API.

Refuses to write any payload that contains row-level patient data.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from typing import Any

CLINICS = ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08"]
APPROVED_HOSTS = {"api.[your-emr-vendor].com"}
PHI_FIELDS = {"patient_name", "first_name", "last_name", "dob",
              "ssn", "mrn", "address", "phone", "email"}


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


def fetch_prod(clinic: str, start: str, end: str) -> dict:
    import urllib.request
    api_key = os.environ.get("EMR_REPORTING_API_KEY")
    if not api_key:
        raise RuntimeError("EMR_REPORTING_API_KEY not set; aborting before any network call")

    url = f"https://api.[your-emr-vendor].com/v1/reports/operational?clinic={clinic}&start={start}&end={end}"
    host = url.split("/")[2]
    if host not in APPROVED_HOSTS:
        raise RuntimeError(f"refusing to call non-allowlisted host: {host}")

    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as exc:
            last_err = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"EMR API failed after retries: {last_err}")


def fetch_one(clinic: str, start: str, end: str) -> dict:
    if os.environ.get("CLINIC_OPS_ENV") == "dev":
        return fetch_dev(clinic, start, end)
    return fetch_prod(clinic, start, end)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--week", default=None,
                        help="ISO week label used for cache directory")
    args = parser.parse_args(argv)

    week_label = args.week or args.start
    cache_dir = pathlib.Path(".cache") / week_label
    cache_dir.mkdir(parents=True, exist_ok=True)

    for clinic in CLINICS:
        payload = fetch_one(clinic, args.start, args.end)
        if not is_aggregate(payload):
            sys.stderr.write(
                f"DEFECT: row-level patient data returned for {clinic}; aborting\n"
            )
            return 2
        out = cache_dir / f"{clinic}.json"
        out.write_text(json.dumps(payload, indent=2))
    print(json.dumps({"cache_dir": str(cache_dir), "clinics": CLINICS}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
