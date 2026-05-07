"""Smoke tests for the clinic-ops pipeline against synthetic data.

Run from the plugin root:
    CLINIC_OPS_ENV=dev python -m unittest tests/test_compute_kpis.py
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(*args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLINIC_OPS_ENV": "dev"}
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT, env=env, capture_output=True, text=True, check=True,
    )


class PipelineSmoke(unittest.TestCase):
    WEEK = "2026-18"

    def setUp(self) -> None:
        cache = ROOT / ".cache" / self.WEEK
        if cache.exists():
            shutil.rmtree(cache)

    def test_full_pipeline(self) -> None:
        run("scripts/fetch_emr_report.py", "--start", "2026-04-27",
            "--end", "2026-05-03", "--week", self.WEEK)
        run("scripts/normalize_clinics.py", "--week", self.WEEK)
        run("scripts/compute_kpis.py", "--week", self.WEEK)

        kpis = json.loads(
            (ROOT / ".cache" / self.WEEK / "kpis.json").read_text()
        )
        self.assertEqual(kpis["company"]["clinic_count"], 8)
        self.assertGreater(kpis["company"]["visits"], 0)
        for c in kpis["clinics"]:
            self.assertIn("visits_per_fte", c)
            self.assertIn("cancellation_pct", c)
            self.assertGreaterEqual(c["visits_per_fte"], 0)


if __name__ == "__main__":
    unittest.main()
