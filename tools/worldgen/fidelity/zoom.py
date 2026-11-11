"""Zoomed fidelity overlays at arbitrary places (ADR 0077): the same layers as run.py, any centre / half-size.

    uv run --project tools/worldgen tools/worldgen/fidelity/zoom.py --region bialystok-industrial-c \
        --out artifacts/islands-r10/zoom --at -283,-197,30,signals --at 565,-695,35,biezenstwa [--plain]

`--plain` also writes the bare orthophoto crop (<name>_ortho.jpg) for before / after / ortho montages.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fidelity import gen as G  # noqa: E402
from fidelity import metrics as Mx  # noqa: E402
from fidelity import ortho as O  # noqa: E402
from fidelity import osm_truth  # noqa: E402
from fidelity import overlays as OV  # noqa: E402
from fidelity.run import REPO, route_edges, yards_polys  # noqa: E402
from roads import pipeline  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--at", action="append", required=True, help="E,N,half_m,name")
    ap.add_argument("--plain", action="store_true")
    a = ap.parse_args(argv)
    reg = pipeline.load_region(a.region)
    rdir = pipeline.REGIONS / a.region
    out = REPO / a.out
    out.mkdir(parents=True, exist_ok=True)
    osm = osm_truth.extract(reg)
    route, _ = route_edges(rdir)
    ortho = O.Ortho(reg)
    g = G.build(a.region)
    ctx = Mx.Ctx(reg, g, osm, ortho, np.array(route["points_en"]))
    yards = yards_polys(rdir, np.array(g.origin))
    rep = []
    gr = g.world.stats.get("gores", {})
    print("gores", gr.get("paved"), "kerb dropped m", gr.get("kerb_dropped_m"), "rejected", len(gr.get("rejected", [])),
          "not built", [x for x in gr.get("gores", []) if not x["built"]], flush=True)
    (out / "gores.json").write_text(json.dumps(gr, indent=1), encoding="utf-8")
    for spec in a.at:
        e, n, half, name = spec.split(",")
        cen, half = (float(e), float(n)), float(half)
        wm = Mx.window_masks(ctx, cen, half, res=0.1 if half <= 60 else 0.2, yards=yards, walk_tris=g.walk_tris)
        gi, miss, imask, mmask = Mx.separations(wm)
        _, gen_only, o_only = Mx.area_diffs(wm)
        notes = [{"xy": x["xy"], "label": f"{x['verdict'][:3]}{x['area_m2']:.0f}"} for x in gi]
        title = f"{name} E {cen[0]:.0f} N {cen[1]:.0f} +-{half:.0f} m | gen separations {len(gi)} | ortho islands on gen {len(miss)}"
        OV.render(out / f"{name}.jpg", wm, g, title, imask, mmask, gen_only, o_only, notes=notes)
        if a.plain:
            im = Image.fromarray(wm["rgb"])
            s = 960 / max(im.size)
            im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS).save(out / f"{name}_ortho.jpg", quality=88)
        rep.append({"name": name, "center_en": cen, "half_m": half, "ortho_src": wm["src"], "gen_separations": gi,
                    "ortho_islands_on_gen": miss})
        print(name, "separations", [(x["verdict"], x["area_m2"], [round(v, 1) for v in x["xy"]]) for x in gi], flush=True)
    (out / "zoom.json").write_text(json.dumps(rep, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()
