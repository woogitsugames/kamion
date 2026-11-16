"""ADR 0220: montage of strip pieces for reading (growing km upwards, L on the left, 1 m ticks, km labels).

    uv run --project tools/worldgen python artifacts/dk65-k1-0220/tools/view.py STRIP.npz OUT.jpg KM [KM ...] [--len 30] [--half 6] [--scale 2]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw


def main():
    a = sys.argv[1:]
    opt = {"--len": 30.0, "--half": 6.0, "--scale": 2}
    pos = []
    i = 0
    while i < len(a):
        if a[i] in opt:
            opt[a[i]] = type(opt[a[i]])(a[i + 1])
            i += 2
        else:
            pos.append(a[i])
            i += 1
    z = np.load(pos[0])
    G = z["g"]
    s0, res, half = float(z["s0"]), float(z["res"]), float(z["half"])
    L, H, k = opt["--len"], opt["--half"], opt["--scale"]
    tiles = []
    for km in map(float, pos[2:]):
        r0 = int(round((km * 1000 - s0) / res))
        r1 = r0 + int(L / res)
        c0, c1 = int(round((half - H) / res)), int(round((half + H) / res)) + 1
        piece = G[max(r0, 0):min(r1, G.shape[0]), c0:c1][::-1]
        im = Image.fromarray(piece).convert("RGB").resize((piece.shape[1] * k, piece.shape[0] * k), Image.NEAREST)
        d = ImageDraw.Draw(im)
        for m in range(-int(H), int(H) + 1):
            px = int(round((H - m) / res * k))
            d.line([(px, 0), (px, 8 if m % 5 else 18)], fill=(255, 0, 0))
        for mm in range(0, int(L) + 1, 5):
            y = im.size[1] - 1 - int(mm / res * k)
            d.line([(0, y), (10, y)], fill=(0, 255, 255))
            d.text((12, y - 10), f"{km + mm / 1000:.3f}", fill=(0, 255, 255))
        tiles.append(im)
    W = sum(t.size[0] for t in tiles) + 6 * (len(tiles) - 1)
    Hh = max(t.size[1] for t in tiles)
    out = Image.new("RGB", (W, Hh), (40, 40, 40))
    x = 0
    for t in tiles:
        out.paste(t, (x, 0))
        x += t.size[0] + 6
    out.save(pos[1], quality=88)


if __name__ == "__main__":
    main()
