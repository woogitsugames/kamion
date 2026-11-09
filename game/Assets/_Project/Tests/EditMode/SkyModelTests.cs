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
