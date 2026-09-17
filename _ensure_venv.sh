# Sourced by garmin-status and garmin-login. Creates the local virtualenv on
# first run so installing this plugin needs no manual pip step -- just
# running either wrapper once bootstraps it. $dir must already be set by the
# caller to its own directory.
#
# requirements.txt is a fully pinned, hash-locked file (see its header for
# how to regenerate it). --require-hashes makes pip refuse to install
# anything -- including transitive deps -- that isn't listed there with a
# matching hash, so a compromised/typosquatted PyPI release of garminconnect
# (which handles the Garmin email/password/MFA/session token) can't be
# silently pulled in on a fresh install.
if [ ! -x "$dir/venv/bin/python" ]; then
  echo "garmin.connect: setting up its virtualenv (first run only)..." >&2
  python3 -m venv "$dir/venv" || exit 1
  "$dir/venv/bin/pip" install --quiet --require-hashes -r "$dir/requirements.txt" || exit 1
fi
