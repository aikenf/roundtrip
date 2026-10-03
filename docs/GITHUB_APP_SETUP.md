# GitHub App Setup & Installation Guide

This guide walks you through registering the **Roundtrip Relay GitHub App**, configuring permissions, downloading credentials, and installing the app across all participating relay stations.

---

## 1. Creating the GitHub App (Coordinator Only)

Only **one** user (the ring coordinator, e.g. `kreier`) needs to create the GitHub App:

1. Navigate to GitHub: **[GitHub Settings > Developer settings > GitHub Apps > New GitHub App](https://github.com/settings/apps/new)**.
2. Fill in the basic application details:
   - **GitHub App name**: `roundtrip-relay` (or a unique variant if taken, e.g. `roundtrip-relay-bench`).
   - **Homepage URL**: `https://github.com/kreier/roundtrip`.
3. Configure the Webhook:
   - **Active**: **Uncheck** this box (webhooks are not needed; the runner calls the GitHub REST API directly).
4. Configure **Repository permissions**:
   - **Contents**: `Read and write` (to update workflow crons and read public files).
   - **Actions**: `Read and write` (to trigger `repository_dispatch` and `workflow_dispatch`).
   - **Metadata**: `Read-only` (selected automatically).
5. Set installation visibility:
   - Under **Where can this GitHub App be installed?**, select **Any account** (Public).
6. Click **Create GitHub App**.

---

## 2. Generating the Private Key & Recording the App ID

Once the App is created:
1. Under **General > About**, note the numeric **App ID** (e.g., `1234567`).
2. Scroll down to **Private keys** and click **Generate a private key**.
3. A `.pem` file will automatically download to your computer (e.g., `roundtrip-relay.2026-10-03.private-key.pem`).
4. Keep this file secure; it provides authentication for the relay dispatch pipeline.

---

## 3. Installing the App on Participating Repositories

For each station in the ring:
1. Open the public installation URL:
   ```
   https://github.com/apps/<your-app-slug>/installations/new
   ```
2. Select the GitHub account that owns the fork (e.g. `kreier`, `offspring26`, etc.).
3. Choose **Only select repositories**, select the `roundtrip` repository, and click **Install**.

> [!NOTE]
> Installing the app grants permission for the App itself to dispatch events in that repository. The repository owner does not need to configure any individual user permissions.

---

## 4. Configuring Secrets & Variables on Each Station

Every participating repository (including forks) must configure the following in `Settings > Secrets and variables > Actions`:

### Repository Secrets
| Secret Name | Value |
|---|---|
| `ROUNDTRIP_APP_ID` | The numeric App ID from Step 2. |
| `ROUNDTRIP_APP_PRIVATE_KEY` | The entire content of the `.pem` private key file, including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`. |

### Repository Variables
| Variable Name | Example Value | Description |
|---|---|---|
| `STATION_ID` | `kreier-station-0` | Unique name for this station. |
| `IS_INITIATOR` | `true` (Station 0) or `false` | Whether this station initiates the monthly cron loop. |
| `NEXT_STATION_REPO` | `offspring26/roundtrip` | The downstream target repository in `owner/repo` format. |
| `EXPECTED_PREVIOUS_STATION` | `kreier-station-0` | Upstream station ID (for relay validation). |
| `TOTAL_RING_STATIONS` | `3` | Total number of stations in the ring (used for loop closure detection). |

---

## 5. Verifying the Installation

To verify that the App can generate an installation token and authenticate:
```bash
python3 scripts/trigger_next.py --dry-run
```
When configured properly, the script outputs the validated installation ID and confirmed permissions for `NEXT_STATION_REPO`.
