# Sourced by garmin-status and garmin-login. Creates the virtualenv on first
# run so installing this plugin needs no manual pip step -- just running
# either wrapper once bootstraps it. $dir must already be set by the caller
# to its own directory; this sets $venv for the caller to run python from.
#
# The venv deliberately lives OUTSIDE the plugin directory. The Omarchy shell
# watches the whole plugin tree with `inotifywait -m -r -e close_write,create,
# delete,move` and reloads the plugin on every event (see PluginRegistry.qml),
# so building a venv in place emits thousands of events mid-install: the bar
# widget gets torn down and respawned continuously, which thrashes the desktop
# and races this script against its own concurrent copies.
venv="${XDG_DATA_HOME:-$HOME/.local/share}/garmin.connect/venv"

# Completion is tracked by .ready, written only once pip install succeeds,
# rather than by $venv/bin/python existing -- the latter is created up front
# by `python3 -m venv` regardless of whether the pip install that follows ever
# finishes, so using it as the "already set up" check lets a venv left
# half-installed by an interrupted run go unnoticed and unretried forever.
# flock serializes concurrent first runs (both wrappers can be launched at
# once by the widget), and the lock lives beside the venv, not in the plugin.
mkdir -p "$(dirname "$venv")" || exit 1
(
  flock -x 9
  if [ ! -f "$venv/.ready" ]; then
    echo "garmin.connect: setting up its virtualenv (first run only)..." >&2
    [ -x "$venv/bin/python" ] || python3 -m venv "$venv" || exit 1
    # requirements.txt is fully pinned and hash-locked (see its header for how
    # to regenerate it). --require-hashes makes pip refuse to install anything
    # -- including transitive deps -- not listed there with a matching hash, so
    # a compromised or typosquatted PyPI release of garminconnect (which
    # handles the Garmin email/password/MFA code/session token) can't be
    # silently pulled in on a fresh install.
    "$venv/bin/pip" install --quiet --require-hashes -r "$dir/requirements.txt" || exit 1
    touch "$venv/.ready"
  fi
) 9>"$(dirname "$venv")/venv.lock" || exit 1
