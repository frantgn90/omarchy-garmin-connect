# Sourced by garmin-status and garmin-login. Creates the local virtualenv on
# first run so installing this plugin needs no manual pip step -- just
# running either wrapper once bootstraps it. $dir must already be set by the
# caller to its own directory.
if [ ! -x "$dir/venv/bin/python" ]; then
  echo "garmin.connect: setting up its virtualenv (first run only)..." >&2
  python3 -m venv "$dir/venv" || exit 1
  "$dir/venv/bin/pip" install --quiet -r "$dir/requirements.txt" || exit 1
fi
