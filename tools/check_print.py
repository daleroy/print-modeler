#!/usr/bin/env python3
"""Printability check for FDM (default: Bambu Lab P2S, see config/printer.json).

Usage:
  python tools/check_print.py part.stl [--material PETG] [--infill 0.2] [--json]
                              [--orient] [--apply-orient out.stl]

Reports: watertight/manifold state, body count, size vs build volume, overhang area
needing support, bed contact area, thin-wall estimate, filament estimate, and
(with --orient) the best print orientations ranked by support need and stability.

Exit code: 0 = PASS or WARN, 2 = FAIL (blocking problem: not watertight, does not fit).
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config" / "printer.json").read_text())


def load_mesh(path: str) -> trimesh.Trimesh:
    m = trimesh.load(path, force="mesh", process=True)
    if isinstance(m, trimesh.Scene):
        m = m.dump(concatenate=True)
    if not isinstance(m, trimesh.Trimesh) or len(m.faces) == 0:
        raise SystemExit(f"Could not load a mesh from {path}")
    return m


def overhang_stats(m: trimesh.Trimesh, max_deg: float):
    """Area of downward-facing faces steeper than the printable overhang limit, excluding the bed layer."""
    nz = m.face_normals[:, 2]
    zmin = m.bounds[0][2]
    face_zmin = m.vertices[m.faces][:, :, 2].min(axis=1)
    on_bed = face_zmin < zmin + 0.05
    # A face overhangs if its normal points down more than (90 - max_deg) from horizontal.
    limit = -math.sin(math.radians(90 - max_deg))
    over = (nz < limit) & ~on_bed
    bed = on_bed & (nz < -0.99)
    return float(m.area_faces[over].sum()), float(m.area_faces[bed].sum()), over


def thin_wall_stats(m: trimesh.Trimesh, min_wall: float, samples: int = 4000):
    """Estimate local wall thickness by casting rays inward from sampled surface points."""
    try:
        pts, fidx = trimesh.sample.sample_surface_even(m, samples)
    except Exception:
        pts, fidx = trimesh.sample.sample_surface(m, samples)
    if len(pts) == 0:
        return None
    normals = m.face_normals[fidx]
    origins = pts - normals * 1e-3
    try:
        locs, ray_idx, _ = m.ray.intersects_location(origins, -normals, multiple_hits=False)
    except Exception:
        return None
    if len(ray_idx) == 0:
        return None
    d = np.linalg.norm(locs - origins[ray_idx], axis=1)
    d = d[d > 1e-3]
    if len(d) == 0:
        return None
    return {
        "p1_mm": round(float(np.percentile(d, 1)), 2),
        "p5_mm": round(float(np.percentile(d, 5)), 2),
        "median_mm": round(float(np.median(d)), 2),
        "frac_below_min": round(float((d < min_wall).mean()), 4),
    }


def filament_estimate(m: trimesh.Trimesh, material: str, infill: float):
    rho = CFG["materials"].get(material, CFG["materials"]["PLA"])["density_g_cm3"]
    vol = abs(m.volume)  # mm^3
    shell = min(vol, m.area * 0.9)  # ~2 walls + top/bottom skins
    printed = shell + infill * max(vol - shell, 0)
    return round(printed / 1000 * rho, 1), round(vol / 1000, 2)


def candidate_orientations(m: trimesh.Trimesh):
    """Axis-aligned rotations plus the mesh's most probable stable resting poses."""
    cands = []
    for axis, ang in [((1, 0, 0), 0), ((1, 0, 0), 90), ((1, 0, 0), 180), ((1, 0, 0), -90),
                      ((0, 1, 0), 90), ((0, 1, 0), -90)]:
        cands.append(("axis", trimesh.transformations.rotation_matrix(math.radians(ang), axis)))
    try:
        poses, probs = trimesh.poses.compute_stable_poses(m, n_samples=1, threshold=0.02)
        for T, p in list(zip(poses, probs))[:6]:
            cands.append((f"stable p={p:.2f}", T))
    except Exception:
        pass
    return cands


def rank_orientations(m: trimesh.Trimesh, max_deg: float, top: int = 3):
    results = []
    for label, T in candidate_orientations(m):
        mm = m.copy()
        mm.apply_transform(T)
        over, bed, _ = overhang_stats(mm, max_deg)
        h = float(mm.extents[2])
        # Lower is better: support area dominates, then height (time), reward bed contact (adhesion).
        score = over + 0.5 * h - 0.05 * bed
        euler = [round(math.degrees(a), 1) for a in trimesh.transformations.euler_from_matrix(T, "sxyz")]
        results.append({"label": label, "rot_xyz_deg": euler, "support_area_mm2": round(over, 1),
                        "height_mm": round(h, 1), "bed_contact_mm2": round(bed, 1), "score": round(score, 1),
                        "_T": T})
    results.sort(key=lambda r: r["score"])
    dedup, seen = [], set()
    for r in results:
        key = (round(r["support_area_mm2"]), round(r["height_mm"]), round(r["bed_contact_mm2"]))
        if key not in seen:
            seen.add(key)
            dedup.append(r)
    return dedup[:top]


def place_on_bed(m: trimesh.Trimesh):
    b = m.bounds
    bv = CFG["build_volume_mm"]
    m.apply_translation([bv[0] / 2 - (b[0][0] + b[1][0]) / 2, bv[1] / 2 - (b[0][1] + b[1][1]) / 2, -b[0][2]])
    return m


