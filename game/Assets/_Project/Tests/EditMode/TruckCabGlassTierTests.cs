using System;
using System.Linq;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0045: the driver always looks through the LOD0 cab glazing, on every quality tier. Low used to draw the
    /// LOD2 glass only, which does not cover the LOD0 cab opening from the eye point, so the cab view showed bare sky.
    /// </summary>
    public class TruckCabGlassTierTests
    {
        const string PrefabPath = "Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab";
        static readonly float[] Sizes = { 0.45f, 0.18f, 0.07f, 0.006f };
        GameObject m_Go;

        [TearDown]
        public void TearDown() { if (m_Go != null) Object.DestroyImmediate(m_Go); }

        [TestCase("Low"), TestCase("Medium"), TestCase("High")]
        public void GlassChain_StartsWithLod0_StrictlyDecreasing_EndsAtCull(string tier)
        {
            var g = TruckVisualRig.GlassLodsFor(tier, Sizes, 0.12f);
            Assert.AreEqual(0, g[0].lod, "LOD0 glazing is the near level on " + tier);
            Assert.That(g[0].size, Is.GreaterThanOrEqualTo(0.12f), "LOD0 glazing covers every distance the interior is drawn at");
            for (int i = 1; i < g.Length; i++) Assert.That(g[i].size, Is.LessThan(g[i - 1].size), "LOD thresholds strictly decreasing");
            Assert.AreEqual(Sizes[3], g[g.Length - 1].size, 1e-6f, "glass culls with the body");
            Assert.AreEqual(TruckVisualRig.ExteriorChainFor(tier, Sizes).Last().lod, g[g.Length - 1].lod, "far glass = far body LOD");
        }

        [Test]
        public void DoubleSidedGlass_AddsInsideFace_OnlyWhenMissing()
        {
            var q = new Mesh
            {
                vertices = new[] { new Vector3(0, 0, 1), new Vector3(1, 0, 1), new Vector3(0, 1, 1) },
                normals = new[] { Vector3.forward, Vector3.forward, Vector3.forward },   // outward (away from an eye at the origin)
                colors = new[] { Color.green, Color.green, Color.green },
                triangles = new[] { 0, 2, 1 },
            };
            var d = Game.Editor.Setup.TruckAssetBuilder.DoubleSidedGlass(q, Vector3.zero, save: false);
            Assert.IsNotNull(d);
            Assert.AreEqual(6, d.vertexCount);
            Assert.AreEqual(Vector3.back, d.normals[3], "inside face normal towards the eye");
            Assert.AreEqual(Color.green, d.colors[4], "tint kept on the inside face");
            CollectionAssert.AreEqual(new[] { 0, 2, 1, 3, 4, 5 }, d.triangles, "inside face has reversed winding");
            Assert.IsNull(Game.Editor.Setup.TruckAssetBuilder.DoubleSidedGlass(d, Vector3.zero, save: false), "already double-sided: unchanged");
            Object.DestroyImmediate(q); Object.DestroyImmediate(d);
        }

        [Test]
        public void Prefab_InCabGlassRenderer_EnabledAndNearLod_OnEveryTier()
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
            Assume.That(prefab, Is.Not.Null, "TRAKT prefab not generated (Kamion/Setup/Rebuild TRAKT truck)");
            m_Go = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            var rig = m_Go.GetComponent<TruckVisualRig>();
            Assert.IsNotNull(rig.glassGroup, "cab glazing has its own LOD group (rebuild the TRAKT prefab)");
            var shield = rig.glassLods[0].renderers.FirstOrDefault(r => r != null && r.name.StartsWith("GLASS_Windscreen", StringComparison.Ordinal));
            Assert.IsNotNull(shield, "LOD0 windscreen in glassLods[0]");
            var eye = m_Go.GetComponentsInChildren<Transform>(true).First(t => t.name == "DriverEyePoint");
            foreach (var g in rig.glassLods.SelectMany(l => l.renderers))
            {
                var mesh = g.GetComponent<MeshFilter>().sharedMesh;
                var eyeOS = g.transform.InverseTransformPoint(eye.position);
                var v = mesh.vertices; var n = mesh.normals;
                Assert.That(Enumerable.Range(0, v.Length).Any(i => Vector3.Dot(n[i], eyeOS - v[i]) > 0f), $"{g.name} has a face towards the driver (Cull Back)");
            }
            Assert.That(rig.exteriorLods.SelectMany(l => l.renderers).Any(r => r != null && r.name.StartsWith("GLASS_", StringComparison.Ordinal)), Is.False,
                "glazing is not also in the exterior LOD group (double glass)");
            try
            {
                for (int level = 0; level < 4; level++)
                {
                    rig.forceLevel = level;
                    rig.Apply();
                    string tier = TruckVisualRig.TierNames[level];
                    var lods = rig.glassGroup.GetLODs();
                    foreach (var r in rig.glassLods[0].renderers)
                    {
                        Assert.IsTrue(r.enabled, $"{r.name} enabled on {tier}");
                        Assert.That(Array.IndexOf(lods[0].renderers, r), Is.GreaterThanOrEqualTo(0), $"{r.name} in the near LOD on {tier}");
                    }
                    Assert.That(lods[0].screenRelativeTransitionHeight, Is.GreaterThanOrEqualTo(rig.interiorCull), $"LOD0 glass wherever the interior is drawn ({tier})");
                    // No double glazing: the near glass level holds the LOD0 glass only.
                    Assert.That(lods[0].renderers.All(r => rig.glassLods[0].renderers.Contains(r)), $"near glass level is LOD0 only on {tier}");
                }
            }
            finally { rig.forceLevel = -1; }
        }

        /// <summary>
        /// ADR 0046: exactly one glass layer per tier. The glazing group (GLASS_*) is the only glass; no exterior body renderer
        /// (CAB_Body_LODn ...) keeps a MI_Ext_Glass slot / submesh, so Low's LOD2 body no longer draws a second glass sheet.
        /// </summary>
        [Test]
        public void Prefab_SingleGlassLayer_OnEveryTier()
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
            Assume.That(prefab, Is.Not.Null, "TRAKT prefab not generated (Kamion/Setup/Rebuild TRAKT truck)");
            m_Go = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            var rig = m_Go.GetComponent<TruckVisualRig>();
            var gb = rig.glassLods.SelectMany(l => l.renderers).Where(g => g != null).Select(g => { var b = g.bounds; b.Expand(0.04f); return b; }).ToArray();
            int lensTris = 0;
            foreach (var rs in rig.slots)
            {
                if (rs.renderer == null || rs.renderer.name.StartsWith("GLASS_", StringComparison.Ordinal)) continue;
                var mf = rs.renderer.GetComponent<MeshFilter>();
                var mesh = mf.sharedMesh;
                Assert.That(rs.slots.Length, Is.EqualTo(mesh.subMeshCount), $"{rs.renderer.name}: slots match submeshes");
                var v = mesh.vertices; var l2w = rs.renderer.transform.localToWorldMatrix;
                for (int sm = 0; sm < rs.slots.Length; sm++)
                {
                    if (rs.slots[sm] != "MI_Ext_Glass") continue;
                    var t = mesh.GetTriangles(sm);
                    for (int i = 0; i < t.Length; i += 3)
                    {
                        var c = l2w.MultiplyPoint3x4((v[t[i]] + v[t[i + 1]] + v[t[i + 2]]) / 3f);
                        Assert.That(gb.Any(b => b.Contains(c)), Is.False, $"{rs.renderer.name}: body glass face duplicates the glazing (double glass)");
                    }
                    lensTris += t.Length / 3;
                }
            }
            Assert.That(lensTris, Is.GreaterThan(0), "lamp lens faces (MI_Ext_Glass on the body) remain");
            try
            {
                for (int level = 0; level < 4; level++)
                {
                    rig.forceLevel = level;
                    rig.Apply();
                    string tier = TruckVisualRig.TierNames[level];
                    // The windscreen is drawn by exactly one glass LOD level at any distance: LOD levels hold disjoint renderers.
                    var all = rig.glassGroup.GetLODs().SelectMany(l => l.renderers).Where(r => r != null && r.name.StartsWith("GLASS_Windscreen", StringComparison.Ordinal)).ToArray();
                    Assert.AreEqual(all.Length, all.Distinct().Count(), $"windscreen renderers appear once across glass LOD levels ({tier})");
                }
            }
            finally { rig.forceLevel = -1; }
        }
    }
}
