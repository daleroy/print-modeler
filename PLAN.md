# Plan

Agreed 2026-10-16. Update this file when decisions change.

## Decisions
| Topic | Decision |
|---|---|
| Form | Claude Code subagent `print-modeler` + `print-modeling` skill, in this standalone repo on the Mac |
| Engines | Hybrid: OpenSCAD for dimension-driven parts and enclosures; Blender (headless) for organic/figure meshes |
| Figures | Meshy.ai (+ Gemini restyle) stays upstream. The agent prepares meshes: repair, scale, joints, base, split, orient |
| Bodies | Print our own (no bought blanks for now) |
| Color | Single color first; multi-color 3MF for the AMS later |
| Inputs | Text, photos, STLs. Locations are listed in each job's `spec.md` (`inputs:`, `output_dir:`) |
| Autonomy | Always check in after the first draft; `config/agent.json` `max_auto_iterations` (starts at 0) |
| Slicing | The agent asks at hand-off whether slicing is needed |
| Libraries | Vendored permissive libs (BOSL2, YAPP_Box, threads.scad, catchnhole, Round-Anything). GPL libs reference-only. License recorded per job; non-commercial geometry banned from shop items |
| Privacy | Photos of kids never enter the repo, git, or any upload |

## Phase 1 — functional and enclosure core  (this delivery)
- [x] Repo scaffold, setup.sh, doctor
- [x] Vendored libraries as pinned submodules
- [x] P2S config (`config/printer.json`) and helper layer (`lib/print_lib.scad`)
- [x] Verification tools: build_scad, render_views, check_print, fit_check
- [x] Job tools: new_job (spec template), finalize
- [x] Agent + skill + references (design rules, libraries, OpenSCAD patterns, report template)
- [x] Examples: controller enclosure, rod clip, tolerance test
- [x] Toolchain set up on the Mac (OpenSCAD snapshot 2026.10.11, Blender 3.6.4) and `tools/selftest.sh` passing (2026-10-16)
- [ ] First real job run end to end on the Mac
- [ ] Print `examples/tolerance_test`; record results in `config/printer.json`, `CLR_*` in print_lib, `$slop`

## Phase 2 — figure pipeline
- Blender headless runner + scripts: import STL/3MF/GLB from Meshy, voxel-remesh repair, scale to target height, flat-cut base
- Joint standard (peg or ball socket; sizes and clearances in config) with a joint fit test print
- Parametric printed body with matching joints (start simple, peg-jointed); look at openly licensed articulated bases for ideas
- Head prep: neck cut + socket; split into printable pieces; orientation to minimise supports on faces
- Display bases and simple accessories (shields, emblems) in OpenSCAD

## Phase 3 — polish
- Calibration loop from tolerance/joint tests into config
- Slicing support if wanted (prepared plate 3MF or Bambu Studio CLI)
- Multi-color 3MF for the AMS
- Library of proven parts from finished jobs
- Raise `max_auto_iterations` once drafts are reliably right
