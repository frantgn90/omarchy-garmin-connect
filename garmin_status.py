#!/usr/bin/env python3
"""Reads today's Garmin Connect summary using the saved session token.

Does not ask for credentials: meant to be invoked non-interactively (e.g.
from a bar widget). If there is no valid token, it exits with code 1 (or 2
for an authentication failure) and a JSON {"error": "..."} on stdout, so the
caller can tell the difference.

Usage:
    garmin_status.py            # prints JSON with steps/goal/calories/...
    garmin_status.py --summary  # prints a human-readable multi-line summary
"""
import datetime
import json
import sys

import garminconnect

TOKEN_DIR = "~/.garminconnect"


def main():
    try:
        client = garminconnect.Garmin()
        client.login(TOKEN_DIR)
        stats = client.get_stats(datetime.date.today().isoformat())
    except garminconnect.GarminConnectAuthenticationError as e:
        # Token missing, expired or rejected: only a fresh interactive login
        # (garmin-login) can fix this, so the caller needs to know it's not
        # a transient network hiccup.
        print(json.dumps({"error": str(e), "needsLogin": True}))
        sys.exit(2)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    data = {
        "steps": int(stats.get("totalSteps") or 0),
        "goal": int(stats.get("dailyStepGoal") or 0),
        "calories": int(stats.get("totalKilocalories") or 0),
        "caloriesActive": int(stats.get("activeKilocalories") or 0),
        "restingHr": stats.get("restingHeartRate"),
        "floors": stats.get("floorsAscended"),
    }

    if "--summary" in sys.argv:
        lines = [f"Steps: {data['steps']} / {data['goal']}",
                 f"Calories: {data['calories']} kcal"]
        if data["restingHr"]:
            lines.append(f"Resting HR: {data['restingHr']} bpm")
        print("\n".join(lines))
    else:
        print(json.dumps(data))


if __name__ == "__main__":
    main()
