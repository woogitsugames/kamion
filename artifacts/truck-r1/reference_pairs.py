"""Qualitative photo/render sheets; different vehicles, poses and illumination are explicitly labelled."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

root = Path(__file__).resolve().parent
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)
small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 14)
for tier in ('Low', 'High'):
    for light in ('overcast', 'clear'):
        render = root / 'final-candidate' / f'{tier}-{light}' / 'truck-34.png'
        if not render.exists():
            continue
        for reference in ('working-tractor', 'paint-reflection'):
            sheet = Image.new('RGB', (960, 410), '#202020')
            for x, path in ((0, root / 'references' / f'{reference}.jpg'), (480, render)):
                with Image.open(path) as source:
                    picture = ImageOps.contain(source.convert('RGB'), (480, 340), Image.Resampling.LANCZOS)
                    sheet.paste(picture, (x + (480-picture.width)//2, 34 + (340-picture.height)//2))
            draw = ImageDraw.Draw(sheet)
            draw.text((8, 8), 'ZDJĘCIE | ' + reference, font=font, fill='white')
            draw.text((488, 8), f'RENDER | TRAKT {tier} {light}', font=font, fill='white')
            draw.text((8, 382), 'Ocena jakościowa materiału: inne pojazdy, pozycje kamer i światło. Autorzy/licencje: references/CREDITS.md.', font=small, fill='white')
            sheet.save(root / f'photo-render-{reference}-{tier}-{light}.jpg', quality=94)
