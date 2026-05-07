"""Apply the plan-of-care signature rule to a fetched claim batch.

See skills/billing-rules/SKILL.md "Plan-of-care signature requirement".
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

import audit

WINDOW_DAYS = 30
# Explicit set, not prefix match — 97161-97164 are EVALS and must not be
# treated as treatment visits (they restart the 30-day window per SKILL.md).
TREATMENT_CPTS = frozenset({
    # Timed treatment codes
    "97110", "97112", "97116", "97124", "97140",
    "97530", "97532", "97533", "97535", "97537", "97542",
    "97760", "97761", "97763",
    # Untimed treatment / modality codes
    "97010", "97012", "97014", "97016", "97018", "97022", "97026",
    "97028", "97032", "97033", "97034", "97035", "97036", "97039",
    "97150",
})


def _parse_date(s: str | None) -> dt.date | None:
    return dt.date.fromisoformat(s) if s else None


def _is_treatment_visit(visit: dict) -> bool:
    cpts = {line.get("cpt") for line in visit.get("timed_lines", []) + visit.get("untimed_lines", [])}
    return any(c in TREATMENT_CPTS for c in cpts if c)


def check_visit(visit: dict, today: dt.date) -> dict | None:
    if not _is_treatment_visit(visit):
        return None

    poc = visit.get("plan_of_care", {})
    eval_date = _parse_date(poc.get("eval_date"))
    sig_date = _parse_date(poc.get("signature_date"))
    visit_date = _parse_date(visit.get("visit_date")) or today
    if not eval_date:
        return None

    deadline = eval_date + dt.timedelta(days=WINDOW_DAYS)
    visit_past_deadline = visit_date > deadline

    if sig_date is None:
        if visit_past_deadline:
            severity = "block"
            reason = "unsigned past 30 days"
        else:
            severity = "warn"
            reason = "unsigned within window"
    elif sig_date > deadline:
        severity = "warn"
        reason = "late signature (clawback risk)"
    else:
        return None

    return {
        "claim_id": visit.get("claim_id"),
        "patient_id": visit.get("patient_id"),
        "visit_date": visit.get("visit_date"),
        "eval_date": eval_date.isoformat(),
        "signature_date": sig_date.isoformat() if sig_date else None,
        "deadline": deadline.isoformat(),
        "severity": severity,
        "reason": reason,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True)
    args = parser.parse_args(argv)

    cache_dir = pathlib.Path(".cache") / args.batch
    src = cache_dir / "claims.json"
    if not src.exists():
        sys.stderr.write(f"missing {src}; run fetch_claims.py first\n")
        return 1

    payload = json.loads(src.read_text())
    claims = payload["claims"]
    today = dt.date.today()
    flags = [f for v in claims if (f := check_visit(v, today)) is not None]

    counts = {"warn": 0, "block": 0}
    for f in flags:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1

    out_path = cache_dir / "pocsign_flags.json"
    out_path.write_text(json.dumps({"label": args.batch, "flags": flags, "counts": counts}, indent=2))

    audit.write(
        "billing-audit-pocsign", status="ok",
        batch=args.batch, audited=len(claims), flags=len(flags),
        warn=counts.get("warn", 0), block=counts.get("block", 0),
    )
    for f in flags:
        audit.write(
            "billing-audit-pocsign-flag",
            batch=args.batch, claim_id=f["claim_id"],
            severity=f["severity"], reason=f["reason"],
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
