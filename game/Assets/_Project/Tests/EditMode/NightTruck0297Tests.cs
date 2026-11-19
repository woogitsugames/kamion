using System.Collections.Generic;
using System.IO;
using Game.Editor.Setup;
using Game.Rendering;
using NUnit.Framework;
using UnityEngine;
using EditorTools = Game.Editor.Build.EditorTools;
using P = Game.Vehicle.Runtime.LampPhotometry;

namespace Game.Tests.EditMode
{
    /// <summary>ADR 0297: rear-lamp halo, lit-plate shoulder, cab instrument spill, night shadow lift, PC soft cab shadows.</summary>
    public class NightTruck0297Tests
    {
        static Mesh Quad(Vector3 c, float size, int group, float mask, bool inward = false)
        {
            var m = new Mesh();
            float h = size * 0.5f;
            m.vertices = new[] { c + new Vector3(-h, -h, 0), c + new Vector3(h, -h, 0), c + new Vector3(h, h, 0), c + new Vector3(-h, h, 0) };
            m.triangles = inward ? new[] { 0, 1, 2, 0, 2, 3 } : new[] { 0, 2, 1, 0, 3, 2 };   // normal -Z (rearward) / +Z (into the lamp)
            var d = new List<Vector4>();
            for (int i = 0; i < 4; i++) d.Add(new Vector4(group, mask, 0, 0));
            m.SetUVs(2, d);
            return m;
        }

        static Mesh Combine(params Mesh[] ms)
        {
            var ci = new CombineInstance[ms.Length];
            for (int i = 0; i < ms.Length; i++) ci[i] = new CombineInstance { mesh = ms[i], transform = Matrix4x4.identity };
            var m = new Mesh();
            m.CombineMeshes(ci, true, true);
            return m;
        }

        [Test]
        public void HaloClusters_OnePerLampAndGroup_AreaAndNormal()
        {
            var mesh = Combine(
                Quad(new Vector3(-1f, 1f, 0f), 0.1f, P.Tail, 1f),     // left tail chamber 100 cm^2
                Quad(new Vector3(-0.85f, 1f, 0f), 0.1f, P.Stop, 1f),  // left stop chamber, same lamp body, other group
                Quad(new Vector3(1f, 1f, 0f), 0.1f, P.Tail, 1f, true),  // right tail chamber, lens wound inward (after2 export)
                Quad(new Vector3(0f, 1f, 0f), 0.1f, P.MarkerSide, 1f), // amber side marker: not a halo group
                Quad(new Vector3(0f, 0.5f, 0f), 0.1f, P.Tail, 0f),    // lens frame without emissive mask
                Quad(new Vector3(0f, 1f, -6f), 0.1f, 0, 0f));         // body behind the lamps (front-corner marker case): still -Z
            var cs = TruckLampHaloBuilder.Clusters(mesh, new HashSet<int>(TruckLampHaloBuilder.HaloGroups));
            Assert.That(cs.Count, Is.EqualTo(3));
            foreach (var c in cs)
            {
                Assert.That(c.area, Is.EqualTo(0.01f).Within(1e-5f));
                Assert.That(Vector3.Dot(c.normal, Vector3.back), Is.GreaterThan(0.999f), "red rear signals emit rearward (-Z)");
            }
            var halo = TruckLampHaloBuilder.BuildMesh(cs, "t");
            Assert.That(halo.vertexCount, Is.EqualTo(12));
            var uv1 = new List<Vector2>(); halo.GetUVs(1, uv1);
            Assert.That(uv1[0].x, Is.EqualTo(cs[0].group));
            Assert.That(halo.bounds.extents.x, Is.GreaterThan(1.5f), "bounds padded for the camera-facing expansion");
        }

        [Test]
        public void HaloGroups_AreTheRedRearSignals()
        {
            CollectionAssert.AreEquivalent(new[] { P.TailBrake, P.MarkerRear, P.FogRear, P.Tail, P.Stop }, TruckLampHaloBuilder.RedRearGroups);
            CollectionAssert.IsSubsetOf(TruckLampHaloBuilder.RedRearGroups, TruckLampHaloBuilder.HaloGroups);   // ADR 0299 adds amber / white
            Assert.That(Shader.Find(TruckLampHaloBuilder.ShaderName), Is.Not.Null);
            string sh = File.ReadAllText(Path.Combine(EditorTools.ProjectRoot, "Assets/_Project/Rendering/Shaders/TruckLampHalo.shader"));
            StringAssert.Contains("#define KAMION_LAMP_TEXELS 32.0", sh, "same state texture layout as TruckExterior");
            StringAssert.Contains("_KamionSkyCapOff", sh, "no halo in the vehicle reflection cube");
        }

        [Test]
        public void TailNits_BrighterThanAdr0197_RegulationRatioKept()
        {
            Assert.That(P.TailNits, Is.GreaterThan(1.3e3f));
            Assert.That(P.BrakeNits / P.TailNits, Is.GreaterThanOrEqualTo(1.05f * P.MinStopToTailRatio));
        }

        [Test]
        public void Spill_ZeroWithoutLight_ScreenLevelAtNight_TinyByDay()
        {
            var s = new CabInteriorLighting.SpillSource { area = 0.04f, meanEmission = 0.2f, luminance = 500f, maxDisplay = 0.9f };
            float night = CabInteriorLighting.SpillPower(s, 0.05f, 1f);      // 500 x 0.05 = 25 -> ceiling 0.9
            Assert.That(night, Is.EqualTo(0.9f * 0.2f * 0.04f).Within(1e-6f));
            float day = CabInteriorLighting.SpillPower(s, 2e-5f, 1f);        // no readability floor: physical 0.01
            Assert.That(day, Is.LessThan(0.02f * night));
            Assert.That(CabInteriorLighting.SpillPower(s, 0.05f, 0f), Is.EqualTo(0f));
        }

        [Test]
        public void NightLift_FadesToShare()
        {
            Assert.That(CabInteriorLighting.NightLiftScale(0f, 0.2f), Is.EqualTo(1f));
            Assert.That(CabInteriorLighting.NightLiftScale(1f, 0.2f), Is.EqualTo(0.2f).Within(1e-6f));
            Assert.That(CabInteriorLighting.NightLiftScale(0.5f, 0.2f), Is.EqualTo(0.6f).Within(1e-6f));
        }

        [Test]
        public void CabShader_HasSoftShadowVariants_AndHardBranchForPhones()
        {
            string sh = File.ReadAllText(Path.Combine(EditorTools.ProjectRoot, "Assets/_Project/Rendering/Shaders/CabInterior.shader"));
            StringAssert.Contains("#pragma multi_compile_fragment _ _SHADOWS_SOFT", sh);
            StringAssert.Contains("_KamionCabSoftShadow < 0.5", sh);
            StringAssert.Contains("CabInstrumentSpill(", sh);
        }
    }
}
