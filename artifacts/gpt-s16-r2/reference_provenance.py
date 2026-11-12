"""Safe local provenance subset; no access-bearing image URLs or tokens."""
import hashlib,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[2];r=Path(__file__).parent
text=(root/'docs/refs/posesje-bialystok.md').read_text(encoding='utf-8-sig')
manifest={str(x['id']):x for line in (root/'Data/raw/mapillary/posesje/manifest.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip() for x in [json.loads(line)]}
rows=[]
for ref in ('P07','P08','P10','P12','P14','P17'):
 match=re.search(r'^\| '+ref+r' \| \[(\d+)\]',text,re.M)
 assert match,ref
 key=match[1];entry=manifest[key];file=Path(entry['file']);file=file if file.is_absolute() else root/file
 if not file.exists():file=root/'Data/raw/mapillary/posesje'/Path(entry['file']).name
 digest=hashlib.sha256(file.read_bytes()).hexdigest();assert digest==entry['sha256'],ref
 rows.append({'reference':ref,'id':key,'file':str(file.relative_to(root)),'sha256':digest,'author':entry['author'],'captured_at':entry['captured_at'],'license':entry['license'],'license_url':entry['license_url'],'page_url':'https://www.mapillary.com/app/?pKey='+key,'relation':'typological only; not same street/pose as rendered region','scope':'QA reference; pixels not used in game textures'})
(r/'reference-provenance.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Verified local reference files:',len(rows))
