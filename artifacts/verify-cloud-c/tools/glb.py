"""Minimal GLB reader (numpy only): yields (node name, material name, attrs dict of arrays, indices) per primitive."""
import json, struct
import numpy as np
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def load(path):
    with open(path, "rb") as f:
        f.read(12); clen, _ = struct.unpack("<II", f.read(8)); j = json.loads(f.read(clen)); blen, _ = struct.unpack("<II", f.read(8)); bin_ = f.read(blen)

    def acc(i):
        a = j["accessors"][i]; bv = j["bufferViews"][a["bufferView"]]; dt = np.dtype(CT[a["componentType"]]); nc = NC[a["type"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0); stride = bv.get("byteStride") or dt.itemsize * nc
        if stride == dt.itemsize * nc:
            arr = np.frombuffer(bin_, dt, a["count"] * nc, off).reshape(a["count"], nc)
        else:
            raw = np.frombuffer(bin_, np.uint8, a["count"] * stride, off).reshape(a["count"], stride)
            arr = raw[:, :dt.itemsize * nc].copy().view(dt).reshape(a["count"], nc)
        if a.get("normalized") and dt != np.float32:
            arr = arr.astype(np.float32) / np.iinfo(dt).max
        return arr

    mats = [m.get("name") for m in j.get("materials", [])]
    for n in j.get("nodes", []):
        if "mesh" not in n:
            continue
        t = np.asarray(n.get("translation", [0, 0, 0]), float)
        for pr in j["meshes"][n["mesh"]]["primitives"]:
            at = {k: acc(v) for k, v in pr["attributes"].items()}
            at["POSITION"] = at["POSITION"].astype(float) + t
            yield n.get("name"), mats[pr["material"]] if "material" in pr else None, at, (acc(pr["indices"]).ravel() if "indices" in pr else None)
