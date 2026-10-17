// Example: snap-in wall clip for a round rod, pipe or conduit.
// Shows: BOSL2 for 2D fillets + teardrop holes, printing a profile on its side
// so the snap ring has no overhangs and its layers run along the flex direction.
// Build:  python tools/build_scad.py examples/rod_clip/model.scad --material PETG
include <../../vendor/BOSL2/std.scad>
include <../../lib/print_lib.scad>

/* [Rod] */
rod_d     = 22;        // measured outside diameter of the rod
grip      = 0.3;       // ring ID is this much smaller than the rod: snaps and holds
opening   = 0.80;      // mouth width as a fraction of rod_d (smaller = harder snap)

/* [Clip] */
ring_w    = 3.2;       // ring wall: 8 perimeters at 0.4. PETG flexes; PLA may crack below ~3 mm
width     = 15;        // clip thickness = print height
plate     = [50, 4];   // wall plate: length (X) x thickness (Y)
screw     = "M4";      // wall screws (pan or truss head)
screw_dx  = 19;        // screw offset from center
fillet    = 2;

$slop = 0.10;          // BOSL2 fit clearance; calibrate with examples/tolerance_test

r_in  = (rod_d - grip) / 2;
r_out = r_in + ring_w;
cy    = plate[1] + r_in + 0.6;            // ring center: just clear of the plate
half_gap = opening * rod_d / 2;
mouth_ang = asin(min(half_gap / r_in, 0.99));   // half-angle of the opening, from +Y

module profile() {
  // fillet where ring meets plate: close (round inside corners) then open (round outside)
  offset(r = -fillet / 2) offset(r = fillet)  offset(r = -fillet / 2)
  union() {
    translate([-plate[0] / 2, 0]) square(plate);
    difference() {
      translate([0, cy]) circle(r = r_out, $fn = 128);
      translate([0, cy]) circle(r = r_in, $fn = 128);
      // mouth: wedge opening toward +Y
      translate([0, cy]) polygon([[0, 0],
        [ (r_out + 5) * sin(mouth_ang) / cos(mouth_ang) * 1.0 + 0, r_out + 5],
        [-(r_out + 5) * sin(mouth_ang) / cos(mouth_ang) * 1.0 - 0, r_out + 5]]);
    }
  }
  // rounded lips at the mouth so the rod slides in
  for (s = [-1, 1])
    translate([0, cy] + (r_in + ring_w / 2) * [s * sin(mouth_ang), cos(mouth_ang)])
      circle(d = ring_w, $fn = 32);
}

difference() {
  linear_extrude(width) profile();
  // screw holes run along Y through the plate, printed sideways: BOSL2 teardrops need no support
  for (x = [-screw_dx, screw_dx])
    translate([x, plate[1] / 2, width / 2])
      teardrop(d = clearance_d(screw), l = plate[1] + 2, ang = 45, spin = 0);
  // head recess on the ring side so the screw head sits flush with the plate face
  for (x = [-screw_dx, screw_dx])
    translate([x, plate[1] + 0.01, width / 2])
      teardrop(d = head_d(screw) + 0.6, l = 2 * 1.6, ang = 45, anchor = CENTER);
}
