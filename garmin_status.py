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

# Garmin has rate-limited the "mobile" login endpoints (HTTP 429) since
# March 2026, so the library's default strategy chain always burns two
# guaranteed failures before falling back to the one that works. Skip
# straight to it; revisit if Garmin ever lifts the block.
SKIP_LOGIN_STRATEGIES = {"mobile+cffi", "mobile+requests"}


def main():
    try:
        client = garminconnect.Garmin()
        client.client.skip_strategies = SKIP_LOGIN_STRATEGIES
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
        "floorsGoal": stats.get("userFloorsAscendedGoal"),
        "bodyBattery": stats.get("bodyBatteryMostRecentValue"),
        "stressLevel": stats.get("averageStressLevel"),
        "stressQualifier": stats.get("stressQualifier"),
    }

    # Weekly aggregate, not part of get_stats(): a day with 0 minutes doesn't
    # mean the week's progress is 0, so this needs its own call. Non-fatal if
    # it fails -- the rest of the widget still has plenty to show.
    try:
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())
        week_end = week_start + datetime.timedelta(days=6)
        weekly = client.get_weekly_intensity_minutes(week_start.isoformat(), week_end.isoformat())
        if weekly:
            latest = weekly[-1]
            moderate = latest.get("moderateValue") or 0
            vigorous = latest.get("vigorousValue") or 0
            data["intensityMinutes"] = moderate + 2 * vigorous
            data["intensityGoal"] = latest.get("weeklyGoal")
    except Exception:
        pass

    if "--summary" in sys.argv:
        lines = [f"Steps: {data['steps']} / {data['goal']}",
                 f"Calories: {data['calories']} kcal"]
        if data["restingHr"]:
            lines.append(f"Resting HR: {data['restingHr']} bpm")
        if data["bodyBattery"] is not None:
            lines.append(f"Body Battery: {data['bodyBattery']}/100")
        print("\n".join(lines))
    else:
        print(json.dumps(data))


if __name__ == "__main__":
    main()
