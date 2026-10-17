// print_lib.scad — FDM-aware helpers for functional parts and enclosures.
// Tuned for Bambu Lab P2S, 0.4 mm nozzle. Units: mm. Z+ is up, bed at z = 0.
// Values mirror config/printer.json; override any default via module arguments.
//
//   include <../../lib/print_lib.scad>   (from jobs/<name>/model.scad)
//
// Conventions
//   * Every module builds its part IN PRINT ORIENTATION, resting on z = 0.
//   * Box-style modules put the OUTER min corner at the origin.
//   * Modules ending in _cut return negative volume: use them inside difference().

// ---------- constants ----------
NOZZLE      = 0.4;
LAYER       = 0.2;
EPS         = 0.01;          // overlap to avoid coincident faces in booleans
CLR_PRESS   = 0.10;
CLR_SNUG    = 0.15;
CLR_SLIDE   = 0.25;
CLR_LOOSE   = 0.40;
EF_CHAMFER  = 0.4;           // elephant-foot chamfer on first-layer edges

// Metric fastener tables: [name, heatset_d, heatset_depth, clearance_d, selftap_d, head_d, nut_flats, nut_thick]
_FAST = [
  ["M2",   3.2, 4.0, 2.4, 1.8, 4.2, 4.3, 1.8],
  ["M2.5", 3.6, 4.5, 2.9, 2.2, 5.0, 5.3, 2.2],
  ["M3",   4.0, 5.7, 3.4, 2.6, 6.0, 5.8, 2.6],
  ["M4",   5.6, 8.1, 4.5, 3.5, 8.0, 7.3, 3.4]
];
function _f(m) = _FAST[search([m], _FAST, 1, 0)[0]];
function heatset_d(m)     = _f(m)[1];
function heatset_depth(m) = _f(m)[2];
function clearance_d(m)   = _f(m)[3];
function selftap_d(m)     = _f(m)[4];
function head_d(m)        = _f(m)[5];
function nut_flats(m)     = _f(m)[6];
function nut_thick(m)     = _f(m)[7];

// Polygon count: fine enough for fits, not so fine renders crawl.
function fn_for(d) = max(24, min(96, ceil(d * 3.2)));

// ---------- 2D primitives ----------
module rounded_rect(size, r = 2) {
  rr = min(r, min(size[0], size[1]) / 2 - EPS);
  if (rr <= 0) square(size);
  else translate([rr, rr]) offset(r = rr) square([size[0] - 2*rr, size[1] - 2*rr]);
}

// ---------- 3D primitives ----------

// Box with rounded vertical edges and an elephant-foot chamfer at the bottom.
module rounded_box(size, r = 2, chamfer = EF_CHAMFER) {
  c = min(chamfer, size[2] / 2);
  hull() {
    linear_extrude(EPS) translate([c, c]) rounded_rect([size[0] - 2*c, size[1] - 2*c], max(r - c, 0));
    translate([0, 0, c]) linear_extrude(size[2] - c) rounded_rect([size[0], size[1]], r);
  }
}

// Horizontal hole that prints without support: circle + 45-degree peak on top.
// Axis runs along Y, centered at origin. Use inside difference().
module teardrop_cut(d, len, center = true) {
  rotate([-90, 0, 0]) translate([0, 0, center ? -len/2 : 0])
    linear_extrude(len) rotate(-90)
      union() {
        circle(d = d, $fn = fn_for(d));
        rotate(-45) square(d / 2);
      }
}

// Vertical hole with optional chamfer at the bed (z=0) to offset elephant foot.
module hole_cut(d, h, chamfer = 0.5) {
  translate([0, 0, -EPS]) cylinder(d = d, h = h + 2*EPS, $fn = fn_for(d));
  if (chamfer > 0)
    translate([0, 0, -EPS]) cylinder(d1 = d + 2*chamfer, d2 = d, h = chamfer + EPS, $fn = fn_for(d));
}

// Pocket for a tapered brass heat-set insert, opening at the top (z = h).
module heatset_cut(m = "M3", h = 10) {
  d = heatset_d(m); dep = heatset_depth(m);
  translate([0, 0, h - dep - 0.5]) cylinder(d = d, h = dep + 0.5 + EPS, $fn = fn_for(d));
  translate([0, 0, h - 0.4]) cylinder(d1 = d, d2 = d + 0.8, h = 0.4 + EPS, $fn = fn_for(d)); // lead-in
}

