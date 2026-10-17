# print-modeler

A Claude Code agent that designs and verifies 3D-printable models for a Bambu Lab P2S.
It writes parametric OpenSCAD, builds it, **looks at renders of its own output**, checks
printability and fit, and checks in with you after the first draft. See [PLAN.md](PLAN.md)
for decisions and phases. Phase 1 (functional parts and enclosures) is in place; the Blender figure
pipeline is Phase 2.

## Setup (macOS, once)
```bash
git clone --recurse-submodules <this repo>   # or: git submodule update --init --recursive
cd print-modeler
brew install --cask openscad@snapshot        # development snapshot: Manifold backend, much faster
./setup.sh                                   # creates .venv, installs Python deps, runs doctor
```
If OpenSCAD is somewhere unusual, set `OPENSCAD_BIN=/path/to/openscad`.
Run `.venv/bin/python tools/doctor.py` any time something will not build.

## Using it
In Claude Code, from the repo root:
```
/model a wall mount for my Ring chime, two screws, 3 mm clearance behind it
```
or "use the print-modeler agent to ...". The agent:
1. creates `jobs/<slug>/spec.md` (dimensions with sources, `inputs:` / `output_dir:` paths, material, for_sale)
2. asks what it cannot know (it never invents the size of the thing a part must fit)
3. writes `jobs/<slug>/model.scad`, builds it, reviews the renders, and runs the checks
4. **stops after the first passing draft** with previews, assumptions and questions
5. on approval, writes `REPORT.md`, copies files to `output_dir`, and asks whether you want slicing

## Tools (run from the repo root with `.venv/bin/python`)
| Command | What it does |
|---|---|
| `tools/new_job.py "Title" --material PETG` | new job folder with spec template and model stub |
| `tools/build_scad.py jobs/x/model.scad --parts base,lid` | export each part, render previews, check printability |
| `tools/render_views.py part.stl --overhangs` | 5-view PNG of any mesh; red = needs support |
| `tools/check_print.py part.stl --orient` | watertight, fits bed, overhangs, thin walls, grams, best orientations |
| `tools/fit_check.py a_installed.stl b_installed.stl` | interference and minimum gap between mating parts |
| `tools/finalize.py jobs/x` | deliver parts + previews + REPORT.md to the spec's `output_dir` |
| `tools/doctor.py` | toolchain diagnosis |

## First thing to print
`examples/tolerance_test` (≈14 g PLA). Try each peg in each hole and update `clearances_mm`
in `config/printer.json`, the `CLR_*` constants in `lib/print_lib.scad`, and `$slop`. Every
fitted part after that gets more accurate.

## Layout
```
.claude/agents/print-modeler.md        the subagent
.claude/skills/print-modeling/         workflow + references (design rules, libraries, patterns, report)
.claude/commands/model.md              /model shortcut
config/printer.json, agent.json        P2S limits, clearances, fasteners, materials; autonomy settings
lib/print_lib.scad                     P2S helpers: fasteners, enclosures, teardrops, standoffs...
vendor/                                BOSL2, YAPP_Box, threads-scad, catchnhole, Round-Anything (submodules)
tools/                                 build, render, check, fit, job tools
templates/spec.md                      job spec template
examples/                              controller_enclosure, rod_clip, tolerance_test
jobs/                                  your jobs (out/ folders are git-ignored)
private/                               git-ignored; for reference photos if you keep any here
```

## Licenses
Repo code: yours. Vendored libraries keep their own licenses (BSD-2, MIT, CC0); see each
`vendor/*/LICENSE`. Geometry borrowed from model sites is tracked per job in `spec.md`.
