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

            // Exterior LOD chain per tier.
            if (exteriorGroup != null)
            {
                Renderer[] R(int i) => exteriorLods != null && i < exteriorLods.Length && exteriorLods[i] != null ? exteriorLods[i].renderers : new Renderer[0];
                LOD[] lods = tier switch
                {
                    "High" => new[] { new LOD(screenSizes[0], R(0)), new LOD(screenSizes[1], R(1)), new LOD(screenSizes[3], R(2)) },
                    "Medium" => new[] { new LOD(screenSizes[1], R(1)), new LOD(screenSizes[3], R(2)) },
                    _ => new[] { new LOD(screenSizes[3], R(2)) },
                };
                for (int i = 0; i < 3; i++) SetEnabled(R(i), lods);
                exteriorGroup.SetLODs(lods);
                exteriorGroup.RecalculateBounds();
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
