using System.Collections.Generic;
using System.IO;
using Game.Editor.Setup;
using Game.Rendering;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering.Universal;
using EditorTools = Game.Editor.Build.EditorTools;
using P = Game.Vehicle.Runtime.LampPhotometry;

namespace Game.Tests.EditMode
{
    /// <summary>ADR 0299: night sky dither, cab screen night mode, indicator / reversing-lamp halo.</summary>
    public class NightPolish0299Tests
    {
        static QualityProfile.Tier Tier(string name, bool post, UpscalingFilterSelection up, bool hdr = true) =>
            new QualityProfile.Tier { name = name, postProcessing = post, upscalingFilter = up, hdr = hdr };

        [Test]
        public void FinalDither_OnlyThePhoneFsrHighIsExempt()
        {
            Assert.That(QualityProfileApplier.FinalDither(Tier("High", true, UpscalingFilterSelection.FSR)), Is.False, "ADR 0108 RCAS rule kept");
            Assert.That(QualityProfileApplier.FinalDither(Tier("High", true, UpscalingFilterSelection.Auto)), Is.True, "PC High (no FSR) dithers");
            Assert.That(QualityProfileApplier.FinalDither(Tier("Ultra", true, UpscalingFilterSelection.Auto)), Is.True);
            Assert.That(QualityProfileApplier.FinalDither(Tier("Low", false, UpscalingFilterSelection.Auto)), Is.False, "no post, no final pass");
            // The PC overlay always resets the upscaler to Auto, so every PC tier with post gets the final dither.
            var pcHigh = PcGraphicsTiers.Overlay(Tier("High", true, UpscalingFilterSelection.FSR));
            Assert.That(QualityProfileApplier.FinalDither(pcHigh), Is.True);
        }

        [Test]
        public void UrpAssets_NoFastSrgbConversion_DitherDoesNotCrushDarks()
        {
            // URP ApplyDithering round-trips GetLinearToSRGB / GetSRGBToLinear; the fast pair maps linear 0.0037 to 0.0021.
            int n = 0;
            foreach (string guid in UnityEditor.AssetDatabase.FindAssets("t:UniversalRenderPipelineAsset", new[] { "Assets/_Project/Rendering" }))
            {
                var a = UnityEditor.AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(UnityEditor.AssetDatabase.GUIDToAssetPath(guid));
                Assert.That(a.useFastSRGBLinearConversion, Is.False, a.name);
                n++;
            }
            Assert.That(n, Is.GreaterThanOrEqualTo(9), "5 phone + 4 PC tier assets");
        }

        [Test]
        public void DisplayNight_EasesAndCaps()
        {
            Assert.That(CabDisplayNight.Step(0f, true, 0f), Is.EqualTo(1f), "still frame jumps");
            float half = CabDisplayNight.Step(0f, true, CabDisplayNight.FadeSeconds * 0.5f);
            Assert.That(half, Is.EqualTo(0.5f).Within(1e-5f));
            Assert.That(CabDisplayNight.Step(1f, false, 100f), Is.EqualTo(0f));
            Assert.That(CabDisplayNight.Cap(0.9f, 0.3f, 0f), Is.EqualTo(0.9f));
            Assert.That(CabDisplayNight.Cap(0.9f, 0.3f, 1f), Is.EqualTo(0.3f).Within(1e-6f));
            Assert.That(CabDisplayNight.Cap(0.9f, 0f, 1f), Is.EqualTo(0.9f), "unset night cap = day cap");
            Assert.That(TruckAssetBuilder.NightMaxDisplay("DISPLAY_Infotainment"), Is.LessThan(0.9f));
            Assert.That(TruckAssetBuilder.NightMaxDisplay("DISPLAY_Cluster"), Is.EqualTo(0.9f), "cluster dims through its palette");
            string sh = File.ReadAllText(Path.Combine(EditorTools.ProjectRoot, "Assets/_Project/Rendering/Shaders/CabDisplay.shader"));
            StringAssert.Contains("_KamionCabDisplayNight", sh);
            StringAssert.Contains("_NightMaxDisplay", sh);
        }

