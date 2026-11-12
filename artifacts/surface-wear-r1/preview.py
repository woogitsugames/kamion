from pathlib import Path
from PIL import Image,ImageDraw
import sys,json
base=Path(__file__).resolve().parent
for stage in sys.argv[1:] or ['before']:
 out=base/(stage+'-960');out.mkdir(exist_ok=True);report=[]
 for cond in sorted((base/stage).iterdir()):
  if not cond.is_dir():continue
  dest=out/cond.name;dest.mkdir(exist_ok=True);files=sorted(cond.glob('*.png'));thumbs=[];wear=[]
  for f in files:
   im=Image.open(f).convert('RGB');im.resize((960,round(im.height*960/im.width)),Image.Resampling.LANCZOS).save(dest/(f.stem+'.jpg'),quality=94)
   thumb=im.resize((320,148),Image.Resampling.LANCZOS);thumbs.append((f.stem,thumb))
   if f.stem.startswith('d_wear_'):wear.append((f.stem,thumb))
  def sheet(items,name):
   board=Image.new('RGB',(960,166*((len(items)+2)//3)),'#222');d=ImageDraw.Draw(board)
   for i,(label,im) in enumerate(items):x=(i%3)*320;y=(i//3)*166;board.paste(im,(x,y+18));d.text((x+3,y+3),label,fill='white')
   board.save(dest/name,quality=94)
  for i in range(0,len(thumbs),12):sheet(thumbs[i:i+12],f'sheet-{i//12+1:02d}.jpg')
  if wear:sheet(wear,'wear-targets.jpg')
  report.append({'condition':cond.name,'frames':len(files),'ids':[f.stem for f in files]});print(stage,cond.name,len(files))
 (base/(stage+'-capture-counts.json')).write_text(json.dumps(report,indent=2)+'\n')
