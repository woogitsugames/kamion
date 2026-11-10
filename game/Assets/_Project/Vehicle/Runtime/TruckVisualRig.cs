using System;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Quality-tier binding of the art truck (TRAKT, track A7): per tier it selects the exterior LOD chain, the single
    /// interior LOD and the material set (High / Medium / Low textures). The prefab references the Low set only (always
    /// resident, ~4 MB); the Medium and High sets load from Resources on demand, so a Low device never loads the 2048
    /// atlases. Tier index = QualitySettings level (0 Low, 1 Medium, 2 High, 3 Ultra = High content).
    /// Manifest mapping: exterior High LOD0-1, Medium LOD1-2, Low LOD2; interior LOD0 on every tier (InteriorLodFor).
    /// Cab glazing (GLASS_*) has its own LOD group: the LOD0 glass is the near level on every tier (from the driver's eye
    /// and wherever the interior is drawn), the tier's exterior chain takes over below that (ADR 0045, GlassLodsFor).
    /// </summary>
    [ExecuteAlways]
    [DefaultExecutionOrder(-50)]
    public sealed class TruckVisualRig : MonoBehaviour
    {
        [Serializable]
        public struct RendererSlots { public Renderer renderer; public string[] slots; }

        public const string ResourcesPrefix = "TRAKT/TruckMaterials_";
        /// <summary>Rendering layer bit of the wheel renderers: Kamion/Truck Exterior flattens the tyre at the physics
        /// rolling radius (global _KamionTyreFlatRadius from <see cref="tyreFlatRadius"/>) - model free radius 0.538 m vs 0.51 m.</summary>
        public const uint TyreRenderingLayer = 1u << 8;
        public static readonly string[] TierNames = { "Low", "Medium", "High", "High" };
        /// <summary>Interior LOD per tier name. Review r3 C3: LOD1/LOD2 facet visibly at 0.3-1.2 m from the driver's eye,
        /// so the interior is LOD0 on every tier (75 k triangles; A16 cost measured in the device run). The material sets
        /// carry the AO atlas of this LOD (TruckAssetBuilder).</summary>
        public static int InteriorLodFor(string tier) => 0;

        [Tooltip("Exterior renderers by LOD (index 0..2)")] public RendererList[] exteriorLods = new RendererList[3];
        [Tooltip("Interior renderers by LOD (index 0..2)")] public RendererList[] interiorLods = new RendererList[3];
        public LODGroup exteriorGroup;
        public LODGroup interiorGroup;
        [Tooltip("Cab glazing renderers by LOD (index 0..2); empty on prefabs built before ADR 0045 (glass in exteriorLods)")]
        public RendererList[] glassLods = new RendererList[3];
        public LODGroup glassGroup;
        public RendererSlots[] slots = new RendererSlots[0];
        [Tooltip("Material set referenced by the prefab (Low)")] public TruckMaterialSet residentSet;
        [Tooltip("Manifest lod_screen_size_suggestion: LOD0 0.45, LOD1 0.18, LOD2 0.07, cull 0.006")]
        public float[] screenSizes = { 0.45f, 0.18f, 0.07f, 0.006f };
        [Tooltip("Interior is culled below this screen height (it is only seen through the glass from near)")]
        public float interiorCull = 0.12f;
        [Tooltip("-1 = follow QualitySettings")] public int forceLevel = -1;
        [Tooltip("Physics tyre rolling radius (m), written by TruckAssetBuilder from the vehicle definition. The wheel meshes " +
                 "(free radius 0.538 m) are flattened at this distance below the wheel centre; 0 = off")]
        public float tyreFlatRadius;
        static readonly int k_TyreFlat = Shader.PropertyToID("_KamionTyreFlatRadius");

        [Serializable]
        public sealed class RendererList { public Renderer[] renderers = new Renderer[0]; }

        int m_Applied = -2;
        public string ActiveTier { get; private set; } = "";

        void OnEnable() { m_Applied = -2; Apply(); }

        void Update()
        {
            int level = Level;
            if (level != m_Applied) Apply();
        }

        int Level => forceLevel >= 0 ? forceLevel : Mathf.Clamp(QualitySettings.GetQualityLevel(), 0, 3);

        public void Apply()
        {
            int level = Level;
            m_Applied = level;
            Shader.SetGlobalFloat(k_TyreFlat, tyreFlatRadius);
            string tier = TierNames[level];
            ActiveTier = tier;
            var set = residentSet != null && residentSet.name.EndsWith(tier, StringComparison.Ordinal) ? residentSet
                : Resources.Load<TruckMaterialSet>(ResourcesPrefix + tier);
            // Default APK ships no High set (build audit 2026-11-09): fall back to the next lower tier before the resident one.
            if (set == null && level > 0)
                for (int l = level - 1; l >= 0 && set == null; l--) set = Resources.Load<TruckMaterialSet>(ResourcesPrefix + TierNames[l]);
            if (set == null) set = residentSet;
            if (set != null)
                foreach (var rs in slots)
                {
                    if (rs.renderer == null || rs.slots == null) continue;
                    var mats = rs.renderer.sharedMaterials;
                    bool changed = mats.Length != rs.slots.Length;
                    if (changed) mats = new Material[rs.slots.Length];
                    for (int i = 0; i < rs.slots.Length; i++)
                    {
                        var m = set.Get(rs.slots[i]);
                        if (m != null && mats[i] != m) { mats[i] = m; changed = true; }
                    }
                    if (changed) rs.renderer.sharedMaterials = mats;
                }

            // Exterior LOD chain per tier: (screen height threshold, LOD index).
            var chain = ExteriorChainFor(tier, screenSizes);
            if (exteriorGroup != null)
            {
                var lods = new LOD[chain.Length];
                for (int i = 0; i < chain.Length; i++) lods[i] = new LOD(chain[i].size, R(exteriorLods, chain[i].lod));
                for (int i = 0; i < 3; i++) SetEnabled(R(exteriorLods, i), lods);
                exteriorGroup.SetLODs(lods);
                exteriorGroup.RecalculateBounds();
            }
            if (glassGroup != null)
            {
                var gchain = GlassLodsFor(tier, screenSizes, interiorCull);
                var lods = new LOD[gchain.Length];
                for (int i = 0; i < gchain.Length; i++) lods[i] = new LOD(gchain[i].size, R(glassLods, gchain[i].lod));
                for (int i = 0; i < 3; i++) SetEnabled(R(glassLods, i), lods);
                glassGroup.SetLODs(lods);
                glassGroup.RecalculateBounds();
            }
            if (interiorGroup != null)
            {
                int il = InteriorLodFor(tier);
                for (int i = 0; i < 3; i++)
                {
                    var rs = interiorLods != null && i < interiorLods.Length && interiorLods[i] != null ? interiorLods[i].renderers : new Renderer[0];
                    foreach (var r in rs) if (r != null) r.enabled = i == il;
                }
                interiorGroup.SetLODs(new[] { new LOD(interiorCull, interiorLods[il].renderers) });
                interiorGroup.RecalculateBounds();
            }
        }

        static Renderer[] R(RendererList[] l, int i) => l != null && i < l.Length && l[i] != null && l[i].renderers != null ? l[i].renderers : new Renderer[0];

        /// <summary>Exterior LOD chain of a tier as (screen height threshold, LOD index): High LOD0-1-2, Medium LOD1-2, Low LOD2.</summary>
        public static (float size, int lod)[] ExteriorChainFor(string tier, float[] s) => tier switch
        {
            "High" => new[] { (s[0], 0), (s[1], 1), (s[3], 2) },
            "Medium" => new[] { (s[1], 1), (s[3], 2) },
            _ => new[] { (s[3], 2) },
        };

        /// <summary>
        /// Cab glazing chain of a tier (ADR 0045): LOD0 glass first on every tier, down to the larger of the tier's first
        /// exterior threshold and the interior cull (the interior is drawn through the glass only above it); below that the
        /// glass follows the exterior chain. Low: LOD0 > 0.12, LOD2 to cull. Medium: LOD0 > 0.18, LOD2. High: as the body.
        /// The LOD0 glazing is 912 triangles in total (windscreen 432 + doors 2 x 240), cheap on any tier.
        /// </summary>
        public static (float size, int lod)[] GlassLodsFor(string tier, float[] s, float interiorCull)
        {
            var c = ExteriorChainFor(tier, s);
            var r = new System.Collections.Generic.List<(float, int)> { (Mathf.Max(c[0].size, interiorCull), 0) };
            if (c[0].lod != 0 && c[0].size < interiorCull) r.Add(c[0]);
            for (int i = 1; i < c.Length; i++) r.Add(c[i]);
            return r.ToArray();
        }

        static void SetEnabled(Renderer[] rs, LOD[] lods)
        {
            foreach (var r in rs)
            {
                if (r == null) continue;
                bool used = false;
                foreach (var l in lods) if (Array.IndexOf(l.renderers, r) >= 0) { used = true; break; }
                r.enabled = used;
            }
        }
    }
}
