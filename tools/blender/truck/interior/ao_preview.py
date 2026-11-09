"""Track A6.1 — QA preview of the cab AO atlas: the LOD0 atlas with empty texels (no baked data) in red.

    uv run --no-project --with pillow --with numpy python tools/blender/truck/interior/ao_preview.py [OUT.jpg]

Needs a fresh a6_export.py run (it saves the bake coverage mask to artifacts/truck-interior/ao_coverage_2048.npy).
"""
import os
import sys

import numpy as np
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "docs", "reports", "visual", "truck-A6",
                                                             "ao_atlas_preview.jpg")
    ao = np.asarray(Image.open(os.path.join(REPO, "art-source", "truck", "interior", "export", "textures", "High",
                                            "T_Cab_AO_LOD0.png")).convert("L"), float)
    cov = np.load(os.path.join(REPO, "artifacts", "truck-interior", "ao_coverage_2048.npy")).astype(bool)
    rgb = np.stack([ao] * 3, -1)
    rgb[~cov] = [200, 40, 40]
    Image.fromarray(rgb.astype(np.uint8)).resize((800, 800), Image.LANCZOS).save(out, quality=85)
    print("WROTE", out, "texels with data", round(float(cov.mean()), 4))


if __name__ == "__main__":
    main()
