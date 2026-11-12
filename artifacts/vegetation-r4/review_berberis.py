"""Fixed before/after crops and costs; photo is appearance-only, pose unverified."""
import argparse
import json
import runpy
from pathlib import Path
from PIL import Image,ImageDraw

here=Path(__file__).resolve().parent
root=here.parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--after-root',default='probe-a')
parser.add_argument('--snapshot',default='candidate-a')
parser.add_argument('--before-root',default='before',help='Explicit ablation baseline; final budget still uses before')
parser.add_argument('--native-crop',action='store_true',help='Fixed470px subset of each ROI, without crop resampling')
args=parser.parse_args()
snapshot_path=here/('snapshot-'+args.snapshot)/'sha256.json'
snapshot=json.loads(snapshot_path.read_text())
stats=runpy.run_path(str(here/'review_images.py'))['stats']
reference=json.loads((here/'berberis-reference.json').read_text())
photo=Image.open(root/reference['local_photo']).convert('RGB')
evidence_label=args.after_root if args.before_root=='before' else args.after_root+'-vs-'+args.before_root
if args.native_crop:
    evidence_label+='-native'
out=here/('berberis-review-'+evidence_label)
out.mkdir(exist_ok=True)
rois={'g3a-rondo-bie-approach':(0,.54,.27,.69),
      'photo-biezenstwa-ground':(.72,.54,1,.73)}
costs=[]
actual_rois={}
for tier in ('Low','High'):
    for lighting in ('overcast','clear'):
        group=tier+'-'+lighting
        before_dir,after_dir=here/args.before_root/group,here/args.after_root/group
        before_stats,after_stats=stats(before_dir/'stats.txt'),stats(after_dir/'stats.txt')
        for camera,new in after_stats.items():
            old=before_stats[camera]
            costs.append(dict(camera=camera,group=group,before=old,after=new,
                delta_draws=new['total_draws']-old['total_draws'],
                delta_triangles_percent=100*(new['total_triangles_k']/old['total_triangles_k']-1)))
        for camera,roi in rois.items():
            before_path,after_path=before_dir/(camera+'.png'),after_dir/(camera+'.png')
            if after_path.stat().st_mtime<snapshot_path.stat().st_mtime:
                raise SystemExit('After frame predates candidate snapshot')
            frames=[Image.open(p).convert('RGB') for p in (before_path,after_path)]
            if frames[0].size!=frames[1].size:
                raise SystemExit('Before/after dimensions differ')
            sheet=Image.new('RGB',(960,1070),'#222222')
            draw=ImageDraw.Draw(sheet)
            ref=photo.copy();ref.thumbnail((950,420));sheet.paste(ref,(5,25))
            draw.text((5,5),'Rakoon | 2020-11-02 | CC0 | APPEARANCE ONLY; POSE UNVERIFIED',fill='white')
            for i,(label,frame) in enumerate(zip(('BEFORE','CANDIDATE'),frames)):
                x=i*490
                full=frame.copy();full.thumbnail((470,220));sheet.paste(full,(x,475))
                draw.text((x+3,452),label+' '+group+' '+camera,fill='white')
                w,h=frame.size
                box=list(round(v*s) for v,s in zip(roi,(w,h,w,h)))
                if args.native_crop:
                    if camera=='g3a-rondo-bie-approach':
                        box[2]=min(box[2],box[0]+470)
                    else:
                        box[0]=max(box[0],box[2]-470)
                actual_rois[group+'/'+camera]=box
                crop=frame.crop(box)
                if not args.native_crop:
                    crop.thumbnail((470,290))
                sheet.paste(crop,(x,730))
                draw.text((x+3,707),label+(' native1:1 pixels' if args.native_crop else ' fixed crop')+'; no segmentation',fill='white')
            draw.text((5,1035),'Same render pose before/after. Reference pose/season differ. Not measured dimensions or GPU time.',fill='white')
            sheet.save(out/(group+'-'+camera+'.jpg'),quality=93)
low=[r for r in costs if r['group'].startswith('Low-')]
result=dict(snapshot_source_sha=snapshot['source_sha'],after_root=args.after_root,before_root=args.before_root,
    reference=reference,fixed_rois=rois,actual_crop_pixels=actual_rois,native_crop=args.native_crop,all_probe_costs=costs,
    maximum_low_draw_delta=max(r['delta_draws'] for r in low),
    maximum_low_triangle_delta_percent=max(r['delta_triangles_percent'] for r in low),
    note='Limited probe only; static/instance draws separate, integer trisK precision. No full-camera acceptance or GPU timing. Ablation baseline is not the final budget baseline.')
(here/(evidence_label+'-comparison.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('Sheets:',len(list(out.glob('*.jpg'))),'Probe camera-condition rows:',len(costs))
print('Low maximum draws delta:',result['maximum_low_draw_delta'],
      'Low maximum triangle % delta:',result['maximum_low_triangle_delta_percent'])
