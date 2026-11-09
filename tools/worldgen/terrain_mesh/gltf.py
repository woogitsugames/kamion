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
    def __init__(self, materials: dict, compact: bool = False):
        """compact=True (Low/Medium chunk variant): int8 normals (KHR_mesh_quantization), 8-bit vertex
        colours, no TEXCOORD_0 on terrain (the terrain shader tiles by world position)."""
        self.compact = compact
        self.materials = materials          # name -> {"color": [r,g,b], "rough": f, "metal": f}
        self.mat_index = {}
        self.bin = bytearray()
        self.views, self.accessors, self.meshes, self.nodes = [], [], [], []
        self.gmats = []
        self.images, self.textures = [], []

    def _mat(self, name):
        if name not in self.mat_index:
            m = self.materials.get(name, {"color": [0.5, 0.5, 0.5], "rough": 0.9, "metal": 0.0})
            self.mat_index[name] = len(self.gmats)
            gm = {"name": name, "pbrMetallicRoughness": {
                "baseColorFactor": [float(x) for x in m["color"]] + [1.0],
                "metallicFactor": float(m.get("metal", 0.0)), "roughnessFactor": float(m["rough"])},
                "extras": {k: v for k, v in m.items() if k not in ("color", "rough", "metal", "texture_png")}}
            if m.get("texture_png"):           # embedded sRGB base colour texture (bytes)
                gm["pbrMetallicRoughness"]["baseColorTexture"] = {"index": self._texture(m["texture_png"])}
                gm["pbrMetallicRoughness"]["baseColorFactor"] = [1.0, 1.0, 1.0, 1.0]
                if m.get("alpha_cutoff"):
                    gm["alphaMode"] = "MASK"
                    gm["alphaCutoff"] = float(m["alpha_cutoff"])
                    gm["doubleSided"] = True
            if m.get("alpha") is not None:     # translucent (e.g. transparent noise screens): BLEND, double-sided
                gm["pbrMetallicRoughness"]["baseColorFactor"][3] = float(m["alpha"])
                gm["alphaMode"] = "BLEND"
                gm["doubleSided"] = True
            self.gmats.append(gm)
        return self.mat_index[name]

    def _texture(self, png: bytes):
        vi = self._view(png)
        self.images.append({"bufferView": vi, "mimeType": "image/png"})
        self.textures.append({"source": len(self.images) - 1, "sampler": 0})
        return len(self.textures) - 1

    def _view(self, data: bytes, target=None, stride=None):
        while len(self.bin) % 4:
            self.bin += b"\0"
        off = len(self.bin)
        self.bin += data
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target:
            v["target"] = target
        if stride:
            v["byteStride"] = stride
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
            # quantise before float32 so tiny float differences between environments (BLAS, numpy builds)
            # do not change the bytes: positions 1 mm, normals / UVs 1e-4
            pos = np.round(to_gltf(V), 3).astype("<f4")
            nor = np.round(to_gltf(Nn), 4).astype("<f4")
            if self.materials.get(p["mat"], {}).get("collision"):
                # collision primitives: positions + indices only (no shading attributes)
                attrs = {"POSITION": self._acc(pos, 5126, "VEC3", 34962, True)}
                idx = np.asarray(T, np.int64).ravel()
                ia = self._acc(idx.astype("<u2" if idx.max() < 65535 else "<u4"),
                               5123 if idx.max() < 65535 else 5125, "SCALAR", 34963)
                gp.append({"attributes": attrs, "indices": ia, "material": self._mat(p["mat"]), "mode": 4})
                continue
            attrs = {"POSITION": self._acc(pos, 5126, "VEC3", 34962, True)}
            if self.compact:              # int8 normalised normals, padded to 4 bytes per vertex
                n8 = np.zeros((len(nor), 4), "<i1")
                n8[:, :3] = np.clip(np.round(nor * 127), -127, 127)
                vi = self._view(n8.tobytes(), 34962, stride=4)
                self.accessors.append({"bufferView": vi, "componentType": 5120, "count": len(nor), "type": "VEC3",
                                       "normalized": True})
                attrs["NORMAL"] = len(self.accessors) - 1
            else:
                attrs["NORMAL"] = self._acc(nor, 5126, "VEC3", 34962)
            terrain = p["mat"] == "terrain_grass"
            for key, sem in (("UV", "TEXCOORD_0"), ("UV1", "TEXCOORD_1")):
                if key == "UV" and terrain and self.compact:
                    continue
                if p.get(key) is not None:
                    uv = np.asarray(p[key], np.float64).copy()
                    uv[:, 1] = 1.0 - uv[:, 1]      # glTF v points down; importers map back to v (up)
                    uv = np.round(uv, 4)
                    attrs[sem] = self._acc(uv.astype("<f4"), 5126, "VEC2", 34962)
            if p.get("COL") is not None:          # per-vertex data (weathering masks), linear RGBA 0..1
                col = np.clip(np.asarray(p["COL"], np.float64), 0, 1)
                if col.shape[1] == 3:
                    col = np.column_stack([col, np.ones(len(col))])
                if self.compact:
                    attrs["COLOR_0"] = self._acc(np.round(col * 255).astype("<u1"), 5121, "VEC4", 34962)
                else:
                    attrs["COLOR_0"] = self._acc(np.round(col * 65535).astype("<u2"), 5123, "VEC4", 34962)
                self.accessors[-1]["normalized"] = True
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
        if self.compact:
            doc["extensionsUsed"] = ["KHR_mesh_quantization"]
            doc["extensionsRequired"] = ["KHR_mesh_quantization"]
        if self.textures:
            doc.update({"images": self.images, "textures": self.textures,
                        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]})
        js = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
        while len(js) % 4:
            js += b" "
        total = 12 + 8 + len(js) + 8 + len(self.bin)
        out = struct.pack("<III", 0x46546C67, 2, total)
        out += struct.pack("<II", len(js), 0x4E4F534A) + js
        out += struct.pack("<II", len(self.bin), 0x004E4942) + bytes(self.bin)
        return out
