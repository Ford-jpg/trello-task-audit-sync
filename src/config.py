import os

# Auto-load .env if present locally without third-party dependencies
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

TRELLO_API_KEY = os.getenv("TRELLO_API_KEY", "")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN", "")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

GOOGLE_SHEET_ID = os.getenv(
    "GOOGLE_SHEET_ID", "16D9s8hfG4l01JXsOoF84k-Vkas11zcfGNYCaz55gr2Y"
)
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_FILE",
    os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        os.path.join(os.path.dirname(__file__), "..", "service_account.json"),
    ),
)

DEVELOPER_NAME = "Johnford Leoniel S. Balignot"
REPOSITORIES = [
    {"owner": "Ford-jpg", "repo": "timegate_app"},
    {"owner": "Ford-jpg", "repo": "envoyr"}
]

CATEGORY_COLORS = {
    "Database Design": "purple",
    "System Module": "blue",
    "System Security": "red",
    "Bug Fix": "green",
    "timegate_app": "black",
    "envoyr": "orange"
}

AUTH_PARAMS = f"key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"

