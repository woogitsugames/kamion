"""Local review artifacts only. Run inside the branch's heavy slot, after World is terminal."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
FONT = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 15)
TITLE = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 19)
VIEWS = ('cab-driver', 'cab-dash', 'cab-mirrors-left', 'cab-mirrors-right',
         'cab-mirror-front', 'cab-grain', 'cab-seat-entry')
STAGES = ('baseline', 'result-0112-night1')

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
            sheet.save(ROOT/f'{stage}-{state}-960.jpg', quality=90)

for tier in ('Low', 'High'):
    sheet = Image.new('RGB', (960, 450), '#eeeeee')
    draw = ImageDraw.Draw(sheet)
    for column, stage in enumerate(STAGES):
        with Image.open(ROOT/stage/f'{tier}-dusk/cab-dash.png') as source:
            for row, roi in enumerate(((450, 820, 1130, 1075), (1300, 935, 1720, 1075))):
                crop = source.crop(roi).convert('RGB')
                crop.thumbnail((480, 180), Image.Resampling.LANCZOS)
                y = 30 + row*210
                sheet.paste(crop, (column*480, y))
                draw.text((column*480+6, y+182), f'{tier} dusk — {"przed" if column == 0 else "po"}', fill='black', font=FONT)
    draw.text((8, 5), 'Legenda przycisków: kierownica i panel centralny', fill='black', font=TITLE)
    sheet.save(ROOT/f'backlight-details-{tier}-960.jpg', quality=94)

sheet = Image.new('RGB', (960, 355), '#eeeeee')
draw = ImageDraw.Draw(sheet)
sheet.paste(tile(ROOT.parent/'cab-r2/reference-volvo-night.jpg', (480, 280)), (0, 0))
sheet.paste(tile(ROOT/'result-0112-night1/High-dusk/cab-driver.png', (480, 280)), (480, 0))
draw.text((7, 283), 'Volvo Trucks / Jonatan Fernström, 2017 (prawa autorskie)', fill='black', font=FONT)
draw.text((487, 283), 'TRAKT, High dusk — odniesienie jakościowe', fill='black', font=FONT)
draw.text((7, 307), 'Inne kabiny, poza i ekspozycja. Zdjęcie nie jest CC0 ani celem liczbowym.', fill='black', font=FONT)
draw.text((7, 329), 'Źródło i ograniczenia: artifacts/cab-r2/NIGHT-REFERENCE.md', fill='black', font=FONT)
sheet.save(ROOT/'photo-night-reference-vs-render-960.jpg', quality=92)
print('CAB_REVIEW_SHEETS: OK (12 macierzy, 2 detale, 1 para referencyjna)')
