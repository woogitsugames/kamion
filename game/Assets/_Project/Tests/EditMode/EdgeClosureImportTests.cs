using System;
using System.IO;
using System.Reflection;
using Game.World;
using Game.World.Streaming;
using NUnit.Framework;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    public class EdgeClosureImportTests
    {
        static Type Builder => Type.GetType("Game.World.Import.WorldEdgeBuilder, Game.World.Import.Editor", true);

        static GameObject Surface(Transform parent, string name, float y)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = new Vector3(0f, y - 0.5f, 0f);
            go.AddComponent<BoxCollider>().size = new Vector3(10f, 1f, 10f);
            return go;
        }

        [TestCase(-137f)]
        [TestCase(-155f)]
        public void RoadY_SamplesOwnRoad_NotRoofOrForeignRegion_AndReturnsLocalHeight(float rootY)
        {
            var root = new GameObject("own");
            var foreign = new GameObject("foreign");
            try
            {
                // Far from scene contents, but with the same negative root Y as an imported tile.
                root.transform.position = new Vector3(90000f, rootY, 90000f);
                foreign.transform.position = root.transform.position;
                Surface(root.transform, "col_asphalt", 142f);
                Surface(root.transform, "col_terrain", 140f);
                Surface(root.transform, "col_concrete", 160f);
                Surface(foreign.transform, "col_asphalt", 175f);
                Physics.SyncTransforms();
                var args = new object[] { root.transform, Vector2.zero, 0f };
                Assert.IsTrue((bool)Builder.GetMethod("RoadY").Invoke(null, args));
                Assert.That((float)args[2], Is.EqualTo(142f).Within(0.01f));
            }
            finally { Object.DestroyImmediate(root); Object.DestroyImmediate(foreign); }
        }

        [Test]
        public void SingleClosureMesh_AppliesRoadHeightAndHeadingOnlyOnce()
        {
            var mesh = new Mesh();
            var go = new GameObject("closure");
            try
            {
                var c = new WorldBoundary.Closure { localPos = new Vector3(200f, 142f, -50f), headingDeg = 90f, widthM = 10f };
                Builder.GetMethod("BuildClosureMesh").Invoke(null, new object[] { mesh, c });
                Assert.That(mesh.bounds.min.y, Is.EqualTo(0f).Within(0.001f));
                Assert.That(mesh.bounds.max.y, Is.EqualTo(2.3f).Within(0.02f));
                go.transform.position = c.localPos;
                go.transform.rotation = Quaternion.Euler(0f, c.headingDeg, 0f);
                foreach (var vertex in mesh.vertices)
                    Assert.That(go.transform.TransformPoint(vertex).y, Is.InRange(142f - 0.001f, 144.31f));
            }
            finally { Object.DestroyImmediate(mesh); Object.DestroyImmediate(go); }
        }

        [Test]
        public void MissingMaterial_StopsImportWithSlotContext()
        {
            var type = Type.GetType("Game.World.Import.WorldMaterialValidation, Game.World.Import.Editor", true);
            var ex = Assert.Throws<TargetInvocationException>(() => type.GetMethod("Require").Invoke(null,
                new object[] { null, "bialystok-maczka/chunk/buildings/plaster_beige slot 3" }));
            Assert.IsInstanceOf<InvalidDataException>(ex.InnerException);
            StringAssert.Contains("plaster_beige slot 3", ex.InnerException.Message);
        }

        [Test]
        public void OpeningOneClosure_DisablesItsRendererAndCollider_LeavesOtherSideClosed()
        {
            var root = new GameObject("edge");
            var mesh = new Mesh();
            try
            {
                GameObject Closure(int index, TileSide side)
                {
                    var c = new WorldBoundary.Closure { localPos = new Vector3(index * 5f, 142f, 0f), widthM = 7f, exitSide = side };
                    return (GameObject)Builder.GetMethod("BuildClosureObject").Invoke(null,
                        new object[] { root.transform, index, c, mesh, Array.Empty<Material>() });
                }
                var north = Closure(0, TileSide.N);
                var east = Closure(1, TileSide.E);
                north.SetActive(!EdgeClosureRules.IsOpen(TileSide.N, TileSide.N));
                east.SetActive(!EdgeClosureRules.IsOpen(TileSide.E, TileSide.N));
                Assert.IsFalse(north.GetComponent<MeshRenderer>().gameObject.activeInHierarchy);
                Assert.IsFalse(north.GetComponent<BoxCollider>().gameObject.activeInHierarchy);
                Assert.IsTrue(east.GetComponent<MeshRenderer>().gameObject.activeInHierarchy);
                Assert.IsTrue(east.GetComponent<BoxCollider>().gameObject.activeInHierarchy);
                north.SetActive(true); // closing before neighbour unload
                Assert.IsTrue(north.GetComponent<BoxCollider>().gameObject.activeInHierarchy);
            }
            finally { Object.DestroyImmediate(root); Object.DestroyImmediate(mesh); }
        }

        [Test]
        public void CurvedExit_KeepsTheActualSeamSide_WhenTangentPointsElsewhere()
        {
            var exitType = Builder.GetNestedType("RoadExit");
            object exit = Activator.CreateInstance(exitType);
            exitType.GetField("edgeEN").SetValue(exit, new Vector2(1024f, 990f));
            exitType.GetField("closureEN").SetValue(exit, new Vector2(970f, 950f));
            exitType.GetField("closureDir").SetValue(exit, Vector2.up);
            exitType.GetField("exitSide").SetValue(exit, TileSide.E);
            var exits = (System.Collections.IList)Activator.CreateInstance(typeof(System.Collections.Generic.List<>).MakeGenericType(exitType));
            exits.Add(exit);
            var closures = (System.Collections.Generic.List<WorldBoundary.Closure>)Builder.GetMethod("PlanClosures").Invoke(null, new object[] { exits });
            Assert.AreEqual(TileSide.E, closures[0].exitSide);
            Assert.IsTrue(EdgeClosureRules.IsOpen(closures[0].exitSide, TileSide.E));
            Assert.IsFalse(EdgeClosureRules.IsOpen(closures[0].exitSide, TileSide.N));
        }
    }
}
