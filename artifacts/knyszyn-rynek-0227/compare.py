"""Create local-only owner-photo / render pairs; source photos never enter git."""
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import sys
root=Path('artifacts/knyszyn-rynek-0227')
iteration=sys.argv[1] if len(sys.argv)>1 else 'r1'
tier=sys.argv[2] if len(sys.argv)>2 else 'High-clear'
photos=Path('Data/raw/refs/owner-knyszyn-2026-11-15')
out=root/'compare'/iteration/tier
out.mkdir(parents=True,exist_ok=True)
for n in range(1,12):
 photo=photos/f'{n}.webp'; camera = 'rynek' if n <= 8 else 'rondo'
 render=root/iteration/tier/f'{camera}-owner-{n:02}.png'
 if not render.exists():
  print(f'{n}: missing {render}')
  continue
 ims=[]
 for path in (photo,render):
  with Image.open(path) as im:
   im=ImageOps.contain(im.convert('RGB'),(960,540))
   canvas=Image.new('RGB',(960,540),'#202020')
   canvas.paste(im,((960-im.width)//2,(540-im.height)//2))
   ims.append(canvas)
 panel=Image.new('RGB',(1920,580),'white'); panel.paste(ims[0],(0,40)); panel.paste(ims[1],(960,40))
 draw=ImageDraw.Draw(panel); draw.text((12,10),f'Owner photo {n} | local reference only',fill='black'); draw.text((972,10),f'{iteration} {tier} | estimated camera',fill='black')
 panel.save(out/f'{n:02}-owner-render.jpg',quality=88)
 print(out/f'{n:02}-owner-render.jpg')


