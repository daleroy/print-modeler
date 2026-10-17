#!/usr/bin/env bash
# End-to-end self-test: toolchain check, build every example, fit check, render previews.
# Run from the repo root after ./setup.sh.  Exit code 0 = everything passed.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=./.venv/bin/python
[ -x "$PY" ] || PY=python3
fail=0
step() { echo; echo "=== $*"; }

step "Toolchain"
$PY tools/doctor.py || fail=1

step "Controller enclosure (base, lid, lid_installed)"
$PY tools/build_scad.py examples/controller_enclosure/model.scad --parts base,lid,lid_installed --material PETG || fail=1
step "Lid vs base fit"
$PY tools/fit_check.py examples/controller_enclosure/out/base.stl \
                       examples/controller_enclosure/out/lid_installed.stl --contact-ok || fail=1

step "Rod clip"
$PY tools/build_scad.py examples/rod_clip/model.scad --material PETG || fail=1

step "Tolerance test (plate, pegs)"
$PY tools/build_scad.py examples/tolerance_test/model.scad --parts plate,pegs || fail=1

step "Font check (lid label must render)"
if grep -q "Can't get font" examples/controller_enclosure/out/*.log 2>/dev/null; then fail=1; fi

echo
if [ $fail -eq 0 ]; then
  echo "SELFTEST PASSED. Previews: examples/*/out/*_views.png"
else
  echo "SELFTEST FAILED: see the sections above."
fi
exit $fail
