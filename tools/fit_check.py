#!/usr/bin/env python3
"""Check how two mating parts fit, given both meshes in their ASSEMBLED positions.

Usage:
  python tools/fit_check.py base_installed.stl lid_installed.stl [--min-gap 0.15]

Reports interference volume (overlap, should be ~0) and the minimum clearance between
the parts, plus where the tightest spot is. Use the SCAD convention of exporting
part="<name>_installed" for each part in assembly coordinates.
Exit code 2 if parts interfere or the tightest gap is below --min-gap.
"""
import argparse
import sys

import numpy as np
import trimesh


def load(p):
    m = trimesh.load(p, force="mesh")
    if isinstance(m, trimesh.Scene):
        m = m.dump(concatenate=True)
    return m


def interference(a, b):
    try:
        import manifold3d as mf
        def to_mf(m):
            return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                                       tri_verts=np.asarray(m.faces, np.uint32)))
        inter = to_mf(a) ^ to_mf(b)
        return float(inter.volume())
    except Exception:
        try:
            return float(a.intersection(b).volume)
        except Exception:
            return None


def min_gap(a, b, samples=20000):
    pa, _ = trimesh.sample.sample_surface_even(a, samples)
    pb, _ = trimesh.sample.sample_surface_even(b, samples)
    _, da, _ = trimesh.proximity.closest_point(b, pa)
    _, db, _ = trimesh.proximity.closest_point(a, pb)
    i, j = int(np.argmin(da)), int(np.argmin(db))
    if da[i] <= db[j]:
        return float(da[i]), pa[i]
    return float(db[j]), pb[j]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--min-gap", type=float, default=0.15, help="smallest acceptable clearance, mm")
    ap.add_argument("--contact-ok", action="store_true",
                    help="parts are meant to touch (e.g. lid resting on rim); only flag interference")
    a = ap.parse_args()
    A, B = load(a.a), load(a.b)
    vol = interference(A, B)
    gap, where = min_gap(A, B)
    bad = False
    print(f"interference volume: {vol if vol is not None else 'n/a'} mm^3")
    if vol is not None and vol > 0.5:
        print("  FAIL: parts overlap. Increase clearance or move geometry.")
        bad = True
    print(f"minimum gap: {gap:.3f} mm near ({where[0]:.1f}, {where[1]:.1f}, {where[2]:.1f})")
    if not a.contact_ok and gap < a.min_gap:
        print(f"  WARN: tighter than {a.min_gap} mm. Fine if these faces are meant to touch (use --contact-ok).")
        bad = True
    sys.exit(2 if bad else 0)


if __name__ == "__main__":
    main()
