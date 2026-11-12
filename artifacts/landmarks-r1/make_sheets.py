"""Produce review sheets no wider than 960 px, without changing source captures."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import sys

ROOT = Path(__file__).resolve().parent
phase = sys.argv[1]
out = ROOT / 'sheets' / phase
out.mkdir(parents=True, exist_ok=True)
reference = ROOT / 'reference7197.jpg'
def tile(path, label, width=480, height=300):
    panel = Image.new('RGB', (width, height + 24), (26, 26, 26))
    im = Image.open(path).convert('RGB')
    im.thumbnail((width, height))
    panel.paste(im, ((width-im.width)//2, 24+(height-im.height)//2))
    ImageDraw.Draw(panel).text((8, 6), label, fill='white')
    return panel

for condition in ('Low-overcast','Low-clear','High-overcast','High-clear'):
    for path in sorted((ROOT / phase / condition).glob('fire-station-*.png')):
        left = reference if path.stem == 'fire-station-ref7197' else ROOT / 'before' / condition / path.name
        if not left.exists():
            continue
        sheet = Image.new('RGB', (960, 324))
        sheet.paste(tile(left, 'Commons 7197, Rakoon CC0' if left == reference else f'before {condition}'), (0,0))
        sheet.paste(tile(path, f'{phase} {condition} {path.stem}'), (480,0))
        sheet.save(out / f'{condition}-{path.stem}.jpg', quality=93)
print(out)
