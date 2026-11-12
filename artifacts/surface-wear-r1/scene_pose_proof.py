"""Compare actual preserved canonical scenes/prefabs, not merely their raw world input hashes."""
from pathlib import Path
import re,json,hashlib
import numpy as np
import yaml
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
BASE=OUT/'baseline-canonical'

def parse(p):
    pieces=re.split(r'(?m)^--- !u!(\d+) &(-?\d+)[^\n]*\n',p.read_text(encoding='utf-8'))
    result={}
    for i in range(1,len(pieces),3):
        kind,id=int(pieces[i]),int(pieces[i+1])
        if kind not in (1,4,20,114,1001):continue
        if kind==114 and CONTROL_GUID not in pieces[i+2]:continue
        value=yaml.load(pieces[i+2],Loader=yaml.CSafeLoader)
        result[id]=(kind,next(iter(value.values())))
    return result

def ref(x):return int(x.get('fileID',0))
def matrix(v):
    p=v.get('m_LocalPosition',dict(x=0,y=0,z=0));q=v.get('m_LocalRotation',dict(x=0,y=0,z=0,w=1));s=v.get('m_LocalScale',dict(x=1,y=1,z=1))
    x,y,z,w=(q[k]for k in 'xyzw');m=np.eye(4)
    m[:3,:3]=np.array([[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]])@np.diag([s[k]for k in 'xyz'])
    m[:3,3]=[p[k]for k in 'xyz'];return m

def scene(path,base):
    records=parse(path);prefabs={};roles={}
    for role,file in [('truck','game/Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab'),('trailer','game/Assets/_Generated/Trailer/Trailer_Curtainsider_Art.prefab')]:
        asset=base/file;guid=re.search(r'guid: (\w+)',Path(str(asset)+'.meta').read_text())[1]
        data=parse(asset);prefabs[guid]=data;roles[guid]=role
    transforms={i:dict(v)for i,(kind,v)in records.items()if kind==4};instances={}
    for i,(kind,v)in records.items():
        if kind!=1001:continue
        guid=v.get('m_SourcePrefab',{}).get('guid')
        if guid not in roles:continue
        source=prefabs[guid];root_id=next(j for j,(k,x)in source.items()if k==4 and ref(x.get('m_Father',{}))==0)
        root=dict(source[root_id][1]);root['m_LocalPosition']=dict(root['m_LocalPosition']);root['m_LocalRotation']=dict(root['m_LocalRotation']);root['m_LocalScale']=dict(root['m_LocalScale'])
        for mod in v['m_Modification'].get('m_Modifications',[]):
            if ref(mod['target'])!=root_id:continue
            prop=mod['propertyPath'].split('.')
            if len(prop)==2 and prop[0]in('m_LocalPosition','m_LocalRotation','m_LocalScale'):root[prop[0]][prop[1]]=float(mod['value'])
        instances[i]=(roles[guid],root)
    for i,v in transforms.items():
        instance=ref(v.get('m_PrefabInstance',{}))
        if instance in instances:
            role,root=instances[instance];source=v.get('m_CorrespondingSourceObject',{});guid=source.get('guid');sid=ref(source)
            if guid in prefabs and sid in prefabs[guid]:
                actual=dict(prefabs[guid][sid][1]);actual.update({k:x for k,x in v.items()if k not in('m_GameObject','m_Father')})
                if ref(prefabs[guid][sid][1].get('m_Father',{}))==0:actual.update(root);actual['m_Father']={'fileID':0}
                transforms[i]=actual
    go_to_transform={ref(v.get('m_GameObject',{})):i for i,v in transforms.items()if ref(v.get('m_GameObject',{}))}
    def world(i,seen=None):
        if not i:return np.eye(4)
        if i not in transforms:return np.eye(4)
        seen=set()if seen is None else seen
        assert i not in seen;seen.add(i);v=transforms[i]
        return world(ref(v.get('m_Father',{})),seen)@matrix(v)
    cameras={ref(v.get('m_GameObject',{})):v for k,v in records.values()if k==20}
    control={}
    for kind,v in records.values():
        if kind!=114 or 'id'not in v:continue
        go=ref(v['m_GameObject']);cam=cameras.get(go)
        if cam is None:continue
        t=go_to_transform[go];control[v['id']]=dict(world_matrix=np.round(world(t),7).tolist(),local_position=transforms[t].get('m_LocalPosition'),local_rotation=transforms[t].get('m_LocalRotation'),fov=cam.get('field of view'),orthographic=cam.get('orthographic'),near=cam.get('near clip plane'),far=cam.get('far clip plane'))
    roots={role:{k:root[k]for k in('m_LocalPosition','m_LocalRotation','m_LocalScale')}for role,root in instances.values()}
    return dict(roots=roots,controls=control,note='Serialized effective transforms including prefab-root overrides. Runtime view-specific pose changes are NOT inferred from this packet.')

