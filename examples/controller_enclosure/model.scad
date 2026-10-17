// Example: 12 V LED-controller enclosure (ESP32 on a 70x50 perfboard).
// Two parts: base (heat-set inserts in corner bosses) and screw-down lid.
// Build:  python tools/build_scad.py examples/controller_enclosure/model.scad --parts base,lid,lid_installed
// Fit:    python tools/fit_check.py examples/controller_enclosure/out/base.stl \
//                                   examples/controller_enclosure/out/lid_installed.stl --contact-ok
include <../../lib/print_lib.scad>

/* [Part] */
part = "all";              // ["all", "base", "lid", "assembled", "base_installed", "lid_installed"]

/* [Interior] */
inner   = [86, 62, 32];    // usable space: board + wiring room
wall    = 2.4;             // 6 perimeters at 0.4
floor_t = 2.4;
lid_t   = 2.4;
r       = 4;
screw   = "M3";

/* [Board] */
pcb       = [70, 50];
pcb_hole_inset = 3;
pcb_gap   = 6;             // standoff height
pcb_xy    = [wall + (inner[0] - pcb[0]) / 2, wall + (inner[1] - pcb[1]) / 2];

/* [Openings] */
dc_jack_d    = 8.2;        // panel-mount 5.5x2.1 barrel jack
gland_d      = 12.6;       // PG7 cable gland
usb_slot     = [11, 5];    // USB-C cable access
label_txt    = "LED CTRL";

outer = enc_outer(inner, wall, floor_t);
z_mid = floor_t + inner[2] / 2;

module base() {
  difference() {
    union() {
      enclosure_base(inner, wall, floor_t, r, screw);
      pcb_standoffs([for (x = [pcb_hole_inset, pcb[0] - pcb_hole_inset],
                          y = [pcb_hole_inset, pcb[1] - pcb_hole_inset])
                     [pcb_xy[0] + x, pcb_xy[1] + y]],
                    h = pcb_gap, z0 = floor_t - EPS, m = "M2.5");
    }
    wall_round_cut(outer, wall, "front", outer[0] * 0.25, z_mid, dc_jack_d);
    wall_round_cut(outer, wall, "back",  outer[0] * 0.70, z_mid, gland_d);
    wall_opening_cut(outer, wall, "right", outer[1] / 2, floor_t + pcb_gap + 4, usb_slot, 2.4);
    // vents on the left wall, kept clear of the corner bosses
    translate([0, outer[1] / 2 - 2.5 * 4, floor_t + 8]) rotate([0, 0, 90])
      vent_slots_cut(count = 6, slot = [2, 14], pitch = 4, thickness = wall * 4);
  }
}

module lid() {
  difference() {
    enclosure_lid(inner, wall, lid_t, r, screw);
    // recessed label on the outside face (bed side). The lid flips about X when installed,
    // so mirror in Y here to make the text read correctly from above.
    translate([outer[0] / 2, outer[1] / 2, -EPS]) mirror([0, 1, 0]) label(label_txt, size = 8, depth = 0.6);
  }
}

module lid_installed() translate([0, outer[1], outer[2] + lid_t]) rotate([180, 0, 0]) lid();

if (part == "base" || part == "base_installed") base();   // base prints in assembly position
else if (part == "lid") lid();
else if (part == "lid_installed") lid_installed();        // for tools/fit_check.py
else if (part == "assembled") { base(); %lid_installed(); }
else { base(); translate([outer[0] + 10, 0, 0]) lid(); }
