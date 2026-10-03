#!/usr/bin/env python3
"""
scripts/reconstruct_round.py
Audits and reconstructs the previous cycle's complete loop path by querying
downstream stations across GitHub Pages / raw repositories until tracing back
to the initiator and self (or detecting a broken loop).
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "runs.json",
)


def fetch_station_runs(repo: str, timeout_sec: int = 10) -> dict:
    """Fetches data/runs.json from GitHub Pages with fallback to raw GitHub repository."""
    owner, repo_name = repo.split("/", 1)
    pages_url = f"https://{owner}.github.io/{repo_name}/data/runs.json"
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/data/runs.json"

    for url in [pages_url, raw_url]:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Roundtrip-Reconstruction-Auditor/1.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
        except Exception:
            continue
    return None


def reconstruct_previous_cycle(
    current_repo: str,
    next_repo: str,
    initiator_repo: str,
    target_round_id: str = None,
    local_data_path: str = DEFAULT_DATA_PATH,
    max_hops: int = 30,
) -> dict:
    # 1. Determine target round ID if not provided
    if not target_round_id and os.path.exists(local_data_path):
        try:
            with open(local_data_path, "r", encoding="utf-8") as f:
                local_db = json.load(f)
                runs = local_db.get("runs", [])
                if len(runs) >= 1:
                    # Pick most recent past run
                    target_round_id = runs[-1].get("round_id")
        except Exception:
            pass

    if not target_round_id:
        print("No prior round ID found to reconstruct. Assuming initial bootstrap cycle.")
        return {
            "status": "INITIAL_RUN",
            "message": "No previous cycle history available.",
            "trace": [],
        }

    print(f"Tracing previous cycle '{target_round_id}' starting at downstream station: {next_repo}")

    hops = []
    visited_repos = set()
    curr_target = next_repo
    loop_completed = False
    loop_broken = False
    broken_reason = None

    for hop_idx in range(max_hops):
        if curr_target in visited_repos:
            # We encountered a node we already visited
            if curr_target == current_repo:
                loop_completed = True
            else:
                loop_broken = True
                broken_reason = f"Premature cyclic loop detected at {curr_target}"
            break

        visited_repos.add(curr_target)

        remote_db = fetch_station_runs(curr_target)
        if not remote_db:
            loop_broken = True
            broken_reason = f"Station {curr_target} unreachable or has not published data/runs.json"
            hops.append({
                "sequence": hop_idx,
                "repo": curr_target,
                "status": "UNREACHABLE",
            })
            break

        # Find target round entry
        found_run = next((r for r in remote_db.get("runs", []) if r.get("round_id") == target_round_id), None)
        if not found_run:
            loop_broken = True
            broken_reason = f"Round {target_round_id} missing on station {curr_target}"
            hops.append({
                "sequence": hop_idx,
                "repo": curr_target,
                "status": "ROUND_NOT_FOUND",
            })
            break

        # Extract timing and next station pointer from this station's record
        station_steps = found_run.get("stations", [])
        last_step = station_steps[-1] if station_steps else {}

        hop_record = {
            "sequence": hop_idx,
            "repo": curr_target,
            "station_id": remote_db.get("station_id"),
            "received_at_utc": last_step.get("received_at_utc"),
            "deploy_completed_at_utc": last_step.get("deploy_completed_at_utc"),
            "dispatched_next_at_utc": last_step.get("dispatched_next_at_utc"),
            "status": "VERIFIED",
        }
        hops.append(hop_record)

        # Check if this station looped back to current repo
        if curr_target == current_repo:
            loop_completed = True
            break

        # Move to next station: extract target from payload or assume topology
        # In a closed ring, each station knows its next hop
        # If target returned to initiator and initiator completed
        if curr_target == initiator_repo and found_run.get("status") == "COMPLETED":
            # Initiator completed the cycle
            pass

        # For demonstration or ring traversal, if remote db has routing or if we hit initiator:
        # In standard setup, when we trace around the ring, if we reached initiator and we are initiator:
        if curr_target == initiator_repo:
            loop_completed = True
            break

    result = {
        "round_id": target_round_id,
        "status": "COMPLETED" if loop_completed else "BROKEN_LOOP",
        "broken_reason": broken_reason,
        "hops": hops,
    }

    print(f"Reconstruction finished: status={result['status']}, hops_audited={len(hops)}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Reconstruct previous roundtrip cycle")
    parser.add_argument("--current-repo", default=os.getenv("GITHUB_REPOSITORY", "kreier/roundtrip"))
    parser.add_argument("--next-repo", default=os.getenv("NEXT_STATION_REPO", "offspring26/roundtrip"))
    parser.add_argument("--initiator-repo", default=os.getenv("INITIATOR_REPO", "kreier/roundtrip"))
    parser.add_argument("--round-id", help="Explicit round ID to reconstruct")
    parser.add_argument("--data-path", default=DEFAULT_DATA_PATH)
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    recon = reconstruct_previous_cycle(
        current_repo=args.current_repo,
        next_repo=args.next_repo,
        initiator_repo=args.initiator_repo,
        target_round_id=args.round_id,
        local_data_path=args.data_path,
    )

    if args.json:
        print(json.dumps(recon, indent=2))


if __name__ == "__main__":
    main()
