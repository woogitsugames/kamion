"""Native-pixel target-centred supplemental comparisons, no artificial enlargement."""
from pathlib import Path
from PIL import Image, ImageDraw
r=Path(__file__).parent/'clear'
for condition in ('Low-clear','Low-overcast','High-clear','High-overcast'):
 out=r/'target-crops'/condition;out.mkdir(parents=True,exist_ok=True)
 for f in sorted((r/'before'/condition).glob('*.png')):
  a=Image.open(f).convert('RGB');b=Image.open(r/'after'/condition/f.name).convert('RGB')
  x,y=a.width//2,a.height//2
  box=(x-240,y-170,x+240,y+170)
  p=Image.new('RGB',(960,370),'white')
  p.paste(a.crop(box),(0,30));p.paste(b.crop(box),(480,30))
  ImageDraw.Draw(p).text((5,5),f'{condition} {f.stem} | PRZED / PO | native pixels, centred look_at',fill='black')
  p.save(out/(f.stem+'.jpg'),quality=94)
print('Supplement native target crops ready')
