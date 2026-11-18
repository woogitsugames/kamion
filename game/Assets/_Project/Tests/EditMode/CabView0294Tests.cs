using Game.Controls;
using Game.Editor.VisualQA;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>
    /// D90 / ADR 0294 (owner, 2026-11-18): cab camera variant B - default vertical FOV 70 deg (was 55), one-time migration of
    /// saves still at the old default (as D85), a FOV the player changed is kept; the speed / gear / air strip of the monitor
    /// HUD is hidden in the cab view (the dash cluster is the speedometer) and shown in the exterior cameras.
    /// </summary>
    public class CabView0294Tests
    {
        [Test]
        public void Default_CabFov_Is70_Schema6()
        {
            Assert.AreEqual(70f, ControlSettings.DefaultCabFovDeg);
            Assert.AreEqual(70f, ControlSettings.Defaults().cabFov);
            Assert.AreEqual(6, ControlSettings.CurrentSchema);
            Assert.That(ControlSettings.DefaultCabFovDeg, Is.InRange(ControlSettings.FovMin, ControlSettings.FovMax), "reachable on the stepper");
            Assert.AreEqual(0f, (ControlSettings.DefaultCabFovDeg - ControlSettings.FovMin) % 5f, "on the 5 deg stepper grid");
        }

        [Test]
        public void Migration_OldDefault55_MovesTo70_Once()
        {
            var s = ControlSettings.FromJson("{\"schema\":5,\"cabFov\":55,\"wheelRangeDeg\":540}");
            Assert.AreEqual(70f, s.cabFov);
            Assert.AreEqual(6, s.schema);
            Assert.AreEqual(540f, s.wheelRangeDeg, "other choices kept");
            // Saved again as v6 and the player sets 55 by hand: that is a choice now, never migrated again.
            s.cabFov = 55f;
            var again = ControlSettings.FromJson(s.ToJson());
            Assert.AreEqual(55f, again.cabFov);
        }

        [TestCase(45f)]
        [TestCase(60f)]
        [TestCase(65f)]
        [TestCase(75f)]
        public void Migration_PlayerChangedFov_IsKept(float fov)
        {
            var s = ControlSettings.FromJson("{\"schema\":5,\"cabFov\":" + fov.ToString(System.Globalization.CultureInfo.InvariantCulture) + "}");
            Assert.AreEqual(fov, s.cabFov);
            Assert.AreEqual(6, s.schema);
        }

        [Test]
        public void Migration_SaveWithoutCameraFields_GetsNewDefault()
        {
            Assert.AreEqual(70f, ControlSettings.FromJson("{\"schema\":1,\"wheelRangeDeg\":270}").cabFov);
            Assert.AreEqual(70f, ControlSettings.FromJson("{\"wheelRangeDeg\":270}").cabFov);
        }

        [Test]
        public void HudStrip_HiddenInCab_ShownOutside()
        {
            var prefs = HudPrefsData.Defaults;
            bool cab = HudVisibility.IsCabView(true, null);
            bool chase = HudVisibility.IsCabView(false, null);
            Assert.IsFalse(HudVisibility.Resolve(prefs.Detail, prefs.Cab, cab, cabInstrumentsLive: true, devDiagnostics: false).Strip, "cab view: no strip over the dash cluster");
            Assert.IsTrue(HudVisibility.Resolve(prefs.Detail, prefs.Cab, chase, cabInstrumentsLive: true, devDiagnostics: false).Strip, "exterior camera: strip");
        }

        [Test]
        public void CabView_RigWins_OverrideForQa_DefaultNotCab()
        {
            Assert.IsTrue(HudVisibility.IsCabView(true, false));
            Assert.IsFalse(HudVisibility.IsCabView(false, true), "the live rig decides");
            Assert.IsTrue(HudVisibility.IsCabView(null, true), "QA render of a cab camera");
            Assert.IsFalse(HudVisibility.IsCabView(null, false));
            Assert.IsFalse(HudVisibility.IsCabView(null, null), "unknown: strip shows");
        }

        [TestCase("cab-driver", true)]
        [TestCase("cab-view-b-fov70-hud", true)]
        [TestCase("lab-cab-eye", true)]
        [TestCase("chase-hud", false)]
        [TestCase("truck-34", false)]
        [TestCase("", false)]
        public void QaCamera_CabViewByPerCameraId(string id, bool cab) => Assert.AreEqual(cab, CabViewQa.IsCabCameraId(id));
    }
}
