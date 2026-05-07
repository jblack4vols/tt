"""Apply the Medicare 8-minute rule to a fetched claim batch.

See skills/billing-rules/SKILL.md for the canonical formula.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import audit

# Payer families that follow the Medicare 8-minute rule. Per
# skills/billing-rules/SKILL.md: WC, MVA, and self-pay are excluded.
RULE_APPLICABLE_PAYERS = {
    "medicare", "medicare_advantage", "commercial",
}


def allowed_units(minutes: int) -> int:
    """Medicare 8-minute rule: units = max(0, (minutes - 8)//15 + 1) for >= 8."""
    if minutes < 8:
        return 0
    return (minutes - 8) // 15 + 1


def severity(billed: int, allowed: int) -> str:
    delta = billed - allowed
    if delta <= 0:
        return "ok"
    if delta == 1:
        return "warn"
    return "block"


def check_visit(visit: dict) -> dict | None:
    """Return a flag dict if the visit overbilled, else None."""
    if not visit.get("apply_8min_rule", True):
        return None
    payer = visit.get("payer_category")
    if payer is not None and payer not in RULE_APPLICABLE_PAYERS:
        return None

    minutes = sum(int(line.get("documented_minutes", 0)) for line in visit.get("timed_lines", []))
    billed = sum(int(line.get("units", 0)) for line in visit.get("timed_lines", []))
    allowed = allowed_units(minutes)
    sev = severity(billed, allowed)
    if sev == "ok":
        return None

    return {
        "claim_id": visit.get("claim_id"),
        "visit_date": visit.get("visit_date"),
        "documented_minutes": minutes,
        "billed_units": billed,
        "allowed_units": allowed,
        "delta": billed - allowed,
        "severity": sev,
        "payer_category": payer,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True, help="Label used as cache directory name")
    args = parser.parse_args(argv)

    cache_dir = pathlib.Path(".cache") / args.batch
    src = cache_dir / "claims.json"
    if not src.exists():
        sys.stderr.write(f"missing {src}; run fetch_claims.py first\n")
        return 1

    payload = json.loads(src.read_text())
    claims = payload["claims"]
    flags = [f for v in claims if (f := check_visit(v)) is not None]

    counts = {"warn": 0, "block": 0}
    for f in flags:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1

    out_path = cache_dir / "eight_min_flags.json"
    out_path.write_text(json.dumps({"label": args.batch, "flags": flags, "counts": counts}, indent=2))

    audit.write(
        "billing-audit-8min", status="ok",
        batch=args.batch, audited=len(claims), flags=len(flags),
        warn=counts.get("warn", 0), block=counts.get("block", 0),
    )
    for f in flags:
        audit.write(
            "billing-audit-8min-flag",
            batch=args.batch, claim_id=f["claim_id"], severity=f["severity"],
            delta=f["delta"],
        )

    print(json.dumps({
        "output": str(out_path),
        "audited": len(claims),
        "flags": len(flags),
        "counts": counts,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
