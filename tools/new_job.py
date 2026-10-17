#!/usr/bin/env python3
"""Create a new job folder: jobs/<slug>/ with spec.md, model.scad stub, inputs/.

Usage:
  python tools/new_job.py "LED controller box" [--engine openscad] [--material PETG]
"""
import argparse
import datetime
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCAD_STUB = """// {title}
// Spec: ./spec.md   Build: python tools/build_scad.py jobs/{slug}/model.scad --parts {parts}
include <../../vendor/BOSL2/std.scad>
include <../../lib/print_lib.scad>

/* [Part] */
part = "all";   // ["all", ...one value per printable part..., "assembled"]

/* [Parameters] */
// Every critical dimension from spec.md is a named variable here, with units and source.

$slop = CLR_PRESS;   // BOSL2 fit clearance (calibrated value from config)

// module part_a() {{ ... }}   // each part built in PRINT orientation, resting on z = 0

if (part == "all") {{
  // all parts laid out on one plate, 10 mm apart
}}
"""


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("title")
    ap.add_argument("--slug")
    ap.add_argument("--engine", default="openscad", choices=["openscad", "blender"])
    ap.add_argument("--material", default="PLA")
    a = ap.parse_args()

    slug = a.slug or slugify(a.title)
    job = ROOT / "jobs" / slug
    if job.exists():
        raise SystemExit(f"{job} already exists")
    (job / "inputs").mkdir(parents=True)

    spec = (ROOT / "templates" / "spec.md").read_text()
    spec = (spec.replace("name: <job-slug>", f"name: {slug}")
                .replace("# <Title>", f"# {a.title}")
                .replace("engine: openscad ", f"engine: {a.engine} ")
                .replace("material: PLA ", f"material: {a.material} ")
                .replace("- <date>: <decision and why>",
                         f"- {datetime.date.today().isoformat()}: job created"))
    (job / "spec.md").write_text(spec)
    if a.engine == "openscad":
        (job / "model.scad").write_text(SCAD_STUB.format(title=a.title, slug=slug, parts="part_a"))
    print(job)


if __name__ == "__main__":
    main()
