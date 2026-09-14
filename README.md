# jfmarve.garmin — widget de Garmin Connect para Omarchy

Muestra en la barra de [Omarchy](https://omarchy.org/) los pasos del día
(con objetivo, calorías y frecuencia cardíaca en reposo en el tooltip),
leyendo tus datos de Garmin Connect.

Usa la librería no oficial [`garminconnect`](https://github.com/cyberjunky/python-garminconnect).
No existe una API pública oficial sencilla para uso personal: Garmin Connect
Health API requiere ser partner empresarial.

## Instalación

```bash
omarchy plugin add <url-de-este-repo> --enable
```

O manualmente:

```bash
git clone <url-de-este-repo> ~/.config/omarchy/plugins/jfmarve.garmin
omarchy plugin enable jfmarve.garmin --section center
```

Después, crea el entorno virtual con las dependencias:

```bash
cd ~/.config/omarchy/plugins/jfmarve.garmin
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

Y haz login una vez (pide email/contraseña, y código MFA si tu cuenta lo usa):

```bash
./garmin-login
```

Esto guarda un token de sesión en `~/.garminconnect` (permisos `600`, solo
tu usuario puede leerlo). El widget ya debería mostrar tus pasos en la
barra; si no, `omarchy restart shell`.

## Uso

- **Clic izquierdo / derecho**: abre Garmin Connect en el navegador.
- **Clic central**: fuerza un refresco inmediato.
- **Hover**: tooltip con pasos/objetivo, calorías y frecuencia cardíaca en reposo.
- Se refresca solo cada 15 minutos.

### Cuando la sesión caduca

Garmin invalida el token de sesión de vez en cuando. Cuando eso pasa, el
widget **no desaparece**: en su lugar muestra `⚠ Garmin`. Un clic (cualquier
botón) abre una terminal flotante y relanza `garmin-login` automáticamente,
para que puedas reautenticarte sin salir de la barra.

## Seguridad

- El email y la contraseña **nunca se guardan en disco**: solo se usan en
  memoria durante el login interactivo.
- Lo único persistido es un token OAuth en `~/.garminconnect/garmin_tokens.json`
  (fuera de esta carpeta, así que nunca se publicará por error si subes este
  repo a git). No lo compartas ni lo subas a ningún sitio: es equivalente a
  una sesión iniciada.
- `venv/` no se versiona (ver `.gitignore`); cada instalación crea la suya
  con `requirements.txt`.

## Nota sobre el login (429 Too Many Requests)

Desde marzo de 2026 Garmin aplica un rate-limit agresivo (HTTP 429) a las
estrategias de login "clásicas" de estas librerías no oficiales, a veces
desde el primer intento. La versión de `garminconnect` fijada en
`requirements.txt` ya incluye un login alternativo vía "SSO embed widget"
que lo esquiva automáticamente; si en el futuro vuelve a fallar, revisa si
hay una versión más reciente de la librería.

## Estructura

```
manifest.json      # manifiesto del plugin de Omarchy
BarWidget.qml       # widget de la barra (Quickshell/QML)
garmin-status        # wrapper -> garmin_status.py (lee datos, JSON por stdout)
garmin_status.py
garmin-login          # wrapper -> garmin_login.py (login interactivo/MFA)
garmin_login.py
requirements.txt
```
