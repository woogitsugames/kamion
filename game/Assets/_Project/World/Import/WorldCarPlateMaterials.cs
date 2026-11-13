using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.World.Import
{
    /// <summary>ADR0089: opt in one existing Lit material only after the complete local-corner migration.</summary>
    public static class WorldCarPlateMaterials
    {
        public const string ShaderName = "Kamion/World Car Plate";
        public const string Keyword = "_PLATE_LOCAL_CORNERS";
        // Material API keys are LightMode tags, not ShaderLab pass names.
        static readonly string[] Passes = { "UniversalForward", "ShadowCaster", "UniversalGBuffer", "DepthOnly", "DepthNormals", "Meta", "Universal2D", "MotionVectors", "XRMotionVectors" };
        static readonly Regex Vehicle = new Regex(@"^(car_(hatch|sedan|estate|suv)_(silver|grey|black|white|blue|red)|van_(white|silver|white2))(\.lod[12])?$", RegexOptions.CultureInvariant);

        public static bool ValidCorners(Vector2[] uv0, Vector2[] local)
        {
            if (uv0 == null || local == null || uv0.Length != 8 || local.Length != 8) return false;
            Vector2 lo = uv0.Aggregate(Vector2.Min), hi = uv0.Aggregate(Vector2.Max);
            if (hi.x - lo.x < .2f || hi.y - lo.y < .1f) return false;
            var counts = new int[4];
            for (int i = 0; i < local.Length; i++)
            {
                var p = local[i];
                if ((p.x != 0f && p.x != 1f) || (p.y != 0f && p.y != 1f)) return false;
                var expected = new Vector2(Mathf.Lerp(lo.x, hi.x, p.x), Mathf.Lerp(lo.y, hi.y, p.y));
                if ((uv0[i] - expected).sqrMagnitude > 1e-8f) return false;
                counts[(int)p.x + 2 * (int)p.y]++;
            }
            return counts.All(n => n == 2);
        }

        public static bool ValidLibrary(GlbReader library)
        {
            var nodes = library.Nodes.Where(n => Vehicle.IsMatch(n.Name)).ToArray();
            if (nodes.Length != 81 || nodes.Select(n => n.Name).Distinct().Count() != 81) return false;
            int plateCount = 0, atlasLod1 = 0;
            foreach (var node in nodes)
            {
                var plates = node.Primitives.Where(p => p.Material == "car_plate").ToArray();
                if (node.Name.EndsWith(".lod2", StringComparison.Ordinal))
                {
                    if (plates.Length != 0) return false;
                    continue;
                }
                // ADR0153: only explicitly migrated LOD1 may move its plate into
                // the two-submesh atlas. Every LOD0 still requires exact local corners.
                if (node.Name.EndsWith(".lod1", StringComparison.Ordinal))
                {
                    string rootName = node.Name.Substring(0, node.Name.Length - ".lod1".Length);
                    var root = nodes.FirstOrDefault(n => n.Name == rootName);
                    if (root?.Extras != null && root.Extras.TryGetValue("vehicle_lod_atlas", out var flag) && flag is bool atlas && atlas)
                    {
                        if (plates.Length != 0 || node.Primitives.Count != 2
                            || node.Primitives.Count(p => p.Material == "vehicle_lod_details") != 1
                            || node.Primitives.Count(p => p.Material != null && p.Material.StartsWith("car_paint_", StringComparison.Ordinal)) != 1)
                            return false;
                        atlasLod1++; continue;
                    }
                }
                if (plates.Length != 1 || plates[0].Indices?.Length != 12 || !ValidCorners(plates[0].Uv0, plates[0].Uv1)) return false;
                plateCount++;
            }
            return plateCount >= 27 && plateCount + atlasLod1 == 54;
        }

        public static bool ForwardOnly(RenderPipelineAsset asset)
        {
            if (!(asset is UniversalRenderPipelineAsset urp) || urp.rendererDataList.Length == 0) return false;
            foreach (var renderer in urp.rendererDataList)
                if (!(renderer is UniversalRendererData data) || data.renderingMode != RenderingMode.Forward) return false;
            return true;
        }

        public static bool ValidNativePlate(Mesh mesh, int submesh)
        {
            if (mesh == null || !mesh.HasVertexAttribute(VertexAttribute.TexCoord0) ||
                !mesh.HasVertexAttribute(VertexAttribute.TexCoord1)) return false;
            foreach (var channel in new[] { VertexAttribute.TexCoord0, VertexAttribute.TexCoord1 })
                if (mesh.GetVertexAttributeStream(channel) != 0 || mesh.GetVertexAttributeDimension(channel) != 2 ||
                    mesh.GetVertexAttributeFormat(channel) != VertexAttributeFormat.Float16) return false;
            var sub = mesh.GetSubMesh(submesh);
            if (sub.indexCount != 12) return false;
            // Editor API intentionally supports UploadMeshData(true): validate the ACTUAL
            // native buffers, not merely the fresh GLB or a matching vertex descriptor.
            using (var snapshot = MeshUtility.AcquireReadOnlyMeshData(mesh))
            {
                var data = snapshot[0];
                var selected = new SortedSet<int>();
                if (mesh.indexFormat == IndexFormat.UInt16)
                {
                    var indices = data.GetIndexData<ushort>();
                    for (int i = 0; i < sub.indexCount; i++) selected.Add(indices[sub.indexStart + i] + sub.baseVertex);
                }
                else
                {
                    var indices = data.GetIndexData<int>();
                    for (int i = 0; i < sub.indexCount; i++) selected.Add(indices[sub.indexStart + i] + sub.baseVertex);
                }
                if (selected.Count != 8) return false;
                byte[] bytes = data.GetVertexData<byte>(0).ToArray();
                int stride = mesh.GetVertexBufferStride(0), offset0 = mesh.GetVertexAttributeOffset(VertexAttribute.TexCoord0),
                    offset1 = mesh.GetVertexAttributeOffset(VertexAttribute.TexCoord1);
                Vector2 Read(int i, int offset) => new Vector2(Mathf.HalfToFloat(BitConverter.ToUInt16(bytes, i * stride + offset)),
                    Mathf.HalfToFloat(BitConverter.ToUInt16(bytes, i * stride + offset + 2)));
                return ValidCorners(selected.Select(i => Read(i, offset0)).ToArray(), selected.Select(i => Read(i, offset1)).ToArray());
            }
        }

        public static bool ValidNativeLibrary(WorldInstanceSet set, Material plate)
        {
            var native = set.prototypes.Where(p => Vehicle.IsMatch(p.name)).ToArray();
            if (native.Length != 27) return false;
            int count = 0, atlasLod1 = 0;
            foreach (var prototype in native)
            {
                if (prototype.lods.Length != 3) return false;
                for (int lod = 0; lod < prototype.lods.Length; lod++)
                {
                    var mesh = prototype.lods[lod];
                    bool atlas = lod == 1 && mesh.subMeshCount == 2 && Enumerable.Range(0, mesh.subMeshCount)
                        .Count(sub =>
                        {
                            var material = set.materials[prototype.materialStart[lod] + sub];
                            return material != null && material.shader != null && material.shader.name == "Kamion/World PBR"
                                && material.GetTag("KamionVehicleLodAtlas", false, "") == "1";
                        }) == 1;
                    if (atlas) atlasLod1++;
                    int seen = 0;
                    for (int sub = 0; sub < mesh.subMeshCount; sub++)
                        if (set.materials[prototype.materialStart[lod] + sub] == plate)
                        {
                            if (!ValidNativePlate(mesh, sub)) return false;
                            seen++; count++;
                        }
                    if (seen != (lod == 2 || atlas ? 0 : 1)) return false;
                }
            }
            return count >= 27 && count + atlasLod1 == 54;
        }

        public static bool EligibleMaterial(string id, Material material)
        {
            return id == "car_plate" && material != null && material.HasProperty("_BaseMap") &&
                material.GetTexture("_BaseMap") != null && material.GetTextureScale("_BaseMap") == Vector2.one &&
                material.GetTextureOffset("_BaseMap") == Vector2.zero && !material.IsKeywordEnabled("LIGHTMAP_ON") &&
                !material.IsKeywordEnabled("DYNAMICLIGHTMAP_ON");
        }

        public static Material PreserveLitPasses(string path, Func<Material> factory)
        {
            var existing = AssetDatabase.LoadAssetAtPath<Material>(path);
            var states = existing == null ? null : Passes.Select(existing.GetShaderPassEnabled).ToArray();
            var material = factory();
            if (states != null) for (int i = 0; i < Passes.Length; i++) material.SetShaderPassEnabled(Passes[i], states[i]);
            return material;
        }

        public static void ChangeShaderPreservingPasses(Material material, Shader shader)
        {
            var states = Passes.Select(material.GetShaderPassEnabled).ToArray();
            material.shader = shader;
            for (int i = 0; i < Passes.Length; i++) material.SetShaderPassEnabled(Passes[i], states[i]);
        }

        public static void Configure(RegionImporter.Result region)
        {
            if (!region.Materials.TryGetValue("car_plate", out var plate)) return;
            // A repeat import starts from ordinary Lit; rejection must never preserve a stale enabled flag.
            var original = Shader.Find("Universal Render Pipeline/Lit");
            if (original == null) return;
            plate.DisableKeyword(Keyword);
            if (plate.HasProperty("_PlatePayloadVersion")) plate.SetFloat("_PlatePayloadVersion", 0f);
            ChangeShaderPreservingPasses(plate, original);
            bool eligible = EligibleMaterial("car_plate", plate) && ForwardOnly(GraphicsSettings.defaultRenderPipeline);
            for (int i = 0; eligible && i < QualitySettings.names.Length; i++)
            {
                var pipeline = QualitySettings.GetRenderPipelineAssetAt(i);
                if (pipeline != null) eligible &= ForwardOnly(pipeline);
            }
            var shader = Shader.Find(ShaderName);
            eligible &= shader != null;
            if (eligible)
                eligible = ValidLibrary(GlbReader.Load(Path.Combine(EditorTools.RepoRoot, "art-source", "world", "props", "street_props.glb")));
            if (eligible) eligible = ValidNativeLibrary(region.Instances, plate);
            if (eligible)
            {
                ChangeShaderPreservingPasses(plate, shader);
                plate.SetFloat("_PlatePayloadVersion", 1f);
                plate.EnableKeyword(Keyword);
            }
            EditorUtility.SetDirty(plate);
            Debug.Log($"[IMPORT] car_plate local-corner remap: {(eligible ? "enabled (complete LOD0 migration validated, Forward only)" : "UV0 fallback (eligibility failed)")}");
        }
    }
}
