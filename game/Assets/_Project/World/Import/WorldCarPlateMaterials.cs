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
            int plateCount = 0;
            foreach (var node in nodes)
            {
                var plates = node.Primitives.Where(p => p.Material == "car_plate").ToArray();
                if (node.Name.EndsWith(".lod2", StringComparison.Ordinal))
                {
                    if (plates.Length != 0) return false;
                    continue;
                }
                if (plates.Length != 1 || plates[0].Indices?.Length != 12 || !ValidCorners(plates[0].Uv0, plates[0].Uv1)) return false;
                plateCount++;
            }
            return plateCount == 54;
        }

        public static bool ForwardOnly(RenderPipelineAsset asset)
        {
            if (!(asset is UniversalRenderPipelineAsset urp) || urp.rendererDataList.Length == 0) return false;
            foreach (var renderer in urp.rendererDataList)
                if (!(renderer is UniversalRendererData data) || data.renderingMode != RenderingMode.Forward) return false;
            return true;
        }

        public static bool EligibleMaterial(string id, Material material)
        {
            return id == "car_plate" && material != null && material.HasProperty("_BaseMap") &&
                material.GetTexture("_BaseMap") != null && material.GetTextureScale("_BaseMap") == Vector2.one &&
                material.GetTextureOffset("_BaseMap") == Vector2.zero && !material.IsKeywordEnabled("LIGHTMAP_ON") &&
                !material.IsKeywordEnabled("DYNAMICLIGHTMAP_ON");
        }

        public static void Configure(RegionImporter.Result region)
        {
            if (!region.Materials.TryGetValue("car_plate", out var plate)) return;
            // A repeat import starts from ordinary Lit; rejection must never preserve a stale enabled flag.
            var original = Shader.Find("Universal Render Pipeline/Lit");
            if (original == null) return;
            plate.shader = original;
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
            var native = region.Instances.prototypes.Where(p => Vehicle.IsMatch(p.name)).ToArray();
            eligible &= native.Length == 27 && native.All(p => p.lods.Length == 3 && p.lods.All(m =>
                m.HasVertexAttribute(VertexAttribute.TexCoord1) && m.GetVertexAttributeDimension(VertexAttribute.TexCoord1) == 2 &&
                m.GetVertexAttributeFormat(VertexAttribute.TexCoord1) == VertexAttributeFormat.Float16));
            if (eligible)
            {
                plate.shader = shader;
                plate.SetFloat("_PlatePayloadVersion", 1f);
            }
            EditorUtility.SetDirty(plate);
            Debug.Log($"[IMPORT] car_plate local-corner remap: {(eligible ? "enabled (54 plates, Forward only)" : "UV0 fallback (eligibility failed)")}");
        }
    }
}
