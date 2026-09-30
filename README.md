# 📋 Trello & Google Sheets Task Audit Sync

Automated bi-monthly synchronization of GitHub repository activities to **Trello** and the **MPOR Google Sheet**, organized by the 4 Monthly Performance Output Report (MPOR) audit metrics:

1. 🟣 **System Database design created** (`Row 12`)
2. 🔵 **System Modules developed** (`Row 13`)
3. 🔴 **System Security** (`Row 14`)
4. 🟢 **Bug Fixes Performed** (`Row 15`)

---

## 🚀 Features

- **Dynamic Week & Month Calculation**: Automatically detects the target week(s) of the month (`Week 1`–`Week 4`), formats the Trello list as `<Name> <Month> <StartDay>-<EndDay> <Year> (Week X)`, and maps to the MPOR sheet's monthly tab (`SEPTEMBER`, `OCTOBER`, etc.) and weekly Efficiency column (`E`, `F`, `G`, `H`).
- **Direct MPOR Google Sheet Updates**: Writes weekly category tallies directly into `{MONTH}!{E..H}12:15` via the Google Sheets API v4 (which automatically recalculates the `TOTAL`, `QUALITY`, and `TIMELINESS` formula columns).
- **Zero External Dependencies**: Uses standard library `urllib` + system `openssl` (or `google-auth` if installed) for Service Account OAuth2 JWT authentication.
- **Automatic Audit Metric Classification**: Parses commit messages and patterns into the 4 official audit categories.
- **Color-Coded Trello Labels & De-duplication**: Applies custom color tags for categories/repositories and skips existing cards.
- **Automated CI/CD**: Includes a GitHub Actions workflow scheduled to run every **1st and 16th of the month at 2:30 AM PHT** (syncing Weeks 1–2 on the 16th, and Weeks 3–4 of the completed month on the 1st).

---

## 📁 Project Structure

```
trello-task-audit-sync/
├── .github/
│   └── workflows/
│       └── weekly-sync.yml       # Scheduled GitHub Action workflow (1st & 16th at 2:30 AM PHT)
├── src/
│   ├── config.py                 # Configuration and credentials loader
│   ├── categorizer.py            # Audit metric classification logic
│   ├── sheets_sync.py            # Google Sheets API v4 MPOR updater
│   └── sync_weekly.py            # Main sync orchestrator
├── scripts/
│   └── run_sync.sh               # Quick local execution script
├── .env.example                  # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Configuration

### 1. Google Cloud Service Account Setup (One-Time)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project, then enable the **Google Sheets API** (**APIs & Services -> Library -> Google Sheets API -> Enable**).
3. Go to **APIs & Services -> Credentials -> Create Credentials -> Service account**.
4. Name it `MPOR Audit Sync` (`mpor-audit-sync`), click **Create and Continue**, then open the created Service Account -> **Keys** tab -> **Add Key -> Create new key -> JSON**.
5. Save the downloaded JSON file as `service_account.json` in the project root (already ignored by `.gitignore`).
6. Copy the `client_email` from inside `service_account.json` (e.g., `mpor-audit-sync@your-project.iam.gserviceaccount.com`), open your **MPOR Google Sheet**, click **Share**, and grant **Editor** access to that email address.

### 2. Environment Variables (Local)

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Fill in your credentials:

```env
TRELLO_API_KEY="your_trello_api_key"
TRELLO_TOKEN="your_trello_token"
TRELLO_BOARD_ID="your_trello_board_id"
GITHUB_TOKEN="your_github_personal_access_token"

GOOGLE_SHEET_ID="your_mpor_google_sheet_id"
GOOGLE_SERVICE_ACCOUNT_FILE="service_account.json"

# Optional overrides (for coworkers):
DEVELOPER_NAME="Your Full Name"
TRELLO_LIST_PREFIX="YourFirstName"
GITHUB_REPOS="owner/repo_one,owner/repo_two"
GITHUB_AUTHOR="your-github-username"
```

---

## 👥 Team / Coworker Replication Guide

Coworkers can replicate this entire automation for their own MPOR Google Sheet, Trello lists, and GitHub repositories **without editing any Python code**:

### Step 1: Fork the Repository
1. Click **Fork** at the top-right of **`Ford-jpg/trello-task-audit-sync`** to create a copy under your own GitHub account.
2. In your forked repository, go to the **Actions** tab and click **"I understand my workflows, go ahead and enable them"**.

### Step 2: Get Your MPOR Google Sheet ID & Share Access
1. Open your MPOR Google Sheet in the browser. Copy the **Sheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/<YOUR_GOOGLE_SHEET_ID>/edit
   ```
   Make sure each monthly tab is named after the month (e.g., `SEPTEMBER`, `OCTOBER`, `NOVEMBER`) and has the 4 core functions in rows `12`–`15`:
   - **Row 12**: `System Database design created`
   - **Row 13**: `System Modules developed`
   - **Row 14**: `System Security`
   - **Row 15**: `Bug Fixes Performed`
