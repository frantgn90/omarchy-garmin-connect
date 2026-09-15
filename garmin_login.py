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
import itertools
import json
import os
import sys
import threading
import time

import garminconnect

TOKEN_DIR = "~/.garminconnect"

# Garmin has rate-limited the "mobile" login endpoints (HTTP 429) since
# March 2026, so the library's default strategy chain always burns two
# guaranteed failures before falling back to the one that works. Skip
# straight to it; revisit if Garmin ever lifts the block.
SKIP_LOGIN_STRATEGIES = {"mobile+cffi", "mobile+requests"}


class Spinner:
    """Minimal terminal spinner so a multi-second network call doesn't look hung."""

    FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    active = None  # the currently running Spinner, if any -- see prompt_mfa()

    def __init__(self, message):
        self.message = message
        self._stop = threading.Event()
        self._paused = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True) if sys.stdout.isatty() else None

    def _spin(self):
        for frame in itertools.cycle(self.FRAMES):
            if self._stop.is_set():
                return
            if not self._paused.is_set():
                sys.stdout.write(f"\r{frame} {self.message}")
                sys.stdout.flush()
            time.sleep(0.08)

    def _clear_line(self):
        sys.stdout.write("\r" + " " * (len(self.message) + 2) + "\r")
        sys.stdout.flush()

    def pause(self):
        self._paused.set()
        self._clear_line()

    def resume(self):
        self._paused.clear()

    class _ClearingStream:
        """Wraps a stream so anything written to it (e.g. garminconnect's own
        logging.warning() calls, which land on stderr) clears the spinner's
        line first instead of getting appended after it mid-line."""

        def __init__(self, spinner, real):
            self._spinner = spinner
            self._real = real

        def write(self, s):
            if s:
                self._spinner._clear_line()
            return self._real.write(s)

        def flush(self):
            self._real.flush()

        def isatty(self):
            return self._real.isatty()

    def __enter__(self):
        if self._thread:
            Spinner.active = self
            self._real_stderr = sys.stderr
            sys.stderr = self._ClearingStream(self, self._real_stderr)
            self._thread.start()
        else:
            print(self.message)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._thread:
            self._stop.set()
            self._thread.join()
            sys.stderr = self._real_stderr
            self._clear_line()
            Spinner.active = None


def prompt_mfa():
    # Called by garminconnect from inside a login() call running under a
    # Spinner -- pause it so the code prompt and what you type don't get
    # overwritten by spinner frames every 80ms.
    if Spinner.active:
        Spinner.active.pause()
    code = input("MFA code received (email/SMS): ")
    if Spinner.active:
        Spinner.active.resume()
    return code


def login():
    if os.path.isdir(os.path.expanduser(TOKEN_DIR)):
        try:
            client = garminconnect.Garmin(prompt_mfa=prompt_mfa)
            client.client.skip_strategies = SKIP_LOGIN_STRATEGIES
            with Spinner("Resuming session..."):
                client.login(TOKEN_DIR)
            print("Session resumed from saved token.")
            return client
        except Exception as e:
            print(f"Could not resume token ({e}), asking to log in again.")

    email = input("Garmin Connect email: ")
    password = getpass.getpass("Password: ")
    client = garminconnect.Garmin(email, password, prompt_mfa=prompt_mfa)
    client.client.skip_strategies = SKIP_LOGIN_STRATEGIES
    with Spinner("Logging in..."):
        client.login(TOKEN_DIR)
    print("Login OK, token saved to", TOKEN_DIR)
    return client


def main():
    client = login()

    today = datetime.date.today().isoformat()

    print("\n--- Today's summary ---")
    with Spinner("Fetching today's summary..."):
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
    with Spinner("Fetching recent activities..."):
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
