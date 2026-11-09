"""Minimal deterministic glTF 2.0 binary (GLB) writer.

Axes: the pipeline works in region-local (E, N, U) metres. glTF is right-handed, +Y up; we write
glTF (x, y, z) = (-E, U, N). Unity glTF importers (glTFast, UnityGLTF) convert glTF -> Unity by
negating x, which yields Unity (x, y, z) = (E, U, N) = ADR 0003 (X east, Y up, Z north). Blender's
importer maps glTF (x, y, z) -> Blender (x, -z, y) = (-E, -N, U), i.e. rotated 180° about Z.
The mapping is a proper rotation, so CCW winding (seen from outside) is preserved.

Determinism: no timestamps, sorted JSON keys, float32 data, fixed buffer layout.
"""

from __future__ import annotations

import json
import struct

import numpy as np

GLTF_AXES = "glTF(x,y,z) = (-E, U, N); Unity import (x negated) -> (E, U, N)"


def to_gltf(v):
    v = np.asarray(v, np.float64)
    return np.column_stack([-v[:, 0], v[:, 2], v[:, 1]])


def smooth_normals(V, T):
    n = np.zeros_like(V)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    fn = np.cross(b - a, c - a)
    for k in range(3):
        np.add.at(n, T[:, k], fn)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1
    return n / ln


class GLB:
    def __init__(self, materials: dict):
        self.materials = materials          # name -> {"color": [r,g,b], "rough": f, "metal": f}
        self.mat_index = {}
        self.bin = bytearray()
        self.views, self.accessors, self.meshes, self.nodes = [], [], [], []
        self.gmats = []

    def _mat(self, name):
        if name not in self.mat_index:
            m = self.materials.get(name, {"color": [0.5, 0.5, 0.5], "rough": 0.9, "metal": 0.0})
            self.mat_index[name] = len(self.gmats)
            self.gmats.append({"name": name, "pbrMetallicRoughness": {
                "baseColorFactor": [float(x) for x in m["color"]] + [1.0],
                "metallicFactor": float(m.get("metal", 0.0)), "roughnessFactor": float(m["rough"])},
                "extras": {k: v for k, v in m.items() if k not in ("color", "rough", "metal")}})
        return self.mat_index[name]

    def _view(self, data: bytes, target=None):
        while len(self.bin) % 4:
            self.bin += b"\0"
        off = len(self.bin)
        self.bin += data
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target:
            v["target"] = target
        self.views.append(v)
        return len(self.views) - 1

    def _acc(self, arr, ctype, typ, target, minmax=False):
        a = np.ascontiguousarray(arr)
        vi = self._view(a.tobytes(), target)
        acc = {"bufferView": vi, "componentType": ctype, "count": int(a.shape[0]), "type": typ}
        if minmax:
            acc["min"] = [float(x) for x in a.min(0)]
            acc["max"] = [float(x) for x in a.max(0)]
        self.accessors.append(acc)
        return len(self.accessors) - 1

    def add_mesh(self, name, prims, extras=None):
        """prims: [{"V": (n,3) ENU, "T": (m,3), "UV": (n,2) optional, "N": (n,3) ENU optional, "mat": str}]"""
        gp = []
        for p in prims:
            V = np.asarray(p["V"], np.float64)
            T = np.asarray(p["T"], np.int64)
            if len(T) == 0:
                continue
            Nn = p.get("N")
            if Nn is None:
                Nn = smooth_normals(V, T)
            pos = to_gltf(V).astype("<f4")
            nor = to_gltf(Nn).astype("<f4")
            attrs = {"POSITION": self._acc(pos, 5126, "VEC3", 34962, True),
                     "NORMAL": self._acc(nor, 5126, "VEC3", 34962)}
            if p.get("UV") is not None:
                uv = np.asarray(p["UV"], np.float64).copy()
                uv[:, 1] = -uv[:, 1]           # glTF v points down
                attrs["TEXCOORD_0"] = self._acc(uv.astype("<f4"), 5126, "VEC2", 34962)
            idx = T.ravel()
            if idx.max() < 65535:
                ia = self._acc(idx.astype("<u2"), 5123, "SCALAR", 34963)
            else:
                ia = self._acc(idx.astype("<u4"), 5125, "SCALAR", 34963)
            gp.append({"attributes": attrs, "indices": ia, "material": self._mat(p["mat"]), "mode": 4})
        if not gp:
            return None
        self.meshes.append({"name": name, "primitives": gp})
        node = {"name": name, "mesh": len(self.meshes) - 1}
        if extras:
            node["extras"] = extras
        self.nodes.append(node)
        return len(self.nodes) - 1

    def bytes(self, scene_extras=None) -> bytes:
        while len(self.bin) % 4:
            self.bin += b"\0"
        doc = {"asset": {"version": "2.0", "generator": "truck-sim-pl worldgen (roads/terrain_mesh)"},
               "scene": 0, "scenes": [{"nodes": list(range(len(self.nodes))), "extras": scene_extras or {}}],
               "nodes": self.nodes, "meshes": self.meshes, "materials": self.gmats,
               "accessors": self.accessors, "bufferViews": self.views,
               "buffers": [{"byteLength": len(self.bin)}]}
        js = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
        while len(js) % 4:
            js += b" "
        total = 12 + 8 + len(js) + 8 + len(self.bin)
        out = struct.pack("<III", 0x46546C67, 2, total)
        out += struct.pack("<II", len(js), 0x4E4F534A) + js
        out += struct.pack("<II", len(self.bin), 0x004E4942) + bytes(self.bin)
        return out
