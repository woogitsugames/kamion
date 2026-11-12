"""Own EC landmark geometry and fail-safe asset replacement, ADR 0116 r3."""
import copy
import hashlib
import json

import numpy as np
import pytest

from conftest import REPO, REGION_ID
from streetscape import ec_chimneys as EC, hero_building as HB


def overrides():
    from roads.pipeline import load_overrides
    return [o for o in load_overrides(REGION_ID) if EC.entry(o,EC.config())]


@pytest.mark.parametrize('index',[0,1])
def test_authored_specs_preserve_locations_heights_and_building_footprints(index):
    cfg=EC.config(); o=overrides()[index]; d=EC.entry(o,cfg)
    spec=EC.make_spec(o,d,cfg,[777995,596223],lambda e,n:137.25)
    assert spec['anchor']==[round(o['epsg2180'][0]-777995,3),round(o['epsg2180'][1]-596223,3),137.25]
    assert spec['chimney']['height_m']==o['height_m']==120
    assert spec['buildings']==[] and spec['footprints']=={}
    assert HB.targets([dict(spec=spec)])=={}
    assert HB.keepout([dict(spec=spec)])==[]
    assert HB.fence_cut([dict(spec=spec)])==[]
    assert spec==EC.make_spec(o,d,cfg,[777995,596223],lambda e,n:137.25)


@pytest.mark.parametrize('index',[0,1])
def test_lods_use_existing_material_budgets_and_have_vertical_axes(index):
    cfg=EC.config(); d=EC.entry(overrides()[index],cfg)
    lods=EC.meshes(d)
    assert len(lods)==2
    assert {p['mat'] for p in lods[0]}=={'chimney_white','chimney_red','chimney_concrete','gantry_steel'}
    assert {p['mat'] for p in lods[1]}=={'chimney_white','chimney_red','chimney_concrete'}
    for lod in lods:
        V=np.concatenate([p['V'] for p in lod])
        assert np.isfinite(V).all()
        assert V[:,2].min()==-1 and V[:,2].max()==120
        for p in lod:
            assert np.isfinite(p['UV']).all()
            assert p['T'].min()>=0 and p['T'].max()<len(p['V'])
        # The shaft's opposite vertices have the same centre at every paint seam.
        for z in d['band_boundaries_m'][:-1]:
            shell=V[np.isclose(V[:,2],z)]
            assert np.max(np.abs((shell[:,:2].min(0)+shell[:,:2].max(0))/2))<1e-8
    assert sum(len(p['T']) for p in lods[1])<sum(len(p['T']) for p in lods[0])


@pytest.mark.parametrize('change',[
    dict(height_m=119),dict(top_d_m=float('nan')),dict(band_boundaries_m=[]),
    dict(band_boundaries_m=[60,48,120]),dict(outlets=4),dict(galleries_m=[125])])
def test_invalid_dimensions_preserve_generic_fallback(change):
    cfg=EC.config(); o=overrides()[0]; d=copy.deepcopy(EC.entry(o,cfg)); d.update(change)
    assert not EC.valid_dimensions(d,o)
    assert EC.make_spec(o,d,cfg,[777995,596223],lambda e,n:137.) is None


def test_disabled_or_unrelated_override_never_suppresses_a_generic_instance(monkeypatch):
    o=overrides()[0]
    monkeypatch.setattr(EC,'config',lambda:None)
    assert EC.active(o,[777995,596223]) is None
    assert EC.entry(dict(kind='sign_gantry',osm_way=o['osm_way']),{'stacks':{str(o['osm_way']):{}}}) is None


