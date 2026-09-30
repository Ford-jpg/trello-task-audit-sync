#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from config import (
    AUTH_PARAMS,
    CATEGORY_COLORS,
    DEVELOPER_NAME,
    GITHUB_AUTHOR,
    GITHUB_TOKEN,
    REPOSITORIES,
    TRELLO_API_KEY,
    TRELLO_BOARD_ID,
    TRELLO_LIST_PREFIX,
    TRELLO_TOKEN,
)
from categorizer import categorize_commit
from sheets_sync import sync_to_google_sheet


def get_week_info(target_date=None):
    if target_date is None:
        target_date = datetime.now(timezone.utc)

    year = target_date.year
    month_name = target_date.strftime("%b")
    day = target_date.day

    if day <= 7:
        week_num = 1
        start_day, end_day = 1, 7
    elif day <= 14:
        week_num = 2
        start_day, end_day = 8, 14
    elif day <= 21:
        week_num = 3
        start_day, end_day = 15, 21
    else:
        week_num = 4
        start_day = 22
        next_month = target_date.replace(day=28) + timedelta(days=4)
        last_day = (next_month - timedelta(days=next_month.day)).day
        end_day = last_day

    list_title = f"{TRELLO_LIST_PREFIX} {month_name} {start_day}-{end_day} {year} (Week {week_num})"
    since_date = datetime(year, target_date.month, start_day, 0, 0, 0, tzinfo=timezone.utc)
    until_date = datetime(year, target_date.month, end_day, 23, 59, 59, tzinfo=timezone.utc)

    return list_title, since_date, until_date, week_num, target_date


