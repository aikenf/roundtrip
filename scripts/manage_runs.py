#!/usr/bin/env python3
"""
scripts/manage_runs.py
Utility to manage, clean, filter, and prune benchmark runs in data/runs.json,
with optional synchronization to the dedicated 'telemetry' git branch.
"""

import argparse
import json
import os
import subprocess
import sys

DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "runs.json",
)


def load_runs(data_path: str = DEFAULT_DATA_PATH) -> dict:
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.", file=sys.stderr)
        sys.exit(1)
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_runs(data: dict, data_path: str = DEFAULT_DATA_PATH):
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Saved updated database to {data_path}")


def list_runs(data: dict):
    runs = data.get("runs", [])
    print(f"Station ID: {data.get('station_id')}")
    print(f"Total Runs: {len(runs)}\n")
    if not runs:
        print("  (No runs recorded)")
        return

    print(f"{'Idx':<4} {'Round ID':<22} {'Status':<12} {'Hops':<6} {'Total Time (ms)':<16} {'Scheduled UTC'}")
    print("-" * 80)
    for idx, r in enumerate(runs):
        round_id = r.get("round_id", "unknown")
        status = r.get("status", "unknown")
        hops = len(r.get("stations", []))
        total_ms = r.get("summary", {}).get("total_roundtrip_ms")
        total_str = f"{total_ms:,} ms" if total_ms is not None else "In Progress"
        sched = r.get("initiator", {}).get("scheduled_time_utc") or "N/A"
        print(f"{idx:<4} {round_id:<22} {status:<12} {hops:<6} {total_str:<16} {sched}")


def delete_run(data: dict, round_id: str) -> bool:
    runs = data.get("runs", [])
    before_count = len(runs)
    data["runs"] = [r for r in runs if r.get("round_id") != round_id]
    deleted = len(data["runs"]) < before_count
    if deleted:
        print(f"Removed round '{round_id}'.")
    else:
        print(f"Round '{round_id}' not found.", file=sys.stderr)
    return deleted


def clean_test_runs(data: dict) -> int:
    runs = data.get("runs", [])
    before_count = len(runs)
    data["runs"] = [
        r for r in runs
        if not ("TEST" in r.get("round_id", "").upper())
    ]
    removed = before_count - len(data["runs"])
    print(f"Removed {removed} test run(s).")
    return removed


def get_default_telemetry_branch() -> str:
    if os.getenv("TELEMETRY_BRANCH"):
        return os.getenv("TELEMETRY_BRANCH")
    try:
        remote_url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        if "kreier/roundtrip" in remote_url:
            return "telemetry-origin"
    except Exception:
        pass
    return "telemetry"


def push_to_telemetry_branch(data_path: str = DEFAULT_DATA_PATH, branch: str = None):
    if not branch:
        branch = get_default_telemetry_branch()
    print(f"Pushing data/runs.json to '{branch}' git branch...")
    try:
        subprocess.run(["git", "config", "user.name", "Roundtrip Manager"], check=True)
        subprocess.run(["git", "config", "user.email", "roundtrip@users.noreply.github.com"], check=True)
        # Stash or copy file
        temp_file = "/tmp/runs_to_push.json"
        with open(data_path, "r", encoding="utf-8") as src, open(temp_file, "w", encoding="utf-8") as dst:
            dst.write(src.read())

        subprocess.run(["git", "checkout", branch], stderr=subprocess.DEVNULL) or \
            subprocess.run(["git", "checkout", "--orphan", branch], check=True)
        subprocess.run(["git", "rm", "-rf", "."], stderr=subprocess.DEVNULL)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        with open(temp_file, "r", encoding="utf-8") as src, open(data_path, "w", encoding="utf-8") as dst:
            dst.write(src.read())
        subprocess.run(["git", "add", data_path], check=True)
        subprocess.run(["git", "commit", "-m", "chore(telemetry): manage runs database [skip ci]"], check=True)
        subprocess.run(["git", "push", "origin", branch], check=True)
        # Return to main
        subprocess.run(["git", "checkout", "main"], check=True)
        print(f"Successfully updated and pushed '{branch}' branch.")
    except Exception as e:
        print(f"Error pushing to {branch} branch: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Manage Roundtrip benchmark runs database")
    parser.add_argument("--data-path", default=DEFAULT_DATA_PATH, help="Path to data/runs.json")
    parser.add_argument("--list", action="store_true", help="List all runs in database")
    parser.add_argument("--delete", metavar="ROUND_ID", help="Delete a specific round by ID")
    parser.add_argument("--clean-tests", action="store_true", help="Remove all test runs with 'TEST' in round ID")
    parser.add_argument("--keep-recent", type=int, metavar="N", help="Keep only the N most recent runs")
    parser.add_argument("--branch", metavar="BRANCH", help="Target git branch (default: telemetry-origin for origin, telemetry for forks)")
    parser.add_argument("--push-telemetry", action="store_true", help="Push updated database to telemetry git branch")

    args = parser.parse_args()

    data = load_runs(args.data_path)
    modified = False

    if args.list or len(sys.argv) == 1:
        list_runs(data)
        return

    if args.delete:
        if delete_run(data, args.delete):
            modified = True

    if args.clean_tests:
        if clean_test_runs(data) > 0:
            modified = True

    if args.keep_recent is not None and args.keep_recent > 0:
        before = len(data.get("runs", []))
        data["runs"] = data.get("runs", [])[-args.keep_recent:]
        print(f"Pruned older runs: kept {len(data['runs'])} of {before}.")
        modified = True

    if modified:
        save_runs(data, args.data_path)
        if args.push_telemetry:
            push_to_telemetry_branch(args.data_path, branch=args.branch)


if __name__ == "__main__":
    main()
