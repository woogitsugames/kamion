from pathlib import Path
import hashlib,json,subprocess,shutil
root=Path.cwd();out=root/'artifacts/truck-paint-r1/baseline-fixture';out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=root/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json';m=json.loads(manifest.read_text())
verified=[]
def walk(node):
 if isinstance(node,dict):
  if 'file' in node and 'sha256' in node:
   p=root/node['file'];actual=sha(p);assert actual==node['sha256'],str(p);verified.append({'file':node['file'],'sha256':actual})
  for v in node.values():walk(v)
 elif isinstance(node,list):
  for v in node:walk(v)
walk(m)
assert len(verified)==192,len(verified)
qa=json.loads((root/'Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json').read_text())['furniture']['megascans']
assert len(qa['available'])==15 and qa['added_props']==320 and qa['drainage_replacements']>=954,qa
sources=[]
for folder in ['art-source/truck/exterior/export','art-source/truck/interior/export','art-source/truck/trailer/export']:
 for p in sorted((root/folder).rglob('*')):
  if p.is_file() and p.suffix.lower() in ['.fbx','.json','.png']:
   sources.append({'file':str(p.relative_to(root)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size})
production=[]
for name in ['game/Assets/_Project/Rendering/Shaders/TruckExterior.shader','game/Assets/_Project/Rendering/Shaders/TruckGlass.shader','game/Assets/_Project/Rendering/Shaders/KamionVehicleEnv.hlsl','game/Assets/_Project/Vehicle/Runtime/TruckLights.cs','game/Assets/_Project/Editor/Setup/TruckAssetBuilder.cs','game/Assets/_Project/Editor/Setup/TrailerAssetBuilder.cs','game/Assets/_Project/Rendering/Runtime/Truck/VehicleReflectionCapture.cs']:
 p=root/name;production.append({'file':name,'sha256':sha(p)})
 assert not subprocess.check_output(['git','diff','HEAD','--',name],text=True),name
assets=[]
for name in ['Truck','Trailer']:
 src=root/'game/Assets/_Generated'/name
 shutil.copytree(src,out/name,dirs_exist_ok=True)
 for p in sorted(src.rglob('*')):
  if p.is_file():assets.append({'file':str(p.relative_to(root)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size})
evidence={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'world_manifest_sha256':sha(manifest),'world_raw_verified':verified,'fab_actual_qa':qa,'source_assets':sources,'production_sources':production,'canonical_generated_assets':assets,'note':'Immutable pre-change canonical binary snapshot for material/shader comparisons; all truck/trailer builders/install completed first.'}
(out/'fixture-proof.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
print('BASELINE_PROOF: world192 verified, Fab15 available/320props, source assets',len(sources),'canonical snapshot files',len(assets))
