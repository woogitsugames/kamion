"""Contact sheets for every original PNG, <=960px in either dimension."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

directory = Path(sys.argv[1])
files = sorted(p for p in directory.glob('*.png') if '_mask' not in p.stem and '_envcube' not in p.stem)
out = directory / 'review'
out.mkdir(exist_ok=True)
for page in range(0, len(files), 12):
    sheet = Image.new('RGB', (960, 704), '#252525')
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(files[page:page+12]):
        im = Image.open(path).convert('RGB')
        im.thumbnail((320, 148))
        x, y = i % 3 * 320, i // 3 * 176
        sheet.paste(im, (x, y+20))
        draw.text((x+4, y+3), path.stem[:43], fill='white')
    name = out / f'sheet-{page//12+1:02}.jpg'
    sheet.save(name, quality=93)
    print(name)
