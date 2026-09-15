#!/usr/bin/env python3
"""Interactive login/re-authentication for the Omarchy Garmin widget.

Usage:
    ./garmin-login

Asks for your email and password (via getpass, never shown on screen or
saved to disk) and, if your account requires it, an MFA code. On success it
saves an OAuth session token to ~/.garminconnect so that garmin-status can
read data without asking for credentials again. This is launched
automatically from the bar widget itself when it detects the session has
expired.
"""
import datetime
import getpass
import json
import os
import sys

import garminconnect

TOKEN_DIR = "~/.garminconnect"

# Garmin has rate-limited the "mobile" login endpoints (HTTP 429) since
# March 2026, so the library's default strategy chain always burns two
# guaranteed failures before falling back to the one that works. Skip
# straight to it; revisit if Garmin ever lifts the block.
SKIP_LOGIN_STRATEGIES = {"mobile+cffi", "mobile+requests"}


def prompt_mfa():
    return input("MFA code received (email/SMS): ")


def login():
    if os.path.isdir(os.path.expanduser(TOKEN_DIR)):
        try:
            client = garminconnect.Garmin(prompt_mfa=prompt_mfa)
            client.client.skip_strategies = SKIP_LOGIN_STRATEGIES
            client.login(TOKEN_DIR)
            print("Session resumed from saved token.")
            return client
        except Exception as e:
            print(f"Could not resume token ({e}), asking to log in again.")

    email = input("Garmin Connect email: ")
    password = getpass.getpass("Password: ")
    client = garminconnect.Garmin(email, password, prompt_mfa=prompt_mfa)
    client.client.skip_strategies = SKIP_LOGIN_STRATEGIES
    client.login(TOKEN_DIR)
    print("Login OK, token saved to", TOKEN_DIR)
    return client


def main():
    client = login()

    today = datetime.date.today().isoformat()

    print("\n--- Today's summary ---")
    stats = client.get_stats(today)
    summary = {
        "steps": stats.get("totalSteps"),
        "goal_steps": stats.get("dailyStepGoal"),
        "calories_total": stats.get("totalKilocalories"),
        "calories_active": stats.get("activeKilocalories"),
        "resting_hr": stats.get("restingHeartRate"),
        "floors_climbed": stats.get("floorsAscended"),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    print("\n--- Recent activities ---")
    activities = client.get_activities(0, 5)
    for a in activities:
        print(f"- {a.get('activityName')} | {a.get('startTimeLocal')} | "
              f"{a.get('distance')} m | {a.get('calories')} kcal")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
