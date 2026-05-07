"""Compute KPIs from normalized clinic data using the canonical formulas
defined in skills/kpi-definitions/SKILL.md. Keep this module the single
implementation site for all metrics.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys


def safe_div(numerator: float, denominator: float) -> float:
    return (numerator / denominator) if denominator else 0.0


def pct(numerator: float, denominator: float) -> float:
    return round(safe_div(numerator, denominator) * 100, 1)


def compute_clinic(c: dict) -> dict:
    return {
        "clinic_code": c["clinic_code"],
        "visits": c["completed"],
        "new_patients": c["new_patients"],
        "units_billed": c["units_billed"],
        "visits_per_fte": round(safe_div(c["completed"], c["fte_total"]), 2),
        "units_per_visit": round(safe_div(c["units_billed"], c["completed"]), 2),
        "cancellation_pct": pct(c["cancelled"], c["scheduled"]),
        "same_day_cancel_pct": pct(c["same_day_cancelled"], c["scheduled"]),
        "no_show_pct": pct(c["no_show"], c["scheduled"]),
        "gross_charges": c["gross_charges"],
        "expected_reimbursement": c["expected_reimbursement"],
        "payer_mix": c["payer_mix"],
    }


def compute_company(clinic_kpis: list[dict]) -> dict:
    total_visits = sum(c["visits"] for c in clinic_kpis)
    total_units = sum(c["units_billed"] for c in clinic_kpis)
    total_charges = sum(c["gross_charges"] for c in clinic_kpis)
    return {
        "visits": total_visits,
        "units_billed": total_units,
        "units_per_visit": round(safe_div(total_units, total_visits), 2),
        "gross_charges": total_charges,
        "clinic_count": len(clinic_kpis),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", required=True)
    parser.add_argument("--by", default=None)
    args = parser.parse_args(argv)

    cache_dir = pathlib.Path(".cache") / args.week
    src = cache_dir / "normalized.json"
    if not src.exists():
        sys.stderr.write(f"missing {src}; run normalize_clinics.py first\n")
        return 1

    data = json.loads(src.read_text())
    clinic_kpis = [compute_clinic(c) for c in data["clinics"]]
    out = {
        "week": args.week,
        "clinics": clinic_kpis,
        "company": compute_company(clinic_kpis),
    }

    out_path = cache_dir / "kpis.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(json.dumps({"output": str(out_path)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
