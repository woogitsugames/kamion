using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// Review r6 C-N5 / C-N6 (ADR 0044 addendum r6): the steering-wheel rim rotates, so it has no AO island of its own and
    /// samples the cloth block of the AO atlas. The block held the median of the bake (0.02): ambient, fill and reflections
    /// of the rim x 0.02 on every tier, black in shade and beige in the sun. It must hold the mean cab ambient.
    /// </summary>
    public class CabInteriorRimAoTests
    {
        const string PrefabPath = "Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab";
        const string SetDir = "Assets/_Generated/Truck/Resources/TRAKT/TruckMaterials_";

        [TestCase("Low"), TestCase("Medium"), TestCase("High")]
        public void RimAo_IsTheMeanCabAmbient_NotBlack(string tier)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
            var set = AssetDatabase.LoadAssetAtPath<TruckMaterialSet>(SetDir + tier + ".asset");
            if (prefab == null || set == null) Assert.Ignore("TRAKT prefab not built (Kamion/Setup/Rebuild TRAKT truck)");

            var rim = prefab.GetComponentsInChildren<MeshRenderer>(true).First(r => r.name == "STEERING_WHEEL_LOD0");
            var mesh = rim.GetComponent<MeshFilter>().sharedMesh;
            int sub = System.Array.FindIndex(rim.sharedMaterials, m => m != null && m.name.StartsWith("MI_Cab_Leather"));
            Assert.That(sub, Is.GreaterThanOrEqualTo(0), "rim leather slot");
            var uv1 = new List<Vector2>();
            mesh.GetUVs(1, uv1);
            Vector2 uv = uv1[mesh.GetIndices(sub)[0]];

            var ao = set.Get("MI_Cab_Leather").GetTexture("_AO") as Texture2D;
            Assert.NotNull(ao, "AO atlas of the " + tier + " leather");
            var png = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);
            png.LoadImage(File.ReadAllBytes(Path.GetFullPath(AssetDatabase.GetAssetPath(ao))));
            float a = png.GetPixel(Mathf.Clamp((int)(uv.x * png.width), 0, png.width - 1), Mathf.Clamp((int)(uv.y * png.height), 0, png.height - 1)).r;
            Object.DestroyImmediate(png);
            Assert.That(a, Is.InRange(0.10f, 0.40f), $"rim AO at uv1 {uv} on {tier} (mean cab ambient; was 0.02)");
        }
    }
}