        [Test]
        public void Spill_NightModeUsesLiveMeanAndNightCap()
        {
            var s = new CabInteriorLighting.SpillSource { area = 0.03f, meanEmission = 0.596f, luminance = 500f, maxDisplay = 0.9f, nightMaxDisplay = 0.3f };
            float day = CabInteriorLighting.SpillPower(s, 1f, 1f);                     // old overload: no night mode
            float night = CabInteriorLighting.SpillPower(s, 1f, 1f, 1f, 0.01f);        // dark night map
            Assert.That(day, Is.EqualTo(0.9f * 0.596f * 0.03f).Within(1e-6f));
            Assert.That(night, Is.EqualTo(0.3f * 0.01f * 0.03f).Within(1e-7f));
            Assert.That(CabInteriorLighting.SpillPower(s, 1f, 1f, 0f, -1f), Is.EqualTo(day), "negative live mean keeps the baked mean");
        }

        static Mesh Quad(Vector3 c, Vector3 normal, float size, int group)
        {
            var rot = Quaternion.FromToRotation(Vector3.forward, normal);
            float h = size * 0.5f;
            var m = new Mesh();
            m.vertices = new[] { c + rot * new Vector3(-h, -h, 0), c + rot * new Vector3(h, -h, 0), c + rot * new Vector3(h, h, 0), c + rot * new Vector3(-h, h, 0) };
            m.triangles = new[] { 0, 1, 2, 0, 2, 3 };   // winding toward +normal or -normal: the builder ignores it
            var d = new List<Vector4>();
            for (int i = 0; i < 4; i++) d.Add(new Vector4(group, 1f, 0, 0));
            m.SetUVs(2, d);
            return m;
        }

        [Test]
        public void HaloEmittingSide_IndicatorsFrontSideRear_ReverseRearward()
        {
            foreach (int g in new[] { P.IndL, P.IndR, P.Reverse }) CollectionAssert.Contains(TruckLampHaloBuilder.HaloGroups, g);
            // Front indicator wound into the lamp (normal -Z) at the front of the part: turned forward.
            Assert.That(TruckLampHaloBuilder.EmittingSide(P.IndL, new Vector3(-1f, 0.2f, 1f), Vector3.back, 0f).z, Is.GreaterThan(0.99f));
            // Rear indicator wound forward: turned rearward.
            Assert.That(TruckLampHaloBuilder.EmittingSide(P.IndR, new Vector3(1f, 0.8f, -6f), Vector3.forward, 0f).z, Is.LessThan(-0.99f));
            // Left side repeater wound inward (+X): turned outward (-X).
            Assert.That(TruckLampHaloBuilder.EmittingSide(P.IndL, new Vector3(-1.2f, 1f, 0.5f), Vector3.right, 0f).x, Is.LessThan(-0.99f));
            // Reversing lamp wound forward: rearward.
            Assert.That(TruckLampHaloBuilder.EmittingSide(P.Reverse, new Vector3(0.8f, 0.8f, 3f), Vector3.forward, 0f).z, Is.LessThan(-0.99f));

            var ci = new[]
            {
                new CombineInstance { mesh = Quad(new Vector3(-1f, 0.2f, 3f), Vector3.back, 0.1f, P.IndL), transform = Matrix4x4.identity },
                new CombineInstance { mesh = Quad(new Vector3(-1f, 0.8f, -3f), Vector3.forward, 0.1f, P.IndL), transform = Matrix4x4.identity },
            };
            var mesh = new Mesh();
            mesh.CombineMeshes(ci, true, true);
            var cs = TruckLampHaloBuilder.Clusters(mesh, new HashSet<int>(TruckLampHaloBuilder.HaloGroups));
            Assert.That(cs.Count, Is.EqualTo(2));
            foreach (var c in cs)
                Assert.That(Mathf.Sign(c.normal.z), Is.EqualTo(Mathf.Sign(c.centre.z)), "front lamp forward, rear lamp rearward");
        }
    }
}
