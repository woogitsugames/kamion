using Game.Core.Settings;
using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// Review #136 P1-1 (ADR 0270 x ADR 0269, D74): the settings choice "auto" is never saved and never overrides the tier
    /// GameBootstrap picked; it stands for the hardware default (weak hardware -> Low); an explicit choice is saved as
    /// before; going back to "auto" forgets the saved tier so the detection runs again on the next start.
    /// Uses the real <see cref="QualityTiers"/> / PlayerPrefs key (<see cref="QualityTiers.SavedTierKey"/>) with injected
    /// hardware; the quality level and the key are restored after every test.
    /// </summary>
    public class PcAutoTierTests
    {
        // D74 classes (same numbers as PcGraphicsTierTableTests).
        static readonly PcHardwareInfo Minimum = new PcHardwareInfo("NVIDIA GeForce GTX 660", 2048, 8150);
        static readonly PcHardwareInfo Recommended = new PcHardwareInfo("NVIDIA GeForce GTX 1660", 6144, 12221);
        static readonly PcHardwareInfo Strong = new PcHardwareInfo("NVIDIA GeForce RTX 4080", 16384, 32000);

        static string Auto => TierChoices.ToQualityLevel(TierChoices.Auto);   // null: "auto" has no quality level

        int m_Level;
        bool m_HadKey;
        string m_OldTier;

        [SetUp]
        public void SetUp()
        {
            m_Level = QualitySettings.GetQualityLevel();
            m_HadKey = PlayerPrefs.HasKey(QualityTiers.SavedTierKey);
            m_OldTier = PlayerPrefs.GetString(QualityTiers.SavedTierKey, "");
            PlayerPrefs.DeleteKey(QualityTiers.SavedTierKey);   // a fresh profile
        }

        [TearDown]
        public void TearDown()
        {
            if (m_HadKey) PlayerPrefs.SetString(QualityTiers.SavedTierKey, m_OldTier); else PlayerPrefs.DeleteKey(QualityTiers.SavedTierKey);
            PlayerPrefs.Save();
            PcGraphicsTiers.RestoreEditorState();
            QualitySettings.SetQualityLevel(m_Level, false);
        }

        /// <summary>What GameBootstrap does on a desktop player without a launch argument: saved tier, else hardware default (not saved).</summary>
        static void BootstrapPick(PcHardwareInfo hw)
        {
            if (QualityTiers.Apply(QualityTiers.SavedTier)) return;
            Assert.IsTrue(PcGraphicsTiers.Apply(PcGraphicsTiers.DefaultFor(hw)));
        }

        [Test]
        public void AutoChoice_HasNoQualityLevel()
        {
            Assert.IsNull(Auto);
            Assert.AreEqual("Low", TierChoices.ToQualityLevel("low"));
            Assert.AreEqual("Ultra", TierChoices.ToQualityLevel("ultra"));
        }

        [Test]
        public void AutoTierName_FollowsHardware_D74()
        {
            Assert.AreEqual("Low", PcTierChoice.AutoTierName(Minimum), "D74 minimum class (GTX 660 2 GB, 8 GB RAM)");
            Assert.AreEqual("High", PcTierChoice.AutoTierName(Recommended), "D74 recommended class");
            Assert.AreEqual("High", PcTierChoice.AutoTierName(Strong), "auto never picks Ultra");
            Assert.AreEqual("Low", PcTierChoice.AutoTierName(new PcHardwareInfo("Intel(R) HD Graphics 630", 0, 8150)), "integrated GPU");
        }

        [Test]
        public void FirstStart_Auto_DoesNotSaveTier_AndKeepsBootstrapPick()
        {
            BootstrapPick(Minimum);
            Assert.AreEqual("Low", QualityTiers.Current);
            Assert.IsFalse(PcTierChoice.ApplyAtStartup(Auto), "auto at startup applies nothing");
            Assert.AreEqual("Low", QualityTiers.Current, "the hardware pick of GameBootstrap is not overridden (was: High)");
            Assert.IsFalse(PlayerPrefs.HasKey(QualityTiers.SavedTierKey), "first start must not write diag.qualityTier");
            Assert.IsFalse(QualityTiers.HasSavedTier);

            // Second start on the same profile: still detected, still not saved.
            BootstrapPick(Minimum);
            PcTierChoice.ApplyAtStartup(Auto);
            Assert.AreEqual("Low", QualityTiers.Current);
            Assert.IsFalse(QualityTiers.HasSavedTier);
        }

        [Test]
        public void FirstStart_Auto_RecommendedHardware_StaysHigh_NotSaved()
        {
            BootstrapPick(Recommended);
            PcTierChoice.ApplyAtStartup(Auto);
            Assert.AreEqual("High", QualityTiers.Current);
            Assert.IsFalse(QualityTiers.HasSavedTier);
        }

        [Test]
        public void ExplicitChoice_IsAppliedAndSaved_AsBefore()
        {
            BootstrapPick(Minimum);
            Assert.IsTrue(PcTierChoice.ApplyFromMenu("Ultra", Minimum));
            Assert.AreEqual("Ultra", QualityTiers.Current);
            Assert.AreEqual("Ultra", QualityTiers.SavedTier);

            // Next start: the saved choice wins over the detection; the file's explicit tier agrees.
            QualityTiers.Apply("Low");
            BootstrapPick(Minimum);
            Assert.AreEqual("Ultra", QualityTiers.Current);
            Assert.IsTrue(PcTierChoice.ApplyAtStartup("Ultra"));
            Assert.AreEqual("Ultra", QualityTiers.Current);
            Assert.AreEqual("Ultra", QualityTiers.SavedTier);
        }

        [Test]
        public void ExplicitChoice_EqualToDetectedTier_IsStillSaved()
        {
            BootstrapPick(Minimum);                       // Low, not saved
            Assert.IsTrue(PcTierChoice.ApplyFromMenu("Low", Minimum));
            Assert.AreEqual("Low", QualityTiers.SavedTier, "an explicit pick is saved also when the level does not change");
        }

        [Test]
        public void ExplicitAtStartup_FromSettingsFile_IsSaved()
        {
            BootstrapPick(Recommended);                   // High by detection
            Assert.IsTrue(PcTierChoice.ApplyAtStartup("Medium"));
            Assert.AreEqual("Medium", QualityTiers.Current);
            Assert.AreEqual("Medium", QualityTiers.SavedTier);
        }

        [Test]
        public void ManualChoice_ThenBackToAuto_DetectionWorksAgain()
        {
            BootstrapPick(Minimum);
            Assert.IsTrue(PcTierChoice.ApplyFromMenu("Ultra", Minimum));
            Assert.IsTrue(QualityTiers.HasSavedTier);

            Assert.IsTrue(PcTierChoice.ApplyFromMenu(Auto, Minimum));
            Assert.AreEqual("Low", QualityTiers.Current, "auto applies the hardware default at once");
            Assert.IsFalse(PlayerPrefs.HasKey(QualityTiers.SavedTierKey), "auto forgets the saved tier");

            // Next start: nothing saved -> GameBootstrap detects again (e.g. after a GPU upgrade).
            Assert.IsFalse(QualityTiers.Apply(QualityTiers.SavedTier), "no saved tier to apply");
            BootstrapPick(Recommended);
            PcTierChoice.ApplyAtStartup(Auto);
            Assert.AreEqual("High", QualityTiers.Current);
            Assert.IsFalse(QualityTiers.HasSavedTier);
        }

        [Test]
        public void BackToAuto_ClearsSavedTier_AlsoWhenLevelDoesNotChange()
        {
            Assert.IsTrue(PcTierChoice.ApplyFromMenu("Low", Minimum));   // explicit Low == what auto would pick
            Assert.IsTrue(QualityTiers.HasSavedTier);
            Assert.IsTrue(PcTierChoice.ApplyFromMenu(Auto, Minimum));
            Assert.AreEqual("Low", QualityTiers.Current);
            Assert.IsFalse(QualityTiers.HasSavedTier, "the saved tier is cleared before the 'already active' shortcut");
        }

        [Test]
        public void ClearSavedTier_DoesNotChangeTheActiveLevel()
        {
            Assert.IsTrue(QualityTiers.Apply("Medium", persist: true));
            QualityTiers.ClearSavedTier();
            Assert.AreEqual("Medium", QualityTiers.Current);
            Assert.IsFalse(QualityTiers.HasSavedTier);
            QualityTiers.ClearSavedTier();   // idempotent
            Assert.IsFalse(QualityTiers.HasSavedTier);
        }
    }
}
