#!/usr/bin/env python3
"""Lee el resumen diario de Garmin Connect usando el token de sesión guardado.

No pide credenciales: pensado para invocarse de forma no interactiva (p. ej.
desde un widget de la barra). Si no hay token válido, sale con código 1 y
un JSON {"error": "..."} en stdout, para que el llamador lo distinga.

Uso:
    garmin_status.py            # imprime JSON con steps/goal/calories/...
    garmin_status.py --summary  # imprime un resumen legible en varias líneas
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
        lines = [f"Pasos: {data['steps']} / {data['goal']}",
                 f"Calorias: {data['calories']} kcal"]
        if data["restingHr"]:
            lines.append(f"FC reposo: {data['restingHr']} ppm")
        print("\n".join(lines))
    else:
        print(json.dumps(data))


if __name__ == "__main__":
    main()
