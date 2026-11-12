from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json
r=Path(__file__).resolve().parent
src=r.parent/'truck-r2/references/tractor-rear-working.jpg'
render=r.parent/'truck-r3/detail-wheels-v3-fleet/High-overcast/truck-step-detail.png'
out=r/'references'; out.mkdir(exist_ok=True)
photo_box=(280,770,510,885); render_box=(730,770,1160,880)
with Image.open(src) as im:
 p=im.convert('RGB').crop(photo_box); p.save(out/'step-photo-crop-no-brand.jpg',quality=95)
with Image.open(render) as im: q=im.convert('RGB').crop(render_box)
sheet=Image.new('RGB',(960,440),(32,32,32)); d=ImageDraw.Draw(sheet)
d.text((8,8),'ZDJECIE | Asurnipal, CC BY-SA 4.0',fill='white')
d.text((488,8),'RENDER | r3 High-overcast, historyczny',fill='white')
for x,pic in ((0,p),(480,q)):
 pic.thumbnail((480,365),Image.Resampling.LANCZOS); sheet.paste(pic,(x+(480-pic.width)//2,34+(365-pic.height)//2))
d.text((8,412),'Pomost | stopien: inne funkcje i swiatlo. Korekta kadru P2, bez kalibracji jasnosci.',fill='white')
sheet.save(r/'photo-render-step-corrected-r3.jpg',quality=94)
meta={'photo_source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'photo_crop':photo_box,'render_source':str(render),'render_crop':render_box,'render_round':'r3, not fresh r4 baseline','modification':'crop only, colors and aspect preserved; excludes right-hand mudflap lettering noted by lead reviewer','max_pair_pixels':960}
(r/'reference-crop-correction.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
print('Corrected qualitative pair, 960x440')
