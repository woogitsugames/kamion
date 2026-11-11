"""Build size-only paired sheets for complete G route conditions; never align or grade."""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw
p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--tier',choices=['Low','High'],required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=True);records=[]
for lighting in ['clear','overcast']:
 condition=f'{a.tier}-{lighting}';old=a.before/condition;new=a.after/condition
 names=sorted(x.name for x in new.glob('*.png'))
 assert len(names)==92,(condition,len(names))
 assert names==sorted(x.name for x in old.glob('*.png')),'camera set changed'
 for start in range(0,len(names),12):
  group=names[start:start+12];board=Image.new('RGB',(960,len(group)*246),(30,30,30));draw=ImageDraw.Draw(board)
  for row,name in enumerate(group):
   draw.text((4,row*246+3),f'{condition} {name}: R3 BEFORE / R4 AFTER',fill='white')
   record={'condition':condition,'camera':Path(name).stem}
   for col,(label,folder) in enumerate([('before',old),('after',new)]):
    path=folder/name;record[label]={'path':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    with Image.open(path) as im:
     record[label]['size']=list(im.size);im=im.convert('RGB');im.thumbnail((480,222));board.paste(im,(col*480,row*246+22))
   records.append(record)
  board.save(a.out/f'{condition}-{start//12+1:02}.jpg',quality=95)
(a.out/'inputs.json').write_text(json.dumps({'method':'Size-only full-frame pairs, no alignment or tonal correction','pairs':records},indent=2)+'\n')
print(f'{len(records)} paired frames; sheets in {a.out.resolve()}')
