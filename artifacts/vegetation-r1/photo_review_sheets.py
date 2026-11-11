from pathlib import Path
import json
from PIL import Image,ImageDraw
p=Path('artifacts/vegetation-r1'); refs=json.loads((p/'photo-references.json').read_text(encoding='utf-8-sig'))['references'];out=p/'photo-review';out.mkdir(exist_ok=True)
for tier in ['Low','High']:
 for start in range(0,len(refs),3):
  sheet=Image.new('RGB',(960,900),'#222222');d=ImageDraw.Draw(sheet)
  for row,r in enumerate(refs[start:start+3]):
   folder=next(x for x in (p/'after').glob(tier+'-clear-photo-*') if (x/(r['camera']+'.png')).exists())
   paths=[Path(r['local_photo']),p/'before'/folder.name/(r['camera']+'.png'),folder/(r['camera']+'.png')]
   for col,(label,path) in enumerate(zip(['ZDJECIE','PRZED','PO B'],paths)):
    im=Image.open(path).convert('RGB');im.thumbnail((316,250));x=col*320;y=row*300;sheet.paste(im,(x,y+25));d.text((x+3,y+4),label+' '+tier,fill='white')
   d.text((3,row*300+265),r['camera']+' | '+r['author']+' | '+r['license']+' | Poza UNVERIFIED',fill='white')
  sheet.save(out/f'{tier}-{start//3+1:02d}.jpg',quality=92)
print(len(list(out.glob('*.jpg'))),'sheets')
