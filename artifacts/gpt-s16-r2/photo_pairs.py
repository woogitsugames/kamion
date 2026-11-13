"""Reference | before | after for six real streets; references are explicitly typological."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
r=Path(__file__).resolve().parent;root=r.parents[1]
streets=json.loads((r/'street-views.json').read_text(encoding='utf-8-sig'))
refs={x['reference']:x for x in json.loads((r/'reference-provenance.json').read_text(encoding='utf-8-sig'))}
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12);title=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
parser=argparse.ArgumentParser();parser.add_argument('--condition',choices=['Low-clear','Low-overcast','High-clear','High-overcast']);args=parser.parse_args()
for condition in ([args.condition] if args.condition else ('Low-clear','Low-overcast','High-clear','High-overcast')):
 out=r/'photo-pairs'/condition;out.mkdir(parents=True,exist_ok=True)
 for index,street in enumerate(streets):
  ref=refs[street['reference']];photo=Image.open(root/ref['file']).convert('RGB');photo.thumbnail((312,260),Image.Resampling.LANCZOS)
  page=Image.new('RGB',(960,470),'white');d=ImageDraw.Draw(page)
  d.text((7,4),f"{street['street']} | {condition} | REF TYPOLOGICZNA: inna lokalizacja i poza",font=title,fill='black')
  d.text((7,30),f"{street['reference']} — ZDJĘCIE",font=font,fill='black');d.text((327,30),'PRZED',font=font,fill='black');d.text((647,30),'PO',font=font,fill='black')
  page.paste(photo,(4,80))
  for row,camera in enumerate(street['cameras']):
   y=55+row*178
   d.text((327,y),camera,font=font,fill='black')
   for column,stage in [(1,'before'),(2,'after')]:
    im=Image.open(r/stage/condition/(camera+'.png')).convert('RGB');im.thumbnail((320,148),Image.Resampling.LANCZOS);page.paste(im,(column*320,y+20))
  d.text((7,416),f"Foto: {ref['author']}, Mapillary, {ref['license']}; id {ref['id']}",font=font,fill='black')
  d.text((7,434),'Porównanie typologii koron/frontów; brak zgodnej pozy i kalibracji barwy. Piksele zdjęcia nie są teksturą gry.',font=font,fill='black')
  page.save(out/f'street-{index+1:02d}.jpg',quality=93)
print('Photo comparisons:',len(streets)*4)
