"""Inspect unequal inherited passenger-car PNGs and prepare bounded review sheets."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFilter

root = Path(__file__).parent
data = json.loads((root / 'passenger-car-frame-check-c.json').read_text())
output = root / 'protected-c-review'
output.mkdir(exist_ok=True)
rows, frames = [], []
for row in data['rows']:
    entry = dict(row)
    entry.update(changed_pixels=0, max_channel_delta=0, bbox=None)
    if not row['png_identical']:
        a_path = root / 'after-a-exact' / row['condition'] / (row['camera'] + '.png')
        c_path = root / 'after-c-exact' / row['condition'] / (row['camera'] + '.png')
        with Image.open(a_path) as ai, Image.open(c_path) as ci:
            a, c = ai.convert('RGB'), ci.convert('RGB')
            delta = np.abs(np.asarray(a).astype(np.int16) - np.asarray(c).astype(np.int16))
            mask = np.any(delta != 0, axis=2)
            yy, xx = np.nonzero(mask)
            entry.update(changed_pixels=int(mask.sum()), max_channel_delta=int(delta.max()),
                         bbox=[int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())] if len(xx) else None)
            frame = Image.new('RGB', (960, 220), '#252525')
            draw = ImageDraw.Draw(frame)
            draw.text((5, 4), f"{row['condition']} | {row['camera']} | A / C / changed pixels (dilated)", fill='white')
            for left, image in ((0, a), (320, c)):
                thumb = ImageOps.contain(image, (320, 160))
                frame.paste(thumb, (left, 25))
            changed = Image.fromarray(mask.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(7))
            heat = Image.merge('RGB', (changed, Image.new('L', changed.size), Image.new('L', changed.size)))
            frame.paste(ImageOps.contain(heat, (320, 160)), (640, 25))
            draw.text((5, 194), f"RGB pixels changed: {entry['changed_pixels']} | max channel delta: {entry['max_channel_delta']} / 255 | bbox {entry['bbox']}", fill='white')
            frames.append(frame)
    rows.append(entry)
for start in range(0, len(frames), 4):
    page = Image.new('RGB', (960, 900), '#252525')
    for i, frame in enumerate(frames[start:start + 4]):
        page.paste(frame, (0, 10 + i * 220))
    page.save(output / f'page-{start // 4:02d}.jpg', quality=94)
result = dict(total=len(rows), png_identical=data['identical'], rgb_identical=sum(r['changed_pixels'] == 0 for r in rows),
              max_changed_pixels=max(r['changed_pixels'] for r in rows), max_channel_delta=max(r['max_channel_delta'] for r in rows), rows=rows)
(root / 'protected-c-pixel-audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')

overview = root / 'c-overview'
overview.mkdir(exist_ok=True)
for condition in ('Low-clear', 'Low-overcast', 'High-clear', 'High-overcast'):
    pages = sorted((root / 'c-review' / condition).glob('page-*.png'))
    for start in range(0, len(pages), 4):
        sheet = Image.new('RGB', (960, 810), '#252525')
        ImageDraw.Draw(sheet).text((5, 5), f'{condition} | C review pages {start} to {min(start + 3, len(pages) - 1)}; inspect full page if unclear', fill='white')
        for i, path in enumerate(pages[start:start + 4]):
            with Image.open(path) as im:
                sheet.paste(im.convert('RGB').resize((480, 390), Image.Resampling.LANCZOS), ((i % 2) * 480, 30 + (i // 2) * 390))
        sheet.save(overview / f'{condition}-{start // 4:02d}.jpg', quality=94)
print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
