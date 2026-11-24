using System.Linq;
using Game.Editor.Setup;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0341 (windscreen-s24): the windscreen carries a dirt mask (glass object xy) and the baked cab image seen from the
    /// driver's eye mirrored in the pane (equirect in the cab frame). Checks the contract the shader relies on: textures
    /// imported as data / colour with the right wrap, assigned on the windscreen material of every tier and off on the
    /// door glass, the dirt rectangle covering the pane, and the windscreen object axes aligned with the cab interior (the
    /// reflection is looked up with the reflected direction in glass object space).
    /// </summary>
    public class WindscreenLayer0341Tests
    {
        const string PrefabPath = "Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab";
        GameObject m_Go;

        [TearDown]
        public void TearDown() { if (m_Go != null) Object.DestroyImmediate(m_Go); }

        [Test]
        public void Textures_ImportedAsDataAndColour()
        {
            var g = AssetImporter.GetAtPath(TruckAssetBuilder.WindscreenGrimePath) as TextureImporter;
            var r = AssetImporter.GetAtPath(TruckAssetBuilder.WindscreenReflectionPath) as TextureImporter;
            Assert.IsNotNull(g, "dirt mask (tools/rendering/windscreen_grime.py)");
            Assert.IsNotNull(r, "cab reflection (tools/blender/truck/interior/bake_windscreen_reflection.py)");
            Assert.IsFalse(g.sRGBTexture, "dirt mask is linear data");
            Assert.AreEqual(TextureWrapMode.Clamp, g.wrapModeU, "dirt mask clamps (lamp lenses share the material, border = 0)");
            Assert.AreEqual(TextureWrapMode.Clamp, g.wrapModeV);
            Assert.IsTrue(r.sRGBTexture, "cab image is colour");
            Assert.AreEqual(TextureWrapMode.Repeat, r.wrapModeU, "equirect wraps in longitude");
            Assert.AreEqual(TextureWrapMode.Clamp, r.wrapModeV, "equirect clamps at the poles");
        }

        [TestCase("Low"), TestCase("Medium"), TestCase("High")]
        public void Windscreen_HasLayers_DoorGlassHasNone(string tier)
        {
            var set = Resources.Load<TruckMaterialSet>("TRAKT/TruckMaterials_" + tier);
            if (set == null) Assert.Ignore("TRAKT material sets not generated (outside git): Kamion/Setup/Rebuild TRAKT truck");
            var ws = set.Get("MI_Ext_Glass");
            Assert.IsNotNull(ws.GetTexture("_GrimeMask"), "dirt mask on " + tier);
            Assert.IsNotNull(ws.GetTexture("_CabReflection"), "cab reflection on " + tier);
            Assert.AreEqual(1f, ws.GetFloat("_CabReflectionGain"), 1e-4f);
            Assert.That(((Vector4)ws.GetVector("_GrimeLayers")).x, Is.GreaterThan(0f));
            foreach (var side in new[] { "L", "R" })
            {
                var dg = set.Get("MI_Ext_DoorGlass" + side);
                Assert.IsNull(dg.GetTexture("_GrimeMask"), "no windscreen dirt on door glass " + side);
                Assert.AreEqual(0f, dg.GetFloat("_CabReflectionGain"), "door glass keeps the analytic interior " + side);
            }
        }

        [Test]
        public void Windscreen_InGrimeRect_AxesAlignedWithCab()
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
            if (prefab == null) Assert.Ignore("TRAKT prefab not generated (outside git): Kamion/Setup/Rebuild TRAKT truck");   // Ignore, not Assume (Inconclusive fails the run)
            var set = Resources.Load<TruckMaterialSet>("TRAKT/TruckMaterials_High");
            Assume.That(set, Is.Not.Null);
            m_Go = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            var ws = m_Go.GetComponentsInChildren<MeshRenderer>(true).First(r => r.name == "GLASS_Windscreen_LOD0");
            var b = ws.GetComponent<MeshFilter>().sharedMesh.bounds;
            Vector4 rect = set.Get("MI_Ext_Glass").GetVector("_GrimeRect");
            float x1 = rect.x + 1f / rect.z, y1 = rect.y + 1f / rect.w;
            Assert.That(b.min.x, Is.GreaterThan(rect.x), "pane inside the dirt rectangle (x min)");
            Assert.That(b.max.x, Is.LessThan(x1), "x max");
            Assert.That(b.min.y, Is.GreaterThan(rect.y - 0.05f), "y min (5 cm frit margin)");
            Assert.That(b.max.y, Is.LessThan(y1), "y max");
            // The cab image is in the cab frame (x right, y up, z forward): the glass object axes must match the cab interior.
            var interior = m_Go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == "CAB_Interior_LOD0");
            Assume.That(interior, Is.Not.Null, "cab interior in the prefab");
            Quaternion rel = Quaternion.Inverse(interior.rotation) * ws.transform.rotation;
            Assert.That(Quaternion.Angle(rel, Quaternion.identity), Is.LessThan(0.5f), "windscreen object axes = cab frame");
        }
    }
}
