# main.py
import sys
import os

# Get the absolute path to the root project directory (where main.py lives)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the root directory to sys.path if not already there
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import asyncio
from datetime import datetime
from scripts.rotation import run_morning_rotation, run_evening_rotation

def get_day_time_args():
    if len(sys.argv) == 3:
        day = sys.argv[1].capitalize()  # e.g. "Monday"
        time_of_day = sys.argv[2].lower()  # "morning" or "evening"
        return day, time_of_day
    else:
        # Fallback to current system time
        now = datetime.now()
        day = now.strftime("%A")
        hour = now.hour
        time_of_day = "morning" if hour < 12 else "evening"
        return day, time_of_day

if __name__ == "__main__":
    day, time_of_day = get_day_time_args()
    print(f"🕐 Running {time_of_day.upper()} rotation for {day}")

    if time_of_day == "morning":
        asyncio.run(run_morning_rotation(current_day=day))
    else:
        asyncio.run(run_evening_rotation(current_day=day))
