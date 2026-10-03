#!/usr/bin/env python3
"""
scripts/calculate_schedule.py
Generates a random day of the month (1-30) for the 3:14 AM UTC roundtrip trigger
and dynamically updates the cron schedule in .github/workflows/roundtrip-initiator.yml.
"""

import argparse
import datetime
import json
import os
import re
import sys

WORKFLOW_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".github",
    "workflows",
    "roundtrip-initiator.yml",
)


def compute_next_schedule(current_date: datetime.date = None):
    if current_date is None:
        current_date = datetime.date.today()

    # Advance to the subsequent calendar month
    if current_date.month == 12:
        next_month = 1
        next_year = current_date.year + 1
    else:
        next_month = current_date.month + 1
        next_year = current_date.year

    # Select random start day (1 to 30)
    # Using 30 ensures valid day for all months including April, June, Sept, Nov (and Feb handles leap/overflow safely)
    import random

    # Seed with time and system random
    rnd = random.SystemRandom()
    next_day = rnd.randint(1, 30)

    # February check: cap at 28 (or 29 in leap year)
    if next_month == 2:
        is_leap = (next_year % 4 == 0 and next_year % 100 != 0) or (
            next_year % 400 == 0
        )
        max_feb = 29 if is_leap else 28
        if next_day > max_feb:
            next_day = rnd.randint(1, max_feb)

    cron_expression = f"14 3 {next_day} {next_month} *"
    target_date_iso = f"{next_year:04d}-{next_month:02d}-{next_day:02d}T03:14:00Z"

    return {
        "day": next_day,
        "month": next_month,
        "year": next_year,
        "cron_expression": cron_expression,
        "target_date_iso": target_date_iso,
    }


def update_initiator_workflow(cron_expression: str, workflow_file: str = WORKFLOW_PATH) -> bool:
    if not os.path.exists(workflow_file):
        print(f"Workflow file not found at {workflow_file}", file=sys.stderr)
        return False

    with open(workflow_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern to match cron line under schedule
    cron_pattern = re.compile(r"(\s*-\s*cron:\s*['\"]).*?(['\"])")
    if not cron_pattern.search(content):
        print(f"Could not find cron schedule pattern in {workflow_file}", file=sys.stderr)
        return False

    updated_content = cron_pattern.sub(rf"\g<1>{cron_expression}\g<2>", content)

    with open(workflow_file, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Successfully updated {workflow_file} with cron: '{cron_expression}'")
    return True


def main():
    parser = argparse.ArgumentParser(description="Calculate next month's random 03:14 UTC roundtrip schedule")
    parser.add_argument("--update-workflow", action="store_true", help="Update the cron schedule in roundtrip-initiator.yml")
    parser.add_argument("--workflow-path", default=WORKFLOW_PATH, help="Path to initiator workflow YAML")
    parser.add_argument("--json", action="store_true", help="Output JSON payload")
    parser.add_argument("--date", help="Simulate execution from ISO date (YYYY-MM-DD)")

    args = parser.parse_args()

    ref_date = None
    if args.date:
        ref_date = datetime.date.fromisoformat(args.date)

    schedule = compute_next_schedule(ref_date)

    if args.update_workflow:
        update_initiator_workflow(schedule["cron_expression"], args.workflow_path)

    if args.json:
        print(json.dumps(schedule, indent=2))
    else:
        print(f"Next Scheduled Run: {schedule['target_date_iso']}")
        print(f"Cron Expression:    {schedule['cron_expression']}")


if __name__ == "__main__":
    main()
