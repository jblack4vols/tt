"""Unit tests for clinic-ops helpers.

Run from the plugin root:
    python -m unittest tests.test_units -v
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import compute_kpis  # noqa: E402
import fetch_emr_report  # noqa: E402
import resolve_week  # noqa: E402


class IsAggregate(unittest.TestCase):
    def test_aggregate_payload(self) -> None:
        self.assertTrue(fetch_emr_report.is_aggregate(
            {"clinic_code": "C01", "visits": 100, "payer_mix": {"medicare": 0.4}}
        ))

    def test_top_level_phi_field(self) -> None:
        self.assertFalse(fetch_emr_report.is_aggregate(
            {"clinic_code": "C01", "patient_name": "Smith"}
        ))

    def test_nested_phi_field(self) -> None:
        self.assertFalse(fetch_emr_report.is_aggregate(
            {"clinic_code": "C01", "rows": [{"visits": 1, "mrn": "A123"}]}
        ))

    def test_phi_variants_caught(self) -> None:
        for field in ("dob", "date_of_birth", "ssn", "medical_record_number",
                      "member_id", "zip_code", "phone_number", "diagnosis_code"):
            with self.subTest(field=field):
                self.assertFalse(fetch_emr_report.is_aggregate({field: "x"}))


class ComputeKPIs(unittest.TestCase):
    SAMPLE = {
        "clinic_code": "C01",
        "scheduled": 400,
        "completed": 360,
        "cancelled": 20,
        "same_day_cancelled": 12,
        "no_show": 20,
        "evals": 30,
        "new_patients": 28,
        "units_billed": 1440,
        "fte_total": 4.0,
        "gross_charges": 80000,
        "expected_reimbursement": 42000,
        "payer_mix": {"medicare": 0.35},
    }

    def test_visits_per_fte(self) -> None:
        out = compute_kpis.compute_clinic(self.SAMPLE)
        self.assertEqual(out["visits_per_fte"], 90.0)

    def test_units_per_visit(self) -> None:
        out = compute_kpis.compute_clinic(self.SAMPLE)
        self.assertEqual(out["units_per_visit"], 4.0)

    def test_cancellation_pct_rounded_one_decimal(self) -> None:
        out = compute_kpis.compute_clinic(self.SAMPLE)
        self.assertEqual(out["cancellation_pct"], 5.0)

    def test_no_show_pct(self) -> None:
        out = compute_kpis.compute_clinic(self.SAMPLE)
        self.assertEqual(out["no_show_pct"], 5.0)

    def test_zero_division_returns_zero(self) -> None:
        empty = {**self.SAMPLE, "completed": 0, "scheduled": 0, "fte_total": 0.0}
        out = compute_kpis.compute_clinic(empty)
        self.assertEqual(out["visits_per_fte"], 0.0)
        self.assertEqual(out["units_per_visit"], 0.0)
        self.assertEqual(out["cancellation_pct"], 0.0)


class ResolveWeek(unittest.TestCase):
    def test_explicit_week(self) -> None:
        out = resolve_week.resolve("2026-18")
        self.assertEqual(out["week"], "2026-18")
        self.assertEqual(out["week_start"], "2026-04-27")
        self.assertEqual(out["week_end"], "2026-05-03")

    def test_default_uses_most_recently_completed_week(self) -> None:
        # We can't pin "today" without monkey-patching; sanity-check the
        # output shape and that week_end is a Sunday.
        out = resolve_week.resolve(None)
        end = dt.date.fromisoformat(out["week_end"])
        self.assertEqual(end.isoweekday(), 7)  # Sunday
        start = dt.date.fromisoformat(out["week_start"])
        self.assertEqual((end - start).days, 6)


if __name__ == "__main__":
    unittest.main()
