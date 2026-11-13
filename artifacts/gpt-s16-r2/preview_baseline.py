from pathlib import Path
from PIL import Image,ImageDraw
r=Path(__file__).parent;folder=r/'before/High-clear';out=r/'inspection';out.mkdir(exist_ok=True)
files=sorted(folder.glob('garden*.png'));sheet=Image.new('RGB',(960,696),'white');draw=ImageDraw.Draw(sheet)
for j,f in enumerate(files):
 im=Image.open(f).convert('RGB');im.thumbnail((960,444));im.save(out/(f.stem+'-before.jpg'),quality=92)
 im.thumbnail((320,148));x=j%3*320;y=j//3*174;sheet.paste(im,(x,y+24));draw.text((x+4,y+4),f.stem,fill='black')
sheet.save(out/'baseline-streets.jpg',quality=92)
