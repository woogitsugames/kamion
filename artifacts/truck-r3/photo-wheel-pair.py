"""Qualitative form reference: real front wheel crop versus the actual QA render."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw,ImageFont,ImageOps

root=Path(__file__).resolve().parent
stage=sys.argv[1]
reference=Path('C:/Users/matma/Documents/Claude/kamion/Data/photos/nowe/Scania_R_400_EA_4x2_NA,_Nufam_2025,_Rheinstetten_(20250927-P1051305).jpg')
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
with Image.open(reference) as source:
    photo=ImageOps.exif_transpose(source).convert('RGB')
    if abs(photo.width/photo.height-4/3)>.001:
        raise ValueError('Reference pose/rotation changed')
    # Fixed crop selected from the previously inspected 960x720 full reference.
    box=(650/960*photo.width,400/720*photo.height,805/960*photo.width,560/720*photo.height)
    photo=photo.crop(tuple(round(v) for v in box))
photo.thumbnail((440,340),Image.Resampling.LANCZOS)
for tier in ('Low','High'):
    condition=f'{tier}-overcast'
    with Image.open(root/stage/condition/'truck-wheel-detail.png') as source:
        if source.size!=(2340,1080):
            raise ValueError('Changed QA camera resolution')
        render=source.convert('RGB').crop((900,450,1650,1065))
    render.thumbnail((440,340),Image.Resampling.LANCZOS)
    sheet=Image.new('RGB',(960,430),(24,24,24))
    draw=ImageDraw.Draw(sheet)
    draw.text((12,10),'ZDJĘCIE | Matti Blume, CC BY-SA 4.0',font=font,fill='white')
    draw.text((492,10),f'RENDER | {condition}',font=font,fill='white')
    for x,pic in ((0,photo),(480,render)):
        sheet.paste(pic,(x+(480-pic.width)//2,42+(340-pic.height)//2))
    draw.text((12,391),'Inne felgi, pozy i światło. Tylko ciągłość formy; bez kalibracji chromu, jasności i brudu.',font=font,fill='white')
    sheet.save(root/f'photo-wheel-{stage}-{tier}.jpg',quality=94)
print('Photo/render wheel pairs: 2, 960 px each')
