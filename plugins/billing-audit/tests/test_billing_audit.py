"""Unit + smoke tests for billing-audit.

Run from the plugin root:
    BILLING_AUDIT_ENV=dev python -m unittest tests.test_billing_audit -v
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_8min_rule  # noqa: E402
import check_poc_signatures  # noqa: E402


class EightMinuteRuleMath(unittest.TestCase):
    """Spot-check the canonical CMS table from skills/billing-rules/SKILL.md."""

    CASES = [
        (0, 0), (7, 0),
        (8, 1), (15, 1), (22, 1),
        (23, 2), (37, 2),
        (38, 3), (52, 3),
        (53, 4), (67, 4),
        (68, 5), (82, 5),
        (83, 6), (97, 6),
        (98, 7), (112, 7),
        (113, 8), (127, 8),
    ]

    def test_table(self) -> None:
        for minutes, expected in self.CASES:
            with self.subTest(minutes=minutes):
                self.assertEqual(check_8min_rule.allowed_units(minutes), expected)

    def test_severity(self) -> None:
        self.assertEqual(check_8min_rule.severity(2, 3), "ok")  # underbilled is OK here
        self.assertEqual(check_8min_rule.severity(3, 3), "ok")
        self.assertEqual(check_8min_rule.severity(4, 3), "warn")  # +1
        self.assertEqual(check_8min_rule.severity(5, 3), "block")  # +2


class EightMinuteRuleCheckVisit(unittest.TestCase):
    def test_correct_billing_not_flagged(self) -> None:
        v = {"claim_id": "X", "payer_category": "medicare",
             "timed_lines": [{"documented_minutes": 30, "units": 2}]}
        self.assertIsNone(check_8min_rule.check_visit(v))

    def test_overbill_warn(self) -> None:
        v = {"claim_id": "X", "payer_category": "medicare",
             "timed_lines": [{"documented_minutes": 27, "units": 3}]}
        flag = check_8min_rule.check_visit(v)
        self.assertIsNotNone(flag)
        self.assertEqual(flag["severity"], "warn")
        self.assertEqual(flag["delta"], 1)

    def test_overbill_block(self) -> None:
        v = {"claim_id": "X", "payer_category": "medicare",
             "timed_lines": [{"documented_minutes": 20, "units": 5}]}
        flag = check_8min_rule.check_visit(v)
        self.assertEqual(flag["severity"], "block")

    def test_workers_comp_excluded(self) -> None:
        v = {"claim_id": "X", "payer_category": "wc",
             "timed_lines": [{"documented_minutes": 20, "units": 5}]}
        self.assertIsNone(check_8min_rule.check_visit(v))


class POCSignatureCheck(unittest.TestCase):
    def _treatment_visit(self, **overrides) -> dict:
        v = {
            "claim_id": "X",
            "patient_id": "P",
            "visit_date": "2026-04-29",
            "timed_lines": [{"cpt": "97110", "documented_minutes": 30, "units": 2}],
            "untimed_lines": [],
            "plan_of_care": {"eval_date": "2026-04-15", "signature_date": "2026-04-22"},
        }
        v.update(overrides)
        return v

    def test_signed_within_window_not_flagged(self) -> None:
        self.assertIsNone(check_poc_signatures.check_visit(
            self._treatment_visit(), dt.date(2026, 4, 29)
        ))

    def test_unsigned_within_window_warn(self) -> None:
        v = self._treatment_visit(
            plan_of_care={"eval_date": "2026-04-25", "signature_date": None},
            visit_date="2026-04-29",
        )
        flag = check_poc_signatures.check_visit(v, dt.date(2026, 4, 29))
        self.assertEqual(flag["severity"], "warn")

    def test_unsigned_past_deadline_block(self) -> None:
        v = self._treatment_visit(
            plan_of_care={"eval_date": "2026-03-15", "signature_date": None},
            visit_date="2026-04-29",
        )
        flag = check_poc_signatures.check_visit(v, dt.date(2026, 4, 29))
        self.assertEqual(flag["severity"], "block")

    def test_late_signature_warn(self) -> None:
        v = self._treatment_visit(
            plan_of_care={"eval_date": "2026-03-01", "signature_date": "2026-04-15"},
        )
        flag = check_poc_signatures.check_visit(v, dt.date(2026, 4, 29))
        self.assertEqual(flag["severity"], "warn")
        self.assertIn("clawback", flag["reason"])

    def test_pure_eval_visit_not_flagged(self) -> None:
        # 97164 is a re-eval — the rule restarts; a pure-eval visit shouldn't
        # be treated as a treatment visit by this v0.1.0 check.
        v = self._treatment_visit(
            timed_lines=[],
            untimed_lines=[{"cpt": "97164", "units": 1}],
        )
        self.assertIsNone(check_poc_signatures.check_visit(v, dt.date(2026, 4, 29)))


class PipelineSmoke(unittest.TestCase):
    LABEL = "synthetic-batch-001"

    def setUp(self) -> None:
        cache = ROOT / ".cache" / self.LABEL
        if cache.exists():
            shutil.rmtree(cache)

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "BILLING_AUDIT_ENV": "dev"}
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT, env=env, capture_output=True, text=True, check=True,
        )

    def test_full_pipeline(self) -> None:
        self._run("scripts/fetch_claims.py", "--batch", self.LABEL)
        self._run("scripts/check_8min_rule.py", "--batch", self.LABEL)
        self._run("scripts/check_poc_signatures.py", "--batch", self.LABEL)

        eight = json.loads((ROOT / ".cache" / self.LABEL / "eight_min_flags.json").read_text())
        poc = json.loads((ROOT / ".cache" / self.LABEL / "pocsign_flags.json").read_text())

        # Hand-traced from the synthetic fixture (see fixture comments):
        # 8-min: CLM-0002 warn, CLM-0004 warn → 2 total
        # POC: CLM-0002 warn, CLM-0004 block, CLM-0006 warn → 3 total
        self.assertEqual(len(eight["flags"]), 2)
        self.assertEqual(eight["counts"]["warn"], 2)
        self.assertEqual(eight["counts"]["block"], 0)

        self.assertEqual(len(poc["flags"]), 3)
        self.assertEqual(poc["counts"]["warn"], 2)
        self.assertEqual(poc["counts"]["block"], 1)


class BAAGate(unittest.TestCase):
    def test_gate_blocks_in_prod_without_env(self) -> None:
        env = {**os.environ}
        env.pop("BILLING_AUDIT_ENV", None)
        env.pop("CLINIC_OPS_ENV", None)
        env.pop("ANTHROPIC_BAA_SIGNED", None)
        result = subprocess.run(
            [sys.executable, "scripts/fetch_claims.py", "--gate-only"],
            cwd=ROOT, env=env, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BAA gate failed", result.stderr)

    def test_gate_passes_in_dev(self) -> None:
        env = {**os.environ, "BILLING_AUDIT_ENV": "dev"}
        env.pop("ANTHROPIC_BAA_SIGNED", None)
        result = subprocess.run(
            [sys.executable, "scripts/fetch_claims.py", "--gate-only"],
            cwd=ROOT, env=env, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
