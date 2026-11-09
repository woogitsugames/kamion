using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;
using static Game.World.Import.MiniJson;

namespace Game.World.Import
{
    /// <summary>
    /// Minimal binary glTF 2.0 reader for the files our own generators write (tools/worldgen chunks with or without
    /// KHR_mesh_quantization, tools/blender prop and tree libraries): triangle lists, POSITION / NORMAL / TEXCOORD_0 /
    /// TEXCOORD_1 / COLOR_0 in float or normalized integer components, 16/32-bit indices, node names + extras, material
    /// names / alpha mode / base-colour image name. Node transforms are not supported (none of our files use them; the
    /// reader throws if one appears). Axis conversion is the same as glTFast's (ADR 0011): x is negated and the triangle
    /// winding flipped, so glTF (−E, U, N) becomes Unity (E, U, N).
    /// Why not glTFast assets: the editor bake needs the raw attributes (masks in COLOR_0, quantized normals, primitive →
    /// material name) and must not drag whole GLB assets into the player build (ADR 0012).
    /// </summary>
    public sealed class GlbReader
    {
        public sealed class Primitive
        {
            public string Material;
            public Vector3[] Positions;
            public Vector3[] Normals;      // null if absent
            public Vector2[] Uv0, Uv1;     // null if absent
            public Color32[] Colors;       // null if absent
            public int[] Indices;
        }

        public sealed class MeshNode
        {
            public string Name;
            public Dictionary<string, object> Extras;
            public readonly List<Primitive> Primitives = new List<Primitive>();
        }

        public sealed class MaterialInfo
        {
            public string Name;
            public string AlphaMode = "OPAQUE";
            public float AlphaCutoff = 0.5f;
            public bool DoubleSided;
            public Color BaseColorFactor = Color.white;
            public string BaseColorImageName;   // images[].name, null if unnamed / no texture
            public bool HasBaseColorTexture;
        }

        public readonly List<MeshNode> Nodes = new List<MeshNode>();
        public readonly List<MaterialInfo> Materials = new List<MaterialInfo>();
        public Dictionary<string, object> SceneExtras;

        Dictionary<string, object> m_Json;
        byte[] m_Bin;

        public static GlbReader Load(string path)
        {
            var r = new GlbReader();
            r.Parse(File.ReadAllBytes(path), path);
            return r;
        }

        public MeshNode Find(string name)
        {
            foreach (var n in Nodes) if (n.Name == name) return n;
            return null;
        }

