#!/usr/bin/env python3
"""Build an OpenSCAD model: export each part, render previews, run the printability check.

Usage:
  python tools/build_scad.py jobs/<name>/model.scad [--parts base,lid] [-D wall=2.4 -D 'label="HI"']
                             [--format stl|3mf] [--material PETG] [--no-check] [--no-render]

Outputs go to jobs/<name>/out/: <part>.stl (or .3mf), <part>_views.png, <part>_check.json.
Multi-part models expose a `part` variable; each listed part is exported separately.

OpenSCAD is found via $OPENSCAD_BIN, PATH, or the default macOS/Windows install paths.
A 2024+ development snapshot is strongly recommended: its Manifold backend renders
booleans 10-100x faster than the 2021.01 release. The script uses it when available.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
CANDIDATES = [
    "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD",
    "/Applications/OpenSCAD-Nightly.app/Contents/MacOS/OpenSCAD",
    r"C:\Program Files\OpenSCAD\openscad.exe",
    r"C:\Program Files\OpenSCAD (Nightly)\openscad.exe",
]


def find_openscad():
    env = os.environ.get("OPENSCAD_BIN")
    if env and Path(env).exists():
        return env
    for name in ("openscad-nightly", "openscad"):
        p = shutil.which(name)
        if p:
            return p
    for c in CANDIDATES:
        if Path(c).exists():
            return c
    sys.exit("OpenSCAD not found. Install it (brew install --cask openscad@snapshot) or set OPENSCAD_BIN.")


def run_openscad(bin_, src, out, defines, part):
    base = [bin_, "-o", str(out)]
    for d in defines:
        base += ["-D", d]
    if part:
        base += ["-D", f'part="{part}"']
    if str(out).endswith(".stl"):
        base += ["--export-format", "binstl"]
    base.append(str(src))
    # Snapshot builds: Manifold backend (fast) + JSON import() (catchnhole reads its tables that way).
    for extra in (["--backend=manifold", "--enable=import-function"], []):
        cmd = base[:1] + extra + base[1:]
        t = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True)
        log = (r.stdout or "") + (r.stderr or "")
        if extra and r.returncode != 0 and ("unrecognised option" in log or "unknown option" in log.lower()
                                           or "backend" in log or "enable" in log):
            continue  # 2021.01 release without these options: retry without them
        return r.returncode, log, time.time() - t
    return r.returncode, log, time.time() - t


def summarize_log(log):
    keep = [l for l in log.splitlines() if any(k in l for k in ("WARNING", "ERROR", "ECHO", "TRACE"))]
    return "\n".join(keep[:40])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scad")
    ap.add_argument("--parts", default="", help="comma-separated values for the `part` variable")
    ap.add_argument("-D", dest="defines", action="append", default=[], help="OpenSCAD -D override, repeatable")
    ap.add_argument("--format", choices=["stl", "3mf"], default="stl")
    ap.add_argument("--material", default=None)
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()

    src = Path(a.scad).resolve()
    outdir = src.parent / "out"
    outdir.mkdir(exist_ok=True)
    bin_ = find_openscad()
    parts = [p.strip() for p in a.parts.split(",") if p.strip()] or [None]
    failed = False
    summary = []

    for part in parts:
        name = part or src.stem
        out = outdir / f"{name}.{a.format}"
        code, log, secs = run_openscad(bin_, src, out, a.defines, part)
        (outdir / f"{name}.log").write_text(log)
        notes = summarize_log(log)
        print(f"== {name}: openscad exit {code} in {secs:.1f}s -> {out}")
        if notes:
            print(notes)
        if code != 0 or not out.exists():
            print(log[-3000:])
            failed = True
            continue
        if "WARNING" in log and ("Can't get font" in log or "undefined" in log.lower() or "Ignoring unknown" in log):
            print("  NOTE: OpenSCAD warnings above usually mean a typo or missing font. Fix before trusting the output.")

        entry = {"part": name, "file": str(out)}
        if name.endswith("_installed") or name == "assembled":
            entry["role"] = "fit-check geometry (not printed as-is): skipped printability check"
            print("  (assembly-position geometry: use with tools/fit_check.py; not checked for printability)")
            summary.append(entry)
            continue
        if not a.no_render:
            png = outdir / f"{name}_views.png"
            subprocess.run([sys.executable, str(TOOLS / "render_views.py"), str(out), "-o", str(png),
                            "--overhangs", "--title", f"{src.parent.name} / {name}"], check=False)
            entry["views"] = str(png)
        if not a.no_check:
            cmd = [sys.executable, str(TOOLS / "check_print.py"), str(out), "--orient", "--json"]
            if a.material:
                cmd += ["--material", a.material]
            r = subprocess.run(cmd, capture_output=True, text=True)
            try:
                rep = json.loads(r.stdout)
                (outdir / f"{name}_check.json").write_text(json.dumps(rep, indent=2))
                entry["verdict"] = rep["verdict"]
                print(f"  [{rep['verdict']}] {rep['extents_mm']} mm, ~{rep['est_filament_g']} g, "
                      f"support area {rep['overhang_area_mm2']} mm2")
                for i in rep["issues"]:
                    print(f"  FAIL: {i}")
                for w in rep["warnings"]:
                    print(f"  WARN: {w}")
                if rep["verdict"] == "FAIL":
                    failed = True
            except Exception:
                print(r.stdout, r.stderr)
                failed = True
        summary.append(entry)

    (outdir / "build_summary.json").write_text(json.dumps(summary, indent=2))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
