import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

IST = ZoneInfo("Asia/Kolkata")
BASE_URL = "https://api.railradar.in/v1/trains"
USAGE_FILE = Path(__file__).with_name("usage.json")
CLASS_CODE = os.getenv("TRAIN_CLASS_CODE", "SL")
QUOTA_CODE = os.getenv("TRAIN_QUOTA_CODE", "GN")
MONTHLY_LIMIT = int(os.getenv("RAILRADAR_MONTHLY_LIMIT") or "1000")

JOURNEYS = [
    {"label": "Thursday outbound", "train_number": "16866", "source": "KMU", "destination": "MS", "weekday": 3},
    {"label": "Friday return", "train_number": "16865", "source": "MS", "destination": "KMU", "weekday": 4},
]

def env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def upcoming_date(target_weekday, today=None):
    today = today or datetime.now(IST).date()
    days_ahead = (target_weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)

def load_usage():
    month = datetime.now(IST).strftime("%Y-%m")
    if USAGE_FILE.exists():
        try:
            data = json.loads(USAGE_FILE.read_text(encoding="utf-8"))
            if data.get("month") == month:
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"month": month, "requests": 0}

def save_usage(usage):
    USAGE_FILE.write_text(json.dumps(usage, indent=2) + "\n", encoding="utf-8")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{env('TELEGRAM_BOT_TOKEN')}/sendMessage"
    response = requests.post(url, json={"chat_id": env("TELEGRAM_CHAT_ID"), "text": message}, timeout=20)
    response.raise_for_status()
    if not response.json().get("ok"):
        raise RuntimeError("Telegram rejected the message.")


def fetch_availability(journey, journey_date, api_key):
    params = {
        "source": journey["source"],
        "destination": journey["destination"],
        "journeyDate": journey_date.isoformat(),
        "classCode": CLASS_CODE,
        "quotaCode": QUOTA_CODE,
    }

    response = requests.get(
        f"{BASE_URL}/{journey['train_number']}/seats",
        params=params,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()

    if payload.get("success") is not True:
        raise RuntimeError(f"RailRadar API request failed: {payload}")

    data = payload.get("data") or {}

    # The actual API response uses "calendar".
    calendar = data.get("calendar") or []

    # Find the entry matching our requested journey date.
    matching_day = next(
        (
            day for day in calendar
            if day.get("date") == journey_date.isoformat()
        ),
        None,
    )

    if matching_day:
        status = matching_day.get("status", "Status not provided")
    else:
        status = "No status returned for requested date"

    train_name = data.get("trainName", "Uzhavan Express")

    return train_name, status


def main():
    api_key = env("RAILRADAR_API_KEY")
    usage = load_usage()
    results, calls = [], 0

    for journey in JOURNEYS:
        date = upcoming_date(journey["weekday"])
        try:
            train_name, status = fetch_availability(journey, date, api_key)
            calls += 1
            results.append(
                f"{journey['label']} — {date.strftime('%a, %d %b %Y')}\n"
                f"{journey['source']} → {journey['destination']} | Train {journey['train_number']} ({train_name})\n"
                f"Class: {CLASS_CODE} | Quota: {QUOTA_CODE}\nAvailability: {status}"
            )
        except requests.HTTPError as exc:
            calls += 1
            detail = exc.response.text[:300] if exc.response is not None else str(exc)
            results.append(f"{journey['label']} — {date.isoformat()}\nTrain {journey['train_number']}: HTTP error: {detail}")
        except Exception as exc:
            results.append(f"{journey['label']} — {date.isoformat()}\nTrain {journey['train_number']}: Error: {exc}")

    usage["requests"] = int(usage.get("requests", 0)) + calls
    save_usage(usage)
    remaining = max(MONTHLY_LIMIT - usage["requests"], 0)
    message = (
        "🚆 Uzhavan Express weekly availability\n\n" + "\n\n".join(results)
        + f"\n\nRailRadar usage estimate for {usage['month']}: "
          f"{usage['requests']}/{MONTHLY_LIMIT} requests used; approximately {remaining} remaining."
        + "\nThis is the bot's local estimate, not the provider's live quota balance."
    )
    send_telegram(message)
    print(message)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Bot failed: {exc}", file=sys.stderr)
        raise
