"""Compare oriented GLB triangles with attributes, independent of vertex indices."""
import collections
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

out = Path(__file__).resolve().parent
root = out.parents[1]
base = out / "baseline-generated"
asset = root / "art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb"

def read(path):
    raw = path.read_bytes()
    size, kind = struct.unpack_from("<II", raw, 12)
    assert kind == 0x4e4f534a
    doc = json.loads(raw[20:20 + size])
    binary = memoryview(raw)[28 + size:]
    widths = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    dtypes = {5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
    def accessor(index):
        a = doc["accessors"][index]
        v = doc["bufferViews"][a["bufferView"]]
        dtype = np.dtype(dtypes[a["componentType"]])
        width = widths[a["type"]]
        start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        return np.ndarray((a["count"], width), dtype=dtype, buffer=binary, offset=start,
                          strides=(v.get("byteStride", dtype.itemsize * width), dtype.itemsize))
    rows = collections.Counter()
    positions = {}
    transforms = {}
    for node in doc["nodes"]:
        if "mesh" not in node:
            continue
        name = node["name"]
        transforms[name] = {k: node[k] for k in ("matrix", "rotation", "translation", "scale") if k in node}
        for p in doc["meshes"][node["mesh"]]["primitives"]:
            assert p.get("mode", 4) == 4
            arrays = {k: accessor(i) for k, i in sorted(p["attributes"].items())}
            indices = accessor(p["indices"]).reshape(-1, 3)
            material = doc["materials"][p["material"]]["name"]
            for tri in indices:
                vertices = [b"".join(a[i].tobytes() for a in arrays.values()) for i in tri]
                cyclic = min(tuple(vertices[i:] + vertices[:i]) for i in range(3))
                key = (name, material, tuple(arrays), cyclic)
                rows[key] += 1
                positions[key] = arrays["POSITION"][tri].copy()
    return rows, positions, transforms

before, bp, bt = read(base / "fire_station_jrg2.glb")
after, ap, at = read(asset)
assert bt == at
assert before != after, "Trial asset is unchanged from baseline"
old_spec = json.loads((base / "fire_station_jrg2.spec.json").read_text(encoding="utf-8-sig"))
new_spec = json.loads((root / "Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json").read_text(encoding="utf-8-sig"))
meta = json.loads(asset.with_name("fire_station_jrg2_meta.json").read_text(encoding="utf-8-sig"))
current_dims = json.loads((asset.parent / "dims.json").read_text(encoding="utf-8-sig"))
assert new_spec["dims"] == current_dims
assert new_spec != old_spec, "Trial spec is unchanged from baseline"
assert meta["glb_sha256"] == hashlib.sha256(asset.read_bytes()).hexdigest()
assert meta["spec_sha256"] == hashlib.sha256(json.dumps(new_spec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
alpha_identical = None
if current_dims["spruce"].get("irregular_core_WORKING_VALUE", False):
    alpha_before = collections.Counter({k: c for k, c in before.items() if k[1] == "fire_station_alpha"})
    alpha_after = collections.Counter({k: c for k, c in after.items() if k[1] == "fire_station_alpha"})
    assert alpha_before == alpha_after, "Variant B must preserve every alpha triangle and attribute"
    alpha_identical = True
assert old_spec["anchor"] == new_spec["anchor"]
assert old_spec["ground"] == new_spec["ground"]
anchor = np.array(old_spec["anchor"])
envelopes = []
for e, n, z, height, radius, _ in old_spec["ground"]["spruce"]:
    center = np.array([-(e - anchor[0]), z - anchor[2], n - anchor[1]])
    # Includes old card corners and the underground part of low boughs.
    envelopes.append((center + [-radius * 1.65, -.8, -radius * 1.65],
                      center + [radius * 1.65, height + .1, radius * 1.65]))
summary = {}
for phase, changed, points in (("removed", before - after, bp), ("added", after - before, ap)):
    per_node = collections.Counter()
    for key, count in changed.items():
        assert not key[0].endswith(".lod2"), "Distant building silhouette changed"
        vertices = points[key]
        assert any(np.all(vertices >= lo - 1e-5) and np.all(vertices <= hi + 1e-5) for lo, hi in envelopes), key[:3]
        per_node[key[0]] += count
    summary[phase] = dict(per_node)
for node, expected in (("landmark_fire_station_jrg2", 9584), ("landmark_fire_station_jrg2.lod1", 2818),
                       ("landmark_fire_station_jrg2.lod2", 164)):
    old_count = sum(c for k, c in before.items() if k[0] == node)
    new_count = sum(c for k, c in after.items() if k[0] == node)
    assert old_count == new_count == expected, (node, old_count, new_count)
    assert summary["removed"].get(node, 0) <= {9584: 672, 2818: 294, 164: 0}[expected]
summary.update(complete=True, unchanged_oriented_triangles=sum((before & after).values()),
               attributes_compared="All exported attributes, oriented cyclic vertex bytes, material and node",
               scope="Every changed triangle is inside one of the three conifer envelopes; all other triangles exact",
               anchor_and_ground_identical=True, lod2_exact=True,
               current_spec_config_meta_glb_fresh=True,
               alpha_triangles_byte_identical=alpha_identical,
               before_sha256=hashlib.sha256((base / "fire_station_jrg2.glb").read_bytes()).hexdigest(),
               after_sha256=hashlib.sha256(asset.read_bytes()).hexdigest())
(out / "crown-asset-audit.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
