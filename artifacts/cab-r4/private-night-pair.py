"""One private photo/render QA pair; copyrighted photo output must remain outside git."""
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
start=time.perf_counter();root=Path(__file__).resolve().parent
sheet=Image.new('RGB',(960,350),'#dddddd');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
paths=(root.parent/'cab-r2/reference-volvo-night.jpg',root/'night-current/High-night/cab-dash.png')
for col,path in enumerate(paths):
    with Image.open(path) as im:sheet.paste(ImageOps.contain(im.convert('RGB'),(480,280),Image.Resampling.LANCZOS),(480*col,0))
d.text((7,283),'Volvo / Jonatan Fernström 2017 — prywatna referencja',font=font,fill='black')
d.text((487,283),'TRAKT High Night — hp15, istniejący preset ADR 0108',font=font,fill='black')
d.text((7,306),'Inny pojazd, poza, reflektory i ekspozycja. Porównanie jakościowe, bez celu RGB/cd/m².',font=font,fill='black')
d.text((7,328),'Źródło/prawa: artifacts/cab-r2/NIGHT-REFERENCE.md. Zdjęcie i ten arkusz pozostają poza git.',font=font,fill='black')
sheet.save(root/'private-night-reference-vs-render-960.jpg',quality=94)
print(f'One private pair written in {time.perf_counter()-start:.3f}s; DO NOT ADD PHOTO OUTPUT TO GIT')
