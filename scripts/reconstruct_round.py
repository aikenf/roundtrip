#!/usr/bin/env python3
"""
scripts/reconstruct_round.py
Reconciles previous benchmark runs in local data/runs.json:
1. Identifies any prior runs still marked as 'IN_PROGRESS'.
2. Checks the origin (initiator) station. If the initiator recorded the run as 'COMPLETED',
   copies the sealed run data (summary, timing, complete hop trace).
3. If not completed at origin, traces downstream station(s) to gather available hop data
   and marks the run as 'INCOMPLETE'.
4. Updates local data/runs.json so past rounds accurately reflect completion status.
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


def fetch_station_runs(repo: str, timeout_sec: int = 8) -> dict:
    """Fetches data/runs.json from telemetry branch, main branch, or GitHub Pages."""
    owner, repo_name = repo.split("/", 1)
    candidate_urls = [
        f"https://raw.githubusercontent.com/{owner}/{repo_name}/telemetry/data/runs.json",
        f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/data/runs.json",
        f"https://{owner}.github.io/{repo_name}/data/runs.json",
    ]

    for url in candidate_urls:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Roundtrip-Reconstruction-Auditor/1.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if isinstance(data, dict) and "runs" in data:
                        return data
        except Exception:
            continue
    return None


def trace_downstream_hops(
    round_id: str,
    start_repo: str,
    origin_repo: str,
    current_repo: str,
    max_hops: int = 15,
) -> dict:
    """Traces downstream stations to collect hops if origin doesn't report COMPLETED."""
    curr_target = start_repo
    visited = {current_repo}
    collected_hops = []
    loop_completed = False
    completed_run_data = None

    for hop_idx in range(max_hops):
        if not curr_target or curr_target in visited:
            break
        visited.add(curr_target)

        remote_db = fetch_station_runs(curr_target)
        if not remote_db:
            print(f"[Trace] Station '{curr_target}' unreachable or has no published telemetry.")
            break

        found_run = next((r for r in remote_db.get("runs", []) if r.get("round_id") == round_id), None)
        if not found_run:
            print(f"[Trace] Round '{round_id}' not found on station '{curr_target}'.")
            break

        for step in found_run.get("stations", []):
            if not any(h.get("sequence") == step.get("sequence") and h.get("station_id") == step.get("station_id") for h in collected_hops):
                collected_hops.append(step)

        if found_run.get("status") == "COMPLETED":
            loop_completed = True
            completed_run_data = found_run
            break

        if curr_target == origin_repo:
            break

        # Follow next hop if available from trace or routing
        next_target = None
        # Check if next station repo can be deduced from found_run hops
        for step in found_run.get("stations", []):
            if step.get("repo") == curr_target and step.get("next_station_repo"):
                next_target = step.get("next_station_repo")
                break
        curr_target = next_target or origin_repo

    return {
        "completed": loop_completed,
        "completed_run_data": completed_run_data,
        "hops": collected_hops,
    }


