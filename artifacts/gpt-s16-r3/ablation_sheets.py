"""Compact diagnostic sheets; original pixels cropped uniformly, never altered."""
from pathlib import Path
import argparse,json
from PIL import Image,ImageDraw
r=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--tier',choices=['Low','High'],required=True);a=p.parse_args()
names=['sbs-g3-a-2818555625124739','sbs-g3-a-3970163613102941','putry-island-1','putry-island-2','putry-island-near']
modes=['zero-bias','baked-only','no-baked','no-shadows']
dest=r/'ablation-sheets'/a.tier;dest.mkdir(parents=True,exist_ok=True)
def frame(path):
 im=Image.open(path).convert('RGB');im=im.crop((0,200,im.width,im.height));im.thumbnail((480,184),Image.Resampling.LANCZOS);return im
for name in names:
 base=r/'ablations'/f'{a.tier}-baseline'/f'{name}.png'
 out=Image.new('RGB',(960,852),'white');d=ImageDraw.Draw(out);d.text((5,4),f'{a.tier} clear | {name} | same crop y=200..1080',fill='black')
 for i,mode in enumerate(modes):
  y=26+i*205;d.text((5,y),'BASELINE',fill='black');d.text((485,y),mode,fill='black')
  out.paste(frame(base),(0,y+18));out.paste(frame(r/'ablations'/f'{a.tier}-{mode}'/f'{name}.png'),(480,y+18))
 out.save(dest/f'{name}.jpg',quality=93)
print('Saved five diagnostic sheets:',a.tier)
