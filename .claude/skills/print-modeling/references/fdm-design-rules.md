# FDM design rules (P2S, 0.4 mm nozzle, 0.2 mm layers)

Numbers here are starting points. `config/printer.json` holds the live values, updated
after printing `examples/tolerance_test`. Prefer the config when they differ.

## Walls and features
| Feature | Minimum | Recommended | Notes |
|---|---|---|---|
| Wall (vertical) | 0.8 mm (2 lines) | 1.6-2.4 mm (4-6 lines) | Make walls a multiple of ~0.42 mm so the slicer does not leave gaps |
| Floor / roof | 0.6 mm (3 layers) | 1.2-2.4 mm | |
| Boss around a screw | wall >= 1.6 mm around the hole | 2 mm+ | Heat-set bosses: OD >= insert hole + 3.2 mm |
| Pin / peg diameter | 2 mm | 3 mm+ | Thin vertical pins snap off along layer lines |
| Embossed/engraved text | 4 mm cap height, 0.4 mm depth | 6-8 mm bold, 0.6 mm | On top faces or the bed face (mirrored correctly); side-wall text blurs |
| Gap between parts printed in place | 0.3 mm | 0.35-0.4 mm | |

## Overhangs, bridges, holes
- Overhangs up to 45 deg from vertical print without support. The checker and previews flag steeper downward faces.
- Bridges up to ~25 mm are fine in PLA/PETG. Longer bridges sag; add a support rib or reorient.
- **Horizontal holes:** use a teardrop (BOSL2 `teardrop()` or `teardrop_cut()`) for anything over ~6 mm, so the top of the hole is a 45 deg peak instead of a flat bridge.
- **Vertical holes print undersized** by ~0.1-0.2 mm. Add `hole_compensation_mm` to holes that must take a pin or screw shank.
- **Elephant foot:** the first layers squish outward ~0.2-0.4 mm. Chamfer bed-side edges 0.4 mm (`rounded_box` does this) and chamfer bed-side hole openings (`hole_cut(chamfer=)`), or the part will not fit its mate.
- Counterbores on the bed side create a floating ceiling; use a countersink, or add a 0.2 mm sacrificial bridge layer you drill through.

## Strength and orientation
- Layers are the weak axis: parts break by peeling layers apart. Orient so the main load and any flexing (snap fits, clips, hinges) run **along** layers, not across them.
- Snap fits and clips: PETG or TPU, never thin PLA. Ring/hook thickness ~3 mm for PETG at 20-30 mm spans. Print so the flexing beam lies in the XY plane.
- Screw threads printed directly are only good for >= M8 or for low-cycle use. For M2-M5 use heat-set inserts (best), captured nuts, or self-tapping into plain holes (`selftap_d`).
- Prefer fillets (r >= 1 mm) on inside corners of load paths; sharp inside corners crack.

## Fits (per side)
| Fit | Clearance | Use |
|---|---|---|
| Press | 0.10 | Pins that should stay put |
| Snug | 0.15 | Lids that should not rattle, sockets |
| Slide | 0.25 | Lids that come off by hand, sliding parts |
| Loose | 0.40 | Anything assembled after painting, or across two printed tolerances |

## Material notes
- PLA: default, stiff, indoor only. Softens around 55 C (hot cars, sunny windows).
- PETG: tougher, slight flex, handles mild heat and outdoor shade. Default for enclosures and clips.
- ASA: outdoor/UV, heat to ~90 C. The enclosed P2S handles it; expect ~0.5% shrink on long parts.
- TPU: flexible gaskets, bumpers, grips. Avoid tight tolerances and bridges.
- Outdoor electronics: ASA or PETG, gasket or lip with 0.15 mm fit, cable glands, drip-down openings, vent with a labyrinth rather than straight slots.

## Before declaring done
- Watertight, single body (unless intended)
- Fits 246 x 246 x 246 mm (5 mm margin)
- No unintended overhang red in the previews
- Bed face is flat and large enough; add a brim note in the report if it is not
- Every mating dimension traced to a source in spec.md
