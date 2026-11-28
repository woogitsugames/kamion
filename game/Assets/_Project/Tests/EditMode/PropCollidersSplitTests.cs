using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.RegularExpressions;
using Game.Editor.Build;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    public class PropCollidersSplitTests
    {
        const string TestRegion = "_test_prop_colliders_synth";

        static Type RegionImporterType => Type.GetType("Game.World.Import.RegionImporter, Game.World.Import.Editor", true);
        static Type WorldSceneBuilderType => Type.GetType("Game.World.Import.WorldSceneBuilder, Game.World.Import.Editor", true);
        static Type GlbReaderType => Type.GetType("Game.World.Import.GlbReader, Game.World.Import.Editor", true);
        static Type InstanceImporterType => Type.GetType("Game.World.Import.InstanceImporter, Game.World.Import.Editor", true);

        [SetUp]
        public void EmptyScene() => EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        [TearDown]
        public void CleanUp()
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            string report = Path.Combine(EditorTools.RepoRoot, "artifacts", "world", TestRegion + "-props-on-road.txt");
            if (File.Exists(report)) File.Delete(report);
        }

        static object NewGlbPrimitive(string material, Vector3[] positions, int[] indices)
        {
            var primType = GlbReaderType.GetNestedType("Primitive", BindingFlags.Public);
            var prim = Activator.CreateInstance(primType);
            primType.GetField("Material").SetValue(prim, material);
            primType.GetField("Positions").SetValue(prim, positions);
            primType.GetField("Indices").SetValue(prim, indices);
            return prim;
        }

        static object NewGlbNode(string name, params object[] primitives)
        {
            var nodeType = GlbReaderType.GetNestedType("MeshNode", BindingFlags.Public);
            var node = Activator.CreateInstance(nodeType);
            nodeType.GetField("Name").SetValue(node, name);
            var list = (IList)nodeType.GetField("Primitives").GetValue(node);
            foreach (var p in primitives) list.Add(p);
            return node;
        }

        static (object result, object chunk, object low) BuildSyntheticChunk(bool includeRoadProp, bool includeYardProp)
        {
            var resultType = RegionImporterType.GetNestedType("Result", BindingFlags.Public);
            var chunkType = RegionImporterType.GetNestedType("Chunk", BindingFlags.Public);
            var collidersType = InstanceImporterType.GetNestedType("Colliders", BindingFlags.Public);

            var result = Activator.CreateInstance(resultType);
            resultType.GetField("Region").SetValue(result, TestRegion);
            var matSurface = (IDictionary)resultType.GetField("MaterialSurface").GetValue(result);
            matSurface["collision_asphalt"] = "asphalt";
            matSurface["yard_asphalt"] = "asphalt";

            // Clockwise quads seen from +Y so downward raycasts hit front faces.
            var roadVerts = new[]
            {
                new Vector3(-4f, 0f, -4f), new Vector3(4f, 0f, -4f),
                new Vector3(-4f, 0f, 4f), new Vector3(4f, 0f, 4f),
            };
            var yardVerts = new[]
            {
                new Vector3(20f, 0f, -4f), new Vector3(28f, 0f, -4f),
                new Vector3(20f, 0f, 4f), new Vector3(28f, 0f, 4f),
            };
            var mergedVerts = roadVerts.Concat(yardVerts).ToArray();
            var mergedTris = new[] { 0, 2, 1, 1, 2, 3, 4, 6, 5, 5, 6, 7 };
            var quadTris = new[] { 0, 2, 1, 1, 2, 3 };

            var low = Activator.CreateInstance(GlbReaderType);
            var nodes = (IList)GlbReaderType.GetField("Nodes").GetValue(low);
            nodes.Add(NewGlbNode("road_collision", NewGlbPrimitive("collision_asphalt", mergedVerts, mergedTris)));
            nodes.Add(NewGlbNode("paved", NewGlbPrimitive("yard_asphalt", yardVerts, quadTris)));

            var chunk = Activator.CreateInstance(chunkType);
            chunkType.GetField("Id").SetValue(chunk, "0_0");
            RegionImporterType.GetMethod("BuildCollisionMeshes", BindingFlags.Public | BindingFlags.Static)
                .Invoke(null, new[] { result, chunk, low });

            var colliders = Activator.CreateInstance(collidersType);
            var items = (IList)collidersType.GetField("Items").GetValue(colliders);
            var box = new Bounds(new Vector3(0f, 0.7f, 0f), new Vector3(1.8f, 1.4f, 4.2f));
            if (includeYardProp)
                items.Add(("car_hatch_v2", Matrix4x4.Translate(new Vector3(24f, 0f, 0f)), box));
            if (includeRoadProp)
                items.Add(("lamp_10m", Matrix4x4.Translate(new Vector3(0f, 0f, 0f)), new Bounds(new Vector3(0f, 1.3f, 0f), new Vector3(0.3f, 2.6f, 0.3f))));
            resultType.GetField("PropColliders").SetValue(result, colliders);

            return (result, chunk, low);
        }

        [Test]
        public void PavedPropGetsCollider_AndRoadPropIsSkippedWithWarning()
        {
            var root = new GameObject("Region_" + TestRegion);
            var createdMeshes = new System.Collections.Generic.List<Mesh>();
            try
            {
                var (result, chunk, _) = BuildSyntheticChunk(includeRoadProp: true, includeYardProp: true);
                var colList = (IList)chunk.GetType().GetField("Collision").GetValue(chunk);
                Assert.AreEqual(2, colList.Count, "road_collision asphalt should split into road and yard_asphalt");

                var surfaces = new System.Collections.Generic.HashSet<string>();
                foreach (var entry in colList)
                {
                    var mesh = (Mesh)entry.GetType().GetField("Item1").GetValue(entry);
                    var surface = (string)entry.GetType().GetField("Item2").GetValue(entry);
                    createdMeshes.Add(mesh);
                    surfaces.Add(surface);
                }
                CollectionAssert.AreEquivalent(new[] { "asphalt", "yard_asphalt" }, surfaces);

                var chunkGo = new GameObject("Chunk_0_0");
                chunkGo.transform.SetParent(root.transform, false);
                WorldSceneBuilderType.GetMethod("BuildChunkCollision", BindingFlags.Public | BindingFlags.Static)
                    .Invoke(null, new object[] { chunk, chunkGo.transform });

                var roadCol = chunkGo.transform.Find("Collision/col_asphalt");
                var yardCol = chunkGo.transform.Find("Collision/col_yard_asphalt");
                Assert.IsNotNull(roadCol);
                Assert.IsNotNull(yardCol);
                Assert.AreEqual(SurfaceKind.DryAsphalt, roadCol.GetComponent<GroundSurface>().kind);
                Assert.AreEqual(SurfaceKind.DryAsphalt, yardCol.GetComponent<GroundSurface>().kind);

                LogAssert.Expect(LogType.Warning, new Regex(@"^\[IMPORT\] 1 props stand on a carriageway \(no collider\):"));
                int built = (int)WorldSceneBuilderType.GetMethod("BuildPropColliders", BindingFlags.Public | BindingFlags.Static)
                    .Invoke(null, new object[] { result, root.transform });
                Assert.AreEqual(1, built);

                var propRoot = root.transform.Find("PropColliders");
                Assert.IsNotNull(propRoot);
                var yardProp = propRoot.Find("car_hatch_v2");
                Assert.IsNotNull(yardProp, "prop on paved yard_asphalt must keep its collider");
                Assert.IsNotNull(yardProp.GetComponent<BoxCollider>());
                Assert.AreEqual(SurfaceKind.Concrete, yardProp.GetComponent<GroundSurface>().kind);
                Assert.IsNull(propRoot.Find("lamp_10m"), "prop on carriageway col_asphalt must get no collider");
            }
            finally
            {
                Object.DestroyImmediate(root);
                foreach (var m in createdMeshes) Object.DestroyImmediate(m);
            }
        }

        [Test]
        public void PavedOnlyProp_ProducesColliderWithoutCarriagewayWarning()
        {
            var root = new GameObject("Region_" + TestRegion);
            var createdMeshes = new System.Collections.Generic.List<Mesh>();
            try
            {
                var (result, chunk, _) = BuildSyntheticChunk(includeRoadProp: false, includeYardProp: true);
                var colList = (IList)chunk.GetType().GetField("Collision").GetValue(chunk);
                foreach (var entry in colList)
                    createdMeshes.Add((Mesh)entry.GetType().GetField("Item1").GetValue(entry));

                var chunkGo = new GameObject("Chunk_0_0");
                chunkGo.transform.SetParent(root.transform, false);
                WorldSceneBuilderType.GetMethod("BuildChunkCollision", BindingFlags.Public | BindingFlags.Static)
                    .Invoke(null, new object[] { chunk, chunkGo.transform });

                int built = (int)WorldSceneBuilderType.GetMethod("BuildPropColliders", BindingFlags.Public | BindingFlags.Static)
                    .Invoke(null, new object[] { result, root.transform });
                Assert.AreEqual(1, built);
                Assert.IsNotNull(root.transform.Find("PropColliders/car_hatch_v2")?.GetComponent<BoxCollider>());
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Object.DestroyImmediate(root);
                foreach (var m in createdMeshes) Object.DestroyImmediate(m);
            }
        }
    }
}