def test_missing_stale_and_changed_assets_cannot_suppress_generic(tmp_path,monkeypatch):
    cfg=EC.config(); o=overrides()[0]; d=EC.entry(o,cfg)
    spec=EC.make_spec(o,d,cfg,[777995,596223],lambda e,n:137.)
    sp=tmp_path/'spec.json'; gp=tmp_path/'asset.glb'; mp=tmp_path/'meta.json'
    monkeypatch.setattr(HB,'spec_path',lambda *a:sp)
    monkeypatch.setattr(HB,'asset_paths',lambda *a:(tmp_path,gp,mp))
    assert EC.active(o,[777995,596223]) is None
    sp.write_text(json.dumps(spec))
    assert EC.active(o,[777995,596223]) is None
    gp.write_bytes(b'fixture payload')
    meta=dict(prototype='landmark_'+d['asset'],spec_sha256=HB._sha(spec),glb_sha256=hashlib.sha256(gp.read_bytes()).hexdigest())
    mp.write_text(json.dumps(meta))
    assert EC.active(o,[777995,596223])==meta
    gp.write_bytes(b'modified payload')
    assert EC.active(o,[777995,596223]) is None
    gp.write_bytes(b'fixture payload')
    changed=copy.deepcopy(cfg); changed['stacks'][str(o['osm_way'])]['paint_start_m']+=1
    monkeypatch.setattr(EC,'config',lambda:changed)
    assert EC.active(o,[777995,596223]) is None
    monkeypatch.setattr(EC,'config',lambda:cfg)
    changed_spec=copy.deepcopy(spec); changed_spec['builder_sha256']='stale'
    sp.write_text(json.dumps(changed_spec))
    assert EC.active(o,[777995,596223]) is None


def test_authored_assets_are_byte_deterministic_and_fresh(tmp_path,monkeypatch):
    cfg=EC.config(); o=overrides()[1]; d=EC.entry(o,cfg)
    spec=EC.make_spec(o,d,cfg,[777995,596223],lambda e,n:137.)
    gp=tmp_path/'ec.glb'; mp=tmp_path/'meta.json'
    monkeypatch.setattr(HB,'asset_paths',lambda *a:(tmp_path,gp,mp))
    first=EC.build_asset(spec); payload=gp.read_bytes()
    assert first==EC.build_asset(spec) and payload==gp.read_bytes()
    assert HB._asset_meta(d['asset'],HB._sha(spec))==(first,'ok')
    assert first['materials_per_lod'][1]==['chimney_concrete','chimney_red','chimney_white']


@pytest.mark.parametrize('verified',[False,True])
def test_landmark_registration_and_hero_application_never_duplicate_a_chimney(monkeypatch,verified):
    from streetscape import landmarks as LM
    cfg=EC.config(); o=overrides()[0]; d=EC.entry(o,cfg)
    meta=dict(prototype='landmark_'+d['asset'],tris=[100,50,50],glb_sha256='fixture',materials=[])
    monkeypatch.setattr(EC,'active',lambda *a:meta if verified else None)
    monkeypatch.setattr(LM.LP,'LANDMARKS',{})
    class Placer:
        def __init__(self): self.items=[]
        def add(self,name,p,yaw,**kw): self.items.append(dict(p=name,src=kw['src']))
    placer=Placer(); report={}
    LM.build(placer,None,dict(nodes=[]),[o],[777995,596223],{},report)
    instances=placer.items
    if verified:
        spec=EC.make_spec(o,d,cfg,[777995,596223],lambda e,n:137.)
        HB.apply(None,[dict(override=o,spec=spec,meta=meta,sha='fixture')],instances,{})
    assert len(instances)==1
    assert instances[0]['src']=='override:'+o['id']
    assert instances[0]['p']==(meta['prototype'] if verified else 'landmark_chimney_120_75')


def test_generated_world_has_exactly_one_authored_instance_per_chimney():
    folder=REPO/'Data/Regions'/REGION_ID/'generated'
    qa=json.loads((folder/'streetscape_qa.json').read_text())
    applied={x['id']:x for x in qa['hero_buildings']['applied']}
    for o in overrides():
        assert o['id'] in applied
        assert applied[o['id']]['asset']==EC.entry(o,EC.config())['asset']
    instances=[]
    for p in (REPO/'Data/raw/derived'/REGION_ID/'world').glob('instances_*.json'):
        value=json.loads(p.read_text())
        instances.extend(value['instances'] if isinstance(value,dict) else value)
    for o in overrides():
        matches=[it for it in instances if it.get('src')=='override:'+o['id']]
        assert len(matches)==1
        assert matches[0]['p']=='landmark_'+EC.entry(o,EC.config())['asset']
