"""Small offline photographic research for the remaining vegetation backlog."""
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw

here=Path(__file__).resolve().parent
root=here.parents[1]
main=Path('C:/Users/matma/Documents/Claude/kamion')
ids=('1528935774382039','500263111404933','320326319617139','209622370971977','468026894483428')
references=json.loads((root/'Data/Regions/bialystok-industrial-c/sbs_references.json').read_text(encoding='utf-8-sig'))['references']
by_id={r['source_id']:r for r in references}
sheet=Image.new('RGB',(960,3*405+60),'#222222')
draw=ImageDraw.Draw(sheet)
rows=[]
for i,sid in enumerate(ids):
    x,y=(i%2)*490,(i//2)*405
    if sid not in by_id:
        draw.text((x+3,y+4),sid+' NOT IN PROVIDED REFERENCE INDEX',fill='white')
        rows.append(dict(source_id=sid,status='not in supplied index'))
        continue
    reference=by_id[sid]
    path=main/reference['photo']
    if not path.exists():raise FileNotFoundError(path)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if reference.get('sha256') and digest!=reference['sha256']:
        raise SystemExit('Raw photo hash changed: '+sid)
    frame=Image.open(path).convert('RGB')
    original_size=frame.size
    frame.thumbnail((470,350))
    sheet.paste(frame,(x,y+43))
    draw.text((x+3,y+4),sid+' | '+str(reference.get('pose_confidence','UNVERIFIED')),fill='white')
    draw.text((x+3,y+22),reference['author']+' | '+reference['captured_at']+' | '+reference['license'],fill='white')
    rows.append(dict(source_id=sid,photo=str(path),sha256=digest,width=original_size[0],height=original_size[1],
        author=reference['author'],captured_at=reference['captured_at'],license=reference['license'],
        page_url=reference['page_url'],pose_confidence=reference.get('pose_confidence','UNVERIFIED'),
        use='Visual reference only; no game texture or surveyed geometry inference'))
draw.text((5,1225),'Original supplied photos; appearance research only. Poses and different capture dates constrain spatial conclusions.',fill='white')
sheet.save(here/'verges-reference-overview.jpg',quality=93)
(here/'verges-reference-research.json').write_text(json.dumps(dict(references=rows,production_changes=False),indent=2)+'\n',encoding='utf-8')
print('Supplied source photographs reviewed in overview:',sum(r.get('sha256') is not None for r in rows))
