"""Unit tests for clinic-ops helpers.

Run from the plugin root:
    python -m unittest tests.test_units -v
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit  # noqa: E402
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
        out = resolve_week.resolve(None)
        end = dt.date.fromisoformat(out["week_end"])
        self.assertEqual(end.isoweekday(), 7)  # Sunday
        start = dt.date.fromisoformat(out["week_start"])
        self.assertEqual((end - start).days, 6)

    def test_iso_week_53(self) -> None:
        # 2026 has 53 ISO weeks; W53 spans 2026-12-28 to 2027-01-03.
        out = resolve_week.resolve("2026-53")
        self.assertEqual(out["week_start"], "2026-12-28")
        self.assertEqual(out["week_end"], "2027-01-03")

    def test_iso_week_1_can_start_in_prior_year(self) -> None:
        # ISO 2025-W01 starts on 2024-12-30 (Thursday rule).
        out = resolve_week.resolve("2025-01")
        self.assertEqual(out["week_start"], "2024-12-30")
        self.assertEqual(out["week_end"], "2025-01-05")


class ResolveWindow(unittest.TestCase):
    def _ns(self, **kwargs: object) -> argparse.Namespace:
        defaults = {"start": None, "end": None, "week": None,
                    "weeks": None, "month": None, "include": []}
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def test_explicit_start_end(self) -> None:
        start, end, label = fetch_emr_report._resolve_window(
            self._ns(start="2026-04-27", end="2026-05-03")
        )
        self.assertEqual((start, end, label), ("2026-04-27", "2026-05-03", "2026-04-27"))

    def test_week_resolves_to_iso_dates(self) -> None:
        start, end, label = fetch_emr_report._resolve_window(self._ns(week="2026-18"))
        self.assertEqual((start, end, label), ("2026-04-27", "2026-05-03", "2026-18"))

    def test_month_uses_full_calendar_month(self) -> None:
        start, end, label = fetch_emr_report._resolve_window(self._ns(month="2026-02"))
        self.assertEqual((start, end, label), ("2026-02-01", "2026-02-28", "2026-02"))

    def test_month_handles_leap_year(self) -> None:
        start, end, _ = fetch_emr_report._resolve_window(self._ns(month="2024-02"))
        self.assertEqual(end, "2024-02-29")

    def test_weeks_rolling_window_label(self) -> None:
        _, _, label = fetch_emr_report._resolve_window(self._ns(weeks=4))
        self.assertEqual(label, "rolling-4w")

    def test_no_args_raises(self) -> None:
        with self.assertRaises(SystemExit):
            fetch_emr_report._resolve_window(self._ns())


class Audit(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.log_path = pathlib.Path(self.tmpdir.name) / "audit" / "access.log"
        self._log_patch = mock.patch.object(audit, "LOG_PATH", self.log_path)
        self._log_patch.start()
        self.addCleanup(self._log_patch.stop)

    def test_format_value_bare_for_simple_strings(self) -> None:
        self.assertEqual(audit._format_value("foo"), "foo")
        self.assertEqual(audit._format_value("user@company.com"), "user@company.com")
        self.assertEqual(audit._format_value("2026-18"), "2026-18")

    def test_format_value_quotes_with_whitespace(self) -> None:
        self.assertEqual(audit._format_value("hello world"), '"hello world"')

    def test_format_value_quotes_with_single_quote(self) -> None:
        # Previously shlex would emit awkward output; now JSON escapes cleanly.
        self.assertEqual(audit._format_value("it's"), '"it\'s"')

    def test_format_value_handles_int(self) -> None:
        self.assertEqual(audit._format_value(42), "42")

    def test_resolve_actor_prefers_env(self) -> None:
        with mock.patch.dict(os.environ, {"CLINIC_OPS_ACTOR": "ops@example.com"}):
            self.assertEqual(audit._resolve_actor(), "ops@example.com")

    def test_write_creates_directory_and_log(self) -> None:
        self.assertFalse(self.log_path.parent.exists())
        with mock.patch.dict(os.environ, {"CLINIC_OPS_ACTOR": "alice@example.com"}):
            audit.write("test-action", week="2026-18", clinics=8)
        self.assertTrue(self.log_path.exists())
        line = self.log_path.read_text().strip()
        self.assertIn("actor=alice@example.com", line)
        self.assertIn("action=test-action", line)
        self.assertIn("status=ok", line)
        self.assertIn("week=2026-18", line)
        self.assertIn("clinics=8", line)

    def test_write_never_raises_on_filesystem_error(self) -> None:
        # Point the log at a path under a nonexistent parent we can't create
        # (read-only mount). Best we can do portably: monkeypatch open().
        with mock.patch("builtins.open", side_effect=PermissionError):
            audit.write("test-action")  # must not raise


if __name__ == "__main__":
    unittest.main()
