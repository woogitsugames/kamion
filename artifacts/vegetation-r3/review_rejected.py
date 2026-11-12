"""Evidence of rejected consumer-input experiment; never a producer result."""
import hashlib
import json
import runpy
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

here = Path(__file__).resolve().parent
camera = 'sbs-g3-b-297817221966185'
group = 'Low-overcast-photo-2048x1536'
stats = runpy.run_path(str(here / 'review_images.py'))['stats']
frames, result = [], {'status': 'REJECTED', 'scope': 'B1 producer output and separate consumer-input diagnostic'}
before = None
for label, folder in [('baseline', 'before'), ('B1', 'probe'),
                      ('maple_height_only', 'diagnostic-maple-height')]:
    directory = here / folder / group
    path = directory / (camera + '.png')
    frame = Image.open(path).convert('RGB')
    array = np.array(frame)
    if before is None:
        before = array
    changed = np.any(array != before, axis=2)
    ys, xs = np.where(changed)
    result[label] = dict(producer_generated=(label != 'maple_height_only'),
                        stats=stats(directory / 'stats.txt')[camera],
                        changed_pixels=int(changed.sum()),
                        changed_bbox=([int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
                                      if len(xs) else None),
                        fixed_crown_zone=[0, 269, 461, 507],
                        changed_pixels_in_fixed_crown_zone=int(changed[269:507,:461].sum()),
                        image_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    if label == 'B1':
        difference = array.copy()
        difference[changed] = (255, 0, 255)
        diff_image = Image.fromarray(difference)
        diff_image.thumbnail((960, 720))
        diff_image.save(here/'B1-difference.png')
    frames.append((label, frame))
ref = next(r for r in json.loads((here/'photo-references.json').read_text())['references']
           if r['camera'] == camera)
frames.append(('zsolt 2017-07-29 CC BY-SA 4.0; pose B WORKING_VALUE',
               Image.open(here.parents[1] / ref['local_photo']).convert('RGB')))
sheet = Image.new('RGB', (960, 820), '#222222')
d = ImageDraw.Draw(sheet)
for i, (label, frame) in enumerate(frames):
    frame.thumbnail((470, 352))
    x, y = (i % 2)*490, (i // 2)*395
    sheet.paste(frame, (x, y+25))
    d.text((x+3, y+3), label, fill='white')
d.text((5, 793), 'Height-only enlarged sparse crown. B8 remains OPEN; all R3 variants rejected.', fill='white')
sheet.save(here/'rejected-comparison.jpg', quality=93)
(here/'rejected-comparison.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, indent=2))
