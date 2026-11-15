import sys, json, struct, numpy as np
from pathlib import Path
sys.path.insert(0, 'tools/worldgen')
from roads import pipeline
R = 'bialystok-kleeberga'
wdir = pipeline.REPO / 'Data' / 'raw' / 'derived' / R / 'world'
def nodes(path):
    b = path.read_bytes(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
    ct = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}; nc = {"SCALAR": 1, "VEC3": 3, "VEC2": 2, "VEC4": 4}
    def acc(i):
        a = j["accessors"][i]; bv = j["bufferViews"][a["bufferView"]]; off = bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        dt = np.dtype(ct[a["componentType"]]); k = nc[a["type"]]
        return np.frombuffer(b, dt, a["count"] * k, off).reshape(a["count"], k)
    for node in j["nodes"]:
        if "mesh" not in node: continue
        t = np.array(node.get("translation", [0, 0, 0]), float)
        for pr in j["meshes"][node["mesh"]]["primitives"]:
            p = acc(pr["attributes"]["POSITION"]).astype(float) + t; idx = acc(pr["indices"]).reshape(-1, 3)
            mat = j["materials"][pr["material"]]["name"] if "material" in pr else "?"
            yield node.get("name", ""), mat, np.stack([-p[:, 0], p[:, 2], p[:, 1]], 1)[idx]
cx, cy = -128.0, -210.0
out = {}
for f in sorted(wdir.glob('chunk_*.glb')):
    if f.name.endswith('.low.glb'): continue
    for nm, mat, tr in nodes(f):
        if 'collision' in nm or 'collision' in mat: continue
        c = tr.mean(1)
        dz = tr[:, :, 2].max(1) - tr[:, :, 2].min(1)
        ext = np.hypot(tr[:, :, 0].max(1) - tr[:, :, 0].min(1), tr[:, :, 1].max(1) - tr[:, :, 1].min(1))
        m = (np.hypot(c[:, 0] - cx, c[:, 1] - cy) < 150) & (dz > 1.5) & (ext > 0.3) & (mat.find('grass') >= 0 or nm.startswith('terrain'))
        if m.any():
            k = (f.name, nm, mat)
            out[k] = (int(m.sum()), np.round(tr[m][:4], 2).tolist(), np.round(c[m], 1))
for k, v in sorted(out.items(), key=lambda x: -x[1][0]):
    print(k, v[0])
    for t in v[1][:3]: print("    ", t)
np.save('artifacts/tunnel-0211/probe_pyr_lod0.npy', np.concatenate([v[2] for k, v in out.items() if k[1].endswith('lod0') or 'lod' not in k[1]]) if out else np.zeros((0,3)))
