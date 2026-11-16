using System;
using Game.Rendering;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>ADR 0269: PC tier data (validity, Low ≤ Medium ≤ High ≤ Ultra) and the first-launch VRAM / RAM / GPU → tier
    /// mapping. Pure logic (no UnityEngine calls), also run outside Unity with a .NET harness.</summary>
    public class PcGraphicsTierTableTests
    {
        [Test]
        public void Defaults_AreValid()
        {
            var errors = PcTierTable.Validate(PcTierTable.Defaults());
            Assert.IsEmpty(errors, string.Join("\n", errors));
        }

        [Test]
        public void Defaults_OrderAndNamesMatchTheQualityLevels()
        {
            var t = PcTierTable.Defaults();
            Assert.AreEqual(PcTierTable.TierCount, t.Length);
            string[] names = { "Low", "Medium", "High", "Ultra" };
            for (int i = 0; i < t.Length; i++)
            {
                Assert.AreEqual((PcTier)i, t[i].tier);
                Assert.AreEqual(names[i], t[i].Name);
                Assert.IsTrue(PcTierTable.TryParse(names[i].ToLowerInvariant(), out var parsed));
                Assert.AreEqual((PcTier)i, parsed);
            }
            Assert.IsFalse(PcTierTable.TryParse("Epic", out _));
        }

        [Test]
        public void Defaults_DistancesAndResolutionsAreMonotonic()
        {
            var t = PcTierTable.Defaults();
            for (int i = 1; i < t.Length; i++)
            {
                var a = t[i - 1]; var b = t[i];
                string p = a.Name + "→" + b.Name;
                Assert.LessOrEqual(a.shadowDistance, b.shadowDistance, p + " shadowDistance");
                Assert.LessOrEqual(a.shadowResolution, b.shadowResolution, p + " shadowResolution");
                Assert.LessOrEqual(a.shadowCascades, b.shadowCascades, p + " shadowCascades");
                Assert.LessOrEqual(a.cameraFarClip, b.cameraFarClip, p + " cameraFarClip");
                Assert.LessOrEqual(a.lodBias, b.lodBias, p + " lodBias");
                Assert.LessOrEqual(a.treeCullM, b.treeCullM, p + " treeCullM");
                Assert.LessOrEqual(a.treeThinStartM, b.treeThinStartM, p + " treeThinStartM");
                Assert.LessOrEqual(a.forestHlodM, b.forestHlodM, p + " forestHlodM");
                Assert.LessOrEqual(a.vehicleCullM, b.vehicleCullM, p + " vehicleCullM");
                Assert.LessOrEqual(a.msaa, b.msaa, p + " msaa");
                Assert.LessOrEqual(a.renderScale, b.renderScale, p + " renderScale");
                Assert.LessOrEqual(a.worldTextureAniso, b.worldTextureAniso, p + " worldTextureAniso");
                Assert.LessOrEqual(a.envCaptureSize, b.envCaptureSize, p + " envCaptureSize");
                Assert.GreaterOrEqual(a.textureMipmapLimit, b.textureMipmapLimit, p + " texture resolution");
                Assert.GreaterOrEqual(a.maximumLodLevel, b.maximumLodLevel, p + " maximumLodLevel");
            }
        }

        [Test]
        public void Defaults_KeepMirrorsAndFoliageCoverageOnEveryTier()
        {
            foreach (var t in PcTierTable.Defaults())
            {
                Assert.GreaterOrEqual(t.mirrorResolutionScale, 1f, t.Name + ": mirrors always usable (docs/06)");
                Assert.GreaterOrEqual(t.msaa, 2, t.Name + ": leaf alpha-to-coverage needs MSAA");
                Assert.IsTrue(t.hdr && t.postProcessing, t.Name + ": one calibrated tonemapped look");
                Assert.AreNotEqual(2, t.softShadows ? t.softShadowQuality : 1, t.Name + ": soft shadow Medium variant is stripped");
                StringAssert.Contains("WORKING_VALUE", t.status, t.Name + ": unmeasured values must say so");
            }
            Assert.AreEqual(30, PcTierTable.Get(PcTier.Low).targetFps, "D74 minimum: Low 30 fps");
            Assert.AreEqual(60, PcTierTable.Get(PcTier.High).targetFps, "D74 recommended: High 60 fps");
        }

        [Test]
        public void Validate_RejectsBrokenTables()
        {
            var t = PcTierTable.Defaults();
            t[2].shadowDistance = t[1].shadowDistance - 1f;          // High below Medium
            t[0].msaa = 1;                                            // no MSAA
            t[3].softShadowQuality = 2;                               // stripped variant
            t[1].cascade4SplitY = 0.01f;                              // splits not increasing
            t[0].mirrorResolutionScale = 0.5f;
            var errors = PcTierTable.Validate(t);
            Assert.IsTrue(errors.Exists(e => e.Contains("shadowDistance decreases")), string.Join("\n", errors));
            Assert.IsTrue(errors.Exists(e => e.Contains("Low: msaa")));
            Assert.IsTrue(errors.Exists(e => e.Contains("Ultra: softShadowQuality")));
            Assert.IsTrue(errors.Exists(e => e.Contains("Medium: cascade4Split")));
            Assert.IsTrue(errors.Exists(e => e.Contains("Low: mirrors")));
            Assert.IsNotEmpty(PcTierTable.Validate(new PcTierSettings[3]));
            Assert.IsNotEmpty(PcTierTable.Validate(null));
        }

        static PcTier Tier(string gpu, int vram, int ram) => PcTierTable.DefaultFor(new PcHardwareInfo(gpu, vram, ram));

        [Test]
        public void DefaultFor_D74Classes()
        {
            // D74 minimum: GTX 660 2 GB / RX 460 2 GB / Intel HD 630, 8 GB RAM -> Low.
            Assert.AreEqual(PcTier.Low, Tier("NVIDIA GeForce GTX 660", 2048, 8150));
            Assert.AreEqual(PcTier.Low, Tier("Radeon RX 460 Series", 2048, 8150));
            Assert.AreEqual(PcTier.Low, Tier("Intel(R) HD Graphics 630", 1024, 8150));
            // D74 recommended: GTX 1660 6 GB / RX 590 8 GB, 12 GB RAM -> High.
            Assert.AreEqual(PcTier.High, Tier("NVIDIA GeForce GTX 1660", 6144, 12221));
            Assert.AreEqual(PcTier.High, Tier("Radeon RX 590 Series", 8192, 16300));
            // Recommended GPU but only 8 GB RAM -> Medium (D74 recommended needs 12 GB).
            Assert.AreEqual(PcTier.Medium, Tier("NVIDIA GeForce GTX 1660", 6144, 8150));
            // 4 GB class -> Medium.
            Assert.AreEqual(PcTier.Medium, Tier("NVIDIA GeForce GTX 1050 Ti", 4096, 16300));
        }

        [Test]
        public void DefaultFor_EdgesAndCeiling()
        {
            Assert.AreEqual(PcTier.High, Tier("NVIDIA GeForce RTX 5070", 12227, 65200), "auto never picks Ultra");
            Assert.AreEqual(PcTier.High, Tier("Intel(R) Arc(TM) A770 Graphics", 16032, 32600), "Arc is a discrete GPU");
            Assert.AreEqual(PcTier.Low, Tier("Intel(R) UHD Graphics 770", 16000, 32600), "integrated: shared memory is not VRAM");
            Assert.AreEqual(PcTier.Low, Tier("AMD Radeon(TM) Graphics", 4096, 16300), "Ryzen iGPU");
            Assert.AreEqual(PcTier.Low, Tier("Microsoft Basic Render Driver", 0, 16300));
            Assert.AreEqual(PcTier.Medium, Tier("Unknown GPU", 0, 16300), "VRAM unknown");
            Assert.AreEqual(PcTier.Medium, Tier(null, 0, 0), "nothing known");
            Assert.AreEqual(PcTier.Low, Tier("NVIDIA GeForce RTX 3060", 12288, 4096), "RAM below the D74 minimum");
            Assert.AreEqual(PcTier.Low, Tier("NVIDIA GeForce GTX 1060 3GB", PcTierTable.LowBelowVramMb - 1, 16300));
            Assert.AreEqual(PcTier.Medium, Tier("x", PcTierTable.LowBelowVramMb, 16300));
            Assert.AreEqual(PcTier.Medium, Tier("x", PcTierTable.MediumBelowVramMb - 1, 16300));
            Assert.AreEqual(PcTier.High, Tier("x", PcTierTable.MediumBelowVramMb, PcTierTable.HighMinRamMb));
            Assert.AreEqual(PcTier.Medium, Tier("x", PcTierTable.MediumBelowVramMb, PcTierTable.HighMinRamMb - 1));
            Assert.AreEqual(PcTier.High, Tier("x", 8192, 0), "RAM unknown does not cap");
            PcTierTable.DefaultFor(new PcHardwareInfo("NVIDIA GeForce GTX 660", 2048, 8150), out string why);
            StringAssert.Contains("VRAM", why);
        }

        [Test]
        public void DefaultFor_IsMonotonicInVram()
        {
            PcTier prev = PcTier.Low;
            for (int vram = 256; vram <= 32768; vram += 256)
            {
                var t = Tier("NVIDIA GeForce", vram, 32000);
                Assert.GreaterOrEqual((int)t, (int)prev, $"vram {vram}");
                Assert.LessOrEqual((int)t, (int)PcTierTable.AutoCeiling);
                prev = t;
            }
        }
    }
}
