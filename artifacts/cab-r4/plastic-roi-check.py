"""One native Plastic ROI pair; single-thread, no full matrix or texture conversion."""
import argparse, hashlib, json, time
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
p=argparse.ArgumentParser();p.add_argument('--stage',default='result-0112-hp15');p.add_argument('--state',choices=('High-clear','Low-overcast'),default='High-clear');p.add_argument('--tag',default='hp15');a=p.parse_args()
if '/' in a.tag or '\\' in a.tag or '..' in a.tag:raise ValueError('invalid tag')
t=time.perf_counter();root=Path(__file__).resolve().parent;roi=(400,660,880,980);ims=[]
for stage in ('baseline',a.stage):
    with Image.open(root/stage/a.state/'cab-grain.png') as im:ims.append(im.convert('RGB').crop(roi))
sheet=Image.new('RGB',(960,352),'#dddddd');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
for col,im in enumerate(ims):
    d.text((col*480+6,5),('baseline' if col==0 else a.stage)+' '+a.state,fill='black',font=font);sheet.paste(im,(480*col,32))
sheet.save(root/f'plastic-{a.tag}-{a.state}-ROI-960.png')
diff=ImageChops.difference(*ims);record=dict(scope='One native 480x320 ROI, no rescaling or whole-frame quality metric',state=a.state,after=a.stage,roi=roi,changed_pixels=sum(v!=(0,0,0) for v in diff.getdata()),pixels=480*320,mean_abs_rgb=ImageStat.Stat(diff).mean,max_channel_delta=max(e[1] for e in diff.getextrema()),sha256=[hashlib.sha256(im.tobytes()).hexdigest() for im in ims],elapsed_seconds=time.perf_counter()-t)
(root/f'plastic-{a.tag}-{a.state}-ROI.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print(json.dumps(record,indent=2))
