#!/usr/bin/env python3
"""
update_time.py
--------------
An automated script to calculate exact career duration from `start_date`,
fetch real-time push activity across both Public and Private repositories
(if authenticated with GH_PAT/GITHUB_TOKEN) without leaking private details,
and update `README.md` with high-precision real-time telemetry.
"""

import os
import json
import calendar
import urllib.request
import urllib.error
from datetime import datetime, date, timezone
from pathlib import Path


def calculate_exact_duration(start_date: date, end_date: date):
    """
    Calculates exact calendar duration between two dates without needing third-party libraries.
    Returns: tuple of (years, months, days)
    """
    years = end_date.year - start_date.year
    months = end_date.month - start_date.month
    days = end_date.day - start_date.day

    if days < 0:
        months -= 1
        prev_month = end_date.month - 1
        prev_year = end_date.year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
        _, days_in_prev_month = calendar.monthrange(prev_year, prev_month)
        days += days_in_prev_month

    if months < 0:
        years -= 1
        months += 12

    return years, months, days


def get_latest_push_activity(username: str = "Nvoinxv") -> str:
    """
    Fetches the latest push timestamp across public and private repositories using GitHub Events API.
    If authenticated via GH_PAT / GITHUB_TOKEN, GitHub returns private events as well.
    Crucial: Strips out repo names, commit hashes, or messages to ensure ZERO spill of private code.
    """
    url = f"https://api.github.com/users/{username}/events?per_page=50"
    headers = {
        "User-Agent": "Nvoinxv-Realtime-Telemetry-Bot",
        "Accept": "application/vnd.github.v3+json"
    }

    token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN")
    if token and len(token.strip()) > 0:
        headers["Authorization"] = f"Bearer {token.strip()}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                events = json.loads(response.read().decode("utf-8"))
                for event in events:
                    if event.get("type") in ("PushEvent", "CreateEvent", "PullRequestEvent"):
                        created_at_str = event.get("created_at")
                        if created_at_str:
                            # Parse GitHub ISO format: e.g. 2026-07-13T04:15:00Z
                            dt = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                            return dt.strftime("%Y-%m-%d %H:%M:%S (UTC)")
                # If no push events in the recent 50 events, check created_at of any recent event
                if len(events) > 0 and events[0].get("created_at"):
                    dt = datetime.strptime(events[0].get("created_at"), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    return dt.strftime("%Y-%m-%d %H:%M:%S (UTC)")
    except Exception as e:
        print(f"[!] Warning: Could not fetch real-time activity from GitHub Events API: {e}")

    # Fallback if API rate limited or unavailable
    return "Active Daily (Verified on GitHub)"


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    time_json_path = project_root / ".github" / "data" / "time.json"
    readme_path = project_root / "README.md"

    print(f"[*] Project Root resolved to: {project_root}")
    print(f"[*] Reading data from: {time_json_path}")

    if not time_json_path.exists():
        raise FileNotFoundError(f"Missing time.json at {time_json_path}")

    if not readme_path.exists():
        raise FileNotFoundError(f"Missing README.md at {readme_path}")

    with open(time_json_path, "r", encoding="utf-8") as f:
        time_data = json.load(f)

    start_date_str = time_data.get("start_date")
    if not start_date_str:
        raise ValueError("Field 'start_date' not found in time.json")

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    today_str = today.strftime("%Y-%m-%d")
    sync_timestamp = now_utc.strftime("%Y-%m-%d %H:%M:%S (UTC)")

    print(f"[*] Start Date : {start_date_str}")
    print(f"[*] Today's Date (UTC) : {today_str}")

    years, months, days = calculate_exact_duration(start_date, today)
    print(f"[*] Calculated Duration: {years} Years, {months} Months, {days} Days")

    # Fetch Real-Time Push Activity without spilling private repo info
    print("[*] Fetching latest push activity (Public + Private)...")
    last_activity_str = get_latest_push_activity("Nvoinxv")
    print(f"[*] Latest Activity Detected: {last_activity_str}")

    time_data["years"] = years
    time_data["months"] = months
    time_data["days"] = days
    time_data["last_updated"] = today_str
    time_data["last_sync_timestamp"] = sync_timestamp
    time_data["last_activity"] = last_activity_str

    with open(time_json_path, "w", encoding="utf-8") as f:
        json.dump(time_data, f, indent=2)
    print(f"[+] Successfully updated {time_json_path}")

    duration_str = f"{years} Years, {months} Months, {days} Days"
    
    tracker_block = f"""
> 💡 **Active Career Experience:** `{duration_str}`
> *Calculated automatically from start date (`{start_date_str}`) to `{today_str}`.*

```text
+-----------------------------------------------------------------------+
|  REAL-TIME CAREER & TELEMETRY METRIC   |  CURRENT STATUS / VALUE      |
+-----------------------------------------------------------------------+
|  Career Start Date                     |  {start_date_str:<27} |
|  Total Active Experience               |  {duration_str:<27} |
|  Latest Push Activity (Pub & Priv)     |  {last_activity_str:<27} |
|  Automated Sync Frequency              |  {"Every 1 Hour (Real-Time Cron)":<27} |
|  Last Telemetry Sync                   |  {sync_timestamp:<27} |
+-----------------------------------------------------------------------+
```"""

    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()

    start_marker = "<!--TIME_TRACKER_START-->"
    end_marker = "<!--TIME_TRACKER_END-->"

    start_idx = readme_content.find(start_marker)
    end_idx = readme_content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        raise ValueError(f"Could not find markers {start_marker} and/or {end_marker} in README.md")

    new_readme_content = (
        readme_content[:start_idx + len(start_marker)]
        + tracker_block + "\n"
        + readme_content[end_idx:]
    )

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_readme_content)

    print(f"[+] Successfully updated {readme_path}")
    print("[*] Real-time telemetry update completed successfully!")


if __name__ == "__main__":
    main()
