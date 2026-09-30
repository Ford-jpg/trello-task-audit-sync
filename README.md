# 📋 Trello & Google Sheets Task Audit Sync

Automated weekly synchronization of GitHub repository activities from **`timegate_app`** and **`envoyr`** to **Trello** and the **MPOR Google Sheet**, organized by the 4 Monthly Performance Output Report (MPOR) audit metrics:

1. 🟣 **System Database design created** (`Row 12`)
2. 🔵 **System Modules developed** (`Row 13`)
3. 🔴 **System Security** (`Row 14`)
4. 🟢 **Bug Fixes Performed** (`Row 15`)

---

## 🚀 Features

- **Dynamic Week Calculation**: Automatically detects the current week of the month (`Week 1`–`Week 4`), formats the Trello list as `Johnford <Month> <StartDay>-<EndDay> <Year> (Week X)`, and maps to the MPOR sheet's monthly tab (`SEPTEMBER`, `OCTOBER`, etc.) and weekly Efficiency column (`E`, `F`, `G`, `H`).
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
│       └── weekly-sync.yml       # Scheduled GitHub Action workflow
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
4. Name it (e.g., `mpor-sheet-sync`), click **Create and Continue**, then open the created Service Account -> **Keys** tab -> **Add Key -> Create new key -> JSON**.
5. Save the downloaded JSON file as `service_account.json` in the project root (already ignored by `.gitignore`).
6. Copy the `client_email` from inside `service_account.json` (e.g., `mpor-sheet-sync@your-project.iam.gserviceaccount.com`), open your **MPOR Google Sheet**, click **Share**, and grant **Editor** access to that email address.

### 2. Environment Variables

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

GOOGLE_SHEET_ID="16D9s8hfG4l01JXsOoF84k-Vkas11zcfGNYCaz55gr2Y"
GOOGLE_SERVICE_ACCOUNT_FILE="service_account.json"
```

---

## 🏃 Usage

### Local Run (Trello + Google Sheets)

```bash
python3 src/sync_weekly.py
```

### Target a Specific Week or Sync Only Google Sheets

```bash
# Update only Google Sheets for Week 3 of September 2026
python3 src/sync_weekly.py --week 3 --month 9 --year 2026 --sheets-only

# Update only Google Sheets for Week 4 of September 2026
python3 src/sync_weekly.py --week 4 --month 9 --year 2026 --sheets-only
```

### GitHub Actions (Automated Cron)

Add the following Repository Secrets to your GitHub repo (**Settings -> Secrets and variables -> Actions**):

- `TRELLO_API_KEY`
- `TRELLO_TOKEN`
- `TRELLO_BOARD_ID`
- `GH_PAT_OR_TOKEN`
- `GOOGLE_SHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON` *(paste the entire contents of `service_account.json`)*

The workflow in `.github/workflows/weekly-sync.yml` will run automatically on the **1st and 16th of every month at 2:30 AM PHT** (`18:30 UTC` on the previous UTC day).
