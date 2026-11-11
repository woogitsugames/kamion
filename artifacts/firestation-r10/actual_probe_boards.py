"""Actual same-camera before/after boards and native-pixel protected-detail crops."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('phase');a=p.parse_args();O=Path(__file__).resolve().parent
for tier in ('Low','High'):
 paths=[O/a.phase/f'{tier}-overcast'/f'{cam}.png' for cam in ('fire-station-ref7197','fire-station-route')]
 if not all(x.exists() for x in paths):continue
 sheet=Image.new('RGB',(960,960),'white');d=ImageDraw.Draw(sheet)
 for i,path in enumerate(paths):
  for j,phase in enumerate(('before',a.phase)):
   im=Image.open(O/phase/f'{tier}-overcast'/path.name).convert('RGB');im.thumbnail((480,450));sheet.paste(im,(j*480,i*470+20));d.text((j*480+5,i*470+3),tier+' '+phase+' '+path.stem,fill='black')
 sheet.save(O/f'{tier}-{a.phase}-before-after.jpg',quality=95)
 ref=Image.open(paths[0]).convert("RGB");ref.thumbnail((960,960));ref.save(O/f'{tier}-{a.phase}-ref960.jpg',quality=95)
 # Fixed native-pixel rectangles identified on the locked2340x1080 before. No exposure matching/rescale.
 regions={'letter-clock':(1085,400,1460,590),'fence-flag':(800,480,1130,805),'foreground-fir':(1410,440,1690,805)}
 board=Image.new('RGB',(960,890),'white');dr=ImageDraw.Draw(board)
 for row,(name,box) in enumerate(regions.items()):
  for col,phase in enumerate(('before',a.phase)):
   im=Image.open(O/phase/f'{tier}-overcast'/'fire-station-ref7197.png').convert('RGB');crop=im.crop(box);crop.thumbnail((460,270));board.paste(crop,(col*480+5,row*295+20));dr.text((col*480+5,row*295+3),name+' / '+phase+' / NATIVE PIXELS',fill='black')
 board.save(O/f'{tier}-{a.phase}-native-details.jpg',quality=95)

