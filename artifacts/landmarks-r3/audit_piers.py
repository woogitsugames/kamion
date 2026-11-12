"""Underdeck correction: same deck buffers, no new stairs, patches or materials."""
import hashlib
import json
import subprocess
from pathlib import Path

out=Path(__file__).resolve().parent
root=out.parents[1]
rel='Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_putry_underdeck.spec.json'
old_bytes=subprocess.run(['git','show','13db2baa:'+rel],cwd=root,check=True,capture_output=True).stdout
old_specs=json.loads(old_bytes)
new_specs=json.loads((root/rel).read_text())
qa_before=json.loads((out/'baseline-generated/streetscape_qa.json').read_text())['hero_bridges']['underdeck']
qa_after=json.loads((root/'Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json').read_text())['hero_bridges']['underdeck']
def canonical_sha(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
by_sha={canonical_sha(s):s for s in old_specs}
assert set(by_sha)=={q['spec_sha256'] for q in qa_before},'Archived spec not the fresh baseline'
assert len(old_specs)==len(new_specs)==len(qa_before)==len(qa_after)==2
after_by_chain={r['chain']:r for r in qa_after}
rows=[]
for old in qa_before:
    new=after_by_chain[old['chain']]
    assert old['deck_before_sha256']==old['deck_after_sha256']==new['deck_before_sha256']==new['deck_after_sha256']
    assert new['new_materials']==[] and new['vegetation_added']==0
    assert new['deck_barriers_unchanged'] is True
    rows.append(dict(chain=old['chain'],deck_sha256=new['deck_after_sha256'],
                     net_tris_before=old['added_net_tris'],net_tris_after=new['added_net_tris'],
                     delta_net_tris=new['added_net_tris']-old['added_net_tris']))
for old,new in zip(old_specs,new_specs):
    assert old['decks']==new['decks']
    assert old['stairs']==new['stairs']==[[],[]]
    assert new['params']['unpainted_chamfers'] is False
    assert new['params']['paint_blobs'] is False
    assert new['params']['paint_weathering'] is True
result=dict(complete=True,baseline_spec_verified_against_fresh_qa=True,all_deck_buffers_identical=True,
            deck_specs_identical=True,stairs_disabled=True,bare_chamfers_disabled=True,abstract_paint_patch_disabled=True,
            weather_retained=True,new_materials=[],rows=rows,
            scope='Exact generator deck V/T/UV hashes and full deck specs; preservation of UV1/COL and collision additionally covered by focused tests and GLB primitive audit')
(out/'pier-geometry-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
