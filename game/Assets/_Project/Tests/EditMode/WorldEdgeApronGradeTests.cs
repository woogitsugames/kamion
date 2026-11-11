using System;
using System.Collections.Generic;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests.EditMode
{
    public class WorldEdgeApronGradeTests
    {
        [TestCase(0.025f)]
        [TestCase(-0.025f)]
        public void ObliqueContinuation_StaysAboveApron_OnTransverseTerrainSlope(float slope)
        {
            var root = new GameObject("edge_grade_fixture");
            root.transform.position = new Vector3(100000f, 0f, 100000f);
            var terrain = new Mesh();
            var apron = new Mesh();
            var groundOnly = new Mesh();
            try
            {
                const float half = 1024f, baseY = 140f;
                terrain.vertices = new[] {
                    new Vector3(-half, baseY-slope*half, -half),
                    new Vector3(-half, baseY-slope*half, half),
                    new Vector3(half, baseY+slope*half, half),
                    new Vector3(half, baseY+slope*half, -half)
                };
                terrain.triangles = new[] { 0, 1, 2, 0, 2, 3 };
                terrain.RecalculateBounds();
                var source = new GameObject("col_terrain");
                source.transform.SetParent(root.transform, false);
                source.AddComponent<MeshCollider>().sharedMesh = terrain;
                Physics.SyncTransforms();

                // Reflect the importer so this regression does not add an asmdef dependency to the test suite.
                var type = Type.GetType("Game.World.Import.WorldEdgeBuilder, Game.World.Import.Editor", true);
                var build = type.GetMethod("BuildApron", BindingFlags.NonPublic | BindingFlags.Static);
                Assert.NotNull(build);
                var direction = new Vector2(0.46f, -0.89f).normalized;
                var stubs = new List<(Vector3 start, Vector2 dir, float width)> {
                    (new Vector3(0f, baseY, -half), direction, 7f)
                };
                build.Invoke(null, new object[] { apron, root.transform,
                    new Vector2(-half, -half), new Vector2(half, half), stubs });
                Assert.AreEqual(2, apron.subMeshCount, "grass and asphalt; no new draw slot");
                Assert.AreEqual(24, apron.GetTriangles(1).Length / 3,
                    "one continuation retains 12 asphalt quads");

                // Raycast only the grass/shoulder submesh, not the asphalt being tested.
                groundOnly.vertices = apron.vertices;
                groundOnly.triangles = apron.GetTriangles(0);
                groundOnly.RecalculateBounds();
                var grass = new GameObject("apron_without_asphalt");
                grass.transform.SetParent(root.transform, false);
                var collider = grass.AddComponent<MeshCollider>();
                collider.sharedMesh = groundOnly;
                Physics.SyncTransforms();
                var vertices = apron.vertices;
                var indices = apron.GetTriangles(1);
                int measured = 0;
                for (int i = 0; i < indices.Length; i += 3)
                {
                    Vector3 centre = (vertices[indices[i]] + vertices[indices[i+1]] + vertices[indices[i+2]]) / 3f;
                    if (Vector2.Dot(new Vector2(centre.x, centre.z + half), direction) < 140f) continue;
                    Vector3 world = root.transform.TransformPoint(centre);
                    Assert.IsTrue(collider.Raycast(new Ray(world + Vector3.up*500f, Vector3.down), out var hit, 1000f));
                    Assert.GreaterOrEqual(world.y - hit.point.y, -0.02f,
                        $"road buried at {centre}; slope {slope}");
                    measured++;
                }
                Assert.Greater(measured, 8);
            }
            finally
            {
                Object.DestroyImmediate(root);
                Object.DestroyImmediate(terrain);
                Object.DestroyImmediate(apron);
                Object.DestroyImmediate(groundOnly);
            }
        }
    }
}
