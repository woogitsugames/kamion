"""Offline geometry preview for drive s24 #13/#15; never builds a world or starts Unity.

uv run --project tools/worldgen python tools/worldgen/qa/preview_embankment_s24.py \
    --baseline <commit-before-fix> --output artifacts/embankment-cli
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LightSource
import numpy as np
import shapely

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from terrain_mesh import conform as CF
from roads import standards as S
from streetscape import far_field as FF


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = subprocess.check_output(["git", "show", f"{args.baseline}:tools/worldgen/streetscape/far_field.py"], text=True)
    fn = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "_add_pylon")
    scope = dict(vars(FF))
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "baseline_pylon", "exec"), scope)

    jj, ii = np.mgrid[:129, :129]
    along = np.array([np.cos(np.deg2rad(23.)), np.sin(np.deg2rad(23.))])
    out = np.array([-along[1], along[0]])
    poly = shapely.Polygon([along * a + out * b for a, b in ((-150, -5.3), (150, -5.3), (150, 5.3), (-150, 5.3))])
    hf = SimpleNamespace(z=np.full((129, 129), 96.), x0=-64., y1=64.)
    mask = shapely.intersects_xy(poly, ii - 64., 64. - jj)
    road = np.where(mask, 100., -np.inf)
    old, da = CF.conform(hf, road, mask)
    old = CF.tidy(old, road, mask, da)
    new, db = CF.conform(hf, road, mask, footprint=poly)
    new = CF.tidy(new, road, mask, db, smooth_slopes=False)
    exact = shapely.distance(shapely.points(ii - 64., 64. - jj), poly)
    expected = np.maximum(hf.z, 99.97 - np.maximum(0., exact - S.BERM_W) / S.EMBANKMENT_SLOPE)
    band = (exact > 2.5) & (exact < 5.)
    fig, axes = plt.subplots(2, 3, figsize=(12, 8), dpi=80, constrained_layout=True)
    for ax, z, title in zip(axes[0, :2], (old, new), ("Skarpa przed (EDT + filtr)", "Skarpa po (obrys ciągły)")):
        light = LightSource(azdeg=315, altdeg=20).hillshade(z, vert_exag=2.)
        rgb = light[..., None] * np.array([.55, .65, .38])
        rgb[mask] = [.28, .28, .28]
        ax.imshow(rgb, extent=(-64, 64, -64, 64))
        ax.set(xlim=(-35, 35), ylim=(-35, 35), title=title, xlabel="E [m]", ylabel="N [m]")
    axes[0, 2].hist((old - expected)[band], bins=40, alpha=.6, label="przed")
    axes[0, 2].hist((new - expected)[band], bins=40, alpha=.6, label="po")
    axes[0, 2].set(title="Błąd profilu 2,5–5 m od drogi", xlabel="odchyłka [m]", ylabel="węzły")
    axes[0, 2].legend()

    counts = []
    for ax, add, title in zip(axes[1, :2], (scope["_add_pylon"], FF._add_pylon), ("Pylon przed", "Pylon po")):
        elev = FF.BorderElevation(1024., [100.] * 2, [100.] * 2, [100.] * 2, [100.] * 2)
        sectors = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
        add(sectors, {"e": 1200., "n": 0., "h": 28.}, elev, 1024., "High", yaw=.4)
        p = sectors["far_east"].primitives()[0]
        v, t = p["V"].copy(), p["T"]
        counts.append(len(t))
        v[:, 0] -= np.mean(v[:, 0])
        v[:, 2] -= 100.
        ax.add_collection(PolyCollection(v[t][:, :, [0, 2]], facecolors=".3", edgecolors="none"))
        ax.autoscale_view()
        ax.set_aspect("equal")
        ax.set(title=f"{title}: {len(t)} tris", xlabel="E [m]", ylabel="wysokość [m]")
    metrics = {"profile_max_error_m_before": float(np.max(abs(old[band] - expected[band]))),
               "profile_max_error_m_after": float(np.max(abs(new[band] - expected[band]))),
               "pylon_triangles_before_after": counts,
               "baseline": args.baseline, "validation": "synthetic geometry, not a Unity render"}
    axes[1, 2].axis("off")
    axes[1, 2].text(0, .9, "Podgląd geometrii Python\nDane syntetyczne / 1 m\nBez Unity i build_world\n\n"
                    f"Maks. błąd przed: {metrics['profile_max_error_m_before']:.3f} m\n"
                    f"Maks. błąd po: {metrics['profile_max_error_m_after']:.3g} m\n"
                    "Obrys i wierzchołki jezdni\npozostają bez zmian.", va="top")
    fig.savefig(args.output / "comparison.png")
    plt.close(fig)
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
