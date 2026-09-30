import base64
import json
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from config import (
    GOOGLE_SERVICE_ACCOUNT_FILE,
    GOOGLE_SERVICE_ACCOUNT_JSON,
    GOOGLE_SHEET_ID,
)

# Default MPOR Row Numbers (Columns A:D in each monthly tab)
DEFAULT_CATEGORY_ROWS = {
    "Database Design": 12,  # System Database design created
    "System Module": 13,    # System Modules developed
    "System Security": 14,  # System Security
    "Bug Fix": 15,          # Bug Fixes Performed
}

CATEGORY_ROW_LABELS = {
    "Database Design": "database design",
    "System Module": "modules developed",
    "System Security": "system security",
    "Bug Fix": "bug fixes",
}

# EFFICIENCY -> WEEK 1..4 columns in the MPOR sheet
WEEK_COLUMNS = {
    1: "E",
    2: "F",
    3: "G",
    4: "H",
}


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def load_service_account_info():
    """
    Loads Google Service Account JSON credentials from:
    1. GOOGLE_SERVICE_ACCOUNT_JSON (raw JSON string, base64 JSON, or file path)
    2. GOOGLE_SERVICE_ACCOUNT_FILE (path to JSON key file, e.g. service_account.json)
    """
    raw = (GOOGLE_SERVICE_ACCOUNT_JSON or "").strip()
    if raw:
        if os.path.isfile(raw):
            with open(raw, "r", encoding="utf-8") as f:
                return json.load(f)
        if raw.startswith("{"):
            return json.loads(raw)
        try:
            decoded = base64.b64decode(raw).decode("utf-8")
            if decoded.strip().startswith("{"):
                return json.loads(decoded)
        except Exception:
            pass

    if GOOGLE_SERVICE_ACCOUNT_FILE and os.path.isfile(GOOGLE_SERVICE_ACCOUNT_FILE):
        with open(GOOGLE_SERVICE_ACCOUNT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return None


def _sign_rs256_openssl(signing_input: bytes, private_key_pem: str) -> bytes:
    """Signs JWT payload with RS256 using system openssl/libressl CLI (zero pip dependencies)."""
    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as key_file:
        key_file.write(private_key_pem)
        key_path = key_file.name

    try:
        proc = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", key_path],
            input=signing_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return proc.stdout
    finally:
        if os.path.exists(key_path):
            os.remove(key_path)


def get_access_token(sa_info: dict) -> str:
    """Exchanges a Service Account JWT assertion for a Google OAuth2 access token."""
    scope = "https://www.googleapis.com/auth/spreadsheets"

    # Try google-auth first if installed
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(
            sa_info, scopes=[scope]
        )
        creds.refresh(Request())
        return creds.token
    except ImportError:
        pass

    # Fallback: zero-dependency OAuth2 JWT assertion via openssl + urllib
    now = int(time.time())
    token_uri = sa_info.get("token_uri", "https://oauth2.googleapis.com/token")

    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": sa_info["client_email"],
        "scope": scope,
        "aud": token_uri,
        "iat": now,
        "exp": now + 3600,
    }

    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")

    signature = _sign_rs256_openssl(signing_input, sa_info["private_key"])
    jwt_assertion = f"{encoded_header}.{encoded_payload}.{_b64url_encode(signature)}"

    body = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt_assertion,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        token_uri,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        token_data = json.loads(resp.read().decode("utf-8"))
        return token_data["access_token"]


