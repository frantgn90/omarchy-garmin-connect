#!/usr/bin/env python3
"""Login interactivo/reautenticación para el widget de Garmin de Omarchy.

Uso:
    ./garmin-login

Pide email y contraseña (con getpass, nunca se muestran en pantalla ni se
guardan en disco) y, si la cuenta lo requiere, un código MFA. Al terminar
guarda un token de sesión OAuth en ~/.garminconnect para que garmin-status
pueda leer datos sin volver a pedir credenciales. Se lanza automáticamente
desde el propio widget de la barra cuando detecta que la sesión ha caducado.
"""
import datetime
import getpass
import json
import os
import sys

import garminconnect

TOKEN_DIR = "~/.garminconnect"


def prompt_mfa():
    return input("Código MFA recibido (email/SMS): ")


def login():
    if os.path.isdir(os.path.expanduser(TOKEN_DIR)):
        try:
            client = garminconnect.Garmin(prompt_mfa=prompt_mfa)
            client.login(TOKEN_DIR)
            print("Sesión reanudada desde token guardado.")
            return client
        except Exception as e:
            print(f"No se pudo reanudar el token ({e}), pidiendo login de nuevo.")

    email = input("Email de Garmin Connect: ")
    password = getpass.getpass("Contraseña: ")
    client = garminconnect.Garmin(email, password, prompt_mfa=prompt_mfa)
    client.login(TOKEN_DIR)
    print("Login OK, token guardado en", TOKEN_DIR)
    return client


def main():
    client = login()

    today = datetime.date.today().isoformat()

    print("\n--- Resumen del día ---")
    stats = client.get_stats(today)
    resumen = {
        "steps": stats.get("totalSteps"),
        "goal_steps": stats.get("dailyStepGoal"),
        "calories_total": stats.get("totalKilocalories"),
        "calories_active": stats.get("activeKilocalories"),
        "resting_hr": stats.get("restingHeartRate"),
        "floors_climbed": stats.get("floorsAscended"),
    }
    print(json.dumps(resumen, indent=2, ensure_ascii=False))

    print("\n--- Últimas actividades ---")
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
