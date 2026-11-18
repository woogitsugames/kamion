using System;
using System.Collections.Generic;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests.EditMode
{
    /// <summary>ADR 0298: the apron of a rural tile carries the farmland flag and starts at the edge with the terrain's own
    /// ground masks (no seam), blending to the apron mask by the 30 m ring.</summary>
    public class WorldEdgeApronFarmMaskTests
    {
        static readonly Type k_Type = Type.GetType("Game.World.Import.WorldEdgeBuilder, Game.World.Import.Editor", true);
        static FieldInfo F(string n) => k_Type.GetField(n, BindingFlags.NonPublic | BindingFlags.Static);

        [Test]
        public void RuralApron_FlagsArableFarmland_EdgeRingCopiesTerrainMask()
        {
            var root = new GameObject("edge_farm_fixture");
            var terrain = new Mesh();
            var apron = new Mesh();
            var farm = F("s_FarmApron");
            var border = F("s_BorderMask");
            Assert.NotNull(farm); Assert.NotNull(border);
            try
            {
                const float half = 1024f;
                terrain.vertices = new[] { new Vector3(-half, 140f, -half), new Vector3(-half, 140f, half), new Vector3(half, 140f, half), new Vector3(half, 140f, -half) };
                terrain.triangles = new[] { 0, 1, 2, 0, 2, 3 };
                var col = new GameObject("col_terrain");
                col.transform.SetParent(root.transform, false);
                col.AddComponent<MeshCollider>().sharedMesh = terrain;
                Physics.SyncTransforms();
                var garden = new Color32(255, 0, 60, 0);
                farm.SetValue(null, true);
                border.SetValue(null, (Func<Vector2, Color32?>)(p => garden));
                k_Type.GetMethod("BuildApron", BindingFlags.NonPublic | BindingFlags.Static).Invoke(null, new object[] {
                    apron, root.transform, new Vector2(-half, -half), new Vector2(half, half), new List<(Vector3, Vector2, float)>() });
                var v = apron.vertices; var c = apron.colors32;
                int edgeIdx = Array.FindIndex(v, p => Mathf.Abs(p.x + half) < 0.01f && Mathf.Abs(p.z) < 20f);
                int farIdx = Array.FindIndex(v, p => Mathf.Abs(p.x + half + 80f) < 0.01f && Mathf.Abs(p.z) < 20f);
                Assert.GreaterOrEqual(edgeIdx, 0); Assert.GreaterOrEqual(farIdx, 0);
                Assert.AreEqual(60, c[edgeIdx].b, "edge ring = the terrain's own mask");
                Assert.AreEqual(255, c[farIdx].b, "80 m out = arable farmland flag");
                Assert.AreEqual(0, c[farIdx].g, "no region-C forest litter zone on a rural apron");
            }
            finally
            {
                farm.SetValue(null, false);
                border.SetValue(null, null);
                Object.DestroyImmediate(root);
                Object.DestroyImmediate(terrain);
                Object.DestroyImmediate(apron);
            }
        }
    }
}
