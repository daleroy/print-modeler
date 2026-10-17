---
name: print-modeling
description: Design and verify 3D-printable models for the Bambu Lab P2S in this repo. Use for any request to model, modify, fix, or check a printable part, enclosure, bracket, mount, joint, or figure mesh; covers the job spec, engine choice, OpenSCAD conventions, the build-render-check loop, and the hand-off report.
---

# Print modeling

Printer: Bambu Lab P2S, 256 x 256 x 256 mm, 0.4 mm nozzle, enclosed, AMS (single color for now).
All defaults live in `config/printer.json`. Read it once per job; never hard-code values that live there.

## The job lifecycle

```
intake -> spec.md -> route -> model -> build+verify loop -> FIRST DRAFT CHECK-IN -> (revisions) -> hand-off -> ask about slicing
```

### 1. Intake: spec first
- Create the job: `python tools/new_job.py "<title>" --material <M>` -> `jobs/<slug>/`.
- Fill `jobs/<slug>/spec.md` from the request. Front matter fields:
  - `inputs:` paths to source files anywhere on the Mac (STLs, photos, .scad projects). Read them from where they are; do not copy photos of people into the repo.
  - `output_dir:` where finished files go. Blank = `jobs/<slug>/out`.
  - `for_sale:` true means every borrowed piece of geometry must have a license that allows commercial use.
- Every critical dimension needs a value AND a source (calipers, datasheet, photo with a scale reference). Never invent a mating dimension. If one is missing and a wrong guess would make the part unusable, stop and ask (see "Asking questions").
- Datasheet dimensions for common parts (ESP32 DevKit, barrel jacks, PG glands, heat-set inserts) may be looked up on the web; record the URL in the spec and mark them "verify with calipers".

### 2. Route to an engine
| Request | Engine |
|---|---|
| Dimension-driven: brackets, mounts, enclosures, adapters, jigs, joints, threads | OpenSCAD (`model.scad`) |
| Modify an existing STL (add holes, mounts, cut, combine) | OpenSCAD `import()` + booleans; Blender if the mesh is broken or organic |
| Organic / sculpted / figure meshes (e.g. Meshy output) | Blender, Phase 2. Until then: run `check_print.py` on the mesh, report problems, and say the figure pipeline is not built yet |

### 3. Model (OpenSCAD)
Read `references/openscad-patterns.md` before writing the first file of a session, and
`references/fdm-design-rules.md` whenever a feature is near a printing limit.
Check `references/libraries.md` before writing any generic mechanism (threads, snaps, hinges,
enclosures, nut traps): use the vendored library rather than writing it from scratch.

Non-negotiable conventions:
1. Every part is built **in print orientation**, resting on z = 0.
2. Multi-part models expose `part = "<name>"`; each printable part is a value, plus `"all"` (plate layout, 10 mm gaps) and `"assembled"` (mated view, other parts with `%`). Mating parts also get `"<name>_installed"` (assembly coordinates) for fit checks.
3. All critical dimensions are named variables at the top of the file with units and a comment saying where the number came from. Group them with `/* [Section] */` so the Customizer shows them.
4. Booleans overlap by `EPS` (0.01) to avoid coincident faces; non-watertight output usually means this was skipped.
5. Clearances come from `CLR_*` constants / config, never ad-hoc literals.

### 4. Build and verify loop
```
python tools/build_scad.py jobs/<slug>/model.scad --parts a,b --material PETG
```
This exports each part to `jobs/<slug>/out/`, renders `<part>_views.png` (iso, front, right, top, underside; red = overhang beyond 45 deg) and writes `<part>_check.json`.

After every build:
1. **Look at every `_views.png` with the Read tool.** Compare against the spec: are holes where they should be, openings on the correct face, text readable, nothing floating? The checker cannot catch a hole on the wrong wall; your eyes can.
2. Read the check verdict. FAIL must be fixed. Each WARN needs either a fix or a one-line justification in the report.
3. For mating parts: export the `_installed` parts and run `python tools/fit_check.py a_installed.stl b_installed.stl` (add `--contact-ok` when faces are meant to touch). Interference > 0.5 mm^3 is a fail.
4. Fix and rebuild. Keep a short decisions log in spec.md.

Stop the loop and check in when: all parts PASS (or WARNs are justified), OR the same problem survives two fix attempts, OR you need information only the user has. `config/agent.json` sets `max_auto_iterations` for revisions after the first draft (currently 0 = always check in).

### 5. First-draft check-in (always)
End the run with a check-in message containing:
- one line per part: verdict, size, est. grams, support needed (yes/no)
- the `_views.png` paths, so they can be shown to the user
- assumptions you made, and the dimensions that came from datasheets instead of calipers
- specific questions (at most 4), each with your recommended answer

Do not finalize until the user approves the draft.

### 6. Hand-off
1. Write `jobs/<slug>/REPORT.md` from `references/report-template.md`.
2. `python tools/finalize.py jobs/<slug> [--parts a,b]` copies parts, previews and the report to `output_dir`.
3. Set `status: done` in spec.md.
4. **Ask whether slicing is needed.** Do not slice or prepare plates unless the user says yes.

## Asking questions
This agent may be run as a subagent, which cannot talk to the user directly. When you need input, finish your run with a block titled `NEEDS INPUT` listing the questions (each with a recommended default), plus what you will do once they are answered. Do not guess past a question whose wrong answer would waste a print.

## Privacy and licensing
- Photos of people, especially children, stay where the user keeps them (or `private/`, which is git-ignored). Never copy them into `jobs/`, never commit them, never upload them anywhere.
- Before using geometry from Printables / MakerWorld / Thingiverse / GitHub, record source and license in spec.md. If `for_sale: true` and the license is non-commercial (e.g. CC BY-NC) or unknown, do not use it; say so and design from scratch. GPL libraries (NopSCADlib, Constructive) are for reference and fit checks only, not in sold designs.

## Tools reference
| Tool | Purpose |
|---|---|
| `tools/new_job.py` | create a job folder with spec.md and model.scad stub |
| `tools/build_scad.py` | export parts, render previews, run checks |
| `tools/render_views.py` | preview PNG for any mesh (`--overhangs`) |
| `tools/check_print.py` | printability report; `--orient` ranks orientations; `--apply-orient out.stl` rotates an imported mesh |
| `tools/fit_check.py` | interference and minimum gap between assembled parts |
| `tools/finalize.py` | deliver to `output_dir` |
| `tools/doctor.py` | diagnose the toolchain when anything fails to run |
