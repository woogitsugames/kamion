"""ADR 0175: quick control renders of the regulation-relevant views straight from the generators (source pieces with
the authoring materials, no bake): rear, lamps close-up, side, front, corners.

    blender -b --factory-startup --python tools/blender/truck/regs_render.py -- --what tractor|trailer --out ABS_DIR \
        [--samples 48] [--tag before] [--views a,b]
"""
import argparse
import os
import sys
import tempfile

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "exterior"))
sys.path.insert(0, os.path.join(HERE, "trailer"))

# trailer: kingpin frame (rear end y = -12.0); tractor: A2 frame (front axle origin, rear end y = -4.55)
CAMS = {
    "trailer": {
        "tyl": dict(loc=(0.0, -19.5, 1.9), target=(0.0, -12.0, 2.0), lens=50),
        "tyl_lampy": dict(loc=(0.55, -14.6, 1.05), target=(0.62, -12.0, 0.80), lens=60),
        "tyl_34": dict(loc=(5.2, -17.5, 2.3), target=(0.4, -11.0, 1.8), lens=45),
        "bok": dict(loc=(-24.0, -5.2, 2.0), target=(0.0, -5.2, 2.0), ortho=15.5),
        "bok_tyl_naroznik": dict(loc=(-4.2, -13.2, 3.3), target=(-1.27, -11.5, 3.45), lens=60),
        "bok_przod_naroznik": dict(loc=(-4.2, 2.6, 3.3), target=(-1.27, 1.1, 3.45), lens=60),
        "bok_obrysowe": dict(loc=(-3.6, -8.4, 1.25), target=(-1.25, -7.0, 1.05), lens=50),
        "przod": dict(loc=(3.0, 6.2, 1.9), target=(0.5, 1.6, 1.9), lens=40),
        "przod_lampa": dict(loc=(1.9, 3.0, 1.55), target=(1.1, 1.6, 1.40), lens=70),
        "tablica": dict(loc=(0.0, -13.3, 0.87), target=(0.0, -12.0, 0.87), lens=70),
    },
    "tractor": {
        "tyl": dict(loc=(0.0, -9.5, 1.3), target=(0.0, -4.5, 0.9), lens=50),
        "tyl_lampy": dict(loc=(-0.3, -6.4, 1.0), target=(-0.75, -4.5, 0.80), lens=60),
        "tyl_34": dict(loc=(4.6, -8.6, 2.0), target=(0.3, -2.6, 1.3), lens=45),
        "bok": dict(loc=(-20.0, -1.4, 1.9), target=(0.0, -1.4, 1.9), ortho=7.2),
        "bok_odblaski": dict(loc=(-4.2, -3.6, 0.9), target=(-1.25, -2.6, 0.6), lens=60),
        "przod": dict(loc=(0.0, 8.5, 1.9), target=(0.0, 1.4, 1.9), lens=45),
        "przod_34": dict(loc=(5.0, 6.5, 2.2), target=(0.2, 0.2, 1.8), lens=45),
        "tablica_przod": dict(loc=(0.0, 2.7, 0.84), target=(0.0, 1.4, 0.84), lens=70),
        "tablica_tyl": dict(loc=(0.68, -5.8, 0.66), target=(0.68, -4.5, 0.66), lens=70),
    },
}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--what", required=True, choices=["tractor", "trailer"])
    p.add_argument("--out", required=True)
    p.add_argument("--samples", type=int, default=48)
    p.add_argument("--tag", default="")
    p.add_argument("--views", default="")
    p.add_argument("--light", default="overcast")
    a = p.parse_args(argv)
    import geom as G
    import materials as M
    import scene as S
    if a.what == "tractor":
        import a6_export as A
        A.build_source()
        M.PARAMS["dirt"] = 0.5
    else:
        import trailer_build as T
        bpy.ops.wm.read_factory_settings(use_empty=True)
        M.TEX_DIR = os.path.join(tempfile.gettempdir(), "kamion_trailer_src")
        M.PARAMS["dirt"] = 0.5
        T.build(hi=False)
    S.setup_render("1600x900", a.samples)
    S.lighting(a.light)
    S.yard()
    sc = bpy.context.scene
    os.makedirs(a.out, exist_ok=True)
    views = [v for v in a.views.split(",") if v] or list(CAMS[a.what])
    for v in views:
        c = CAMS[a.what][v]
        sc.camera = S.add_camera("cam_" + v, c["loc"], c.get("target"), c.get("lens", 45), c.get("ortho"))
        S.stamp(f"ADR 0175 | {a.what} | {v} | {a.tag} | source build, {a.light}")
        sc.render.filepath = os.path.join(a.out, f"{a.what}_{v}{'_' + a.tag if a.tag else ''}.jpg")
        sc.render.image_settings.file_format = "JPEG"
        sc.render.image_settings.quality = 90
        bpy.ops.render.render(write_still=True)
        print("WROTE", sc.render.filepath)


if __name__ == "__main__":
    main()
