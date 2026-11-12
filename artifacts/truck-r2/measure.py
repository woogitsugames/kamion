"""Native display measurements; rectangular ROIs are not material segmentation."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
# Coordinates from the earlier review, scaled from the 2340x1080 native frame.
FRONT = {
    'windscreen_upper': (820, 180, 1520, 280),
    'windscreen_lower': (820, 370, 1520, 470),
    'left_lamp': (695, 645, 845, 755),
}
# Previous owner-method crops, expressed at 1024 px width, retained for continuity.
PAINT = {'glass': (380, 160, 460, 200), 'door': (514, 218, 533, 252), 'deflector': (440, 120, 520, 134)}

def luminance(rgb):
    return np.asarray(rgb, dtype=np.float64) @ np.array([.2126, .7152, .0722]) / 255 * 100

def crop_stats(im, box, reference_width):
    k = im.width / reference_width
    box = tuple(round(v * k) for v in box)
    rgb = np.asarray(im.crop(box))
    y = luminance(rgb)
    return {'native_box': box, 'p50_display_percent': float(np.median(y)),
            'sigma_display_points': float(y.std()),
            'p99_minus_p50_points': float(np.percentile(y, 99) - np.median(y)),
            'vertical_profile_range_points': float(np.ptp(y.mean(axis=1))),
            'all_channels_ge254_pixels': int((rgb.min(axis=2) >= 254).sum()),
            'all_channels_ge254_share': float((rgb.min(axis=2) >= 254).mean())}

def main(stage):
    results = {}
    for condition in sorted((ROOT / stage).iterdir()):
        if not condition.is_dir():
            continue
        row = {}
        for camera, rois, width in [('truck-front', FRONT, 2340), ('truck-34', PAINT, 1024)]:
            file = condition / f'{camera}.png'
            if not file.exists():
                continue
            im = Image.open(file).convert('RGB')
            row[camera] = {key: crop_stats(im, box, width) for key, box in rois.items()}
            legacy = im.resize((1024, round(im.height * 1024 / im.width)), Image.Resampling.LANCZOS)
            for key, box in rois.items():
                row[camera][key]['legacy1024'] = crop_stats(legacy, box, width)
            preview = im.copy()
            draw = ImageDraw.Draw(preview)
            for key, value in row[camera].items():
                draw.rectangle(value['native_box'], outline='magenta', width=3)
                draw.text(value['native_box'][:2], key, fill='magenta')
            preview.thumbnail((960, 960))
            preview.save(condition / f'{camera}-roi.jpg', quality=92)
        for file in sorted(condition.glob('*.png')):
            if file.name.endswith('_envcube.png') or file.name.endswith('_mask.png'):
                continue
            before = ROOT / 'before' / condition.name / file.name
            if stage != 'before' and before.exists():
                im = Image.open(file).convert('RGB')
                base = Image.open(before).convert('RGB')
                if im.size != base.size:
                    raise ValueError(f'Inconsistent registration dimensions: {file}')
                delta = np.asarray(im, float) - np.asarray(base, float)
                row.setdefault('image_rmse_percent', {})[file.stem] = float(np.sqrt((delta**2).mean()) / 255 * 100)
                sheet = Image.new('RGB', (960, 468), '#202020')
                for x, picture, title in [(0, base, 'PRZED'), (480, im, 'PO')]:
                    picture.thumbnail((480, 440))
                    sheet.paste(picture, (x, 28))
                    ImageDraw.Draw(sheet).text((x+8, 8), title, fill='white')
                sheet.save(condition / f'{file.stem}-paired.jpg', quality=92)
        results[condition.name] = row
    (ROOT / f'{stage}-metrics.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'before')
