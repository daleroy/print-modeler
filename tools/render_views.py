#!/usr/bin/env python3
"""Render a mesh to a multi-view PNG contact sheet the agent can look at.

Usage:
  python tools/render_views.py part.stl [-o part_views.png] [--overhangs] [--title "Base v3"] [--size 520]

Views: isometric, front (-Y), right (+X), top, and underside. With --overhangs, faces
steeper than the printer's overhang limit are tinted red so support needs are visible.

Uses a small depth-buffered software rasterizer (numpy only), so it runs anywhere
without OpenSCAD, Blender, or a GPU, and hidden surfaces are handled correctly.
"""
import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config" / "printer.json").read_text())
MAX_FACES = 150000

# title, elevation (deg above XY plane), azimuth (deg, 0 = looking from +X toward origin)
VIEWS = [
    ("Isometric", 30, -55),
    ("Front (from -Y)", 0, -90),
    ("Right (from +X)", 0, 0),
    ("Top (from +Z)", 90, -90),
    ("Underside", -35, -125),
]


def load(path):
    m = trimesh.load(path, force="mesh")
    if isinstance(m, trimesh.Scene):
        m = m.dump(concatenate=True)
    if len(m.faces) > MAX_FACES:
        try:
            m = m.simplify_quadric_decimation(face_count=MAX_FACES)
        except Exception:
            pass
    return m


def camera_basis(elev, azim):
    e, a = math.radians(elev), math.radians(azim)
    fwd = -np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])  # camera looks along fwd
    up_hint = np.array([0, 0, 1.0]) if abs(elev) < 89 else np.array([0, 1.0, 0])
    right = np.cross(fwd, up_hint)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return right, up, fwd


