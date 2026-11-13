using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>D23 "like a phone photo" (docs/11, ADR 0016): tone curve and exposure table, review r3 G1-G3 targets.</summary>
    public class LookGradingTests
    {
        static AnimationCurve Master(LightingPreset p) => new AnimationCurve(LookGrading.MasterCurveKeys(p.lookBlackLevel, p.lookWhiteClip));

        [Test]
        public void ToneCurve_BlackFloor_MidGrey_WhiteClips()
        {
            foreach (var p in new[] { LightingPreset.CreateClear(), LightingPreset.CreateOvercast(), LightingPreset.CreateLowSun(), LightingPreset.CreateDusk() })
            {
                var c = Master(p);
                Assert.That(LookGrading.Display(c, 0f), Is.InRange(0.005f, 0.02f), $"{p.name}: black ≤ 2 % (G1), was 21 %");
                Assert.That(LookGrading.Display(c, 0.002f), Is.LessThan(0.04f), $"{p.name}: deep shadow ≤ 4 % (cab p1)");
                Assert.That(LookGrading.Display(c, 0.18f), Is.InRange(0.46f, 0.51f), $"{p.name}: mid-grey kept (ADR 0010)");
                Assert.That(LookGrading.Display(c, 0.55f), Is.InRange(0.80f, 0.93f), $"{p.name}: lit wall 80-92 % with detail");
                Assert.That(LookGrading.Display(c, p.lookWhiteClip + 0.1f), Is.GreaterThan(0.985f), $"{p.name}: sky clips (≥ 97 %)");
                float prev = -1f;
                for (float x = 0f; x < 3f; x += 0.01f)
                {
                    float d = LookGrading.Display(c, x);
                    Assert.That(d, Is.GreaterThanOrEqualTo(prev - 1e-4f), $"{p.name}: monotone at {x}");
                    prev = d;
                }
                Object.DestroyImmediate(p);
            }
        }

        [Test]
        public void ExposureTable_HighSunUnchanged_LowSunWalls_DuskDarker()
        {
            var clear = LightingPreset.CreateClear();
            var over = LightingPreset.CreateOvercast();
            var low = LightingPreset.CreateLowSun();
            var dusk = LightingPreset.CreateDusk();
            try
            {
                var mc = clear.CreateModel(); var mo = over.CreateModel(); var ml = low.CreateModel(); var md = dusk.CreateModel();
                // High sun: incident meter + D23 1 EV (ADR 0010 / D23 v1) within 0.15 EV.
                Assert.AreEqual(SkyModel.IncidentEv100(mc.HorizontalIlluminanceLux) - 1f, clear.ResolveEv100(mc), 0.15f);
                // overcast: owner variant 3 biases the preset by -0.2 EV (ADR 0080)
                Assert.AreEqual(SkyModel.IncidentEv100(mo.HorizontalIlluminanceLux) - 1f - over.exposureCompensation, over.ResolveEv100(mo), 0.15f);
                // Low sun: 0.6-albedo wall facing the sun around 1.0 linear (was 2.8 → flat white).
                float wall = 0.6f * (ml.SunNormalIlluminanceLux + 0.5f * ml.SkyHorizontalIlluminanceLux) / Mathf.PI * ml.Exposure;
                Assert.That(wall, Is.InRange(0.45f, 0.7f), "sunlit wall at 9° sun");
                // Dusk: review r3 G3 asked for 2-3 EV under overcast noon; review s18 (0175/0178 P2) found that still read as
                // a dull day. ADR 0182: lamp-anchored exposure, ambient-lit grey 3.5-4.9 EV under overcast noon (4.4 at EV100 4).
                float greyOver = mo.HorizontalIlluminanceLux * mo.Exposure, greyDusk = md.HorizontalIlluminanceLux * md.Exposure;
                Assert.That(Mathf.Log(greyOver / greyDusk, 2f), Is.InRange(3.5f, 4.9f), "dusk vs overcast noon");
            }
            finally { Object.DestroyImmediate(clear); Object.DestroyImmediate(over); Object.DestroyImmediate(low); Object.DestroyImmediate(dusk); }
        }
    }
}
