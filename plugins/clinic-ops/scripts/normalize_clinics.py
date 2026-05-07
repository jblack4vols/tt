"""Normalize per-clinic JSON payloads into a single canonical structure.

Standardizes clinic codes, payer categories, CPT groupings, and therapist IDs.
Outputs a single JSON file; parquet is optional and only used in prod.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

PAYER_CATEGORIES = {
    "Medicare": "medicare",
    "Medicare Advantage": "medicare_advantage",
    "BCBS": "commercial",
    "Aetna": "commercial",
    "Cigna": "commercial",
    "UHC": "commercial",
    "Workers Comp": "wc",
    "Auto/MVA": "mva",
    "Self Pay": "self_pay",
}


def normalize_payer(name: str) -> str:
    return PAYER_CATEGORIES.get(name, "other")


def normalize_clinic(clinic_payload: dict) -> dict:
    out = {
        "clinic_code": clinic_payload["clinic_code"],
        "scheduled": clinic_payload.get("scheduled_appointments", 0),
        "completed": clinic_payload.get("completed_appointments", 0),
        "cancelled": clinic_payload.get("cancellations", 0),
        "same_day_cancelled": clinic_payload.get("same_day_cancellations", 0),
        "no_show": clinic_payload.get("no_shows", 0),
        "evals": clinic_payload.get("evals", 0),
        "new_patients": clinic_payload.get("new_patients", 0),
        "units_billed": clinic_payload.get("units_billed", 0),
        "fte_total": clinic_payload.get("fte_total", 0.0),
        "gross_charges": clinic_payload.get("gross_charges", 0),
        "expected_reimbursement": clinic_payload.get("expected_reimbursement", 0),
        "payer_mix": {
            normalize_payer(k): v
            for k, v in clinic_payload.get("payer_mix", {}).items()
        },
        "therapists": clinic_payload.get("therapists", []),
    }
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", required=True)
    args = parser.parse_args(argv)

    cache_dir = pathlib.Path(".cache") / args.week
    if not cache_dir.is_dir():
        sys.stderr.write(f"cache dir not found: {cache_dir}\n")
        return 1

    clinics = []
    for f in sorted(cache_dir.glob("C*.json")):
        with f.open() as fh:
            clinics.append(normalize_clinic(json.load(fh)))

    out = cache_dir / "normalized.json"
    out.write_text(json.dumps({"week": args.week, "clinics": clinics}, indent=2))
    print(json.dumps({"output": str(out), "clinic_count": len(clinics)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
