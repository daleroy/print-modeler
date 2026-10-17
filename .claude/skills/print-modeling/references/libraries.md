# Libraries: use these before writing mechanisms from scratch

All are vendored under `vendor/` as pinned git submodules. Include paths below are relative to
a job file at `jobs/<slug>/model.scad`. Verify a module's signature by grepping its source
(`grep -n "^module name" vendor/...`) before using unfamiliar parameters; the docs live in
comments above each module.

## Permissive (OK in parts sold through the shop)

### BOSL2 (BSD-2-Clause) — default toolkit
`include <../../vendor/BOSL2/std.scad>` (core shapes, attachments, rounding), plus feature files:
| Need | Include | Modules |
|---|---|---|
| Rounded / chamfered blocks and cylinders | std | `cuboid(size, rounding=, chamfer=, edges=, anchor=)`, `cyl(d=, h=, rounding=, chamfer=)`, `prismoid`, `tube`, `wedge` |
| Horizontal holes without support | std | `teardrop(d=, l=, ang=45)` (axis along Y, point toward +Z) |
| Text on surfaces | std | `text3d()`, `path_text()` |
| Positioning parts relative to each other | std | `attach()`, `position()`, anchors (`TOP`, `BOTTOM`, `LEFT`...), `diff()` + `tag("remove")` |
| Threads (printable, >= M8 or custom) | `threading.scad` | `threaded_rod()`, `threaded_nut()` |
| Metric screws, screw holes, nut traps | `screws.scad` | `screw_hole()`, `nut_trap_side()`, `nut_trap_inline()` |
| Snap pins, dovetails, clips, split joints | `joiners.scad` | `snap_pin()`, `snap_pin_socket()`, `dovetail()`, `rabbit_clip()`, `half_joiner()` |
| Hinges | `hinges.scad` | `knuckle_hinge()`, `living_hinge_mask()` |
| Split parts too big for the bed | std | `partition()` |
| Gears | `gears.scad` | `spur_gear()` and friends |
| Bottle threads/caps | `bottlecaps.scad` | |
BOSL2 fit clearance is `$slop` (per side). Set `$slop = CLR_PRESS;` (or the calibrated value) at the top of every file that uses BOSL2 fitted parts.

### YAPP_Box (MIT) — PCB-driven project boxes
`vendor/YAPP_Box/YAPPgenerator_v3.scad`, start from a copy of `YAPP_Template_v3.scad`.
Use it when the box is defined by a PCB (standoffs at its holes, cutouts at its connectors)
and snap-fit or insert-based lids are wanted. Configure via variables (`pcbLength`,
`pcbWidth`, wall/padding, cutout arrays per face). Use `lib/print_lib.scad` `enclosure_base`/`enclosure_lid`
instead for simple screw-lid boxes or when you need full control. Note: YAPP's X/Y naming
(X = front-to-back) differs from ours; check renders.

### threads.scad (CC0) — quick metric hardware
`use <../../vendor/threads-scad/threads.scad>`: `ScrewThread()`, `ScrewHole()`, `MetricBolt()`,
`MetricNut()`, `ClearanceHole()`, `RodStart()/RodEnd()`. Simpler than BOSL2 threading; fine for knobs and caps.

### catchnhole (MIT) — bolts, nut catches, countersinks
`use <../../vendor/catchnhole/catchnhole.scad>`: `bolt(options, length=, kind=)`, `nutcatch_parallel()`,
`nutcatch_sidecut()`. Dimension tables in `bolts.json` / `nuts.json`, loaded with OpenSCAD's experimental
JSON `import()`: needs a development snapshot run with `--enable=import-function` (build_scad.py passes it).
Its `bolt()` is positive geometry meant for `difference()`; check its direction in the renders.

### Round-Anything (MIT) — fillets on 2D profiles
`use <../../vendor/Round-Anything/polyround.scad>`: `polyRound([[x,y,r],...])`, `polyRoundExtrude()`,
`beamChain()`, `shell2d()`. Best for organic-looking functional profiles (hooks, clips, handles).

### Gridfinity Rebuilt (MIT) — not vendored
https://github.com/kennetek/gridfinity-rebuilt-openscad. Add as a submodule if a job needs Gridfinity bins.

## Copyleft (reference and fit checks only; do NOT include in sold designs)
- **NopSCADlib (GPL-3.0)** — https://github.com/nophead/NopSCADlib. Accurate models of real screws, PCBs, connectors, fans, displays. Useful as `%` ghost geometry to check fit. Not vendored by default.
- **Constructive (GPL-2.0)** — ideas for designing parts that fit together.

## Model sites (inspiration; license per model)
Printables, MakerWorld, Thingiverse. Licenses vary by model and are often CC BY-NC (no commercial use).
Record source + license in spec.md before borrowing any geometry; for `for_sale: true` jobs, only CC0, CC BY, CC BY-SA, MIT, BSD or similar.

## Our own layer: `lib/print_lib.scad`
P2S constants and helpers that the libraries above do not cover the way we want:
fastener tables (`heatset_d("M3")`, `clearance_d`, `selftap_d`, `head_d`, `nut_flats`), `heatset_cut`,
`screw_cut`, `hole_cut` (with elephant-foot chamfer), `teardrop_cut`, `rounded_box`, `standoff`/`pcb_standoffs`,
`vent_slots_cut`, `label`, `enclosure_base`/`enclosure_lid` with `enc_outer`/`enc_boss_xy`, `wall_opening_cut`/`wall_round_cut`,
`gusset`, `slot_cut`, `inside_fillet_x`. It coexists with BOSL2 (both can be included).