def reconcile_prior_runs(
    current_repo: str,
    next_repo: str,
    initiator_repo: str,
    current_round_id: str = None,
    target_round_id: str = None,
    local_data_path: str = DEFAULT_DATA_PATH,
    update_local: bool = True,
) -> list:
    """Reconciles prior in-progress runs with origin station or downstream trace."""
    if not os.path.exists(local_data_path):
        print(f"Local database {local_data_path} not found.")
        return []

    with open(local_data_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    runs = db.get("runs", [])
    if not runs:
        print("No local runs found to reconcile.")
        return []

    reconciled_reports = []
    db_modified = False

    for run in runs:
        rid = run.get("round_id")
        status = run.get("status")

        # Skip current actively running round
        if current_round_id and rid == current_round_id:
            continue

        # If a specific round is targeted, skip others
        if target_round_id and rid != target_round_id:
            continue

        # Only reconcile runs that are still marked IN_PROGRESS
        if status != "IN_PROGRESS":
            continue

        origin_repo = (run.get("initiator") or {}).get("repo") or initiator_repo
        print(f"Reconciling prior run '{rid}' (origin: {origin_repo})...")

        # Step 1: Query Origin Station
        origin_db = fetch_station_runs(origin_repo)
        origin_run = None
        if origin_db:
            origin_run = next((r for r in origin_db.get("runs", []) if r.get("round_id") == rid), None)

        if origin_run and origin_run.get("status") == "COMPLETED":
            print(f"-> Origin '{origin_repo}' reports '{rid}' as COMPLETED. Adopting sealed data.")
            run["status"] = "COMPLETED"
            if origin_run.get("initiator"):
                run["initiator"] = origin_run["initiator"]
            if origin_run.get("summary"):
                run["summary"] = origin_run["summary"]

            # Merge stations: use origin's stations if more complete
            if len(origin_run.get("stations", [])) >= len(run.get("stations", [])):
                run["stations"] = origin_run["stations"]

            db_modified = True
            reconciled_reports.append({
                "round_id": rid,
                "status": "COMPLETED",
                "source": origin_repo,
                "stations_count": len(run.get("stations", [])),
            })
            continue

        # Step 2: Fallback - Origin does not report COMPLETED -> Trace Downstream
        print(f"-> Origin '{origin_repo}' does not report '{rid}' as COMPLETED. Tracing downstream '{next_repo}'...")
        trace_result = trace_downstream_hops(
            round_id=rid,
            start_repo=next_repo,
            origin_repo=origin_repo,
            current_repo=current_repo,
        )

        if trace_result["completed"] and trace_result["completed_run_data"]:
            comp_data = trace_result["completed_run_data"]
            print(f"-> Downstream trace confirmed completion for '{rid}'.")
            run["status"] = "COMPLETED"
            if comp_data.get("summary"):
                run["summary"] = comp_data["summary"]
            if comp_data.get("initiator"):
                run["initiator"] = comp_data["initiator"]
        else:
            print(f"-> Downstream trace found no completion for '{rid}'. Marking as INCOMPLETE.")
            run["status"] = "INCOMPLETE"
            if not run.get("summary") or not run["summary"].get("total_roundtrip_ms"):
                run["summary"] = {
                    "total_roundtrip_ms": None,
                    "stations_count": len(run.get("stations", [])),
                    "round_completed_at_utc": None,
                    "note": "Cycle did not reach initiator or terminated prematurely",
                }

        # Merge any newly discovered hops from trace
        existing_seqs = {s.get("sequence") for s in run.get("stations", [])}
        for hop in trace_result["hops"]:
            if hop.get("sequence") not in existing_seqs:
                run["stations"].append(hop)
                existing_seqs.add(hop.get("sequence"))

        run["stations"].sort(key=lambda s: s.get("sequence", 0))
        run["summary"]["stations_count"] = len(run["stations"])

        db_modified = True
        reconciled_reports.append({
            "round_id": rid,
            "status": run["status"],
            "source": "downstream_trace",
            "stations_count": len(run["stations"]),
        })

    if db_modified and update_local:
        with open(local_data_path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)
        print(f"Saved reconciled runs to {local_data_path}")

    return reconciled_reports


def main():
    parser = argparse.ArgumentParser(description="Reconcile and reconstruct previous roundtrip cycles")
    parser.add_argument("--current-repo", default=os.getenv("GITHUB_REPOSITORY", "kreier/roundtrip"))
    parser.add_argument("--next-repo", default=os.getenv("NEXT_STATION_REPO", "offspring26/roundtrip"))
    parser.add_argument("--initiator-repo", default=os.getenv("INITIATOR_REPO", "kreier/roundtrip"))
    parser.add_argument("--current-round-id", help="Active incoming round ID (to exclude from reconciliation)")
    parser.add_argument("--round-id", help="Explicit round ID to reconcile")
    parser.add_argument("--data-path", default=DEFAULT_DATA_PATH)
    parser.add_argument("--no-save", action="store_true", help="Do not save changes to data/runs.json")
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    results = reconcile_prior_runs(
        current_repo=args.current_repo,
        next_repo=args.next_repo,
        initiator_repo=args.initiator_repo,
        current_round_id=args.current_round_id,
        target_round_id=args.round_id,
        local_data_path=args.data_path,
        update_local=not args.no_save,
    )

    if args.json:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
