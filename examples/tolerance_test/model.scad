// Calibration print: find the real clearances for YOUR printer, filament and settings.
// Print both parts (part="all"), then try each peg in each hole and record:
//   * the tightest hole a peg PRESSES into     -> clearances_mm.press_fit
//   * the tightest hole a peg SLIDES through   -> clearances_mm.slide_fit
//   * whether a nominal 10.0 mm hole measures small (calipers) -> hole_compensation_mm
// Update config/printer.json and CLR_* in lib/print_lib.scad, and $slop for BOSL2 parts.
// Holes and pegs are identified by notches: 1 notch = first clearance in the list, etc.
include <../../lib/print_lib.scad>

part = "all";                          // ["all", "plate", "pegs"]
clearances = [0.00, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40];   // per side, mm
d_nom   = 10;                          // nominal peg diameter
pitch   = 16;
plate_t = 4;
peg_h   = 10;

n = len(clearances);

module notches(k, side_len) {          // k small V notches along an edge, for identification
  for (i = [0 : k - 1]) translate([i * 2.2 - (k - 1) * 1.1, 0, -EPS])
    rotate([0, 0, 45]) cube([1.2, 1.2, 50], center = true);
}

module plate() {
  w = pitch * n + 4; h = pitch + 8;
  difference() {
    rounded_box([w, h, plate_t], 2);
    for (i = [0 : n - 1]) {
      x = 2 + pitch / 2 + i * pitch;
      translate([x, h / 2, 0]) hole_cut(d_nom + 2 * clearances[i], plate_t, chamfer = 0.4);
      translate([x, 0, 0]) notches(i + 1);                       // notches on the front edge
    }
  }
}

module peg(i) {
  difference() {
    union() {
      cylinder(d = d_nom, h = peg_h, $fn = fn_for(d_nom));
      // grip tab so the peg is easy to hold and its identity is visible
      translate([-d_nom / 2, -2, 0]) cube([d_nom, 4 + d_nom / 2 + 6, 2]);
    }
    translate([0, d_nom / 2 + 8, 0]) notches(i + 1);
  }
  // the peg's first layers are inside the tab, so elephant foot never reaches the tested diameter
}

module pegs() { for (i = [0 : n - 1]) translate([i * pitch, 0, 0]) peg(i); }

if (part == "plate") plate();
else if (part == "pegs") pegs();
else { plate(); translate([2 + pitch / 2, pitch + 20, 0]) pegs(); }
