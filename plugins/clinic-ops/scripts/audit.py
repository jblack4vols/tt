"""Audit-log helper for clinic-ops commands.

The plugin's compliance posture depends on every PHI-adjacent action emitting
an audit line. Centralizing the write here means scripts cannot silently skip
it — call sites that touch the EMR API import this module.

Format (one space-separated KV line per action):
    <ISO-8601 UTC>  actor=<email>  action=<name>  status=<ok|err>  ...kv

The `actor` resolves from CLINIC_OPS_ACTOR (preferred), then `git config
user.email`, then "unknown".
"""
from __future__ import annotations

import datetime as dt
import os
import pathlib
import shlex
import subprocess

LOG_PATH = pathlib.Path(__file__).resolve().parents[1] / "audit" / "access.log"


def _resolve_actor() -> str:
    actor = os.environ.get("CLINIC_OPS_ACTOR")
    if actor:
        return actor
    try:
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    return "unknown"


def _format_value(value: object) -> str:
    s = str(value)
    return shlex.quote(s) if any(c.isspace() for c in s) else s


def write(action: str, status: str = "ok", **fields: object) -> None:
    """Append one structured audit line. Never raises — audit must not crash callers."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        actor = _resolve_actor()
        parts = [
            timestamp,
            f"actor={actor}",
            f"action={action}",
            f"status={status}",
        ]
        parts.extend(f"{k}={_format_value(v)}" for k, v in fields.items())
        line = " ".join(parts) + "\n"
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        pass