def analyze(path, material, infill, orient):
    m = load_mesh(path)
    max_deg = CFG["max_overhang_deg"]
    issues, warns = [], []

    bodies = m.split(only_watertight=False)
    watertight = bool(m.is_watertight)
    winding = bool(m.is_winding_consistent)
    if not watertight:
        issues.append("Mesh is not watertight (open edges/holes). Slicer may fail or fill unpredictably. "
                      "OpenSCAD: check for coincident faces / missing EPS overlap. Blender: run voxel remesh.")
    if not winding:
        warns.append("Inconsistent face winding (flipped normals).")
    if watertight and m.volume < 0:
        warns.append("Negative volume: normals point inward.")

    ext = m.extents
    bv = np.array(CFG["build_volume_mm"]) - 2 * CFG["safe_margin_mm"]
    fits = bool(np.all(ext <= bv))
    if not fits:
        if np.all(np.sort(ext) <= np.sort(bv)):
            warns.append(f"Extents {ext.round(1).tolist()} exceed the build volume as oriented, but fit if rotated.")
        else:
            issues.append(f"Extents {ext.round(1).tolist()} mm exceed usable build volume {bv.tolist()} mm. Split the part.")

    over, bed, _ = overhang_stats(m, max_deg)
    if bed < 1.0:
        warns.append("Almost no flat bed contact as oriented: needs a flat base, brim, or reorientation.")
    elif bed < 0.02 * m.area:
        warns.append(f"Small bed contact ({bed:.0f} mm^2). Consider a brim or a flat base.")
    if over > 0.05 * m.area:
        warns.append(f"{over:.0f} mm^2 of overhang beyond {max_deg} deg will need supports.")

    if len(bodies) > 1:
        warns.append(f"{len(bodies)} separate bodies. Intended (print plate / print-in-place)? Otherwise union them.")

    thin = thin_wall_stats(m, CFG["min_wall_mm"]) if watertight else None
    if thin and thin["frac_below_min"] > 0.01:
        warns.append(f"{thin['frac_below_min']*100:.1f}% of sampled surface is thinner than "
                     f"{CFG['min_wall_mm']} mm (1st pct {thin['p1_mm']} mm). Thicken or accept fragile spots.")

    grams, vol_cm3 = filament_estimate(m, material, infill) if watertight else (None, None)

    report = {
        "file": str(path),
        "verdict": "FAIL" if issues else ("WARN" if warns else "PASS"),
        "issues": issues,
        "warnings": warns,
        "watertight": watertight,
        "winding_consistent": winding,
        "bodies": len(bodies),
        "triangles": int(len(m.faces)),
        "extents_mm": ext.round(2).tolist(),
        "fits_build_volume": fits,
        "volume_cm3": vol_cm3,
        "surface_area_mm2": round(float(m.area), 1),
        "overhang_area_mm2": round(over, 1),
        "bed_contact_mm2": round(bed, 1),
        "thickness": thin,
        "material": material,
        "infill": infill,
        "est_filament_g": grams,
    }
    if orient:
        ranked = rank_orientations(m, max_deg)
        report["orientations"] = [{k: v for k, v in r.items() if k != "_T"} for r in ranked]
        report["_best_T"] = ranked[0]["_T"] if ranked else None
    return m, report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mesh")
    ap.add_argument("--material", default=CFG["default_material"])
    ap.add_argument("--infill", type=float, default=CFG["default_infill"])
    ap.add_argument("--orient", action="store_true", help="rank candidate print orientations")
    ap.add_argument("--apply-orient", metavar="OUT", help="write mesh rotated to the best orientation, centered on bed")
    ap.add_argument("--json", action="store_true", help="print JSON only")
    a = ap.parse_args()

    m, rep = analyze(a.mesh, a.material, a.infill, a.orient or bool(a.apply_orient))
    T = rep.pop("_best_T", None)
    if a.apply_orient and T is not None:
        mm = m.copy()
        mm.apply_transform(T)
        place_on_bed(mm).export(a.apply_orient)
        rep["oriented_output"] = a.apply_orient

    if a.json:
        print(json.dumps(rep, indent=2))
    else:
        print(f"[{rep['verdict']}] {rep['file']}")
        print(f"  size {rep['extents_mm']} mm | volume {rep['volume_cm3']} cm3 | ~{rep['est_filament_g']} g {a.material} @ {int(a.infill*100)}%")
        print(f"  watertight={rep['watertight']} bodies={rep['bodies']} tris={rep['triangles']}")
        print(f"  overhang needing support: {rep['overhang_area_mm2']} mm2 | bed contact: {rep['bed_contact_mm2']} mm2")
        if rep["thickness"]:
            t = rep["thickness"]
            print(f"  wall thickness: 1st pct {t['p1_mm']} mm, median {t['median_mm']} mm")
        for i in rep["issues"]:
            print(f"  FAIL: {i}")
        for w in rep["warnings"]:
            print(f"  WARN: {w}")
        for i, o in enumerate(rep.get("orientations", []), 1):
            print(f"  orient #{i}: rot {o['rot_xyz_deg']} support {o['support_area_mm2']} mm2, "
                  f"height {o['height_mm']} mm, bed {o['bed_contact_mm2']} mm2 ({o['label']})")
        if "oriented_output" in rep:
            print(f"  wrote {rep['oriented_output']}")
    sys.exit(2 if rep["verdict"] == "FAIL" else 0)


if __name__ == "__main__":
    main()
