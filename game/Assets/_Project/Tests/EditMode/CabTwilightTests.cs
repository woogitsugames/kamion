using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// D84 polish (review P1-3): the day-time cab-view lift fades out through twilight so the wheel is not brighter than
    /// the world at dusk; the day presets (LP_Clear 42 deg, LP_Overcast 41 deg, LP_LowSun 9 deg) must keep their look.
    /// </summary>
    public class CabTwilightTests
    {
        [Test]
        public void NightFactor_IsZeroForDayPresets_AndOneAtDusk()
        {
            var cl = new GameObject("cab").AddComponent<CabInteriorLighting>();
            foreach (float sun in new[] { 42f, 41f, 9f, cl.twilightStartSunDeg })
                Assert.That(CabInteriorLighting.NightFactor(sun, cl.twilightStartSunDeg, cl.twilightFullSunDeg), Is.EqualTo(0f).Within(1e-6f), $"sun {sun} deg");
            Assert.That(CabInteriorLighting.NightFactor(LightingPreset.DuskSunElevationDeg, cl.twilightStartSunDeg, cl.twilightFullSunDeg), Is.EqualTo(1f).Within(1e-6f));
            float prev = 0f;
            for (float sun = cl.twilightStartSunDeg; sun >= cl.twilightFullSunDeg; sun -= 0.5f)
            {
                float n = CabInteriorLighting.NightFactor(sun, cl.twilightStartSunDeg, cl.twilightFullSunDeg);
                Assert.That(n, Is.GreaterThanOrEqualTo(prev - 1e-6f), "monotone through twilight");
                prev = n;
            }
            Object.DestroyImmediate(cl.gameObject);
        }

        [Test]
        public void CabViewStops_DayUnchanged_NightCappedByNightViewEv()
        {
            Assert.That(CabInteriorLighting.CabViewStops(2.5f, 1f, 0.45f, 0f), Is.EqualTo(2.5f));
            Assert.That(CabInteriorLighting.CabViewStops(2.5f, 1f, 0.45f, 1f), Is.EqualTo(0.45f).Within(1e-6f));
            Assert.That(CabInteriorLighting.CabViewStops(2.5f, 0.2f, 0.45f, 1f), Is.EqualTo(0.2f).Within(1e-6f), "never above the day cab-view lift");
        }
    }
}
