using System.IO;
using System.Text.RegularExpressions;
using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0191 (review s19 0182 P1-4): street-lamp pools with a road-luminaire footprint - long along the road, short
    /// behind the column, visible dips between columns at the spacing of the generated lamps, the flux of a real
    /// luminaire, one pool per luminaire on its arm, and a GGX highlight only on the High / Ultra tiers.
    /// </summary>
    public class StreetLampOpticsTests
    {
        const float I0 = StreetLamps.DownIntensityCd;
        static readonly Vector2 ArmEast = new Vector2(1f, 0f);   // arm points +x (carriageway), road runs along z

        static float E(float h, float x, float z, bool road = true) =>
            StreetLampOptics.GroundLux(new Vector3(0f, h, 0f), ArmEast, road, new Vector3(x, 0f, z), I0);

        [Test]
        public void Nadir_IsInverseSquareOfTheMountingHeight()
        {
            foreach (float h in new[] { 8f, 9f, 10f, 11f })
                Assert.AreEqual(StreetLampOptics.NadirFactor * I0 / (h * h), E(h, 0f, 0f), 1e-3f * I0 / (h * h), $"h {h}");
        }

        [Test]
        public void Footprint_IsLongAlongTheRoad_AndShortBehindTheColumn()
        {
            const float h = 9f;
            float along = E(h, 0f, 1.5f * h), street = E(h, 1.0f * h, 0f), house = E(h, -1.0f * h, 0f);
            Assert.Greater(along, 0.2f * E(h, 0f, 0f), "1.5 h along the road still lit");
            Assert.Greater(street, 3f * house, "carriageway side >> house side");
            Assert.Less(E(h, -0.75f * h, 0f), 0.05f * E(h, 0f, 0f), "only the soft tail 0.75 h behind the column");
            Assert.AreEqual(0f, E(h, -1.06f * h, 0f), 1e-6f, "nothing 1.06 h behind the column (0.7 h x tail 1.5)");
            Assert.AreEqual(0f, E(h, 0f, 3.65f * h), 1e-6f, "footprint ends at 2.4 h x tail 1.5 along");
            Assert.That(E(h, 0f, 2.4f * h) / E(h, 0f, 0f), Is.InRange(0.01f, 0.08f), "review P1-3: soft rim, no drawn edge at the old radius");
            Assert.Greater(E(h, 0f, 1.5f * h), E(h, 1.5f * h, 0f), "elongated along the road, not round");
        }

        [Test]
        public void SymmetricPostTop_IsRound()
        {
            const float h = 6f;
            float a = E(h, 0f, 1.0f * h, false), b = E(h, 1.0f * h, 0f, false), c = E(h, -1.0f * h, 0f, false);
            Assert.AreEqual(a, b, 1e-4f); Assert.AreEqual(a, c, 1e-4f);
        }

        [Test]
        public void BetweenColumns_AtTheGeneratedSpacing_LightDipsButDoesNotVanish()
        {
            // Generated lamps (bialystok-industrial-c, 698 luminaire columns): nearest-neighbour spacing p50 28.9 m,
            // standards.LAMP 30-36 m at 8-11 m. EN 13201 M3-M5: Uo >= 0.35-0.4 (luminance). The pool must read as a pool.
            foreach (var (h, s) in new[] { (8f, 30f), (9f, 29f), (10f, 33f), (11f, 36f) })
            {
                float peak = 0f, min = float.MaxValue, sum = 0f; int n = 0;
                for (float z = 0f; z <= s; z += 0.25f)
                {
                    float e = E(h, 0.5f * h, z) + E(h, 0.5f * h, z - s) + E(h, 0.5f * h, z + s);
                    peak = Mathf.Max(peak, e); min = Mathf.Min(min, e); sum += e; n++;
                }
                float avg = sum / n;
                Assert.That(min / peak, Is.InRange(0.15f, 0.65f), $"h {h} S {s}: dip min/peak {min / peak:F2}");
                Assert.That(min / avg, Is.GreaterThanOrEqualTo(0.28f), $"h {h} S {s}: Uo-like min/avg {min / avg:F2}");
            }
        }

        [Test]
        public void IntensityTable_IsAPlausibleBatwing_WithFullCutoff()
        {
            const float h = 9f;
            var lamp = new Vector3(0f, h, 0f);
            float max = 0f, gammaAtMax = 0f;
            for (float g = 0f; g < 89f; g += 0.5f)
            {
                float t = Mathf.Tan(g * Mathf.Deg2Rad) * h;
                float i = StreetLampOptics.RelativeIntensity(lamp, ArmEast, true, new Vector3(0f, 0f, t));
                if (i > max) { max = i; gammaAtMax = g; }
                if (g >= 75f) Assert.AreEqual(0f, i, 1e-6f, $"cutoff at {g}°");
            }
            Assert.That(max, Is.InRange(1.3f, 2.5f), "peak along the road vs nadir (typical LED road optic ~2x)");
            Assert.That(gammaAtMax, Is.InRange(40f, 65f), "peak angle");
            Assert.AreEqual(0f, StreetLampOptics.RelativeIntensity(lamp, ArmEast, true, new Vector3(3f, h + 1f, 0f)), "nothing upwards");
        }

        [Test]
        public void DownwardFlux_MatchesTheClosedForm_AndARealLuminaire()
        {
            const float h = 10f, step = 0.2f;
            double flux = 0;
            for (float x = -1.6f * h; x <= 2.4f * h; x += step)
                for (float z = -3.7f * h; z <= 3.7f * h; z += step)
                    flux += E(h, x, z) * step * step;
            float closed = StreetLampOptics.DownwardFluxLm(I0, true);
            Assert.AreEqual(closed, (float)flux, 0.03f * closed, "numeric vs closed form");
            Assert.That(closed, Is.InRange(5000f, 8000f), "8-12 klm luminaire x utilance ~0.6 on the ground (WORKING_VALUE)");
        }

        [Test]
        public void Glass_SingleArm_DoubleArm_PostTop()
        {
            var pos = new Vector3[2]; var arm = new Vector2[2];
            // props.lamp(10, 1.5): glass 0.04-0.6 m beyond the arm end (1.5 m), along +y of the generator
            int n = StreetLampOptics.LuminairesFromGlass(new Bounds(new Vector3(0f, 9.92f, 1.82f), new Vector3(0.26f, 0f, 0.56f)), pos, arm);
            Assert.AreEqual(1, n);
            Assert.AreEqual(1.82f, pos[0].z, 1e-4f); Assert.AreEqual(Vector2.up, arm[0]);
            // lamp_double: two glass quads in one submesh, -2.1..+2.1 m
            n = StreetLampOptics.LuminairesFromGlass(new Bounds(new Vector3(0f, 9.92f, 0f), new Vector3(0.26f, 0f, 4.2f)), pos, arm);
            Assert.AreEqual(2, n);
            Assert.AreEqual(-pos[0].z, pos[1].z, 1e-4f); Assert.Greater(Mathf.Abs(pos[0].z), 1.5f);
            Assert.AreEqual(-arm[0].y, arm[1].y, 1e-6f);
            // post-top (no arm): symmetric
            n = StreetLampOptics.LuminairesFromGlass(new Bounds(new Vector3(0f, 5f, 0f), new Vector3(0.3f, 0.1f, 0.3f)), pos, arm);
            Assert.AreEqual(1, n); Assert.AreEqual(Vector2.zero, arm[0]);
        }

        [Test]
        public void ShaderRadii_MirrorTheCSharpOptics()
        {
            string src = File.ReadAllText("Assets/_Project/Rendering/Shaders/KamionLampPools.hlsl");
            float Def(string name)
            {
                var m = Regex.Match(src, @"#define\s+" + name + @"\s+([0-9.]+)");
                Assert.IsTrue(m.Success, name);
                return float.Parse(m.Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture);
            }
            Assert.AreEqual(StreetLampOptics.AlongRadiusH, Def("KAMION_LAMP_RA"), 1e-6f);
            Assert.AreEqual(StreetLampOptics.StreetSideRadiusH, Def("KAMION_LAMP_RS"), 1e-6f);
            Assert.AreEqual(StreetLampOptics.HouseSideRadiusH, Def("KAMION_LAMP_RH"), 1e-6f);
            Assert.AreEqual(StreetLampOptics.SymmetricRadiusH, Def("KAMION_LAMP_RSYM"), 1e-6f);
            Assert.AreEqual(StreetLampOptics.TailShare, Def("KAMION_LAMP_TAIL_S"), 1e-6f);
            Assert.AreEqual(StreetLampOptics.TailRadius, Def("KAMION_LAMP_TAIL_R"), 1e-6f);
        }

        [Test]
        public void SodiumTint_HasTheLedLuminance()
        {
            Color r = StreetLamps.SodiumTintRatio;
            var led = new Color(1f, 0.93f, 0.82f);
            float yl = 0.2126f * led.r + 0.7152f * led.g + 0.0722f * led.b;
            float ys = 0.2126f * led.r * r.r + 0.7152f * led.g * r.g + 0.0722f * led.b * r.b;
            Assert.AreEqual(yl, ys, 1e-4f);
            Assert.Greater(r.r, r.g); Assert.Greater(r.g, r.b);
        }

        [Test]
        public void SpecularHighlight_OnlyHighAndUltra_LowUnchanged()
        {
            foreach (var x in QualityProfile.Defaults())
                Assert.AreEqual(x.name == "High" || x.name == "Ultra", x.lampPoolSpecular, x.name);
            var qp = QualityProfile.Load();
            Assert.IsNotNull(qp);
            Assert.IsTrue(qp.TryGet("Low", out var low)); Assert.IsFalse(low.lampPoolSpecular, "asset Low");
            Assert.AreEqual(4, low.lampPools, "asset Low: pool count unchanged");
            Assert.IsTrue(qp.TryGet("High", out var high)); Assert.IsTrue(high.lampPoolSpecular, "asset High");
        }
    }
}
