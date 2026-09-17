# 📋 Trello Task Audit Sync

Automated weekly synchronization of GitHub repository activities from **`timegate_app`** and **`envoyr`** to **Trello**, organized by the 4 Monthly Performance Output Report (MPOR) audit metrics:

1. 🟣 **System Database design created**
2. 🔵 **System Modules developed**
3. 🔴 **System Security**
4. 🟢 **Bug Fixes Performed**

---

## 🚀 Features

- **Dynamic Week Calculation**: Automatically detects the current week of the month (`Week 1`, `Week 2`, `Week 3`, `Week 4`) and formats the Trello list as `Johnford <Month> <StartDay>-<EndDay> <Year> (Week X)`.
- **Automatic Audit Metric Classification**: Parses commit messages and patterns into the 4 official audit categories.
- **Color-Coded Trello Labels**: Applies custom color tags for both categories and repositories.
- **De-duplication**: Checks existing cards on Trello before creating new ones to prevent duplicates.
- **Automated CI/CD**: Includes a GitHub Actions workflow scheduled to run every Sunday at midnight (PHT).

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

### 1. Environment Variables

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
```

---

## 🏃 Usage

### Local Run

```bash
python3 src/sync_weekly.py
```

Or using the shell helper:

```bash
./scripts/run_sync.sh
```

### GitHub Actions (Automated Cron)

Add the following Repository Secrets to your GitHub repo (**Settings -> Secrets and variables -> Actions**):

- `TRELLO_API_KEY`
- `TRELLO_TOKEN`
- `TRELLO_BOARD_ID`
- `GH_PAT_OR_TOKEN`

The workflow in `.github/workflows/weekly-sync.yml` will run automatically every Sunday at **16:00 UTC** (12:00 AM PHT Monday).