        void Parse(byte[] data, string path)
        {
            if (data.Length < 20 || BitConverter.ToUInt32(data, 0) != 0x46546C67) throw new InvalidDataException(path + ": not a GLB");
            int jsonLen = BitConverter.ToInt32(data, 12);
            if (BitConverter.ToUInt32(data, 16) != 0x4E4F534A) throw new InvalidDataException(path + ": first chunk is not JSON");
            m_Json = Obj(MiniJson.Parse(Encoding.UTF8.GetString(data, 20, jsonLen)));
            int binStart = 20 + jsonLen;
            if (binStart + 8 <= data.Length)
            {
                int binLen = BitConverter.ToInt32(data, binStart);
                m_Bin = new byte[binLen];
                Buffer.BlockCopy(data, binStart + 8, m_Bin, 0, binLen);
            }

            var images = m_Json.Get("images") is List<object> il ? il : new List<object>();
            var textures = m_Json.Get("textures") is List<object> tl ? tl : new List<object>();
            if (m_Json.Get("materials") is List<object> ml)
                foreach (var mo in ml)
                {
                    var m = Obj(mo);
                    var mi = new MaterialInfo { Name = Str(m.Get("name")) };
                    if (m.Get("alphaMode") != null) mi.AlphaMode = Str(m.Get("alphaMode"));
                    if (m.Get("alphaCutoff") != null) mi.AlphaCutoff = (float)Num(m.Get("alphaCutoff"));
                    mi.DoubleSided = m.Get("doubleSided") is bool ds && ds;
                    if (m.Get("pbrMetallicRoughness") is Dictionary<string, object> pbr)
                    {
                        if (pbr.Get("baseColorFactor") is List<object> f)
                            mi.BaseColorFactor = new Color((float)Num(f[0]), (float)Num(f[1]), (float)Num(f[2]), (float)Num(f[3]));
                        if (pbr.Get("baseColorTexture") is Dictionary<string, object> bt)
                        {
                            mi.HasBaseColorTexture = true;
                            var tex = Obj(textures[(int)Num(bt.Get("index"))]);
                            if (tex.Get("source") != null)
                            {
                                var img = Obj(images[(int)Num(tex.Get("source"))]);
                                mi.BaseColorImageName = img.Get("name") as string;
                            }
                        }
                    }
                    Materials.Add(mi);
                }

            if (m_Json.Get("scenes") is List<object> sl && sl.Count > 0)
                SceneExtras = Obj(sl[0]).Get("extras") as Dictionary<string, object>;

            var meshes = Arr(m_Json.Get("meshes"));
            foreach (var no in Arr(m_Json.Get("nodes")))
            {
                var n = Obj(no);
                if (n.Get("translation") != null || n.Get("rotation") != null || n.Get("scale") != null || n.Get("matrix") != null)
                    throw new NotSupportedException($"{path}: node '{Str(n.Get("name"))}' has a transform (not used by our generators)");
                if (n.Get("mesh") == null) continue;
                var node = new MeshNode { Name = Str(n.Get("name")), Extras = n.Get("extras") as Dictionary<string, object> };
                var mesh = Obj(meshes[(int)Num(n.Get("mesh"))]);
                foreach (var po in Arr(mesh.Get("primitives")))
                {
                    var p = Obj(po);
                    if (p.Get("mode") != null && (int)Num(p.Get("mode")) != 4) throw new NotSupportedException($"{path}: non-triangle primitive");
                    var a = Obj(p.Get("attributes"));
                    var prim = new Primitive
                    {
                        Material = p.Get("material") != null ? Materials[(int)Num(p.Get("material"))].Name : null,
                        Positions = ReadVec3(a.Get("POSITION"), true),
                        Normals = a.Get("NORMAL") != null ? ReadVec3(a.Get("NORMAL"), true) : null,
                        Uv0 = a.Get("TEXCOORD_0") != null ? ReadVec2(a.Get("TEXCOORD_0"), true) : null,
                        // The generator writes every UV set with v flipped (glTF convention, terrain_mesh/gltf.py), so
                        // TEXCOORD_1 is flipped back like TEXCOORD_0 (before ADR 0022 it was read as 1 - v: far facades
                        // drew panes only on the ground floor, REVIEW r4 W-H4 / W-H7).
                        Uv1 = a.Get("TEXCOORD_1") != null ? ReadVec2(a.Get("TEXCOORD_1"), true) : null,
                        Colors = a.Get("COLOR_0") != null ? ReadColor(a.Get("COLOR_0")) : null,
                    };
                    var idx = ReadScalars(p.Get("indices"));
                    // Mirror (x negated) → flip the winding to keep front faces.
                    for (int i = 0; i + 2 < idx.Length; i += 3) { int t = idx[i + 1]; idx[i + 1] = idx[i + 2]; idx[i + 2] = t; }
                    prim.Indices = idx;
                    node.Primitives.Add(prim);
                }
                Nodes.Add(node);
            }
        }

        // ------------------------------------------------------------------ accessors
        struct View { public int Offset, Stride, Count, Comps, CompType; public bool Normalized; }

