"""Render the weekly KPI rollup as Markdown (and optionally PDF)."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys


def render_markdown(kpis: dict) -> str:
    week = kpis["week"]
    company = kpis["company"]
    lines = [
        f"# Weekly KPI Rollup — {week}",
        "",
        "## Company totals",
        f"- Visits: **{company['visits']:,}**",
        f"- Units billed: **{company['units_billed']:,}**",
        f"- Units/visit: **{company['units_per_visit']}**",
        f"- Gross charges: **${company['gross_charges']:,}**",
        f"- Clinics reporting: {company['clinic_count']}",
        "",
        "## Per-clinic",
        "",
        "| Clinic | Visits | V/FTE | U/V | Cxl% | NS% |",
        "|--------|-------:|------:|----:|-----:|----:|",
    ]
    for c in kpis["clinics"]:
        lines.append(
            f"| {c['clinic_code']} | {c['visits']} | "
            f"{c['visits_per_fte']} | {c['units_per_visit']} | "
            f"{c['cancellation_pct']}% | {c['no_show_pct']}% |"
        )

    flagged = [c for c in kpis["clinics"] if c["no_show_pct"] > 15.0]
    if flagged:
        lines += ["", "## Action: clinics > 15% no-show"]
        for c in flagged:
            lines.append(f"- {c['clinic_code']}: {c['no_show_pct']}%")

    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", required=True)
    parser.add_argument("--format", default="md", choices=["md", "pdf", "both"])
    args = parser.parse_args(argv)

    cache_dir = pathlib.Path(".cache") / args.week
    src = cache_dir / "kpis.json"
    if not src.exists():
        sys.stderr.write(f"missing {src}; run compute_kpis.py first\n")
        return 1

    kpis = json.loads(src.read_text())
    out_dir = pathlib.Path("reports") / args.week
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / "rollup.md"
    md_path.write_text(render_markdown(kpis))
    print(json.dumps({"markdown": str(md_path)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
