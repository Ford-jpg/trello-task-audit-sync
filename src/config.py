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

GOOGLE_SHEET_ID = (
    os.getenv("GOOGLE_SHEET_ID", "").strip()
    or "16D9s8hfG4l01JXsOoF84k-Vkas11zcfGNYCaz55gr2Y"
)
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_SERVICE_ACCOUNT_FILE = (
    os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
    or os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    or os.path.join(os.path.dirname(__file__), "..", "service_account.json")
)

DEVELOPER_NAME = (
    os.getenv("DEVELOPER_NAME", "").strip() or "Johnford Leoniel S. Balignot"
)
TRELLO_LIST_PREFIX = (
    os.getenv("TRELLO_LIST_PREFIX", "").strip()
    or DEVELOPER_NAME.split()[0]
)
GITHUB_AUTHOR = os.getenv("GITHUB_AUTHOR", "").strip()

_repos_env = (
    os.getenv("GITHUB_REPOS", "").strip()
    or "Ford-jpg/timegate_app,Ford-jpg/envoyr"
)
REPOSITORIES = []
for _item in _repos_env.split(","):
    _item = _item.strip()
    if "/" in _item:
        _owner, _repo = _item.split("/", 1)
        REPOSITORIES.append({"owner": _owner.strip(), "repo": _repo.strip()})

CATEGORY_COLORS = {
    "Database Design": "purple",
    "System Module": "blue",
    "System Security": "red",
    "Bug Fix": "green",
    "timegate_app": "black",
    "envoyr": "orange"
}

for _r in REPOSITORIES:
    CATEGORY_COLORS.setdefault(_r["repo"], "sky")

AUTH_PARAMS = f"key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"


