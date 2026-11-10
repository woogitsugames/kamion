using Game.Rendering;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Tests
{
    /// <summary>ADR 0080 r11: colour of the overcast dome (fixed daylight white balance), ground haze of the preset.</summary>
    public class OvercastDomeTests
    {
        static float Lum(Color c) => 0.2126f * c.r + 0.7152f * c.g + 0.0722f * c.b;

        [Test]
        public void DaylightRgb_D65IsWhite_HigherCctIsCooler_LuminanceOne()
        {
            var d65 = SkyModel.DaylightRgb(6504f);
            Assert.AreEqual(1f, d65.r, 0.01f); Assert.AreEqual(1f, d65.g, 0.01f); Assert.AreEqual(1f, d65.b, 0.01f);
            float prev = 0f;
            foreach (float t in new[] { 5500f, 6504f, 6800f, 7000f, 7500f, 9000f })
            {
                var c = SkyModel.DaylightRgb(t);
                Assert.AreEqual(1f, Lum(c), 1e-4f, $"luminance 1 at {t} K");
                Assert.That(c.b - c.r, Is.GreaterThan(prev - 1f), "defined");
                if (t > 5500f) Assert.That(c.b / c.r, Is.GreaterThan(prev), $"cooler at {t} K");
                prev = c.b / c.r;
            }
            // the two branches of the daylight locus meet at 7000 K
            var a = SkyModel.DaylightRgb(6999.9f); var b = SkyModel.DaylightRgb(7000.1f);
            Assert.AreEqual(a.b / a.r, b.b / b.r, 2e-3f);
        }

        [Test]
        public void OvercastPreset_DomeIsCool_IlluminanceAndExposureUnchanged()
        {
            var p = LightingPreset.CreateOvercast();
            try
            {
                Assert.That(p.overcastCctK, Is.InRange(6600f, 7500f), "slightly cooler than the D65 white balance");
                var tinted = p.CreateModel();
                float keep = p.overcastCctK;
                p.overcastCctK = 0f;
                var neutral = p.CreateModel();
                p.overcastCctK = keep;
                Assert.AreEqual(neutral.HorizontalIlluminanceLux, tinted.HorizontalIlluminanceLux, 1e-3f);
                Assert.AreEqual(neutral.Exposure, tinted.Exposure, 1e-9f);
                Assert.AreEqual(Color.white.r, neutral.AdaptedWhite.r, 1e-6f, "0 K = the achromatic CIE dome");
                var up = new Vector3(0.2f, 0.9f, 0.1f).normalized;
                Color ct = tinted.ExposedRadiance(up), cn = neutral.ExposedRadiance(up);
                Assert.AreEqual(Lum(cn), Lum(ct), Lum(cn) * 1e-3f, "same luminance");
                Assert.That(ct.b / ct.r, Is.InRange(1.03f, 1.20f), "dome B / R (linear)");
                Color fog = tinted.HorizonColorExposed();
                Assert.That(fog.b, Is.GreaterThan(fog.r), "the haze takes the dome colour");
                // the ambient keeps the dome colour under an overcast sky (the saturation cut is for the clear share)
                var sh = tinted.AmbientProbe(new Color(0.15f, 0.15f, 0.15f), 24, p.ambientSkySaturation, p.lowSunAmbientCool);
                var res = new Color[1];
                sh.Evaluate(new[] { Vector3.up }, res);
                Assert.AreEqual(ct.b / ct.r, res[0].b / res[0].r, 0.02f, "ambient on an up-facing surface = dome colour");
            }
            finally { Object.DestroyImmediate(p); }
        }

        [Test]
        public void OvercastPreset_GroundHaze_MidDistanceShare()
        {
            var p = LightingPreset.CreateOvercast();
            try
            {
                float beta = 3.912f / (p.visibilityKm * 1000f);
                // eye 2.5 m above the layer base, target at eye height: share of the horizon colour in the pixel
                float Share(float d) => 1f - Mathf.Exp(-WorldAtmosphere.FogTau(beta, p.hazeGroundFactor, p.hazeScaleHeightM, 0f, 2.5f, 2.5f, d));
                Assert.That(Share(20f), Is.LessThan(0.04f), "near field stays clear");
                Assert.That(Share(100f), Is.InRange(0.10f, 0.20f));
                Assert.That(Share(300f), Is.InRange(0.30f, 0.45f));
                Assert.That(Share(500f), Is.InRange(0.45f, 0.62f));
                // tall distant objects sit above the layer: a 60 m chimney top at 1 km is hazed less than its foot
                float foot = WorldAtmosphere.FogTau(beta, p.hazeGroundFactor, p.hazeScaleHeightM, 0f, 2.5f, 2.5f, 1000f);
                float top = WorldAtmosphere.FogTau(beta, p.hazeGroundFactor, p.hazeScaleHeightM, 0f, 2.5f, 60f, 1000f);
                Assert.That(top, Is.LessThan(foot * 0.85f));
            }
            finally { Object.DestroyImmediate(p); }
        }
    }
}
