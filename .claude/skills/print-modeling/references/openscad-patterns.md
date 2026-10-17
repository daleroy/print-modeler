# OpenSCAD patterns for this repo

Worked examples (read the closest one before starting a similar job):
- `examples/controller_enclosure/` — two-part screw-lid enclosure: heat-set bosses, PCB standoffs, wall cutouts, vents, recessed lid label, `_installed` parts for fit checks.
- `examples/rod_clip/` — 2D profile extruded on its side; BOSL2 teardrops for horizontal screw holes; fillets via `offset()`.
- `examples/tolerance_test/` — calibration print; multi-body plate with identification notches.

## File skeleton
```openscad
include <../../vendor/BOSL2/std.scad>      // only if BOSL2 is used
include <../../lib/print_lib.scad>

/* [Part] */
part = "all";            // ["all", "base", "lid", "assembled", "base_installed", "lid_installed"]

/* [Critical dimensions] */
board = [70, 50];        // mm, ESP32 perfboard, calipers 2026-10-16
...
$slop = CLR_PRESS;

module base() { ... }    // print orientation, z = 0 is the bed
module lid()  { ... }
module lid_installed() translate([...]) rotate([180, 0, 0]) lid();

if      (part == "base") base();
else if (part == "lid")  lid();
else if (part == "lid_installed") lid_installed();
else if (part == "assembled") { base(); %lid_installed(); }
else    { base(); translate([outer[0] + 10, 0, 0]) lid(); }
```

## Coordinate conventions
- X = width (left to right as seen from the front), Y = depth (front y=0, back y=max), Z = up.
- Box-like parts: outer min corner at the origin. Round parts: centered on the Z axis.
- Lids print upside down. Text on the bed face must be `mirror([0,1,0])`'d when the lid flips about X to install, or it reads backwards.
- `wall_opening_cut(outer, wall, face, u, v, size)`: `u` is the absolute coordinate of the opening's center along the wall (x for front/back, y for left/right), `v` is absolute z.

## Booleans
- Always overlap cutters through the surface by `EPS` or more: `translate([0,0,-EPS]) cylinder(h = t + 2*EPS)`.
- Do not union two solids that only touch along a face or edge; overlap them by `EPS`.
- `$fn`: use `fn_for(d)` (24-96 segments by size). Large `$fn` on many small features makes renders crawl.
- `hull()` and `minkowski()` are expensive; prefer BOSL2 `cuboid(rounding=)` over `minkowski()`.

## Importing STLs to modify
```openscad
difference() {
  import("/Users/.../part.stl", convexity = 6);   // path from spec.md inputs
  translate([...]) hole_cut(3.4, 20);
}
```
Run `check_print.py` on the input first: an imported mesh that is not watertight will poison every boolean. Reorient with `check_print.py --orient --apply-orient fixed.stl` before modeling around it.

## Debugging
- `echo()` values; `build_scad.py` prints ECHO and WARNING lines.
- Any `WARNING: Ignoring unknown variable/module` is a bug (usually a typo or a missing include).
- `%` shows ghost geometry in `assembled` views only; it is never exported.
- A non-watertight result: look for coincident faces, zero-thickness walls, or an imported mesh with holes.

## Speed
A development snapshot with the Manifold backend renders in seconds what 2021.01 takes minutes on. If a build takes >60 s, reduce `$fn` on repeated features, avoid `minkowski()`, and build parts separately with `--parts`.
