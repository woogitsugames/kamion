using System;
using System.Reflection;
using Game.Rendering;
using Game.World;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// pc-shadows-s23: on the PC Low and Medium tiers trees cast no shadow on the road (knyszyn-s, Windows player), although
    /// [PC_TIER] declares 60 m / 100 m shadows. Cause: treeShadowLodMask 1 (LOD0 only, the mobile A16 value) with
    /// treeCardLodScale 0.5 and the tree LOD ends 20/60 m (InstanceImporter.Policy) - LOD0 ends 10 m from the camera, so only
    /// trees closer than that cast. This checks the distance from the camera up to which a tree still casts, per PC tier,
    /// with the same LOD selection as WorldInstances.Render (lodScale = min(lodBias, treeCardLodScale), cull x lodBias).
    /// </summary>
    public class PcTreeShadowReachTests
    {
        /// <summary>Cab camera → roadside tree on a 2-lane road with a verge, plus the trees ahead that shade the lane in front of
        /// the bonnet (knyszyn-s start view): ~10-30 m. WORKING_VALUE.</summary>
        const float MinRoadsideReachM = 25f;

        static (float[] ends, int shadowMask) Policy(string proto, int lodCount)
        {
            var t = Type.GetType("Game.World.Import.InstanceImporter, Game.World.Import.Editor", true);
            var m = t.GetMethod("Policy", BindingFlags.NonPublic | BindingFlags.Static);
            Assert.IsNotNull(m, "InstanceImporter.Policy not found");
            return ((float[], int))m.Invoke(null, new object[] { proto, lodCount });
        }

        /// <summary>Farthest camera distance (0.25 m steps, up to the tier's shadow distance) at which a tree LOD that casts on
        /// this tier is selected. Mirrors WorldInstances.Render (ls) and WorldInstances.Flush (mask).</summary>
        static float CastReach(PcTierSettings s)
        {
            var (ends, protoMask) = Policy("tree_pine", 3);
            int mask = protoMask & s.treeShadowLodMask;
            float ls = Mathf.Min(s.lodBias, s.treeCardLodScale);
            float reach = 0f;
            for (float d = 0f; d <= s.shadowDistance; d += 0.25f)
            {
                int lod = WorldInstances.LodAt(ends, d, ls, s.lodBias);
                if (lod >= 0 && (mask & (1 << lod)) != 0) reach = d;
            }
            return reach;
        }

        [Test]
        public void TreesCastAlongTheRoad_OnEveryPcTier()
        {
            foreach (var s in PcTierTable.Defaults())
            {
                float r = CastReach(s);
                Assert.GreaterOrEqual(r, MinRoadsideReachM,
                    $"{s.Name}: trees cast only up to {r:F1} m from the camera (shadow distance {s.shadowDistance} m, mask {s.treeShadowLodMask}, " +
                    $"card scale {s.treeCardLodScale}) - no tree shadow on the road from the cab");
            }
        }

        [Test]
        public void TreeShadowReach_IsMonotonicAcrossPcTiers()
        {
            var t = PcTierTable.Defaults();
            for (int i = 1; i < t.Length; i++)
                Assert.LessOrEqual(CastReach(t[i - 1]), CastReach(t[i]), t[i - 1].Name + "→" + t[i].Name);
        }

        [Test]
        public void TreesCastBeyondLod0_OnEveryPcTier()
        {
            // Regression guard on the mask itself: LOD1 cards must be in the PC shadow pass (bit 1), otherwise the reach
            // collapses to LOD0 end x card scale (10 m on Low/Medium).
            foreach (var s in PcTierTable.Defaults())
                Assert.AreNotEqual(0, s.treeShadowLodMask & 0b10, s.Name + ": treeShadowLodMask without LOD1");
        }
    }
}
