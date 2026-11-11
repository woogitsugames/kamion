from PIL import Image,ImageDraw
from pathlib import Path
r=Path('artifacts/car-paint-r1');(r/'r2-focus-checks').mkdir(exist_ok=True)
for f in sorted((r/'r2-focused').iterdir()):
 if len(list(f.glob('*.png')))!=6:continue
 o=Image.new('RGB',(960,740));d=ImageDraw.Draw(o)
 for i in range(4):
  im=Image.open(f/f'g_dirt_level_{i}.png').convert('RGB').crop((450,380,1490,1080));im.thumbnail((480,350));o.paste(im,((i%2)*480,(i//2)*370+20));d.text(((i%2)*480+4,(i//2)*370+4),f'R2 {f.name} actual level{i}/3',fill='white')
 o.save(r/'r2-focus-checks'/f'{f.name}.jpg')
