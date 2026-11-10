using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0044 addendum r7: the cab view on Low (no LUT) writes the D23 toe itself (KamionToeParity.hlsl), so
    /// plain sRGB of the corrected value must match the master curve's display wherever the cab lives (scene 0..0.2).</summary>
    public class CabToeParityTests
    {
        [Test]
        public void NoPostToeParity_MatchesMasterCurve_InTheCabRange()
        {
            foreach (var p in new[] { LightingPreset.CreateClear(), LightingPreset.CreateOvercast(), LightingPreset.CreateLowSun(), LightingPreset.CreateDusk() })
            {
                var c = new AnimationCurve(LookGrading.MasterCurveKeys(p.lookBlackLevel, p.lookWhiteClip));
                float prev = -1f;
                for (float x = 0f; x <= 0.2f; x += 0.0005f)
                {
                    float low = LookGrading.LinearToSrgb(LookGrading.ToeParity(LookGrading.NoPostToeParity, x));
                    float high = LookGrading.Display(c, x);
                    Assert.That(Mathf.Abs(low - high), Is.LessThan(0.006f), $"{p.name}: Low {low:F4} vs High {high:F4} at {x}");
                    Assert.That(low, Is.GreaterThanOrEqualTo(prev), $"{p.name}: monotone at {x}");
                    prev = low;
                }
                Object.DestroyImmediate(p);
            }
        }
    }
}
