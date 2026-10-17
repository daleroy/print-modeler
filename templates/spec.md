---
# Job spec. The print-modeler agent fills this in from your request, then asks only about
# fields marked REQUIRED that it could not work out. Paths may be absolute or ~/...
name: <job-slug>
status: draft            # draft -> modeling -> review -> done
engine: openscad         # openscad | blender (Phase 2)
inputs: []               # source files: STLs to remix, reference photos, existing .scad projects
output_dir:              # where final STL/3MF + report go; blank = this job's out/ folder
material: PLA            # PLA | PETG | ASA | ABS | TPU | PETG-CF
use: indoor              # indoor | outdoor | high-heat | flexible
for_sale: false          # true = shop item: borrowed geometry must allow commercial use
color: single            # single (multi-color 3MF is a later phase)
---

# <Title>

## Purpose
What it does, where it goes, what it holds or attaches to.

## Critical dimensions (REQUIRED)
Measured values with units and how they were measured (calipers, datasheet, photo + reference).
| Feature | Value | Source |
|---|---|---|
|  |  |  |

## Mating parts and fasteners
Things this must fit: boards, connectors, screws, inserts, magnets, other printed parts.

## Constraints
Size limits, load, temperature, water, appearance, print time, assembly order.

## Borrowed geometry and licenses
| Source | URL / path | License | Commercial OK? |
|---|---|---|---|

## Decisions log
- <date>: <decision and why>

## Open questions
- 
