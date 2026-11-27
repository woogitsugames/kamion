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

        /// <summary>render-artifacts-s24 (critic s24 wave 11 pkt 10, ADR 0332 addendum 2): the HDRI's lens ghost of the sun
        /// (lat 23.8 / lon 51.8 deg) was a white round blot in a grey cumulus (core luminance G 0.70 vs. 0.46 around).
        /// tools/rendering/clear_clouds_ghost_repair.py replaces it; its core must not be brighter than the cloud ring.</summary>
        [Test]
        public void LensGhost_IsNotABrightBlotInTheCloud()
        {
            var tex = Load(out _);
            var px = tex.GetPixels32();
            int w = tex.width, h = tex.height;
            var c = Dir(23.8f, 51.8f);
            float core = 0f, ring = 0f; int nc = 0, nr = 0;
            for (int y = 0; y < h; y++)
            {
                float lat = 180f * ((y + 0.5f) / h - 0.5f);           // LoadImage: row 0 = bottom
                if (lat < 17f || lat > 31f) continue;
                for (int x = 0; x < w; x++)
                {
                    float lon = 360f * ((x + 0.5f) / w - 0.5f);
                    if (lon < 43f || lon > 61f) continue;
                    float a = Mathf.Acos(Mathf.Clamp(Vector3.Dot(Dir(lat, lon), c), -1f, 1f)) * Mathf.Rad2Deg;
                    var p = px[y * w + x];
                    if (a < 1.2f) { core += p.g / 255f; nc++; }
                    else if (a > 3.2f && a < 5.2f && p.r > 25) { ring += p.g / 255f; nr++; }
                }
            }
            Assert.Greater(nc, 50); Assert.Greater(nr, 200);
            Assert.That(core / nc, Is.LessThan(ring / nr + 0.08f), "ghost core luminance vs. the cloud ring around it");
        }

        static Vector3 Dir(float latDeg, float lonDeg)
        {
            float la = latDeg * Mathf.Deg2Rad, lo = lonDeg * Mathf.Deg2Rad;
            return new Vector3(Mathf.Sin(lo) * Mathf.Cos(la), Mathf.Sin(la), Mathf.Cos(lo) * Mathf.Cos(la));
        }

        [Test]
        public void CircumsolarCap_HasNoSoftGlowRing()
        {
            var tex = Load(out var sun);
            Stats(tex, sun, 0f, 9f, out int n, out _, out int semi);
            Assert.That(semi / (float)n, Is.LessThan(0.10f), "semi-transparent share within 9 deg (ADR 0108 map: ~0.31)");
        }

        [Test]
        public void CloudVariants_AreAvailable_SoftEdged_AndMirrorPreservesSunAndHorizon()
        {
            Game.Rendering.PhotographicClouds.ResetCache();
            Assert.GreaterOrEqual(Game.Rendering.PhotographicClouds.VariantCount, 3, "expected at least 3 CC0 cloud variants (ADR 0332 agy-clouds-s24)");
            var preset = Game.Rendering.LightingPreset.CreateClear();
            try
            {
                Vector3 sun = preset.CreateModel().SunDirection;
                for (int i = 0; i < Game.Rendering.PhotographicClouds.VariantCount; i++)
                {
                    Assert.IsTrue(Game.Rendering.PhotographicClouds.TryGet(i, out var tex, out var sourceSun), $"variant {i} loaded");
                    Assert.IsNotNull(tex);
                    Assert.AreEqual(4096, tex.width, $"variant {i} width");
                    Assert.AreEqual(2048, tex.height, $"variant {i} height");
                    var m0 = Game.Rendering.PhotographicClouds.SourceMatrix(sun, sourceSun, false);
                    var m1 = Game.Rendering.PhotographicClouds.SourceMatrix(sun, sourceSun, true);
                    Assert.Less(Vector3.Angle(m0.MultiplyVector(sun), sourceSun), 0.05f, $"variant {i} unmirrored sun alignment");
                    Assert.Less(Vector3.Angle(m1.MultiplyVector(sun), sourceSun), 0.05f, $"variant {i} mirrored sun alignment");
                    Assert.AreEqual(Vector3.Angle(m0.MultiplyVector(Vector3.up), Vector3.up),
                                    Vector3.Angle(m1.MultiplyVector(Vector3.up), Vector3.up), 0.05f,
                                    $"variant {i} mirror must not add horizon roll");
                }
                // Deterministic variation across seeds / scenes / hours (and tier suffix invariance Low vs High)
                Game.Rendering.PhotographicClouds.ResolveVariant(0, "World_knyszyn-w_High", 12f, 200f, out int vHigh, out bool mirHigh, out _);
                Game.Rendering.PhotographicClouds.ResolveVariant(0, "World_knyszyn-w", 12f, 200f, out int vLow, out bool mirLow, out _);
                Assert.AreEqual(vHigh, vLow, "Low and High tiers of the same scene must share the cloud variant");
                Assert.AreEqual(mirHigh, mirLow, "Low and High tiers of the same scene must share the mirror flag");
                var seen = new System.Collections.Generic.HashSet<int>();
                for (int seed = 0; seed < 24; seed++)
                {
                    Game.Rendering.PhotographicClouds.ResolveVariant(seed, "World_knyszyn-w", 12f, 200f, out int v, out bool mir, out _);
                    seen.Add(v * 2 + (mir ? 1 : 0));
                }
                Assert.GreaterOrEqual(seen.Count, 5, "seeds must span variants and meridian mirrors");
            }
            finally { Object.DestroyImmediate(preset); }
        }

        [Test]
        public void CloudEdges_AreSoftened_NotHardBinaryCutout()
        {
            var tex = Load(out _);
            var px = tex.GetPixels32();
            int w = tex.width, h = tex.height;
            int half = h / 2; // LoadImage row 0 = bottom -> upper hemisphere is rows [half..h)
            int edgeCount = 0, steepCount = 0;
            for (int y = half + 4; y < h - 4; y += 2)
            {
                for (int x = 0; x < w; x += 2)
                {
                    float r = px[y * w + x].r / 255f;
                    if (r <= 0.05f || r >= 0.95f) continue;
                    edgeCount++;
                    float rx = px[y * w + ((x + 1) % w)].r / 255f;
                    float ry = px[(y + 1) * w + x].r / 255f;
                    float g = Mathf.Sqrt((rx - r) * (rx - r) + (ry - r) * (ry - r));
                    if (g > 0.16f) steepCount++;
                }
            }
            Assert.Greater(edgeCount, 50000, "soft transition band should have substantial wispy coverage");
            Assert.That(steepCount / (float)edgeCount, Is.LessThan(0.05f), "share of steep (>0.16/texel) cutout cliffs at cloud edges");
        }
    }
}
