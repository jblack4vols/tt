"""Resolve an ISO week argument to start/end dates.

Usage:
    python scripts/resolve_week.py [--week YYYY-WW]

If --week is omitted, returns the most recently completed ISO week.
Output: JSON to stdout with week, week_start (Mon), week_end (Sun).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys


def resolve(week_arg: str | None) -> dict:
    if week_arg:
        year_str, week_str = week_arg.split("-")
        year, week = int(year_str), int(week_str)
    else:
        today = dt.date.today()
        last_completed = today - dt.timedelta(days=today.weekday() + 1)
        iso = last_completed.isocalendar()
        year, week = iso.year, iso.week

    monday = dt.date.fromisocalendar(year, week, 1)
    sunday = dt.date.fromisocalendar(year, week, 7)
    return {
        "week": f"{year}-{week:02d}",
        "week_start": monday.isoformat(),
        "week_end": sunday.isoformat(),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", default=None)
    args = parser.parse_args(argv)
    print(json.dumps(resolve(args.week)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