2. Click **Share** on your MPOR Google Sheet and grant **Editor** access to either:
   - **Team Shared Service Account**: Ask for the team's `mpor-audit-sync@...iam.gserviceaccount.com` email and JSON key (fastest—takes 30 seconds), **OR**
   - **Your Own Service Account**: Follow [Section 1](#-setup--configuration) above to generate your own `service_account.json`.

### Step 3: Get Your Trello & GitHub Credentials
1. **Trello API Key & Token**:
   - Visit [https://trello.com/power-ups/admin](https://trello.com/power-ups/admin), select or create a workspace integration, copy your **API Key**, and click the **Token** link to authorize and copy your token.
   - To find the **Trello Board ID**, open the Trello board in your browser and append `.json` to the URL (e.g., `https://trello.com/b/xxxxxx/board-name.json`) — the `"id"` field at the very beginning is the `TRELLO_BOARD_ID`.
2. **GitHub Personal Access Token (`GH_PAT_OR_TOKEN`)**:
   - Go to **GitHub Settings -> Developer settings -> Personal access tokens -> Tokens (classic) -> Generate new token**.
   - Check the **`repo`** scope (required if any of your repositories are private) and copy the token.

### Step 4: Add GitHub Actions Secrets
In your forked repository, go to **Settings -> Secrets and variables -> Actions -> New repository secret** and add:

| Secret Name | Required | Example / Description |
| :--- | :---: | :--- |
| `TRELLO_API_KEY` | Yes | Your Trello API key |
| `TRELLO_TOKEN` | Yes | Your Trello OAuth token |
| `TRELLO_BOARD_ID` | Yes | Target Trello Board ID (e.g., `69f8061c53db3e1fd1c752f2`) |
| `GH_PAT_OR_TOKEN` | Yes | Your GitHub Personal Access Token (`repo` read scope) |
| `GOOGLE_SHEET_ID` | Yes | Your MPOR spreadsheet ID from its URL |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes | Full JSON content of `service_account.json` |
| `DEVELOPER_NAME` | Yes (for coworkers) | Your full name on Trello cards (e.g., `Juan Dela Cruz`) |
| `TRELLO_LIST_PREFIX` | Yes (for coworkers) | First name used in Trello list titles (e.g., `Juan`) |
| `GITHUB_REPOS` | Yes (for coworkers) | Comma-separated repos to audit (e.g., `juandc/project_a,juandc/project_b`) |
| `GITHUB_AUTHOR` | Optional | Your GitHub username (`juandc`) — set this if multiple developers commit to the same shared repo so only **your** commits are counted |

### Step 5: Test It Immediately
1. Go to the **Actions** tab in your forked repo.
2. Select **Bi-Monthly Task Audit Sync (Trello & Google Sheets)** on the left.
3. Click **Run workflow -> Run workflow** to trigger a live test run.

---

## 🏃 Local CLI Usage

### Default Run (Trello + Google Sheets)

```bash
python3 src/sync_weekly.py
```

### Target a Specific Week or Sync Only Google Sheets

```bash
# Update only Google Sheets for Week 3 of September 2026
python3 src/sync_weekly.py --week 3 --month 9 --year 2026 --sheets-only

# Update only Google Sheets for Week 4 of September 2026
python3 src/sync_weekly.py --week 4 --month 9 --year 2026 --sheets-only

# Update only Trello for a specific date
python3 src/sync_weekly.py --date 2026-09-18 --trello-only
```

---

## ⏰ Automated Schedule

The workflow in [`.github/workflows/weekly-sync.yml`](.github/workflows/weekly-sync.yml) runs automatically on the **1st and 16th of every month at 2:30 AM PHT** (`18:30 UTC` on the previous UTC day):

- **16th of the Month (2:30 AM PHT)**: Syncs **Week 1** (`Days 1–7`) and **Week 2** (`Days 8–14`) of the current month.
- **1st of the Month (2:30 AM PHT)**: Syncs **Week 3** (`Days 15–21`) and **Week 4** (`Days 22–End`) of the completed previous month.
