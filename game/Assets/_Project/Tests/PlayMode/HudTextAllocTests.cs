using System;
using System.Collections;
using System.Globalization;
using System.Reflection;
using Game.Controls;
using Game.UI;
using Game.UI.Driving;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Profiling;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace Game.Tests
{
    /// <summary>
    /// M23 (variant (b): UnityEngine.UI.Text, no TextMeshPro): HUD/overlay label updates during driving must not
    /// allocate GC memory. Counts GC.Alloc samples on this thread with Profiling.Recorder (same mechanism as
    /// Is.Not.AllocatingGCMemory; proven in the r3 review: legacy gyro concat = 1003 samples / 500 updates) over 500
    /// updates with varying values and expects 0. GC.GetAllocatedBytesForCurrentThread returns 0 in the editor.
    /// </summary>
    public class HudTextAllocTests
    {
        /// <summary>Number of GC.Alloc samples on this thread while running <paramref name="a"/>.</summary>
        static int CountAllocs(Action a)
        {
            var r = Recorder.Get("GC.Alloc");
            r.enabled = false;
            r.FilterToCurrentThread();
            r.enabled = true;
            a();
            r.enabled = false;
            int n = r.sampleBlockCount;
            r.CollectFromAllThreads();
            return n;
        }

        DrivingHud m_Hud;
        DiagnosticsOverlay m_Overlay;
        Camera m_Cam;
        int m_SavedTargetFps;

        [SetUp]
        public void SetUp() { m_SavedTargetFps = Application.targetFrameRate; }

        [TearDown]
        public void TearDown()
        {
            Application.targetFrameRate = m_SavedTargetFps;
            if (m_Hud != null) UnityEngine.Object.Destroy(m_Hud.gameObject);
            if (m_Overlay != null) UnityEngine.Object.Destroy(m_Overlay.gameObject);
            if (m_Cam != null) UnityEngine.Object.Destroy(m_Cam.gameObject);
        }

        /// <summary>Typed setter for GyroSteering.RelativeTiltDeg (private setter) — calling it does not box.</summary>
        static Action<GyroSteering, float> MakeTiltSetter()
        {
            var m = typeof(GyroSteering).GetProperty("RelativeTiltDeg", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic).GetSetMethod(true);
            return (Action<GyroSteering, float>)Delegate.CreateDelegate(typeof(Action<GyroSteering, float>), m);
        }

        static readonly FieldInfo s_NextTelemetry = typeof(DrivingHud).GetField("m_NextTelemetry", BindingFlags.Instance | BindingFlags.NonPublic);
        static readonly FieldInfo s_GyroLabel = typeof(DrivingHud).GetField("m_GyroLabel", BindingFlags.Instance | BindingFlags.NonPublic);
        static readonly FieldInfo s_RpmStrings = typeof(DrivingHud).GetField("k_RpmStrings", BindingFlags.Static | BindingFlags.NonPublic);
        static readonly FieldInfo s_GyroStrings = typeof(DrivingHud).GetField("k_GyroStrings", BindingFlags.Static | BindingFlags.NonPublic);
        static readonly FieldInfo s_Panel = typeof(DiagnosticsOverlay).GetField("m_Panel", BindingFlags.Instance | BindingFlags.NonPublic);
        static readonly FieldInfo s_FpsLabel = typeof(DiagnosticsOverlay).GetField("m_FpsButtonLabel", BindingFlags.Instance | BindingFlags.NonPublic);

        /// <summary>500 RefreshNow() calls with varying gyro tilt and brake-cruise values: 0 GC.Alloc samples.</summary>
        [UnityTest]
        public IEnumerator HudLabels_500VaryingUpdates_ZeroGcAlloc()
        {
            float cruise = 0f;
            var ctx = new DrivingHudContext
            {
                IsGyroMode = () => true,
                Gyro = new GyroSteering(),
                BrakeCruiseKmh = () => cruise,
            };
            m_Hud = DrivingHud.Create(null, ctx, overlay: true);
            yield return null;
            m_Hud.RefreshNow();
            yield return null;

            var setTilt = MakeTiltSetter();
            var gyro = ctx.Gyro;
            var zero = (object)0f;   // boxed once; reused so the measurement loop itself does not allocate
            // Warm up the reflection paths (one-time caches) outside the measured window.
            setTilt(gyro, 1.23f); s_NextTelemetry.SetValue(m_Hud, zero); m_Hud.RefreshNow();
            yield return null;

            // Baseline: the reflection write that forces the 0.2 s gyro/telemetry branch (test harness only).
            int harness = CountAllocs(() => { for (int i = 0; i < 500; i++) s_NextTelemetry.SetValue(m_Hud, zero); });
            int total = CountAllocs(() =>
            {
                for (int i = 0; i < 500; i++)
                {
                    setTilt(gyro, ((i * 37) % 1801 - 900) / 10f + 0.007f);   // varying, not bucket-aligned
                    cruise = 1f + (i % 119) + 0.5f;                          // varying brake cruise
                    s_NextTelemetry.SetValue(m_Hud, zero);                   // force the 0.2 s gyro/telemetry branch
                    m_Hud.RefreshNow();
                }
            });
            var label = (Text)s_GyroLabel.GetValue(m_Hud);
            Debug.Log($"[HudAlloc] DrivingHud 500 varying updates: {total} GC.Alloc (harness SetValue {harness}); gyro label '{label.text}'");
            long allocs = total - harness;
            yield return null;
            Assert.AreEqual(0, allocs, $"500 HUD label updates with varying values allocated {allocs} GC.Alloc samples (expected 0)");
        }

        /// <summary>The counter sees allocations: the old gyro label path (main before M23) allocates.</summary>
        [Test]
        public void Counter_SeesLegacyConcatAllocations()
        {
            var go = new GameObject("legacy", typeof(RectTransform));
            try
            {
                var t = go.AddComponent<Text>();
                t.font = UiFonts.Default;
                var ci = CultureInfo.InvariantCulture;
                for (int i = 0; i < 10; i++) t.text = "Gyro: " + (i * 0.1f).ToString("F1", ci) + "°";
                int n = CountAllocs(() => { for (int i = 0; i < 500; i++) t.text = "Gyro: " + (i * 0.1f - 20f).ToString("F1", ci) + "°"; });
                Debug.Log($"[HudAlloc] legacy gyro concat: {n} GC.Alloc / 500 updates");
                Assert.Greater(n, 0);
            }
            finally { UnityEngine.Object.DestroyImmediate(go); }
        }

        /// <summary>The prebuilt gyro/rpm strings are exactly the strings the old per-frame formatting produced.</summary>
        [Test]
        public void LabelTables_MatchOldFormatting()
        {
            var ci = CultureInfo.InvariantCulture;
            var gyro = (string[])s_GyroStrings.GetValue(null);
            var rpm = (string[])s_RpmStrings.GetValue(null);

            Assert.AreEqual(401, rpm.Length);
            Assert.AreEqual("0 obr/min", rpm[0]);
            Assert.AreEqual("600 obr/min", rpm[12]);
            Assert.AreEqual("20000 obr/min", rpm[400]);
            Assert.AreEqual((12 * 50).ToString(ci) + " obr/min", rpm[12]);

            Assert.AreEqual(1801 * 2, gyro.Length);
            // key = (tenth + 900) * 2 + (hasSensor ? 1 : 0)
            Assert.AreEqual("Gyro: " + (123 / 10f).ToString("F1", ci) + "°", gyro[(900 + 123) * 2 + 1]);
            Assert.AreEqual("Gyro: " + (-900 / 10f).ToString("F1", ci) + "°" + "  (brak czujnika)", gyro[0]);
            Assert.AreEqual("Gyro: " + (0 / 10f).ToString("F1", ci) + "°", gyro[900 * 2 + 1]);
            // Same text as the old concat for an arbitrary unrounded tilt: the label shows the rounded value.
            float tilt = 12.34f;
            int key = (Mathf.Clamp(Mathf.RoundToInt(tilt * 10f), -900, 900) + 900) * 2 + 1;
            Assert.AreEqual("Gyro: " + tilt.ToString("F1", ci) + "°", gyro[key]);
        }

        /// <summary>The gyro label on a real HUD shows exactly the old format after a refresh with a known tilt.</summary>
        [UnityTest]
        public IEnumerator GyroLabel_OnHud_MatchesOldFormat()
        {
            var ctx = new DrivingHudContext { IsGyroMode = () => true, Gyro = new GyroSteering() };
            m_Hud = DrivingHud.Create(null, ctx, overlay: true);
            yield return null;

            var setTilt = MakeTiltSetter();
            var gyro = ctx.Gyro;
            float tilt = -7.26f;
            setTilt(gyro, tilt);
            s_NextTelemetry.SetValue(m_Hud, (object)0f);
            m_Hud.RefreshNow();

            var label = (Text)s_GyroLabel.GetValue(m_Hud);
            string expected = "Gyro: " + tilt.ToString("F1", CultureInfo.InvariantCulture) + "°" + (gyro.HasSensor ? "" : "  (brak czujnika)");
            Assert.AreEqual(expected, label.text);
        }

        /// <summary>500 overlay refreshes with an unchanged state: 0 GC.Alloc; a changed target FPS updates the label.</summary>
        [UnityTest]
        public IEnumerator DiagnosticsButtonLabels_500Updates_ZeroGcAlloc_AndChangeGated()
        {
            var go = new GameObject("DiagCam");
            m_Cam = go.AddComponent<Camera>();
            m_Overlay = DiagnosticsOverlay.Create(m_Cam, null, null);
            ((GameObject)s_Panel.GetValue(m_Overlay)).SetActive(false);   // isolate the button labels from the body
            yield return null;
            m_Overlay.RefreshNow();
            yield return null;

            var label = (Text)s_FpsLabel.GetValue(m_Overlay);
            Application.targetFrameRate = 60;
            m_Overlay.RefreshNow();
            string at60 = label.text;

            long allocs = CountAllocs(() => { for (int i = 0; i < 500; i++) m_Overlay.RefreshNow(); });
            Debug.Log($"[HudAlloc] DiagnosticsOverlay 500 refreshes (panel hidden): {allocs} GC.Alloc");
            yield return null;
            Assert.AreEqual(0, allocs, $"500 diagnostics overlay refreshes (unchanged state) allocated {allocs} GC.Alloc samples (expected 0)");
            Assert.AreEqual(at60, label.text);

            Application.targetFrameRate = 30;
            m_Overlay.RefreshNow();
            Assert.AreEqual("Cel: 30 FPS", label.text);
        }
    }
}
