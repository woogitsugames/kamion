import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/refs'))
import sbs_gate3 as s
refs={r['camera']:r for r in s.read(s.REGION/'sbs_references.json')['references']}
probes=s.read(s.ROOT/'artifacts/sbs-r1/pose-probes.json')['probes']
out=s.ROOT/'artifacts/sbs-r1/pose-galleries';out.mkdir(parents=True,exist_ok=True)
for camera in sorted({p['camera'] for p in probes}):
    ref=refs[camera]; group=[p for p in probes if p['camera']==camera]
    canvas=Image.new('RGB',(960,1120),'#202020');d=ImageDraw.Draw(canvas)
    d.text((8,4),camera+' | XY pose probes, fixed height and heading | WORKING_VALUE',fill='white')
    paths=[(s.ROOT/ref.get('comparison_photo',ref['photo']),'PHOTO '+ref['author']+' | '+ref['license'],0,28)]
    for i,p in enumerate(group):
        paths.append((s.ROOT/'artifacts/sbs-r1/pose-renders'/(p['probe']+'.png'),f"E {p['east_delta_m']:+g}m N {p['north_delta_m']:+g}m",(i%3)*320,292+(i//3)*264))
    for path,label,x,y in paths:
        with Image.open(path) as im:thumb=ImageOps.contain(im.convert('RGB'),(318,238))
        canvas.paste(thumb,(x,y+20));d.text((x+4,y+2),label,fill='white')
    d.text((330,50),ref['page_url'],fill='white')
    d.text((330,70),'Photo is rectified; candidate renders are diagnostics only.',fill='white')
    canvas.save(out/(camera+'.jpg'),quality=92)
print('Saved',len(list(out.glob('*.jpg'))),'pose galleries at width 960')
