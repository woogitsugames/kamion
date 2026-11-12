from pathlib import Path
from PIL import Image,ImageDraw
r=Path('artifacts/gpt-s16-r1')
fs=sorted((r/'clear/after/Low-clear').glob('*.png'))
for s in range(0,len(fs),12):
 p=Image.new('RGB',(960,680),'white'); d=ImageDraw.Draw(p)
 for j,f in enumerate(fs[s:s+12]):
  im=Image.open(f).convert('RGB'); im.thumbnail((320,148))
  x=j%3*320;y=j//3*170; p.paste(im,(x,y+22)); d.text((x+3,y+3),f.stem.replace('clear_',''),fill='black')
 p.save(r/'inspection'/f'clear-gpu-preview-{s//12:02d}.jpg',quality=90)
