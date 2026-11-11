from pathlib import Path
import json,hashlib,re,sys,yaml
root=Path.cwd();base=root/'artifacts/truck-paint-r1'
proof=json.loads((base/'baseline-fixture/fixture-proof.json').read_text())
changed=[]
for r in proof['canonical_generated_assets']:
 p=root/r['file'];actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
 if actual!=r['sha256']:changed.append({'file':r['file'],'before_sha256':r['sha256'],'candidate_sha256':actual})
def transforms(path):
 text=path.read_text(encoding='utf-8-sig');text=re.sub(r'^%.*\n','',text,flags=re.M)
 text=re.sub(r'^--- !u!(\d+) &(\d+)\s*$',lambda m:'---\n__type: '+m[1]+'\n__id: '+m[2],text,flags=re.M)
 docs=list(yaml.safe_load_all(text));gos={d['__id']:d['GameObject'] for d in docs if d['__type']==1}
 ts={d['__id']:d['Transform'] for d in docs if d['__type']==4}
 cache={}
 def name(i):
  if not i:return ''
  if i in cache:return cache[i]
  t=ts[i];cache[i]=name(t['m_Father']['fileID'])+'/'+gos[t['m_GameObject']['fileID']]['m_Name'];return cache[i]
 result={}
 for i,t in ts.items():
  k=name(i)
  if k in result:raise ValueError('Duplicate hierarchy path '+k)
  result[k]={v:t[v] for v in ['m_LocalPosition','m_LocalRotation','m_LocalScale']}
 return result
before=transforms(base/'baseline-fixture/Truck/Tractor4x2_TRAKT.prefab');after=transforms(root/'game/Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab')
paths=sorted(set(before)|set(after));pose=[{'path':p,'before':before.get(p),'after':after.get(p)} for p in paths if before.get(p)!=after.get(p)]
mesh_changes=[r for r in changed if '/Meshes/' in r['file'] or r['file'].lower().endswith('.fbx')]
stage=sys.argv[1] if len(sys.argv)>1 else 'candidate1-partial'
result={'stage':stage,'baseline_files':len(proof['canonical_generated_assets']),'changed_files':changed,'mesh_or_fbx_changes':mesh_changes,'truck_transform_nodes_before':len(before),'truck_transform_nodes_after':len(after),'truck_pose_or_hierarchy_changes':pose,'note':'Ignores nondeterministic prefab fileIDs; compares hierarchy paths/local transforms. Binary source meshes separately hashed. Not a rendered budget/GPU claim.'}
(base/(stage+'-fixture-proof.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('mesh/fbx changes',len(mesh_changes),'transform nodes',len(before),len(after),'semantic pose changes',len(pose),'total changedfiles',len(changed))
