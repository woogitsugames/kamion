"""Stream-check rendered runtime data and owned source inputs around final tests."""
import hashlib
import json
import sys
from pathlib import Path

out=Path(__file__).resolve().parent
root=out.parents[1]
stage=sys.argv[1]
def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""): h.update(block)
    return h.hexdigest()
manifest_path=root/"Data/Regions/bialystok-industrial-c/generated/world_manifest.json"
manifest=load(manifest_path)
records=[]
for chunk in manifest["chunks"]:
    for tier,entry in (("High",chunk),("Low",chunk["low"]),("instances",chunk["instances"])):
        name=entry["file"]
        assert name.startswith("Data/raw/derived/bialystok-industrial-c/world/")
        p=root/name;actual=sha(p)
        assert actual==entry["sha256"],f"Stale runtime: {name}"
        if "bytes" in entry: assert p.stat().st_size==entry["bytes"]
        records.append(dict(tier=tier,file=name,sha256=actual,bytes=p.stat().st_size))
assert len(records)==192
names=["tools/blender/world/landmarks/make_fire_station.py",
       "art-source/world/landmarks/fire_station_jrg2/dims.json",
       "art-source/world/landmarks/fire_station_jrg2/atlas_layout.json",
       "art-source/world/landmarks/fire_station_jrg2/conifer_source.json",
       "art-source/world/landmarks/fire_station_jrg2/conifer_foliage_meta.json",
       "art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb",
       "art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2_meta.json",
       "art-source/world/textures/fire_station_alpha.png",
       "art-source/world/materials/_src/sets_fire_station.py",
       "art-source/world/materials/materials_spec.json",
       "tools/worldgen/streetscape/materials.py","tools/worldgen/streetscape/hero_building.py",
       "tools/worldgen/streetscape/hero_bridge.py","tools/worldgen/streetscape/landmarks.py",
       "tools/worldgen/streetscape/ec_chimneys.py","tests/gis/test_fire_station_r7.py",
       "tests/gis/test_hero_building.py","Data/Regions/bialystok-industrial-c/ec_chimneys.json",
       "Data/Regions/bialystok-industrial-c/viaduct_underdeck.json",
       "Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json"]
for asset in ("ec_chimney_single","ec_chimney_multi"):
    names += [f"art-source/world/landmarks/{asset}/{asset}.glb",f"art-source/world/landmarks/{asset}/{asset}_meta.json"]
maps=load(root/"art-source/world/materials/materials_spec.json")["sets"]["fire_station"]["files"]["Medium"]
names += [f"art-source/world/materials/{maps['dir']}/{name}" for name in maps["files"]]
result=dict(stage=stage,files=records,all_manifest_hashes_match=True,manifest_sha256=sha(manifest_path),
            source_sha256={name:sha(root/name) for name in sorted(set(names))})
if stage!="before-tests":
    before=load(out/"cache-before-tests.json")
    for key in ("files","manifest_sha256","source_sha256"):
        assert result[key]==before[key],f"Changed during final tests: {key}"
    result["unchanged_since_rendered_checkpoint"]=True
(out/f"cache-{stage}.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(f"{stage}:192 runtime hashes and {len(result['source_sha256'])} source/material hashes verified")
