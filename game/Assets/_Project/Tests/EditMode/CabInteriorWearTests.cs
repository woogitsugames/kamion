using System.Collections.Generic;
using System.Linq;
using Game.Rendering;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0044 addendum r8 (HANDOVER: rim / seat wear invisible under the r6 black-albedo cap 0.05). On the exported rim
    /// data (vertex tint, roughness, uv2 wear) the shader mirror CabWearModel must give: worn spots lighter and neutral grey
    /// inside a plausible worn-black band, unworn leather unchanged, and a satin (not lacquer) roughness on the patches.
    /// Detail texel at its nominal value (R 0.5, G 0.85, B 0.5).
    /// </summary>
    public class CabInteriorWearTests
    {
        const string PrefabPath = "Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab";
        const string SetDir = "Assets/_Generated/Truck/Resources/TRAKT/TruckMaterials_";

        [Test]
        public void RimWear_IsLighterNeutralGreyAndSatin_WithinPlausibleBlack()
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
            if (prefab == null) Assert.Ignore("TRAKT prefab not built (Kamion/Setup/Rebuild TRAKT truck)");
            var rim = prefab.GetComponentsInChildren<MeshRenderer>(true).First(r => r.name == "STEERING_WHEEL_LOD0");
            var mesh = rim.GetComponent<MeshFilter>().sharedMesh;
            int sub = System.Array.FindIndex(rim.sharedMaterials, m => m != null && m.name.StartsWith("MI_Cab_Leather"));
            Assert.That(sub, Is.GreaterThanOrEqualTo(0), "rim leather slot");
            var cols = new List<Color>();
            var uv2 = new List<Vector2>();
            mesh.GetColors(cols);
            mesh.GetUVs(2, uv2);
            var idx = mesh.GetIndices(sub).Distinct().ToArray();
            Assert.That(cols.Count, Is.EqualTo(mesh.vertexCount), "rim vertex colours");

            const float detR = 0.5f, detG = 0.85f, detB = 0.5f;
            float roughMin = CabWearModel.RoughMinFor("Leather");
            var worn = new List<(Vector3 a, float r)>();
            var unworn = new List<(Vector3 a, float r)>();
            foreach (int i in idx)
            {
                var c = cols[i];
                var tint = new Vector3(Mathf.GammaToLinearSpace(c.r), Mathf.GammaToLinearSpace(c.g), Mathf.GammaToLinearSpace(c.b));
                float wear = uv2[i].x, mixD = uv2[i].y > 0f ? 1f : 0f;
                Vector3 baseCol = tint * Mathf.Lerp(1f, (0.7f + 0.6f * detR) * (0.4f + 0.6f * detG), mixD);
                float wk = CabWearModel.Shape(wear, detR, mixD);
                var a = CabWearModel.Albedo(tint, baseCol, wear, wk, detR, mixD);
                float r = CabWearModel.Roughness(c.a, detB, mixD, wear, wk, roughMin);
                if (wear >= 0.6f) worn.Add((a, r));
                else if (wear <= 0.02f) unworn.Add((a, r));
            }
            Assert.That(worn.Count, Is.GreaterThan(20), "rim has hand patches (uv2.x >= 0.6)");
            Assert.That(unworn.Count, Is.GreaterThan(20), "rim has unworn leather");

            static float Mean(Vector3 v) => (v.x + v.y + v.z) / 3f;
            float aw = worn.Average(t => Mean(t.a)), au = unworn.Average(t => Mean(t.a));
            float chroma = worn.Max(t => (Mathf.Max(t.a.x, t.a.y, t.a.z) - Mathf.Min(t.a.x, t.a.y, t.a.z)) / Mean(t.a));
            float rw = worn.Average(t => t.r), ru = unworn.Average(t => t.r);
            TestContext.WriteLine($"rim albedo worn {aw:F4} unworn {au:F4} chroma {chroma:P1}; roughness worn {rw:F3} unworn {ru:F3}");

            Assert.That(aw, Is.InRange(0.055f, 0.09f), "worn black leather: lighter, still black (sRGB ~66-84)");
            Assert.That(au, Is.InRange(0.015f, 0.04f), "unworn black leather (docs/06 corridor >= sRGB 30)");
            Assert.That(aw / au, Is.GreaterThanOrEqualTo(1.8f), "the wear must read in albedo");
            Assert.That(chroma, Is.LessThanOrEqualTo(0.06f), "worn spots go neutral grey, not towards the warm tint (D33)");
            Assert.That(rw, Is.InRange(roughMin - 1e-4f, ru - 0.12f), "satin polish: smoother than the grain, not lacquer");
        }

        [TestCase("Low"), TestCase("Medium"), TestCase("High")]
        public void SlotMaterials_CarryTheWearParameters(string tier)
        {
            var set = AssetDatabase.LoadAssetAtPath<TruckMaterialSet>(SetDir + tier + ".asset");
            if (set == null) Assert.Ignore("TRAKT material sets not built");
            foreach (var slot in new[] { "Plastic", "Leather", "Fabric", "Rubber", "Metal" })
            {
                var m = set.Get("MI_Cab_" + slot);
                Assert.NotNull(m, slot);
                Assert.That(m.GetFloat("_WearBlackAlbedo"), Is.EqualTo(CabWearModel.WornBlackAlbedo).Within(1e-5f), slot);
                Assert.That(m.GetFloat("_WearRoughMin"), Is.EqualTo(CabWearModel.RoughMinFor(slot)).Within(1e-5f), slot);
            }
        }
    }
}