CONTROL_GUID=re.search(r'guid: (\w+)',(ROOT/'game/Assets/_Project/Rendering/Runtime/ControlCamera.cs.meta').read_text())[1]
def prefab_transforms(path):
    records=parse(path);names={i:v.get('m_Name','')for i,(k,v)in records.items()if k==1};trs={i:v for i,(k,v)in records.items()if k==4}
    def route(i):
        v=trs[i];name=names.get(ref(v.get('m_GameObject',{})),'UNKNOWN');parent=ref(v.get('m_Father',{}))
        return(route(parent)+'/'if parent in trs else'')+name
    rows={}
    for i,v in trs.items():rows.setdefault(route(i),[]).append({k:v.get(k)for k in('m_LocalPosition','m_LocalRotation','m_LocalScale')})
    return {k:sorted(v,key=lambda x:json.dumps(x,sort_keys=True))for k,v in rows.items()}

def main():
    fixture=json.loads((OUT/'baseline-canonical-fixture.json').read_text());assets=[]
    for f in fixture['files']:
        if not('/_Generated/Truck/'in f['file']or'/_Generated/Trailer/'in f['file']):continue
        p=ROOT/f['file'];h=hashlib.sha256(p.read_bytes()).hexdigest();assets.append(dict(file=f['file'],identical=h==f['sha256']))
    prefab_pose=[]
    for file in ['game/Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab','game/Assets/_Generated/Trailer/Trailer_Curtainsider_Art.prefab']:
        a=prefab_transforms(BASE/file);b=prefab_transforms(ROOT/file);prefab_pose.append(dict(file=file,transform_count_before=sum(map(len,a.values())),transform_count_after=sum(map(len,b.values())),differences={k:dict(before=v,after=b.get(k))for k,v in a.items()if v!=b.get(k)},added_paths=sorted(b.keys()-a.keys())))
    rows=[]
    for name in ('WorldC','WorldC_High'):
        rel=f'game/Assets/_Generated/World/bialystok-industrial-c/{name}.unity';a=scene(BASE/rel,BASE);b=scene(ROOT/rel,ROOT)
        differences={k:dict(before=v,after=b['controls'].get(k))for k,v in a['controls'].items()if v!=b['controls'].get(k)}
        rows.append(dict(scene=name,roots_identical=a['roots']==b['roots'],root_before=a['roots'],root_after=b['roots'],camera_count_before=len(a['controls']),camera_count_after=len(b['controls']),camera_differences=differences))
    packet=dict(vehicle_assets=len(assets),vehicle_asset_mismatches=[x['file']for x in assets if not x['identical']],prefab_transform_comparison=prefab_pose,scenes=rows,note='Actualprivatebefore files vs currentbus-onlycanonical import+Install. Serialized proof only; nextplannedrender must dump actual runtime camera/vehicle/trailer poses. No372pixelstable claim.')
    (OUT/'scene-pose-proof.json').write_text(json.dumps(packet,indent=2)+'\n');print(json.dumps(packet))
if __name__=='__main__':main()
