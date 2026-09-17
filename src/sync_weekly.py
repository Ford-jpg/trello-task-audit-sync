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
    GITHUB_TOKEN,
    REPOSITORIES,
    TRELLO_API_KEY,
    TRELLO_BOARD_ID,
    TRELLO_TOKEN,
)
from categorizer import categorize_commit


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

    list_title = f"Johnford {month_name} {start_day}-{end_day} {year} (Week {week_num})"
    since_date = datetime(year, target_date.month, start_day, 0, 0, 0, tzinfo=timezone.utc)
    until_date = datetime(year, target_date.month, end_day, 23, 59, 59, tzinfo=timezone.utc)

    return list_title, since_date, until_date


def fetch_github_commits(owner, repo, since_iso, until_iso):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?since={since_iso}&until={until_iso}&per_page=100"
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


def run():
    list_title, since_date, until_date = get_week_info()
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
                "repo": r["repo"],
                "sha": sha,
                "date": commit_date,
                "url": html_url,
                "desc": msg
            })

    print(f"[+] Found {len(activities)} substantive activities.")
    if not activities:
        print("[!] No new activities found for this period. Completed.")
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
            f"**Repository**: [{item['repo']}](https://github.com/Ford-jpg/{item['repo']})\n"
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

    print(f"\n[✓] Sync complete! Uploaded {uploaded} new cards to '{list_title}'.")


if __name__ == "__main__":
    run()
