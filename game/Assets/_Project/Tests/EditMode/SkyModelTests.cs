using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>Look-development calibration (ADR 0010): the sky model, exposure and the ambient SH agree.</summary>
    public class SkyModelTests
    {
        [Test]
        public void ClearSky_IlluminanceMatchesHandbookFits()
        {
            var m = new SkyModel(45f, 180f, 2.5f, 0f, 15f);
            // E_dn = 127.5 exp(-0.21 m), m(45°) ≈ 1.413 → ≈ 94.6 klx; E_kh = 0.8 + 15.5 sqrt(sin 45°) ≈ 13.83 klx
            Assert.AreEqual(94600f, m.SunNormalIlluminanceLux, 600f);
            Assert.AreEqual(13830f, m.SkyHorizontalIlluminanceLux, 100f);
            // Sky dome integrates to the handbook diffuse illuminance (normalisation).
            float e = 0f; const int n = 64;
            for (int r = 0; r < n; r++)
            for (int c = 0; c < 2 * n; c++)
            {
                float z = (r + 0.5f) / n, s = Mathf.Sqrt(1 - z * z), phi = (c + 0.5f) * Mathf.PI / n;
                var col = m.Radiance(new Vector3(s * Mathf.Cos(phi), z, s * Mathf.Sin(phi)));
                e += (0.2126f * col.r + 0.7152f * col.g + 0.0722f * col.b) * z * (1f / n) * (Mathf.PI / n);
            }
            Assert.AreEqual(m.SkyHorizontalIlluminanceLux, e, m.SkyHorizontalIlluminanceLux * 0.06f, "dome luminance integral");
        }

        [Test]
        public void LowSun_SkyAwayFromTheSunIsBlue_AndTheAmbientIsNotWarm()
        {
            // Review r4 L2: at 9 deg the sky opposite the sun must be bluish (B >= R) and the shade ambient not warm.
            var p = LightingPreset.CreateLowSun();
            var m = p.CreateModel();
            float az = (p.sunAzimuthDeg + 180f) * Mathf.Deg2Rad;
            var warm = new System.Collections.Generic.List<string>();
            foreach (float elDeg in new[] { 5f, 12f, 20f, 45f, 90f })
            {
                float el = elDeg * Mathf.Deg2Rad;
                var d = new Vector3(Mathf.Cos(el) * Mathf.Sin(az), Mathf.Sin(el), Mathf.Cos(el) * Mathf.Cos(az));
                var c = m.Radiance(d);
                Debug.Log($"[TEST] lowsun anti-sun sky el {elDeg}: rgb/max {c.r / c.maxColorComponent:F3} {c.g / c.maxColorComponent:F3} {c.b / c.maxColorComponent:F3}");
                // 5 deg: the long hazy horizon path stays warm (logged only); review r4 measured the sky 15-25 deg up.
                if (elDeg >= 10f && c.b < c.r) warm.Add(elDeg.ToString());
            }
            var sh = m.AmbientProbe(p.groundAlbedo, 24, p.ambientSkySaturation);
            var res = new Color[1];
            sh.Evaluate(new[] { Vector3.up }, res);
            Debug.Log($"[TEST] lowsun ambient up rgb {res[0].r:F4} {res[0].g:F4} {res[0].b:F4}");
            Assert.IsEmpty(warm, "sky opposite the sun is warm at these elevations");
            Assert.That(res[0].b, Is.GreaterThanOrEqualTo(res[0].r), "shade ambient (sky) is warm");
        }

        [Test]
        public void IncidentMeterExposure_SunnySixteen()
        {
            var m = new SkyModel(45f, 180f, 2.5f, 0f, 0f);
            float ev = SkyModel.IncidentEv100(m.HorizontalIlluminanceLux);
            Assert.That(ev, Is.InRange(14.5f, 15.5f), "a sunny day meters around EV 15 (sunny-16 rule)");
            var o = new SkyModel(30f, 180f, 4f, 1f, 0f);
            Assert.That(SkyModel.IncidentEv100(o.HorizontalIlluminanceLux), Is.InRange(11.5f, 13.5f), "overcast EV 12-13");
            Assert.AreEqual(0f, o.SunNormalIlluminanceLux, 1e-3f, "no direct sun when fully overcast");
        }

        [Test]
        public void AmbientProbe_ReproducesSkyIrradiance()
        {
            var albedo = new Color(0.16f, 0.17f, 0.12f);
            foreach (var m in new[] { new SkyModel(42f, 200f, 2.5f, 0f, 14.5f), new SkyModel(30f, 200f, 4f, 1f, 12f) })
            {
                var sh = m.AmbientProbe(albedo);
                var dirs = new[] { Vector3.up, Vector3.right, Vector3.down };
                var res = new Color[3];
                sh.Evaluate(dirs, res);
                for (int i = 0; i < dirs.Length; i++)
                {
                    Color want = m.ExpectedAmbient(dirs[i], albedo);
                    float lw = want.grayscale, lg = res[i].grayscale;
                    Debug.Log($"[TEST] SH {dirs[i]}: probe {lg:F4} expected {lw:F4} (overcast {m.Overcast})");
                    Assert.AreEqual(lw, lg, lw * 0.12f + 1e-4f, $"ambient for normal {dirs[i]}");
                }
            }
        }

        [Test]
        public void SunColour_IsWarmDaylight()
        {
            var m = new SkyModel(42f, 200f, 2.5f, 0f, 14.5f);
            Assert.Greater(m.SunColor.r, m.SunColor.b, "direct sun is warmer than white at 42°");
            Assert.Less(m.SunColor.r / m.SunColor.b, 1.5f, "not a sunset colour at 42°");
        }
    }
}