// Through-hole for a screw, optional countersink at z = 0 (bed side).
module screw_cut(m = "M3", h = 3, countersink = true) {
  d = clearance_d(m); hd = head_d(m);
  translate([0, 0, -EPS]) cylinder(d = d, h = h + 2*EPS, $fn = fn_for(d));
  if (countersink)
    translate([0, 0, -EPS]) cylinder(d1 = hd + 0.4, d2 = d, h = (hd + 0.4 - d) / 2, $fn = fn_for(hd));
}

// Hex nut trap from the bottom (z = 0), with a sacrificial bridge layer above it.
module nut_trap_cut(m = "M3", extra = 0.2) {
  f = nut_flats(m) + extra; t = nut_thick(m) + extra;
  translate([0, 0, -EPS]) cylinder(d = f / cos(30), h = t + EPS, $fn = 6);
}

// Cylindrical standoff for PCB mounting; hole for self-tap or heat-set.
module standoff(h = 5, od = 6, m = "M2.5", insert = false) {
  difference() {
    cylinder(d = od, h = h, $fn = fn_for(od));
    if (insert) heatset_cut(m, h);
    else translate([0, 0, 1]) cylinder(d = selftap_d(m), h = h, $fn = fn_for(od));
  }
}

// Standoffs at each [x, y] in holes[], rising from z = z0.
module pcb_standoffs(holes, h = 5, z0 = 0, od = 6, m = "M2.5", insert = false) {
  for (p = holes) translate([p[0], p[1], z0]) standoff(h, od, m, insert);
}

// Row of vent slots for subtracting through a wall that lies in the XZ plane (front/back walls).
module vent_slots_cut(count = 6, slot = [2, 15], pitch = 4, thickness = 10) {
  for (i = [0 : count - 1])
    translate([i * pitch, -thickness / 2, 0])
      hull() {
        translate([slot[0] / 2, 0, slot[0] / 2]) rotate([-90, 0, 0]) cylinder(d = slot[0], h = thickness, $fn = 24);
        translate([slot[0] / 2, 0, slot[1] - slot[0] / 2]) rotate([-90, 0, 0]) cylinder(d = slot[0], h = thickness, $fn = 24);
      }
}

// Raised or recessed text. depth > 0 raises, use inside difference() to recess.
module label(txt, size = 6, depth = 0.6, font = "Liberation Sans:style=Bold", halign = "center") {
  linear_extrude(depth) text(txt, size = size, font = font, halign = halign, valign = "center");
}

// ---------- Enclosures ----------
// An enclosure is described by:
//   inner = [x, y, z]  usable interior (z = floor top to lid underside)
//   wall, floor, lid_t thicknesses; r = outer corner radius
// Outer size = [inner.x + 2*wall, inner.y + 2*wall, floor + inner.z]  (base only)

function enc_outer(inner, wall, floor) = [inner[0] + 2*wall, inner[1] + 2*wall, floor + inner[2]];

// Corner screw-boss centers (XY), inset so a boss of diameter boss_d hugs the inner corner.
function enc_boss_xy(inner, wall, boss_d) =
  let(o = wall + boss_d / 2, ox = inner[0] + 2*wall - o, oy = inner[1] + 2*wall - o)
  [[o, o], [ox, o], [o, oy], [ox, oy]];

// Base shell with four corner bosses holding heat-set inserts for lid screws.
module enclosure_base(inner, wall = 2, floor = 2, r = 3, m = "M3", boss_d = 0) {
  bd = boss_d > 0 ? boss_d : heatset_d(m) + 3.2;
  outer = enc_outer(inner, wall, floor);
  difference() {
    union() {
      difference() {
        rounded_box(outer, r);
        translate([wall, wall, floor]) linear_extrude(inner[2] + EPS)
          rounded_rect([inner[0], inner[1]], max(r - wall, 0.5));
      }
      // corner bosses, hulled into the corner for stiffness. The anchor sits mid-wall so the
      // hull's flat sides cross the wall instead of lying on its inner face (coincident faces
      // leave zero-thickness slivers); clipping to the shell keeps the hull inside the outer rounding.
      intersection() {
        rounded_box(outer, r);
        union() for (p = enc_boss_xy(inner, wall, bd))
          hull() {
            translate([p[0], p[1], 0]) cylinder(d = bd, h = outer[2], $fn = fn_for(bd));
            translate([p[0] < outer[0] / 2 ? wall / 2 : outer[0] - wall / 2 - EPS,
                       p[1] < outer[1] / 2 ? wall / 2 : outer[1] - wall / 2 - EPS, 0])
              cube([EPS, EPS, outer[2]]);
          }
      }
    }
    for (p = enc_boss_xy(inner, wall, bd))
      translate([p[0], p[1], 0]) heatset_cut(m, outer[2]);
  }
}

