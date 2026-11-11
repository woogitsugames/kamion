"""PNG-native fixed ROI measurements; coords refer to a 1280-wide view.
High-frequency RMS excludes edges via a 4px border and reports radii0.65/1.5/3px.
No JPEG measurements, image alterations or synthetic before frames.
"""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROIS = {
    'r10_block_3': {'sky': (600, 40, 760, 100), 'grey_gable': (1085, 150, 1180, 300),
                    'grey_front': (480, 108, 570, 140), 'plinth': (1110, 328, 1220, 355)},
    'r10_block_4': {'sky': (700, 60, 800, 160), 'brick': (250, 80, 450, 280),
                    'peach': (1120, 110, 1180, 200)},
    'r10_house_2': {'sky': (500, 30, 800, 90)},
}

def measure(directory):
    result = {}
    for camera, rois in ROIS.items():
        path = directory / f'{camera}.png'
        if not path.exists():
            continue
        im = Image.open(path).convert('RGB')
        scale = im.width / 1280
        values = {}
        for label, rect in rois.items():
            box = tuple(round(v * scale) for v in rect)
            crop = im.crop(box)
            rgb = np.asarray(crop, float)
            lum = crop.convert('L')
            a = np.asarray(lum, float)
            hf = {str(radius): float((a - np.asarray(lum.filter(ImageFilter.GaussianBlur(radius)), float))[4:-4, 4:-4].std())
                  for radius in (.65, 1.5, 3)}
            values[label] = {'rect_1280': rect, 'rgb_mean': rgb.mean((0, 1)).round(3).tolist(),
                             'rgb_p95': np.percentile(rgb, 95, axis=(0, 1)).round(3).tolist(),
                             'clip_ge250_percent': float((rgb.max(2) >= 250).mean() * 100),
                             'hf_rms_srgb_levels': hf}
        result[camera] = values
    return result

if __name__ == '__main__':
    d = Path(sys.argv[1])
    result = {'directory': str(d), 'coordinates': '1280-wide normalized, original PNG sampled', 'measurements': measure(d)}
    (d / 'measurements.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
