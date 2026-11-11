"""Resumable before/final contact pages; original PNGs are never modified."""
import json
from PIL import Image,ImageDraw
from bus_world_proof import OUT
KEYS={'d-wear-lane-old','d-wear-crossing','d-wear-missing-uv-1','d-wear-missing-uv-2','d-wear-newroad-negative','d-wear-patch-putry','d-wear-gate-tracks','fire-station-ref7197','stretch-05-docks','truck-front','truck-side','truck-at-gate','cab-driver'}
def main():
    baseline=json.loads((OUT/'baseline-capture-proof.json').read_text());report=[]
    for spec in baseline['rows']:
        stage='after'if spec['stage']=='before'else'after-legacy';cond=spec['condition'];directory=OUT/stage/cond
        if not directory.exists()or {f.stem for f in directory.glob('*.png')}!=set(spec['ids']):continue
        dest=OUT/'final-review-960'/stage/cond;dest.mkdir(parents=True,exist_ok=True);ids=sorted(spec['ids'])
        for offset in range(0,len(ids),12):
            batch=ids[offset:offset+12];board=Image.new('RGB',(960,129*((len(batch)+1)//2)),'#222');draw=ImageDraw.Draw(board)
            for n,name in enumerate(batch):
                x=(n%2)*480;y=(n//2)*129;draw.text((x+3,y+2),cond+' | '+name,fill='white')
                for side,path in enumerate([OUT/spec['stage']/cond/(name+'.png'),directory/(name+'.png')]):
                    im=Image.open(path).convert('RGB');im.thumbnail((240,111));board.paste(im,(x+side*240,y+18))
            board.save(dest/f'paired-page-{offset//12+1:02d}.jpg',quality=94)
        for name in ids:
            if name.replace('_','-')not in KEYS:continue
            board=Image.new('RGB',(960,924),'#222');draw=ImageDraw.Draw(board)
            for i,(path,label)in enumerate([(OUT/spec['stage']/cond/(name+'.png'),'Original pristine BEFORE'),(directory/(name+'.png'),'Selected production1dc FINAL')]):
                im=Image.open(path).convert('RGB');im.thumbnail((960,444));board.paste(im,(0,i*462+18));draw.text((8,i*462+3),cond+' | '+name+' | '+label,fill='white')
            board.save(dest/('fullpair-'+name+'.jpg'),quality=94)
        report.append(dict(stage=stage,condition=cond,paired_frames=len(ids),pages=(len(ids)+11)//12));print(stage,cond,len(ids),'paired')
    (OUT/'final-review-pages.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