def fetch_github_commits(owner, repo, since_iso, until_iso):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?since={since_iso}&until={until_iso}&per_page=100"
    if GITHUB_AUTHOR:
        url += f"&author={urllib.parse.quote(GITHUB_AUTHOR)}"
    headers = {"User-Agent": "Trello-Task-Audit-Sync"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[-] Error fetching {owner}/{repo}: {e}")
        return []


def sync_to_trello(activities, list_title):
    if not activities:
        print("[!] No new activities found for Trello. Skipping Trello card creation.")
        return

    if not (TRELLO_API_KEY and TRELLO_TOKEN and TRELLO_BOARD_ID):
        print("[!] Missing Trello credentials. Skipping Trello sync.")
        return

    # 1. Get or create Trello list
    lists_url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists?{AUTH_PARAMS}"
    with urllib.request.urlopen(urllib.request.Request(lists_url)) as resp:
        existing_lists = json.loads(resp.read().decode("utf-8"))

    list_id = None
    for l in existing_lists:
        if l["name"].strip().lower() == list_title.lower():
            list_id = l["id"]
            print(f"[+] Found existing list: {list_title} ({list_id})")
            break

    if not list_id:
        create_list_url = f"https://api.trello.com/1/lists?name={urllib.parse.quote(list_title)}&idBoard={TRELLO_BOARD_ID}&pos=bottom&{AUTH_PARAMS}"
        req = urllib.request.Request(create_list_url, method="POST")
        with urllib.request.urlopen(req) as resp:
            created = json.loads(resp.read().decode("utf-8"))
            list_id = created["id"]
            print(f"[+] Created new list: {list_title} ({list_id})")

    # 2. Get or create labels
    labels_url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/labels?{AUTH_PARAMS}"
    with urllib.request.urlopen(urllib.request.Request(labels_url)) as resp:
        existing_labels = json.loads(resp.read().decode("utf-8"))

    label_map = {l["name"]: l["id"] for l in existing_labels if l.get("name")}
    for cat_name, color in CATEGORY_COLORS.items():
        if cat_name not in label_map:
            create_lbl = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/labels?name={urllib.parse.quote(cat_name)}&color={color}&{AUTH_PARAMS}"
            with urllib.request.urlopen(urllib.request.Request(create_lbl, method="POST")) as resp:
                created_lbl = json.loads(resp.read().decode("utf-8"))
                label_map[cat_name] = created_lbl["id"]

    # 3. Check existing cards
    cards_url = f"https://api.trello.com/1/lists/{list_id}/cards?{AUTH_PARAMS}"
    with urllib.request.urlopen(urllib.request.Request(cards_url)) as resp:
        existing_cards = json.loads(resp.read().decode("utf-8"))
    existing_card_names = {c["name"] for c in existing_cards}

    # 4. Upload cards
    uploaded = 0
    for idx, item in enumerate(activities, 1):
        if item["title"] in existing_card_names:
            print(f"  [-] Skipping existing: {item['title'][:50]}...")
            continue

        lbl_ids = []
        if item["category"] in label_map:
            lbl_ids.append(label_map[item["category"]])
        if item["repo"] in label_map:
            lbl_ids.append(label_map[item["repo"]])

        card_desc = (
            f"**Developer**: {DEVELOPER_NAME}\n"
            f"**Repository**: [{item['repo']}](https://github.com/{item['owner']}/{item['repo']})\n"
            f"**Commit**: [{item['sha']}]({item['url']})\n"
            f"**Date**: {item['date']}\n"
            f"**Audit Category**: `{item['category']}`\n\n"
            f"**Details**:\n{item['desc']}"
        )

        data = urllib.parse.urlencode({
            "idList": list_id,
            "name": item["title"],
            "desc": card_desc,
            "idLabels": ",".join(lbl_ids),
            "key": TRELLO_API_KEY,
            "token": TRELLO_TOKEN
        }).encode("utf-8")

        card_url = "https://api.trello.com/1/cards"
        try:
            req = urllib.request.Request(card_url, data=data, method="POST")
            with urllib.request.urlopen(req) as resp:
                uploaded += 1
                print(f"  [{idx:02d}/{len(activities)}] Created: {item['title'][:55]}...")
        except Exception as e:
            print(f"  [{idx:02d}/{len(activities)}] Failed: {item['title'][:55]}... | {e}")
        time.sleep(0.12)

    print(f"\n[✓] Trello sync complete! Uploaded {uploaded} new cards to '{list_title}'.")


def run(target_date=None, skip_trello=False, skip_sheets=False):
    list_title, since_date, until_date, week_num, effective_date = get_week_info(target_date)
    since_iso = since_date.isoformat()
    until_iso = until_date.isoformat()

    print(f"[*] Starting Weekly Sync for: {list_title}")
    print(f"[*] Date Range: {since_iso} to {until_iso}")

    activities = []
    for r in REPOSITORIES:
        commits = fetch_github_commits(r["owner"], r["repo"], since_iso, until_iso)
        for c in commits:
            parents = len(c.get("parents", []))
            msg = c["commit"]["message"].strip()
            if parents > 1 or msg.startswith("Merge ") or "chore(master): release" in msg:
                continue

            first_line = msg.split("\n")[0]
            category = categorize_commit(msg)
            sha = c["sha"][:7]
            commit_date = c["commit"]["author"]["date"][:10]
            html_url = c.get("html_url", f"https://github.com/{r['owner']}/{r['repo']}/commit/{sha}")

            title = f"[{category}] {first_line}"
            if len(title) > 120:
                title = title[:117] + "..."

            activities.append({
                "title": title,
                "category": category,
                "owner": r["owner"],
                "repo": r["repo"],
                "sha": sha,
                "date": commit_date,
                "url": html_url,
                "desc": msg
            })

    print(f"[+] Found {len(activities)} substantive activities.")

    if not skip_trello:
        sync_to_trello(activities, list_title)

    if not skip_sheets:
        sync_to_google_sheet(activities, effective_date, week_num)


PHT = timezone(timedelta(hours=8))


def get_target_dates_for_schedule(now_pht=None):
    """
    Determines which week(s) to sync for the 1st and 16th bi-monthly schedule:
    - On the 1st of the month: syncs Week 3 and Week 4 of the previous month.
    - On the 16th of the month: syncs Week 1 and Week 2 of the current month.
    - Any other day (manual run without flags): syncs the current week.
    """
    if now_pht is None:
        now_pht = datetime.now(PHT)

    if now_pht.day == 1:
        prev_month_last_day = now_pht.replace(day=1) - timedelta(days=1)
        y, m = prev_month_last_day.year, prev_month_last_day.month
        return [
            datetime(y, m, 15, tzinfo=timezone.utc),  # Week 3 of previous month
            datetime(y, m, 22, tzinfo=timezone.utc),  # Week 4 of previous month
        ]
    elif now_pht.day == 16:
        y, m = now_pht.year, now_pht.month
        return [
            datetime(y, m, 1, tzinfo=timezone.utc),   # Week 1 of current month
            datetime(y, m, 8, tzinfo=timezone.utc),   # Week 2 of current month
        ]
    else:
        return [now_pht.astimezone(timezone.utc)]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync GitHub commits to Trello and MPOR Google Sheet for audit")
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD format")
    parser.add_argument("--week", type=int, choices=[1, 2, 3, 4], help="Specific week of the month (1-4)")
    parser.add_argument("--month", type=int, default=None, help="Month number (1-12, defaults to current month)")
    parser.add_argument("--year", type=int, default=None, help="Year (defaults to current year)")
    parser.add_argument("--sheets-only", action="store_true", help="Only update the MPOR Google Sheet (skip Trello)")
    parser.add_argument("--trello-only", action="store_true", help="Only update Trello (skip Google Sheets)")
    args = parser.parse_args()

    if args.date:
        target_dates = [datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)]
    elif args.week:
        now = datetime.now(PHT)
        year = args.year or now.year
        month = args.month or now.month
        day_map = {1: 1, 2: 8, 3: 15, 4: 22}
        target_dates = [datetime(year, month, day_map[args.week], tzinfo=timezone.utc)]
    else:
        target_dates = get_target_dates_for_schedule()

    for dt in target_dates:
        run(
            dt,
            skip_trello=args.sheets_only,
            skip_sheets=args.trello_only,
        )


