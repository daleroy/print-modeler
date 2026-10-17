#!/usr/bin/env python3
"""Check that this machine can run the print-modeler toolchain. Run after setup or when builds fail.

Usage:  python tools/doctor.py
"""
import importlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent
ok = True


def report(good, msg, fix=""):
    global ok
    print(("  OK   " if good else "  FAIL ") + msg + ("" if good or not fix else f"\n         fix: {fix}"))
    ok = ok and good


print("Python packages")
for mod in ["trimesh", "numpy", "scipy", "rtree", "manifold3d", "matplotlib", "yaml"]:
    try:
        importlib.import_module(mod)
        report(True, mod)
    except Exception:
        report(False, mod, "pip install -r requirements.txt")
try:
    importlib.import_module("fast_simplification")
    report(True, "fast_simplification (optional: faster previews of big meshes)")
except Exception:
    print("  --   fast_simplification not installed (optional)")

print("OpenSCAD")
try:
    from build_scad import find_openscad
    import io, contextlib
    with contextlib.redirect_stderr(io.StringIO()):
        bin_ = find_openscad()
    v = subprocess.run([bin_, "--version"], capture_output=True, text=True)
    ver = (v.stdout + v.stderr).strip().splitlines()[-1] if (v.stdout + v.stderr).strip() else "unknown"
    report(True, f"{bin_}  ({ver})")
    h = subprocess.run([bin_, "--help"], capture_output=True, text=True)
    if "backend" in (h.stdout + h.stderr):
        report(True, "Manifold backend available (fast booleans)")
    else:
        print("  WARN no --backend option: this is the 2021 release. Install a development snapshot for 10-100x faster renders.")
except SystemExit as e:
    report(False, "OpenSCAD not found", str(e))

print("Vendored libraries (git submodules)")
for lib, probe in [("BOSL2", "std.scad"), ("YAPP_Box", "YAPPgenerator_v3.scad"),
                   ("threads-scad", "threads.scad"), ("catchnhole", "catchnhole.scad"),
                   ("Round-Anything", "polyround.scad")]:
    report((ROOT / "vendor" / lib / probe).exists(), lib, "git submodule update --init --recursive")

print("Blender (needed from Phase 2, figure pipeline)")
for cand in ["/Applications/Blender.app/Contents/MacOS/Blender", "blender"]:
    try:
        r = subprocess.run([cand, "-b", "--version"], capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            print(f"  OK   {r.stdout.splitlines()[0]}")
            break
    except Exception:
        continue
else:
    print("  --   not found (fine for Phase 1): brew install --cask blender")

print("\nAll required checks passed." if ok else "\nSome checks failed; see fixes above.")
sys.exit(0 if ok else 1)