def rasterize(m, colors, elev, azim, size, center, radius):
    right, up, fwd = camera_basis(elev, azim)
    v = m.vertices - center
    sx = (v @ right / radius * 0.5 + 0.5) * (size - 1)
    sy = (0.5 - v @ up / radius * 0.5) * (size - 1)
    depth = v @ fwd  # larger = farther
    img = np.ones((size, size, 3))
    zbuf = np.full((size, size), np.inf)

    F = m.faces
    x0, y0, z0 = sx[F[:, 0]], sy[F[:, 0]], depth[F[:, 0]]
    x1, y1, z1 = sx[F[:, 1]], sy[F[:, 1]], depth[F[:, 1]]
    x2, y2, z2 = sx[F[:, 2]], sy[F[:, 2]], depth[F[:, 2]]
    area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    keep = np.abs(area) > 1e-9
    xmin = np.clip(np.floor(np.minimum(np.minimum(x0, x1), x2)), 0, size - 1).astype(int)
    xmax = np.clip(np.ceil(np.maximum(np.maximum(x0, x1), x2)), 0, size - 1).astype(int)
    ymin = np.clip(np.floor(np.minimum(np.minimum(y0, y1), y2)), 0, size - 1).astype(int)
    ymax = np.clip(np.ceil(np.maximum(np.maximum(y0, y1), y2)), 0, size - 1).astype(int)

    for i in np.nonzero(keep)[0]:
        xs = np.arange(xmin[i], xmax[i] + 1)
        ys = np.arange(ymin[i], ymax[i] + 1)
        if len(xs) == 0 or len(ys) == 0:
            continue
        px, py = np.meshgrid(xs + 0.5, ys + 0.5)
        w0 = ((x1[i] - px) * (y2[i] - py) - (x2[i] - px) * (y1[i] - py)) / area[i]
        w1 = ((x2[i] - px) * (y0[i] - py) - (x0[i] - px) * (y2[i] - py)) / area[i]
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        z = w0 * z0[i] + w1 * z1[i] + w2 * z2[i]
        sub = zbuf[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
        upd = inside & (z < sub)
        if upd.any():
            sub[upd] = z[upd]
            img[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1][upd] = colors[i]

    # silhouette / crease emphasis: darken pixels where depth jumps
    zb = np.where(np.isinf(zbuf), np.nan, zbuf)
    gy, gx = np.gradient(np.nan_to_num(zb, nan=np.nanmax(zb) + radius if np.isfinite(np.nanmax(zb)) else 0))
    edge = (np.hypot(gx, gy) > radius * 0.02) | (np.isnan(zb) ^ np.isnan(np.roll(zb, 1, 0))) | \
           (np.isnan(zb) ^ np.isnan(np.roll(zb, 1, 1)))
    img[edge] *= 0.35
    return img, right, up


def face_colors(m, overhangs, view_fwd):
    n = m.face_normals
    key = np.array([0.4, -0.5, 0.75]); key /= np.linalg.norm(key)
    head = -view_fwd
    shade = 0.25 + 0.45 * np.clip(n @ key, 0, 1) + 0.35 * np.abs(n @ head)
    cols = np.outer(np.clip(shade, 0, 1), [0.58, 0.70, 0.84])
    if overhangs:
        limit = -math.sin(math.radians(90 - CFG["max_overhang_deg"]))
        zmin = m.bounds[0][2]
        on_bed = m.vertices[m.faces][:, :, 2].min(axis=1) < zmin + 0.05
        mask = (n[:, 2] < limit) & ~on_bed
        cols[mask] = np.outer(np.clip(shade[mask], 0, 1), [0.95, 0.35, 0.30])
    return np.clip(cols, 0, 1)


def render(path, out, overhangs=False, title=None, size=520):
    m = load(path)
    lo, hi = m.bounds
    center = (lo + hi) / 2
    radius = np.linalg.norm(hi - lo) / 2 * 1.08
    span = hi - lo

    fig, axes = plt.subplots(2, 3, figsize=(15, 10), dpi=100)
    for ax, (name, elev, azim) in zip(axes.flat, VIEWS):
        _, _, fwd = camera_basis(elev, azim)
        img, right, up = rasterize(m, face_colors(m, overhangs, fwd), elev, azim, size, center, radius)
        ax.imshow(img, extent=[-radius, radius, -radius, radius])
        ax.set_title(name, fontsize=11)
        ax.set_xticks([]); ax.set_yticks([])
        # axis gizmo
        for vec, lab, c in [((1, 0, 0), "X", "#c0392b"), ((0, 1, 0), "Y", "#27ae60"), ((0, 0, 1), "Z", "#2e86de")]:
            d = np.array([np.dot(vec, right), np.dot(vec, up)]) * radius * 0.15
            if np.hypot(*d) > radius * 0.02:
                o = np.array([-radius * 0.8, -radius * 0.8])
                ax.annotate("", xy=o + d, xytext=o, arrowprops=dict(arrowstyle="->", color=c, lw=1.5))
                ax.text(*(o + d * 1.25), lab, color=c, fontsize=9, ha="center", va="center")
        # scale bar: 10 mm (or 1/5 of span, rounded)
        bar = max(1, round(float(span.max()) / 5, -1 if span.max() > 50 else 0))
        ax.plot([radius * 0.45, radius * 0.45 + bar], [-radius * 0.88] * 2, color="k", lw=2)
        ax.text(radius * 0.45 + bar / 2, -radius * 0.8, f"{bar:g} mm", ha="center", fontsize=8)

    ax = axes.flat[5]
    ax.axis("off")
    lines = [title or Path(path).name, "",
             f"extents  X {span[0]:.2f}  Y {span[1]:.2f}  Z {span[2]:.2f} mm",
             f"min corner ({lo[0]:.1f}, {lo[1]:.1f}, {lo[2]:.1f})",
             f"triangles {len(m.faces):,}",
             f"watertight {m.is_watertight}"]
    if m.is_watertight:
        lines.append(f"volume {abs(m.volume) / 1000:.2f} cm3")
    if overhangs:
        lines += ["", f"red = overhang > {CFG['max_overhang_deg']} deg", "(would need support)"]
    ax.text(0.02, 0.95, "\n".join(lines), va="top", family="monospace", fontsize=11)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mesh")
    ap.add_argument("-o", "--out")
    ap.add_argument("--overhangs", action="store_true")
    ap.add_argument("--title")
    ap.add_argument("--size", type=int, default=520, help="pixels per view")
    a = ap.parse_args()
    out = a.out or str(Path(a.mesh).with_suffix("")) + "_views.png"
    print(render(a.mesh, out, a.overhangs, a.title, a.size))


if __name__ == "__main__":
    main()
