# roundtrip

> A distributed, multi-account GitHub Actions benchmark and visualizer tracking execution time, scheduling jitter, and workflow propagation across a ring of repositories.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

---

## Overview

**Roundtrip** explores the performance, reliability, and propagation latency of GitHub Actions across independent user accounts and repositories arranged in a ring topology:

1. **Monthly Initiation**: An elected Initiator station kicks off the roundtrip once per calendar month at **03:14 AM UTC** on a randomly selected day ($1 \le D \le 30$).
2. **Scheduler Jitter Measurement**: The initiator precisely measures runner queue latency and scheduler jitter against the theoretical 03:14 UTC mark.
3. **Sequential Relay**: Each station records local execution telemetry, builds and deploys an interactive Vite + React visualization to GitHub Pages, and triggers the next station in the sequence via a **GitHub App**.
4. **Prior Cycle Reconstruction**: Before triggering the next hop, each station audits and reconstructs the previous month's round by querying downstream and upstream endpoints back to Station 0.
5. **Dynamic Rescheduling**: When the signal returns to Station 0, the cycle is sealed, and a new random day is chosen and committed for the following month.

---

## Documentation

- **[AGENTS.md](AGENTS.md)** — Core guidelines, invariants, and operational instructions for AI coding agents and human contributors.
- **[System Architecture](docs/ARCHITECTURE.md)** — Ring topology, state machine lifecycle, failure recovery, and GitHub App security model.
- **[Station Configuration & Fork Sync Safety](docs/STATION_CONFIG.md)** — How forks maintain custom station routing without merge conflicts when syncing with upstream `main`.
- **[Dispatch Protocol](docs/PROTOCOL.md)** — `repository_dispatch` webhook payload schemas, token exchange, and validation rules.
- **[Database Schema & Reconstruction](docs/DATABASE_SCHEMA.md)** — Telemetry data schema in `data/runs.json` and the loop reconstruction algorithm.
- **[Cron Scheduler](docs/CRON_SCHEDULER.md)** — Details on the 3:14 AM UTC cron timing, jitter calculation, and dynamic day election.
- **[Frontend Dashboard & Gantt Chart](docs/FRONTEND_GANTT.md)** — Specification for the Vite + React interactive Gantt visualization deployed to GitHub Pages.

---

## Quick Reference

### Station Roles
- **Initiator (`kreier/roundtrip`)**: Manages the monthly schedule, measures initial cron jitter, initiates the cycle, and schedules the subsequent month.
- **Relay Stations (Forks)**: Run workflows on `repository_dispatch`, reconstruct the prior round, deploy Pages, and dispatch the next station.

### Authentication
Inter-station triggering uses a shared **GitHub App** installed on each station's repository, generating short-lived installation access tokens without personal access tokens (PATs).
