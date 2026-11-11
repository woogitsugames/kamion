"""Reproducible 960 previews; raw PNG measurements remain authoritative."""
from pathlib import Path
from PIL import Image,ImageDraw
import sys
root=Path(__file__).resolve().parent
stage=sys.argv[1] if len(sys.argv)>1 else 'after-final'
pivots={'fire-station-ref7197','route-putry-entry-signs','stretch-05-docks','dk8-dk19-exit','truck-at-gate','driver-andersa-to-putry','r10_house_2','r10_block_3','g3b-eye-s1482','kwadrat-park-gate','photo-biezenstwa-ground'}
def preview(path,width=960):
 im=Image.open(path).convert('RGB');return im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS)
def label(im,text):
 out=Image.new('RGB',(im.width,im.height+20),(25,25,25));out.paste(im,(0,20));ImageDraw.Draw(out).text((5,3),text,fill='white');return out
for cond in sorted((root/stage).iterdir()):
 if not cond.is_dir():continue
 dest=root/(stage+'-960')/cond.name;dest.mkdir(parents=True,exist_ok=True)
 compare=root/'compare-final'/cond.name;compare.mkdir(parents=True,exist_ok=True)
 thumbs=[]
 for path in sorted(cond.glob('*.png')):
  after=preview(path);after.save(dest/(path.stem+'.jpg'),quality=90)
  before=preview(root/'before'/cond.name/path.name)
  if path.stem in pivots:
   a=label(before,cond.name+' BEFORE '+path.stem);b=label(after,cond.name+' AFTER FINAL '+path.stem)
   pair=Image.new('RGB',(960,a.height+b.height));pair.paste(a,(0,0));pair.paste(b,(0,a.height));pair.save(compare/('paired-'+path.stem+'.jpg'),quality=93)
  a=label(before.resize((480,222)),path.stem+' BEFORE');b=label(after.resize((480,222)),path.stem+' FINAL')
  pair=Image.new('RGB',(960,242));pair.paste(a,(0,0));pair.paste(b,(480,0));thumbs.append(pair)
 for offset in range(0,len(thumbs),6):
  page=Image.new('RGB',(960,242*len(thumbs[offset:offset+6])))
  for j,im in enumerate(thumbs[offset:offset+6]):page.paste(im,(0,j*242))
  page.save(compare/f'sheet-{offset//6+1:02}.jpg',quality=90)
 print(cond.name,len(thumbs),'previews')
