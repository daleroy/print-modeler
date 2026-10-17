#!/usr/bin/env python3
"""Deliver a finished job: copy the chosen parts, their previews, and REPORT.md
to the spec's output_dir (or jobs/<name>/out if blank).

Usage:
  python tools/finalize.py jobs/<name> [--parts base,lid]

Expects jobs/<name>/REPORT.md written by the agent (print settings, orientation,
material, filament estimate, assembly notes, open issues).
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jobspec import resolve_output_dir  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job")
    ap.add_argument("--parts", default="", help="comma-separated part names; default = everything in out/")
    a = ap.parse_args()

    job = Path(a.job).resolve()
    build = job / "out"
    dest = resolve_output_dir(job)
    if not build.exists():
        sys.exit(f"No build output in {build}. Run tools/build_scad.py first.")
    report = job / "REPORT.md"
    if not report.exists():
        sys.exit(f"Missing {report}. Write the hand-off report before finalizing.")

    wanted = [p.strip() for p in a.parts.split(",") if p.strip()]
    meshes = [p for p in build.iterdir() if p.suffix in (".stl", ".3mf")
              and (not wanted or p.stem in wanted)]
    if not meshes:
        sys.exit("No matching meshes to deliver.")

    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    for m in meshes:
        for f in [m, build / f"{m.stem}_views.png"]:
            if f.exists() and f.parent.resolve() != dest.resolve():
                shutil.copy2(f, dest / f.name)
                copied.append(f.name)
    if report.parent.resolve() != dest.resolve():
        shutil.copy2(report, dest / "REPORT.md")
        copied.append("REPORT.md")
    print(f"Delivered to {dest}:")
    for c in copied:
        print("  " + c)


if __name__ == "__main__":
    main()
