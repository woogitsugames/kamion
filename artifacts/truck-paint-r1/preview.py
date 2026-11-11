from pathlib import Path
from PIL import Image,ImageDraw
import sys
root=Path(__file__).resolve().parent
stage=sys.argv[1] if len(sys.argv)>1 else "before"
def read(path,width=960):
 im=Image.open(path).convert("RGB");return im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS)
def label(im,text):
 out=Image.new("RGB",(im.width,im.height+18),(24,24,24));out.paste(im,(0,18));ImageDraw.Draw(out).text((4,3),text,fill="white");return out
for cond in sorted((root/stage).iterdir()):
 if not cond.is_dir():continue
 dst=root/(stage+"-960")/cond.name;dst.mkdir(parents=True,exist_ok=True)
 thumbs=[]
 for path in sorted(cond.glob("*.png")):
  if path.stem.endswith(("_envcube","_mask")):continue
  im=read(path);im.save(dst/(path.stem+".jpg"),quality=92)
  thumbs.append(label(read(path,320),path.stem))
  old=root/"before"/cond.name/path.name
  if stage!="before" and old.exists():
   a=label(read(old),cond.name+" BEFORE "+path.stem);b=label(im,cond.name+" "+stage+" "+path.stem)
   pair=Image.new("RGB",(960,a.height+b.height));pair.paste(a,(0,0));pair.paste(b,(0,a.height));pair.save(dst/("paired-"+path.stem+".jpg"),quality=93)
 for offset in range(0,len(thumbs),12):
  subset=thumbs[offset:offset+12];h=subset[0].height;page=Image.new("RGB",(960,h*((len(subset)+2)//3)))
  for j,im in enumerate(subset):page.paste(im,((j%3)*320,(j//3)*h))
  page.save(dst/f"sheet-{offset//12+1:02}.jpg",quality=91)
 print(stage,cond.name,len(thumbs),"previews")
