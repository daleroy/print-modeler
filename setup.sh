#!/usr/bin/env bash
# One-time setup on macOS. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")"

echo "== Submodules (BOSL2, YAPP_Box, threads-scad, catchnhole, Round-Anything)"
git submodule update --init --recursive

echo "== Python environment (.venv)"
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip -q
./.venv/bin/pip install -r requirements.txt -q

if ! command -v openscad >/dev/null && [ ! -d /Applications/OpenSCAD.app ] && [ ! -d /Applications/OpenSCAD-Nightly.app ]; then
  echo "== OpenSCAD not found."
  echo "   Install a development snapshot (much faster Manifold backend), e.g.:"
  echo "     brew install --cask openscad@snapshot"
  echo "   or download one from https://openscad.org/downloads.html#snapshots"
fi

echo "== Checking toolchain"
./.venv/bin/python tools/doctor.py || true
echo
echo "Activate with:  source .venv/bin/activate"