def _resolve_sheet_tab(sheet_id: str, target_month_name: str, access_token: str) -> str:
    """Matches the target month name (e.g. 'SEPTEMBER') against existing tabs in the spreadsheet."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}?fields=sheets.properties.title"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {access_token}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
            titles = [
                s.get("properties", {}).get("title", "")
                for s in meta.get("sheets", [])
            ]
            for title in titles:
                if title.strip().lower() == target_month_name.lower():
                    return title
    except Exception:
        pass
    return target_month_name.upper()


def _resolve_category_rows(sheet_id: str, tab_name: str, access_token: str) -> dict:
    """
    Reads rows A1:D25 of the monthly tab to dynamically confirm the row numbers
    for the 4 MPOR audit metrics, falling back to DEFAULT_CATEGORY_ROWS (12..15).
    """
    rows_map = dict(DEFAULT_CATEGORY_ROWS)
    encoded_range = urllib.parse.quote(f"'{tab_name}'!A1:D25")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{encoded_range}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {access_token}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            values = data.get("values", [])
            for row_idx, row_cells in enumerate(values, start=1):
                joined_text = " ".join(str(c) for c in row_cells).lower()
                for cat, needle in CATEGORY_ROW_LABELS.items():
                    if needle in joined_text:
                        rows_map[cat] = row_idx
    except Exception:
        pass
    return rows_map


def compute_mpor_counts(activities: list) -> dict:
    """Tallies commit activities into the 4 MPOR audit categories."""
    counts = {
        "Database Design": 0,
        "System Module": 0,
        "System Security": 0,
        "Bug Fix": 0,
    }
    for item in activities:
        cat = item.get("category")
        if cat in counts:
            counts[cat] += 1
    return counts


def sync_to_google_sheet(activities: list, target_date, week_num: int) -> bool:
    """
    Updates the MPOR Google Sheet for the given month tab and week column (E, F, G, or H).
    Returns True if the sheet was updated, False if skipped or failed.
    """
    counts = compute_mpor_counts(activities)
    month_tab_default = target_date.strftime("%B").upper()
    col_letter = WEEK_COLUMNS.get(week_num, "E")

    print(f"\n[*] MPOR Summary Counts for {month_tab_default} (Week {week_num} -> Column {col_letter}):")
    for cat, row_num in DEFAULT_CATEGORY_ROWS.items():
        print(f"    - {cat:<17}: {counts[cat]:>3}  (target cell: {month_tab_default}!{col_letter}{row_num})")

    if not GOOGLE_SHEET_ID:
        print("[!] GOOGLE_SHEET_ID is not set. Skipping Google Sheets update.")
        return False

    sa_info = load_service_account_info()
    if not sa_info:
        print(
            "[!] No Google Service Account credentials found "
            "(set GOOGLE_SERVICE_ACCOUNT_JSON or place service_account.json in the project root). "
            "Skipping Google Sheets update."
        )
        return False

    try:
        access_token = get_access_token(sa_info)
        tab_name = _resolve_sheet_tab(GOOGLE_SHEET_ID, month_tab_default, access_token)
        category_rows = _resolve_category_rows(GOOGLE_SHEET_ID, tab_name, access_token)

        batch_data = []
        for cat, count in counts.items():
            row_num = category_rows[cat]
            cell_range = f"'{tab_name}'!{col_letter}{row_num}"
            batch_data.append(
                {
                    "range": cell_range,
                    "values": [[count]],
                }
            )

        update_url = f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEET_ID}/values:batchUpdate"
        payload = json.dumps(
            {
                "valueInputOption": "USER_ENTERED",
                "data": batch_data,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            update_url,
            data=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            updated_cells = result.get("totalUpdatedCells", len(batch_data))
            print(
                f"[✓] Google Sheet updated! Wrote {updated_cells} cells to "
                f"'{tab_name}' (Column {col_letter}, Rows {min(category_rows.values())}-{max(category_rows.values())})."
            )
            return True

    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"[-] Google Sheets API error ({e.code}): {err_body}")
        if e.code == 403:
            client_email = sa_info.get("client_email", "your service account email")
            print(
                f"    [Tip] Make sure the Google Sheet is shared (Editor access) with: {client_email}"
            )
        return False
    except Exception as e:
        print(f"[-] Failed to update Google Sheet: {e}")
        return False
