"""Source photo comparisons and uniform native crops of both receiver and caster surfaces."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
r=Path(__file__).resolve().parent;root=r.parents[1]
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
refs=json.loads((r/'reference-provenance.json').read_text())
for condition in ['Low-clear','Low-overcast','High-clear','High-overcast']:
 dest=r/'photo-pairs'/condition;dest.mkdir(parents=True,exist_ok=True)
 for ref in refs:
  page=Image.new('RGB',(960,330),'white');d=ImageDraw.Draw(page)
  d.text((6,4),condition+' | foto / przed / po | poza B; światło niekalibrowane',font=font,fill='black')
  for col,(label,p) in enumerate([('FOTO',root/ref['photo']),('PRZED',r/'before'/condition/(ref['camera']+'.png')),('PO',r/'after'/condition/(ref['camera']+'.png'))]):
   im=Image.open(p).convert('RGB');im.thumbnail((312,240),Image.Resampling.LANCZOS);page.paste(im,(col*320+4,50+(240-im.height)//2));d.text((col*320+5,28),label,font=font,fill='black')
  d.text((6,296),'richlv 2020 | CC BY-SA 4.0 | Mapillary '+ref['source_id'],font=font,fill='black')
  page.save(dest/(ref['source_id']+'.jpg'),quality=93)
 crops={'sbs-g3-a-2818555625124739':(100,650,1060,1080),'sbs-g3-a-3970163613102941':(100,650,1060,1080),'putry-island-1':(500,620,1460,1050),'putry-island-2':(500,620,1460,1050),'biezenstwa-above':(690,350,1650,780),'putry-above':(690,350,1650,780)}
 dest=r/'target-crops'/condition;dest.mkdir(parents=True,exist_ok=True)
 for camera,box in crops.items():
  page=Image.new('RGB',(960,920),'white');d=ImageDraw.Draw(page)
  for i,stage in enumerate(['before','after']):
   im=Image.open(r/stage/condition/(camera+'.png')).convert('RGB').crop(box);page.paste(im,(0,i*460+25));d.text((5,i*460+4),condition+' | '+camera+' | '+stage+' | native pixels, crop '+str(box),font=font,fill='black')
  page.save(dest/(camera+'.jpg'),quality=94)
for tier in ['Low','High']:
 camera='putry-island-near';page=Image.new('RGB',(960,920),'white');d=ImageDraw.Draw(page)
 for i,(stage,p) in enumerate([('before',r/'ablations'/f'{tier}-baseline'/f'{camera}.png'),('after',r/'final-near'/f'{tier}-clear'/f'{camera}.png')]):
  im=Image.open(p).convert('RGB').crop((400,620,1360,1050));page.paste(im,(0,i*460+25));d.text((5,i*460+4),tier+' clear | close island | '+stage+' | native crop (400,620,1360,1050)',font=font,fill='black')
 dest=r/'target-crops'/f'{tier}-clear';dest.mkdir(parents=True,exist_ok=True);page.save(dest/'putry-island-near.jpg',quality=94)
print('8 photo comparisons and 26 native crop pairs')
