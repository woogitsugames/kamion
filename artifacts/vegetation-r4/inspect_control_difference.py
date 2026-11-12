"""Small read-only two-frame QA; no render/build/test."""
import json
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw

here=Path(__file__).resolve().parent
rows=[]
for lighting in ('clear','overcast'):
    group='High-'+lighting
    paths=[here/stage/group/'fire-station-ref7197.png' for stage in ('before','probe-b')]
    images=[Image.open(p).convert('RGB') for p in paths]
    delta=ImageChops.difference(*images)
    bbox=delta.getbbox()
    changed=sum(p!=(0,0,0) for p in delta.getdata())
    rows.append(dict(group=group,camera='fire-station-ref7197',changed_pixels=changed,bbox=bbox))
    sheet=Image.new('RGB',(960,750),'#222222')
    draw=ImageDraw.Draw(sheet)
    for i,(label,frame) in enumerate(zip(('BEFORE','B2'),images)):
        full=frame.copy();full.thumbnail((470,230));sheet.paste(full,(i*490,25))
        draw.text((i*490+3,5),label+' '+group,fill='white')
        if bbox:
            x0,y0,x1,y1=bbox
            region=frame.crop((max(0,x0-10),max(0,y0-10),min(frame.width,x1+10),min(frame.height,y1+10)))
            region.thumbnail((470,450));sheet.paste(region,(i*490,280))
    draw.text((4,730),'Changed pixels: '+str(changed)+' | bbox '+str(bbox)+' | diagnostic crop',fill='white')
    sheet.save(here/('control-diff-'+group+'.jpg'),quality=93)
(here/'probe-b-control-differences.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows,indent=2))
