using System;
using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// ADR 0240 (B-088, REVIEW s20-gate3-phone P1-3): which world casters are too thin for the main-light shadow map of a
    /// tier that switches them off (<see cref="QualityProfile.Tier.thinCasterShadowsOff"/>, Low). On the A16 the Low map is
    /// one 1024 px cascade over 35 m, about 8 cm per texel (ESTIMATED from the cascade sphere): a lamp arm, a sign post or
    /// a fence wire is narrower than two texels and its shadow was a dashed smear on the carriageway.
    ///
    /// Rule = category (prototype name prefix) first, geometry (bounding box) as the fallback for prototypes this list
    /// does not know. The prefix list is calibrated on the prop library with tools/rendering/thin_shadow_audit.py
    /// (share of the ground shadow that is at least two Low texels wide: thin families &lt; 0.8, the rest &gt;= 0.9) and
    /// mirrored there (THIN_PREFIXES / THIN_EXACT / MaxRodWidthM) - keep the two in sync.
    /// Pure functions, no allocation: WorldInstances calls them once per prototype at load.
    /// </summary>
    public static class ThinShadowCasterPolicy
    {
        /// <summary>A prototype whose middle bounding-box dimension is below this is a rod (post, bollard, boom, chain):
        /// two small dimensions. Plates and boxes have at most one. 0.20 m = about 2.5 Low shadow texels. WORKING_VALUE.</summary>
        public const float MaxRodWidthM = 0.20f;

        // Lamp columns and arms 0.16-0.23 m mean shadow width, lattice gantries / pylons 0.14 m members, sign and signal
        // posts 0.06-0.15 m, bollards, chains, railings, mesh fences and gate grilles 0.03-0.08 m (thin_shadow_audit.py).
        // Not here on purpose (resolved >= 0.9 at Low): signal_mast (0.24 m), signal heads, plate_ / board_ sign faces,
        // power_pole (0.29 m), lift_gate, cantilever_gate, bins, cabinets, shelters, vehicles.
        static readonly string[] k_ThinPrefixes =
        {
            "lamp_", "signal_pole", "sign_post", "sign_g3_", "sign_gantry_", "sign_cantilever_", "bollard", "railing_",
            "fence_", "sliding_gate", "barrier_arm", "barrier_boom", "chain_", "wire_",
        };
        static readonly string[] k_ThinExact = { "pylon" };   // the HV lattice tower; "pylon_u5a" is a 0.3 m marker post

        // Chunk-merged furniture / plot materials (RegionImporter -> Kamion/World PBR _LowNoShadow, like the manifest flag
        // "shadow_low": false of ADR 0123): fence posts 4 cm, W-beam posts (the beam is already flagged).
        // Solid fences are "concrete_fence" / wall materials and do not match. The welded mesh panels ("fence_*_mesh")
        // are NOT handled here: ADR 0239 (FenceMeshCoverage.CastsShadow) switches their caster off on every tier.
        const string k_FenceMeshSuffix = "_mesh";
        static readonly string[] k_ThinMaterialPrefixes = { "fence_", "barrier_post", "chain_" };

        /// <summary>True when an instanced prototype must not cast on a tier with thin casters off.</summary>
        /// <param name="prototype">Prototype name (WorldInstanceSet.Prototype.name).</param>
        /// <param name="boundsSize">Size of the LOD0 mesh bounds, metres.</param>
        public static bool IsThin(string prototype, Vector3 boundsSize)
        {
            if (!string.IsNullOrEmpty(prototype))
            {
                // Trees have their own caster policy (treeShadowLodMask); vehicles and their contact patches never match.
                if (prototype.StartsWith("tree_", StringComparison.Ordinal)) return false;
                for (int i = 0; i < k_ThinExact.Length; i++)
                    if (string.Equals(prototype, k_ThinExact[i], StringComparison.Ordinal)) return true;
                for (int i = 0; i < k_ThinPrefixes.Length; i++)
                    if (prototype.StartsWith(k_ThinPrefixes[i], StringComparison.Ordinal)) return true;
            }
            float w = RodWidth(boundsSize);
            return w > 0f && w < MaxRodWidthM;
        }

        /// <summary>Middle dimension of a bounding box (m): the thickness of a rod-like object in its second-thinnest axis.</summary>
        public static float RodWidth(Vector3 size)
        {
            float a = Mathf.Abs(size.x), b = Mathf.Abs(size.y), c = Mathf.Abs(size.z);
            return Mathf.Max(Mathf.Min(a, b), Mathf.Min(Mathf.Max(a, b), c));
        }

        /// <summary>True when a chunk material (manifest id) is thin street furniture that casts nothing on Low.</summary>
        public static bool IsThinMaterial(string materialId)
        {
            if (string.IsNullOrEmpty(materialId)) return false;
            if (materialId.StartsWith("fence_", StringComparison.Ordinal) && materialId.EndsWith(k_FenceMeshSuffix, StringComparison.Ordinal))
                return false;   // ADR 0239 owns the fence mesh
            for (int i = 0; i < k_ThinMaterialPrefixes.Length; i++)
                if (materialId.StartsWith(k_ThinMaterialPrefixes[i], StringComparison.Ordinal)) return true;
            return false;
        }
    }
}
