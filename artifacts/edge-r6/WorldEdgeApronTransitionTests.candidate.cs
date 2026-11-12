// Prepared candidate only: not installed in Assets or compiled before fresh Before.
using System;
using System.Collections.Generic;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests.EditMode
{
    [NonParallelizable]
    public class WorldEdgeApronTransitionTests
    {
        // Independent 16 m perimeter fixture: one 130 m sample and twelve 140 m
        // neighbours. At the documented end of near easing the target is the
        // uniform mean minus the 0.15 m profile offset, not a sampled ring value.
        const float NearTarget = (12f * 140f + 130f) / 13f - 0.15f;

        [TestCase(-1f)]
        [TestCase(1f)]
        public void DitchTransition_ActualTrianglesMeetSmoothedProfile(float side)
        {
            using (var fixture = new DitchApron())
                Assert.AreEqual(NearTarget, fixture.HeightAt(0f, side * (1024f + 220f)), 0.01f,
                    "triangulated apron must not undershoot the smoothed profile at the end of near easing");
        }

        [TestCase(-1f, 220f)]
        [TestCase(1f, 220f)]
        [TestCase(-1f, 232f)]
        [TestCase(1f, 232f)]
        public void BuriedCurtainProxy_DoesNotFloatAboveActualApron(float side, float distance)
        {
            using (var fixture = new DitchApron())
            {
                // A half-metre buried base near the completed near profile.
                // The far easing changes this target by much less than 1 mm at
                // 232 m. Tolerance is geometric WORKING_VALUE, not photo alpha.
                float baseY = NearTarget - 0.5f;
                float ground = fixture.HeightAt(0f, side * (1024f + distance));
                Assert.LessOrEqual(baseY - ground, 0.05f,
                    "a deliberate curtain skirt must not float because of missing apron profile resolution");
            }
        }

        [TestCase(-1f)]
        [TestCase(1f)]
        public void BoundaryAndExistingGeometryBudget_AreRetained(float side)
        {
            using (var fixture = new DitchApron())
            {
                Assert.AreEqual(130f - 0.04f, fixture.HeightAt(0f, side * 1024f), 0.01f);
                Assert.AreEqual(4752, fixture.Apron.vertexCount, "existing apron budget, no new ring");
                Assert.AreEqual(8448, fixture.Apron.GetTriangles(0).Length / 3);
                Assert.AreEqual(2, fixture.Apron.subMeshCount, "existing grass/asphalt slots");
                Assert.AreEqual(0, fixture.Apron.GetTriangles(1).Length);
            }
        }

        sealed class DitchApron : IDisposable
        {
            readonly GameObject root;
            readonly Mesh terrain;
            public readonly Mesh Apron;

            public DitchApron()
            {
                root = new GameObject("edge_transition_fixture");
                root.transform.position = new Vector3(100000f, 0f, 100000f);
                terrain = new Mesh();
                Apron = new Mesh();
                try
                {
                    float[] xs = { -1024f, -16f, 0f, 16f, 1024f };
                    var positions = new Vector3[10];
                    for (int row = 0; row < 2; row++)
                        for (int col = 0; col < xs.Length; col++)
                            positions[row * xs.Length + col] = new Vector3(
                                xs[col], col == 2 ? 130f : 140f, row == 0 ? -1024f : 1024f);
                    var triangles = new List<int>();
                    for (int col = 0; col + 1 < xs.Length; col++)
                    {
                        int a = col, b = col + 1, c = col + 1 + xs.Length, d = col + xs.Length;
                        triangles.AddRange(new[] { a, d, c, a, c, b });
                    }
                    terrain.vertices = positions;
                    terrain.triangles = triangles.ToArray();
                    terrain.RecalculateBounds();
                    var source = new GameObject("col_terrain");
                    source.transform.SetParent(root.transform, false);
                    source.AddComponent<MeshCollider>().sharedMesh = terrain;
                    Physics.SyncTransforms();
                    var type = Type.GetType("Game.World.Import.WorldEdgeBuilder, Game.World.Import.Editor", true);
                    var build = type.GetMethod("BuildApron", BindingFlags.NonPublic | BindingFlags.Static);
                    Assert.NotNull(build);
                    build.Invoke(null, new object[] { Apron, root.transform,
                        new Vector2(-1024f, -1024f), new Vector2(1024f, 1024f),
                        new List<(Vector3 start, Vector2 dir, float width)>() });
                }
                catch { Dispose(); throw; }
            }

            public float HeightAt(float e, float n)
            {
                var p = new Vector2(e, n);
                var positions = Apron.vertices;
                var triangles = Apron.GetTriangles(0);
                float highest = float.NegativeInfinity;
                for (int i = 0; i < triangles.Length; i += 3)
                {
                    var a = positions[triangles[i]];
                    var b = positions[triangles[i + 1]];
                    var c = positions[triangles[i + 2]];
                    var ab = new Vector2(b.x - a.x, b.z - a.z);
                    var ac = new Vector2(c.x - a.x, c.z - a.z);
                    var ap = p - new Vector2(a.x, a.z);
                    float det = ab.x * ac.y - ab.y * ac.x;
                    if (Mathf.Abs(det) < 1e-7f) continue;
                    float u = (ap.x * ac.y - ap.y * ac.x) / det;
                    float v = (ab.x * ap.y - ab.y * ap.x) / det;
                    if (u < -1e-5f || v < -1e-5f || u + v > 1.00001f) continue;
                    highest = Mathf.Max(highest, a.y + u * (b.y - a.y) + v * (c.y - a.y));
                }
                Assert.IsFalse(float.IsNegativeInfinity(highest), "test point must have actual apron triangles");
                return highest;
            }

            public void Dispose()
            {
                Object.DestroyImmediate(root);
                Object.DestroyImmediate(terrain);
                Object.DestroyImmediate(Apron);
            }
        }
    }
}
