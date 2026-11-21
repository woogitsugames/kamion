"""Look-dev preview of the Knyszyn king (ADR 0325) outside Unity: writes the monument (plinth, figure, sundial block) of
`knyszyn_park_props_0227._king` as an OBJ with one object per material, for tools/blender/world/king_preview_0325.py.

  uv run --project tools/worldgen python tools/worldgen/qa/king_preview_0325.py <out.obj> [--low]

Local frame of the file: x = right of the figure, y = its front, z up, ground at z = 0 (metres). QA only.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from streetscape import knyszyn_park_props_0227 as P      # noqa: E402
from streetscape import materials as MAT                   # noqa: E402
from streetscape.buildings_mesh import Acc                 # noqa: E402


SPEC = __import__("json").loads((Path(__file__).resolve().parents[3] / "art-source/world/materials/materials_spec.json")
                                .read_text(encoding="utf-8"))["sets"]


def main():
    out = Path(sys.argv[1])
    layer = "buildings_low" if "--low" in sys.argv else "buildings"
    acc = Acc()
    P._king(acc, layer, [0.0, 0.0], 0.0)
    f, t = P.KING_FORWARD, P.KING_TANGENT
    lines, base = [f"mtllib {out.with_suffix('.mtl').name}"], 1
    mtl = []
    for (lay, mat), items in sorted(acc.d.items()):
        m = MAT.M.get(mat, {"color": [0.05, 0.05, 0.05], "rough": 0.6})
        mtl += [f"newmtl {mat}", "Kd {:.4f} {:.4f} {:.4f}".format(*m["color"]),
                f"Pr {m.get('rough', 0.9)}", f"Pm {m.get('metal', 0.0)}"]
        if m.get("texture_set") in SPEC:          # custom keys read by the Blender preview script only
            tile = SPEC[m["texture_set"]]["tile_m"]
            mtl += [f"#set {m['texture_set']} {tile[0]} {tile[1]} {m.get('set_metal', 0.0)}"]
        for k, (V, T, UV, *_rest) in enumerate(items):
            lines += [f"o {mat}_{k}", f"usemtl {mat}", "s 1"]
            V = np.asarray(V, float)
            L = np.column_stack([V[:, :2] @ t, V[:, :2] @ f, V[:, 2]])
            lines += ["v {:.5f} {:.5f} {:.5f}".format(*p) for p in L]
            lines += ["vt {:.5f} {:.5f}".format(*uv) for uv in np.asarray(UV, float)]
            lines += ["f {0}/{0} {1}/{1} {2}/{2}".format(*(np.asarray(tri) + base)) for tri in T]
            base += len(V)
    out.write_text("\n".join(lines) + "\n", encoding="ascii")
    out.with_suffix(".mtl").write_text("\n".join(mtl) + "\n", encoding="ascii")
    print(out, "triangles", sum(len(i[1]) for items in acc.d.values() for i in items))


if __name__ == "__main__":
    main()
