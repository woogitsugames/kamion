from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path.cwd(); base=root/'artifacts/truck-paint-r1'
before=json.loads((base/'gis-input-before.json').read_text()); expected={r['file']:r for r in before['files']}
changes=[];restored=[];unrestored=[]
for relative,row in expected.items():
 p=root/relative; actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
 if actual==row['sha256']:continue
 changes.append(dict(file=relative,before_sha256=row['sha256'],after_sha256=actual))
 backup=base/'gis-pre-fixture'/relative
 if backup.is_file() and hashlib.sha256(backup.read_bytes()).hexdigest()==row['sha256']:
  if p.is_file():
   archive=base/'gis-mutated-products'/relative;archive.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,archive)
  p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(backup,p)
  if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise RuntimeError('Restore failed '+relative)
  restored.append(relative)
 else:unrestored.append(relative)
found=set()
for folder in ['Data/Regions','Data/raw/derived','art-source/world','game/Assets/_Generated','tools/worldgen']:
 for p in (root/folder).rglob('*'):
  if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts and '.venv' not in p.parts:found.add(p.relative_to(root).as_posix())
added=sorted(found-set(expected))
packet=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),pinned_files=len(expected),before_pin_sha256=hashlib.sha256((base/'gis-input-before.json').read_bytes()).hexdigest(),changes=changes,restored_exactly=restored,unrestored=unrestored,new_files_in_scopes=added,canonical_inputs_restored_or_unchanged=not unrestored,note='Each prior input rehashed. Any changed backed-up canonical asset/JSON archived and restored byte-exactly before future renders. New files reported, never silently deleted.')
(base/'gis-input-after.json').write_text(json.dumps(packet,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in packet.items() if k not in ['changes']},indent=2))
if unrestored:raise SystemExit(1)
