using System.IO;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// glass-sky-s24 (ADR 0332 addendum, critic s24 build #8 P1#4): the photographic Clear cloud map is rotated so its
    /// photographed sun sits on the game sun, so its circumsolar cap is always next to the sun. The ADR 0108 generator left
    /// a zero-opacity disc there ("hole in the cloud") and a soft semi-transparent glow ring ("halo");
    /// tools/rendering/clear_clouds_sun_repair.py fills the disc and re-mattes the ring.
    /// </summary>
    public class ClearCloudsSunTests
    {
        [System.Serializable] sealed class Source { public Vector3 sunDirection; }

        static Texture2D Load(out Vector3 sun)
        {
            string dir = Path.Combine(Application.dataPath, "_Project", "Rendering", "Resources", "Sky");
            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);
            Assert.IsTrue(tex.LoadImage(File.ReadAllBytes(Path.Combine(dir, "T_ClearClouds.png"))));
            sun = JsonUtility.FromJson<Source>(File.ReadAllText(Path.Combine(dir, "ClearCloudsSource.json"))).sunDirection.normalized;
            return tex;
        }

        // Same layout as Kamion/Sky: u = atan2(x, z) / 2pi + 0.5, v = asin(y) / pi + 0.5.
        static void Stats(Texture2D tex, Vector3 sun, float minDeg, float maxDeg, out int n, out int holes, out int semi)
        {
            n = holes = semi = 0;
            var px = tex.GetPixels32();
            int w = tex.width, h = tex.height;
            float cosMax = Mathf.Cos(maxDeg * Mathf.Deg2Rad), cosMin = Mathf.Cos(minDeg * Mathf.Deg2Rad);
            for (int y = 0; y < h; y++)
            {
                float lat = Mathf.PI * ((y + 0.5f) / h - 0.5f);         // LoadImage: row 0 = bottom = v 0
                for (int x = 0; x < w; x++)
                {
                    float lon = 2f * Mathf.PI * ((x + 0.5f) / w - 0.5f);
                    var d = new Vector3(Mathf.Sin(lon) * Mathf.Cos(lat), Mathf.Sin(lat), Mathf.Cos(lon) * Mathf.Cos(lat));
                    float c = Vector3.Dot(d, sun);
                    if (c < cosMax || c > cosMin) continue;
                    n++;
                    float r = px[y * w + x].r / 255f;
                    if (r < 0.5f) holes++;
                    if (r > 0.1f && r < 0.9f) semi++;
                }
            }
        }

        [Test]
        public void SunDisc_IsFilled_NoHole()
        {
            var tex = Load(out var sun);
            Stats(tex, sun, 0f, 2f, out int n, out int holes, out _);
            Assert.Greater(n, 100);
            Assert.That(holes / (float)n, Is.LessThan(0.02f), "opacity < 0.5 within 2 deg of the photographed sun (zeroed disc)");
        }

        [Test]
        public void CircumsolarCap_HasNoSoftGlowRing()
        {
            var tex = Load(out var sun);
            Stats(tex, sun, 0f, 9f, out int n, out _, out int semi);
            Assert.That(semi / (float)n, Is.LessThan(0.10f), "semi-transparent share within 9 deg (ADR 0108 map: ~0.31)");
        }
    }
}
