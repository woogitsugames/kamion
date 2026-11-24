using Game.Core;
using Game.Rendering;
using Game.Vehicle.Runtime;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>ADR 0342: mirror render-texture quality per tier (MSAA, window-following height, shadows switch).</summary>
    public class MirrorQuality0342Tests
    {
        [TearDown]
        public void Reset()
        {
            MirrorOverrides.Msaa = null; MirrorOverrides.Shadows = null; MirrorOverrides.Legacy = false;
            MirrorOverrides.TierMsaa = 1; MirrorOverrides.TierShadows = false; MirrorOverrides.TierWindowTexelsPerPixel = 0f;
            MirrorOverrides.WindowPixelHeight = 0f; MirrorOverrides.Resolution = null;
        }

        [Test]
        public void HeightForWindow_IsFloorOffAndCapped()
        {
            Assert.AreEqual(384, VehicleCameraBudget.HeightForWindow(384, 312f, 1f), "1080p window below the tier height: floor");
            Assert.AreEqual(432, VehicleCameraBudget.HeightForWindow(384, 432f, 1f), "1440p window: 1:1");
            Assert.AreEqual(648, VehicleCameraBudget.HeightForWindow(384, 432f, 1.5f), "supersampled 1.5");
            Assert.AreEqual(VehicleCameraBudget.MaxMirrorHeight, VehicleCameraBudget.HeightForWindow(384, 5000f, 1.5f), "capped");
            Assert.AreEqual(384, VehicleCameraBudget.HeightForWindow(384, 0f, 1f), "no window known: tier height");
            Assert.AreEqual(384, VehicleCameraBudget.HeightForWindow(384, 800f, 0f), "off");
            Assert.AreEqual(1100, VehicleCameraBudget.HeightForWindow(1100, 800f, 1f), "never below the (scaled) tier height");
        }

        [Test]
        public void Msaa_FollowsTierAndOverride_LegacyIsOff()
        {
            MirrorOverrides.TierMsaa = 4;
            Assert.AreEqual(4, VehicleCameraBudget.MirrorMsaa);
            MirrorOverrides.Msaa = 2;
            Assert.AreEqual(2, VehicleCameraBudget.MirrorMsaa);
            MirrorOverrides.Legacy = true;
            Assert.AreEqual(1, VehicleCameraBudget.MirrorMsaa, "rq_mirror_legacy = the pre-0342 picture");
            Assert.AreEqual(1, VehicleCameraBudget.NormalizeMsaa(0));
            Assert.AreEqual(4, VehicleCameraBudget.NormalizeMsaa(3 + 1));
            Assert.AreEqual(8, VehicleCameraBudget.NormalizeMsaa(16));
        }

        [Test]
        public void Shadows_DefaultOffAndSwitchable()
        {
            Assert.IsFalse(VehicleCameraBudget.MirrorShadows);
            MirrorOverrides.Shadows = true;
            Assert.IsTrue(VehicleCameraBudget.MirrorShadows);
            MirrorOverrides.Legacy = true;
            Assert.IsFalse(VehicleCameraBudget.MirrorShadows);
        }

        [Test]
        public void PcTiers_LowMediumUnchanged_HighUltraAntiAliased()
        {
            var t = PcTierTable.Defaults();
            Assert.AreEqual(1, t[(int)PcTier.Low].mirrorMsaa, "Low: budget tier, no change");
            Assert.AreEqual(0f, t[(int)PcTier.Low].mirrorWindowTexelsPerPixel);
            Assert.AreEqual(1, t[(int)PcTier.Medium].mirrorMsaa);
            Assert.GreaterOrEqual(t[(int)PcTier.High].mirrorMsaa, 4);
            Assert.GreaterOrEqual(t[(int)PcTier.Ultra].mirrorMsaa, t[(int)PcTier.High].mirrorMsaa);
            Assert.GreaterOrEqual(t[(int)PcTier.Ultra].mirrorWindowTexelsPerPixel, t[(int)PcTier.High].mirrorWindowTexelsPerPixel);
            Assert.IsEmpty(PcTierTable.Validate(t));
        }

        [Test]
        public void Validate_RejectsBadMirrorMsaaAndDecrease()
        {
            var t = PcTierTable.Defaults();
            t[2].mirrorMsaa = 3;
            t[3].mirrorMsaa = 4; t[2].mirrorMsaa = 8;   // decreasing High -> Ultra
            var e = PcTierTable.Validate(t);
            Assert.IsTrue(e.Exists(x => x.Contains("mirrorMsaa decreases")), string.Join("\n", e));
            t[2].mirrorMsaa = 3;
            e = PcTierTable.Validate(t);
            Assert.IsTrue(e.Exists(x => x.Contains("High: mirrorMsaa 3")), string.Join("\n", e));
        }

        [Test]
        public void MobileProfile_KeepsMirrorsAsBefore()
        {
            var tier = new QualityProfile.Tier();
            Assert.AreEqual(0, tier.mirrorMsaa, "unset = none (QualityProfileApplier maps to 1)");
            Assert.IsFalse(tier.mirrorShadows);
            Assert.AreEqual(0f, tier.mirrorWindowTexelsPerPixel);
        }
    }
}
