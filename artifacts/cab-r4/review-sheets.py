"""Generate cab review sheets under heavy; outputs are unreviewed until opened by the author."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--after', default='result-0112-hp15')
options = parser.parse_args()
STAGES = ('baseline', options.after)
VIEWS = ('cab-driver', 'cab-dash', 'cab-mirrors-left', 'cab-mirrors-right', 'cab-mirror-front', 'cab-grain', 'cab-seat-entry')
FONT = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 15)
TITLE = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 19)
outputs = []


def tile(path, size):
    with Image.open(path) as source:
        return ImageOps.contain(source.convert('RGB'), size, Image.Resampling.LANCZOS)


for stage in STAGES:
    for tier in ('Low', 'High'):
        for light in ('clear', 'overcast', 'dusk'):
            state = f'{tier}-{light}'
            sheet = Image.new('RGB', (960, 660), '#eeeeee')
            draw = ImageDraw.Draw(sheet)
            draw.text((8, 5), f'{stage} — {state}', fill='black', font=TITLE)
            for i, view in enumerate(VIEWS):
                x, y = (i % 3) * 320, 32 + (i // 3) * 208
                sheet.paste(tile(ROOT/stage/state/f'{view}.png', (320, 180)), (x, y))
                draw.text((x+5, y+183), view, fill='black', font=FONT)
            path = ROOT/f'{stage}-{state}-960.jpg'
            sheet.save(path, quality=92)
            outputs.append(path.name)

for tier in ('Low', 'High'):
    for light in ('clear', 'overcast'):
        sheet = Image.new('RGB', (960, 660), '#eeeeee')
        draw = ImageDraw.Draw(sheet)
        for column, stage in enumerate(STAGES):
            path = ROOT/stage/f'{tier}-{light}/cab-grain.png'
            draw.text((column*480+6, 5), f'{tier} {light} — {stage}', fill='black', font=FONT)
            sheet.paste(tile(path, (480, 270)), (column*480, 30))
            with Image.open(path) as source:
                # Exact same native-pixel region in both captures; no invented detail.
                sheet.paste(source.convert('RGB').crop((400, 660, 880, 980)), (column*480, 326))
        draw.text((8, 304), 'Pełny kadr oraz ten sam wycinek 480 × 320 pikseli źródłowych', fill='black', font=FONT)
        path = ROOT/f'plastic-detail-{tier}-{light}-960.jpg'
        sheet.save(path, quality=95)
        outputs.append(path.name)

sheet = Image.new('RGB', (960, 350), '#eeeeee')
draw = ImageDraw.Draw(sheet)
sheet.paste(tile(ROOT.parent/'cab-r1/reference-daf-xf-cockpit-960.jpg', (480, 280)), (0, 0))
sheet.paste(tile(ROOT/options.after/'High-overcast/cab-dash.png', (480, 280)), (480, 0))
draw.text((7, 282), 'DAF XF Cockpit — Spacekid, CC0 1.0', fill='black', font=FONT)
draw.text((487, 282), 'TRAKT, High overcast — odniesienie jakościowe', fill='black', font=FONT)
draw.text((7, 305), 'Inny pojazd, poza i ekspozycja; bez ilościowego dopasowania materiału.', fill='black', font=FONT)
draw.text((7, 327), 'Źródło i licencja: artifacts/cab-r1/REFERENCES-0112.md', fill='black', font=FONT)
path = ROOT/'photo-plastic-reference-vs-render-960.jpg'
sheet.save(path, quality=94)
outputs.append(path.name)
(ROOT/'generated-review-sheets.json').write_text(json.dumps({'status': 'generated, not yet visually reviewed', 'after': options.after, 'files': outputs}, indent=2), encoding='utf-8')
print(f'CAB_REVIEW_SHEETS: OK ({len(outputs)} arkuszy; obejrzeć przed akceptacją)')