        View Accessor(object index, int comps)
        {
            var acc = Obj(Arr(m_Json.Get("accessors"))[(int)Num(index)]);
            var bv = Obj(Arr(m_Json.Get("bufferViews"))[(int)Num(acc.Get("bufferView"))]);
            int ct = (int)Num(acc.Get("componentType"));
            int compSize = ct == 5126 || ct == 5125 ? 4 : ct == 5122 || ct == 5123 ? 2 : 1;
            int n = TypeComps(Str(acc.Get("type")));
            if (comps > 0 && n < comps) throw new InvalidDataException("accessor has fewer components than expected");
            int stride = bv.Get("byteStride") != null ? (int)Num(bv.Get("byteStride")) : n * compSize;
            int offset = (bv.Get("byteOffset") != null ? (int)Num(bv.Get("byteOffset")) : 0) + (acc.Get("byteOffset") != null ? (int)Num(acc.Get("byteOffset")) : 0);
            return new View { Offset = offset, Stride = stride, Count = (int)Num(acc.Get("count")), Comps = n, CompType = ct, Normalized = acc.Get("normalized") is bool b && b };
        }

        static int TypeComps(string t) => t == "SCALAR" ? 1 : t == "VEC2" ? 2 : t == "VEC3" ? 3 : t == "VEC4" ? 4 : throw new InvalidDataException("type " + t);

        float Comp(in View v, int i, int c)
        {
            int o = v.Offset + i * v.Stride;
            switch (v.CompType)
            {
                case 5126: return BitConverter.ToSingle(m_Bin, o + c * 4);
                case 5120: { float x = (sbyte)m_Bin[o + c]; return v.Normalized ? Mathf.Max(x / 127f, -1f) : x; }
                case 5121: { float x = m_Bin[o + c]; return v.Normalized ? x / 255f : x; }
                case 5122: { float x = BitConverter.ToInt16(m_Bin, o + c * 2); return v.Normalized ? Mathf.Max(x / 32767f, -1f) : x; }
                case 5123: { float x = BitConverter.ToUInt16(m_Bin, o + c * 2); return v.Normalized ? x / 65535f : x; }
                case 5125: return BitConverter.ToUInt32(m_Bin, o + c * 4);
                default: throw new InvalidDataException("componentType " + v.CompType);
            }
        }

        Vector3[] ReadVec3(object index, bool mirrorX)
        {
            var v = Accessor(index, 3);
            var r = new Vector3[v.Count];
            float sx = mirrorX ? -1f : 1f;
            for (int i = 0; i < v.Count; i++) r[i] = new Vector3(sx * Comp(v, i, 0), Comp(v, i, 1), Comp(v, i, 2));
            return r;
        }

        /// <param name="flipV">texture coordinates: glTF v = 0 is the top of the image, Unity v = 0 the bottom (as glTFast).
        /// The generator flips every set on export, so metric TEXCOORD_1 data is flipped back as well.</param>
        Vector2[] ReadVec2(object index, bool flipV)
        {
            var v = Accessor(index, 2);
            var r = new Vector2[v.Count];
            for (int i = 0; i < v.Count; i++) r[i] = new Vector2(Comp(v, i, 0), flipV ? 1f - Comp(v, i, 1) : Comp(v, i, 1));
            return r;
        }

        Color32[] ReadColor(object index)
        {
            var v = Accessor(index, 3);
            var r = new Color32[v.Count];
            for (int i = 0; i < v.Count; i++)
            {
                float a = v.Comps > 3 ? Comp(v, i, 3) : 1f;
                r[i] = new Color32(B(Comp(v, i, 0)), B(Comp(v, i, 1)), B(Comp(v, i, 2)), B(a));
            }
            return r;
        }

        static byte B(float x) => (byte)Mathf.Clamp(Mathf.RoundToInt(x * 255f), 0, 255);

        int[] ReadScalars(object index)
        {
            var v = Accessor(index, 1);
            var r = new int[v.Count];
            for (int i = 0; i < v.Count; i++)
            {
                int o = v.Offset + i * v.Stride;
                r[i] = v.CompType == 5125 ? (int)BitConverter.ToUInt32(m_Bin, o) : v.CompType == 5123 ? BitConverter.ToUInt16(m_Bin, o) : m_Bin[o];
            }
            return r;
        }
    }
}
