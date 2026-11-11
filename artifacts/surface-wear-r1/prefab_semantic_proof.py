"""Normalize local serialized file IDs by actual object hierarchy/component identity."""
from pathlib import Path
import re,json
import yaml
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent

def normalized(path):
    pieces=re.split(r'(?m)^--- !u!(\d+) &(-?\d+)[^\n]*\n',path.read_text())
    records={}
    for i in range(1,len(pieces),3):
        d=yaml.load(pieces[i+2],Loader=yaml.CSafeLoader);records[int(pieces[i+1])]=(int(pieces[i]),next(iter(d.values())))
    transforms={i:v for i,(k,v)in records.items()if k==4}
    go_to_transform={v['m_GameObject']['fileID']:i for i,v in transforms.items()}
    def route(i):
        v=transforms[i];go=records[v['m_GameObject']['fileID']][1];parent=v.get('m_Father',{}).get('fileID',0)
        return(route(parent)+'/'if parent in transforms else'')+go['m_Name']
    keys={}
    for i,(kind,v)in records.items():
        go=i if kind==1 else v.get('m_GameObject',{}).get('fileID')
        name=route(go_to_transform[go])if go in go_to_transform else v.get('m_Name','ROOT')
        script=v.get('m_Script',{}).get('guid','')if kind==114 else''
        keys[i]=f'{kind}:{script}@{name}'
    def norm(v):
        if isinstance(v,dict):
            if set(v)=={'fileID'}and v['fileID']in keys:return {'local_object':keys[v['fileID']]}
            return {k:norm(x)for k,x in v.items()}
        if isinstance(v,list):return [norm(x)for x in v]
        if isinstance(v,float)and v==0:return 0
        return v
    groups={}
    for i,(kind,v)in records.items():groups.setdefault(keys[i],[]).append(norm(v))
    return {k:sorted(v,key=lambda x:json.dumps(x,sort_keys=True))for k,v in groups.items()}

def main():
    rows=[]
    for file in ['game/Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab','game/Assets/_Generated/Trailer/Trailer_Curtainsider_Art.prefab']:
        a=normalized(OUT/'baseline-canonical'/file);b=normalized(ROOT/file)
        diff={k:dict(before=v,after=b.get(k))for k,v in a.items()if v!=b.get(k)}
        rows.append(dict(file=file,serialized_records_before=sum(map(len,a.values())),serialized_records_after=sum(map(len,b.values())),changed_semantic_records=diff,added_keys=sorted(b.keys()-a.keys()),duplicate_identity_groups=[k for k,v in a.items()if len(v)>1]))
    packet=dict(note='Actualpreserved canonicalprefabs vs bus-onlyinstalledprefabs. LocalfileIDs normalized toGameObjecthierarchy+componentclass/scriptGUID, signedzeros normalized. Duplicateidentitygroups explicitlylisted; not a runtimeposeclaim.',prefabs=rows)
    (OUT/'prefab-semantic-proof.json').write_text(json.dumps(packet,indent=2)+'\n');print(json.dumps(packet))
if __name__=='__main__':main()
