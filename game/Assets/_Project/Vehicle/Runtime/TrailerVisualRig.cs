using System;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Quality-tier binding and moving parts of the art curtainsider trailer (TrailerAssetBuilder, manifest
    /// art-source/truck/trailer/export/trailer_manifest.json). Same scheme as <see cref="TruckVisualRig"/>: per tier the
    /// LOD chain (High LOD0-1-2, Medium LOD1-2, Low LOD2) and the material set (the prefab holds Low; Medium/High load from
    /// Resources). Also: the trailer tyre contact-patch radius (global, rendering layer bit 9 in Kamion/Truck Exterior),
    /// the landing-gear crank turned from the leg travel that <see cref="TrailerVisuals"/> already drives from the solver,
    /// and the rear doors (open fraction, manifest: +/-270 deg about the hinge). Visual only: no physics here.
    /// </summary>
    [ExecuteAlways]
    [DefaultExecutionOrder(62)]   // after TrailerVisuals (61): reads the leg position it wrote this frame
    public sealed class TrailerVisualRig : MonoBehaviour
    {
        public const string ResourcesPrefix = "TRAILER/TrailerMaterials_";
        /// <summary>Rendering layer bit of the trailer wheel renderers (tractor: bit 8, TruckVisualRig.TyreRenderingLayer).</summary>
        public const uint TyreRenderingLayer = 1u << 9;
        /// <summary>ADR 0182: rendering layer bit of the rear door leaves (Kamion/Truck Exterior rear-face soiling).</summary>
        public const uint RearDoorRenderingLayer = 1u << 11;

        public TruckVisualRig.RendererList[] lods = new TruckVisualRig.RendererList[3];
        public LODGroup group;
        public TruckVisualRig.RendererSlots[] slots = new TruckVisualRig.RendererSlots[0];
        [Tooltip("Material set referenced by the prefab (Low)")] public TruckMaterialSet residentSet;
        [Tooltip("Manifest lod_screen_size_suggestion: LOD0 0.4, LOD1 0.16, LOD2 0.05, cull 0.005")]
        public float[] screenSizes = { 0.4f, 0.16f, 0.05f, 0.005f };
        [Tooltip("-1 = follow QualitySettings")] public int forceLevel = -1;
        [Tooltip("Trailer tyre rolling radius from the physics definition (m); the wheel meshes (free radius 0.536 m) are flattened at it. 0 = off")]
        public float tyreFlatRadius;

        [Header("Moving parts")]
        [Tooltip("Landing-gear inner leg driven by TrailerVisuals (local y = foot height)")] public Transform leg;
        public float raisedFootY = 0.45f;
        public Transform crank;
        [Tooltip("Leg travel per crank turn (m). WORKING_VALUE, manifest: gear ratio UNVERIFIED, 1 turn = 0.01 m")]
        public float metresPerTurn = 0.01f;
        public Transform doorLeft, doorRight;
        [Range(0f, 1f)] public float doorsOpen;

        static readonly int k_TyreFlat = Shader.PropertyToID("_KamionTrailerTyreFlatRadius");
        int m_Applied = -2;
        Quaternion m_CrankRest = Quaternion.identity;
        bool m_CrankRestSet;

        void OnEnable() { m_Applied = -2; Apply(); }

        void Update()
        {
            if (Level != m_Applied) Apply();
        }

        void LateUpdate()
        {
            if (crank != null && leg != null)
            {
                if (!m_CrankRestSet) { m_CrankRest = crank.localRotation; m_CrankRestSet = true; }
                float turns = (raisedFootY - leg.localPosition.y) / Mathf.Max(1e-4f, metresPerTurn);
                crank.localRotation = m_CrankRest * Quaternion.Euler(Mathf.Repeat(turns, 1f) * 360f, 0f, 0f);
            }
            if (doorLeft != null) doorLeft.localRotation = Quaternion.Euler(0f, 270f * doorsOpen, 0f);
            if (doorRight != null) doorRight.localRotation = Quaternion.Euler(0f, -270f * doorsOpen, 0f);
        }

        int Level => forceLevel >= 0 ? forceLevel : Mathf.Clamp(QualitySettings.GetQualityLevel(), 0, 3);

        public void Apply()
        {
            int level = Level;
            m_Applied = level;
            Shader.SetGlobalFloat(k_TyreFlat, tyreFlatRadius);
            string tier = TruckVisualRig.TierNames[level];
            var set = residentSet != null && residentSet.name.EndsWith(tier, StringComparison.Ordinal) ? residentSet : null;
            // A build without the High sets falls back to the next lower tier, then to the resident (Low) set.
            for (int l = level; set == null && l >= 0; l--) set = Resources.Load<TruckMaterialSet>(ResourcesPrefix + TruckVisualRig.TierNames[l]);
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
            if (group == null) return;
            Renderer[] R(int i) => lods != null && i < lods.Length && lods[i] != null ? lods[i].renderers : new Renderer[0];
            LOD[] chain = tier switch
            {
                "High" => new[] { new LOD(screenSizes[0], R(0)), new LOD(screenSizes[1], R(1)), new LOD(screenSizes[3], R(2)) },
                "Medium" => new[] { new LOD(screenSizes[1], R(1)), new LOD(screenSizes[3], R(2)) },
                _ => new[] { new LOD(screenSizes[3], R(2)) },
            };
            for (int i = 0; i < 3; i++)
                foreach (var r in R(i))
                {
                    if (r == null) continue;
                    bool used = false;
                    foreach (var l in chain) if (Array.IndexOf(l.renderers, r) >= 0) { used = true; break; }
                    r.enabled = used;
                }
            group.SetLODs(chain);
            group.RecalculateBounds();
        }
    }
}