// Lid, built upside-down for printing: flat top on the bed, locating lip pointing up.
// The lip drops inside the base walls with clearance `clr` and is notched around bosses.
module enclosure_lid(inner, wall = 2, lid_t = 2, r = 3, m = "M3", boss_d = 0,
                     lip_h = 3, lip_t = 1.2, clr = CLR_SLIDE) {
  bd = boss_d > 0 ? boss_d : heatset_d(m) + 3.2;
  outer_xy = [inner[0] + 2*wall, inner[1] + 2*wall];
  bosses = enc_boss_xy(inner, wall, bd);
  difference() {
    union() {
      rounded_box([outer_xy[0], outer_xy[1], lid_t], r);
      // lip ring
      translate([0, 0, lid_t - EPS]) linear_extrude(lip_h + EPS)
        difference() {
          translate([wall + clr, wall + clr])
            rounded_rect([inner[0] - 2*clr, inner[1] - 2*clr], max(r - wall - clr, 0.5));
          translate([wall + clr + lip_t, wall + clr + lip_t])
            rounded_rect([inner[0] - 2*(clr + lip_t), inner[1] - 2*(clr + lip_t)], max(r - wall - clr - lip_t, 0.5));
          for (p = bosses) translate(p) circle(d = bd + 2*clr + 1, $fn = fn_for(bd));
        }
    }
    for (p = bosses) translate([p[0], p[1], 0]) screw_cut(m, lid_t, countersink = true);
  }
}

// Cut an opening through one side wall of an enclosure base.
//   face: "front" (y=0), "back" (y=max), "left" (x=0), "right" (x=max)
//   u: absolute coordinate of the opening CENTER along the wall (x for front/back, y for left/right)
//   v: absolute Z of the opening CENTER
//   size = [width, height]; r = corner radius (use r >= height/2 for round/obround holes)
module wall_opening_cut(outer, wall, face, u, v, size, r = 0.5) {
  t = wall * 3;
  module prof() translate([-size[0] / 2, -size[1] / 2]) rounded_rect(size, r);
  if (face == "front")      translate([u, -wall, v])            rotate([-90, 0, 0]) mirror([0,1,0]) linear_extrude(t) prof();
  else if (face == "back")  translate([u, outer[1] - 2*wall, v]) rotate([-90, 0, 0]) mirror([0,1,0]) linear_extrude(t) prof();
  else if (face == "left")  translate([-wall, u, v])            rotate([90, 0, 90]) linear_extrude(t) prof();
  else if (face == "right") translate([outer[0] - 2*wall, u, v]) rotate([90, 0, 90]) linear_extrude(t) prof();
}

// Round hole through a side wall (cable glands, DC jacks, buttons). Same addressing as above.
module wall_round_cut(outer, wall, face, u, v, d) {
  wall_opening_cut(outer, wall, face, u, v, [d, d], d / 2);
}

// ---------- Functional-part helpers ----------

// Gusset (triangular brace) in the XZ plane, thickness along Y.
module gusset(w = 15, h = 15, t = 3) {
  rotate([90, 0, 0]) translate([0, 0, -t / 2]) linear_extrude(t) polygon([[0, 0], [w, 0], [0, h]]);
}

// Slot for adjustable mounting (obround), vertical through-cut.
module slot_cut(len = 10, d = 3.4, h = 10) {
  hull() for (x = [0, len]) translate([x, 0, -EPS]) cylinder(d = d, h = h + 2*EPS, $fn = fn_for(d));
}

// Fillet a 90-degree inside edge along X (concave corner at origin between XY floor and XZ wall).
module inside_fillet_x(len, r = 2) {
  difference() {
    cube([len, r, r]);
    translate([-EPS, r, r]) rotate([0, 90, 0]) cylinder(r = r, h = len + 2*EPS, $fn = fn_for(2*r));
  }
}

// Debug: ghosted assembly view helper (not for export).
module ghost() { %children(); }
