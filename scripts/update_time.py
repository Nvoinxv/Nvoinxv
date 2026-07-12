#!/usr/bin/env python3
"""
update_time.py
--------------
An automated script to calculate exact duration (Years, Months, Days) from `start_date`
stored in `.github/data/time.json` to today's date (in UTC), update the JSON file with the
calculated duration and last_updated timestamp, and replace the content between
`<!--TIME_TRACKER_START-->` and `<!--TIME_TRACKER_END-->` markers in `README.md`.
"""

import json
import calendar
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
        # Calculate days in the previous month relative to end_date
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


def main():
    # Resolve project root directory dynamically based on script location
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

    # 1. Read start_date from time.json
    with open(time_json_path, "r", encoding="utf-8") as f:
        time_data = json.load(f)

    start_date_str = time_data.get("start_date")
    if not start_date_str:
        raise ValueError("Field 'start_date' not found in time.json")

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    today = datetime.now(timezone.utc).date()
    today_str = today.strftime("%Y-%m-%d")

    print(f"[*] Start Date : {start_date_str}")
    print(f"[*] Today's Date (UTC) : {today_str}")

    # 2. Calculate exact calendar difference
    years, months, days = calculate_exact_duration(start_date, today)
    print(f"[*] Calculated Duration: {years} Years, {months} Months, {days} Days")

    # 3. Update time.json with new values
    time_data["years"] = years
    time_data["months"] = months
    time_data["days"] = days
    time_data["last_updated"] = today_str

    with open(time_json_path, "w", encoding="utf-8") as f:
        json.dump(time_data, f, indent=2)
    print(f"[+] Successfully updated {time_json_path}")

    # 4. Generate markdown block for README.md
    duration_str = f"{years} Years, {months} Months, {days} Days"
    
    tracker_block = f"""
> 💡 **Active Career Experience:** `{duration_str}`
> *Calculated automatically from start date (`{start_date_str}`) to `{today_str}`.*

```text
+-----------------------------------------------------------------------+
|  EXPERIENCE METRIC          |  VALUE                                  |
+-----------------------------------------------------------------------+
|  Career Start Date          |  {start_date_str:<38} |
|  Total Active Experience    |  {duration_str:<38} |
|  Last Automated Sync        |  {today_str + " (UTC)":<38} |
+-----------------------------------------------------------------------+
```"""

    # 5. Read and update README.md between markers
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
    print("[*] Update completed successfully!")


if __name__ == "__main__":
    main()
