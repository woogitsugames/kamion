from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
stage = sys.argv[1] if len(sys.argv) > 1 else 'fog-only'
try:
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)
except OSError:
    font = ImageFont.load_default()
boxes = {'truck-front': (650, 90, 1720, 600), 'cab-driver': None, 'truck-34': (800, 230, 1380, 700),
         'lamps-front': (650, 600, 1720, 820), 'lamp-left': (660, 620, 900, 780)}
for condition in sorted((ROOT / stage).iterdir()):
    if not condition.is_dir() or not (condition / 'complete.ok').exists():
        continue
    for label, box in boxes.items():
        camera = 'truck-front' if label in ('lamps-front', 'lamp-left') else label
        if not (condition / (camera + '.png')).exists():
            continue
        left = Image.open(ROOT / 'before' / condition.name / (camera + '.png')).convert('RGB')
        right = Image.open(condition / (camera + '.png')).convert('RGB')
        if left.size != right.size:
            raise ValueError('Mismatched image dimensions')
        if box:
            left, right = left.crop(box), right.crop(box)
        height = round(left.height * 480 / left.width)
        sheet = Image.new('RGB', (960, height + 34), '#202020')
        sheet.paste(left.resize((480, height), Image.Resampling.LANCZOS), (0, 34))
        sheet.paste(right.resize((480, height), Image.Resampling.LANCZOS), (480, 34))
        draw = ImageDraw.Draw(sheet)
        draw.text((8, 8), 'PRZED | ' + condition.name, font=font, fill='white')
        draw.text((488, 8), 'PO | ' + stage, font=font, fill='white')
        output = condition / ('review-' + label + '.jpg')
        sheet.save(output, quality=94)
        print(output.relative_to(ROOT))
