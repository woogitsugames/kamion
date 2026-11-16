using System;
using System.Collections.Generic;
using System.IO;
using Game.Core;
using Game.Core.Settings;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>ADR 0270 PC settings: JSON round trip, atomic save, migrations, out-of-range values, resolution list,
    /// frame pacing mapping, keep / revert countdown. Pure logic (Game.Core), no Unity objects.</summary>
    public class PcSettingsTests
    {
        sealed class DictLegacy : ILegacySettingsSource
        {
            public readonly Dictionary<string, object> Values = new Dictionary<string, object>();
            public bool HasKey(string key) => Values.ContainsKey(key);
            public string GetString(string key) => Values.TryGetValue(key, out var v) ? v as string ?? "" : "";
            public int GetInt(string key) => Values.TryGetValue(key, out var v) && v is int i ? i : 0;
            public float GetFloat(string key) => Values.TryGetValue(key, out var v) && v is float f ? f : 0f;
        }

        string m_Dir;

        [SetUp] public void SetUp()
        {
            m_Dir = Path.Combine(Path.GetTempPath(), "kamion-pcsettings-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(m_Dir);
        }

        [TearDown] public void TearDown()
        {
            try { Directory.Delete(m_Dir, true); } catch (IOException) { }
        }

        static PcSettingsData Custom()
        {
            var d = PcSettingsData.Defaults();
            d.display.width = 2560; d.display.height = 1440; d.display.refreshNumerator = 144000; d.display.refreshDenominator = 1000;
            d.display.mode = WindowModes.Exclusive;
            d.vsync = true; d.fpsCap = 144; d.graphicsTier = "ultra"; d.hudScale = 1.2f;
            d.volumes.master = 0.8f; d.volumes.engine = 0.55f; d.volumes.ambient = 0.3f; d.volumes.ui = 0f;
            return d;
        }

        // ------------------------------------------------------------------ defaults

        [Test]
        public void Defaults_MatchAdr0261DesktopBehaviour()
        {
            var d = PcSettingsData.Defaults();
            Assert.AreEqual(PcSettingsData.CurrentSchemaVersion, d.schemaVersion);
            Assert.AreEqual(60, d.fpsCap, "ADR 0261: desktop 60 fps");
            Assert.IsFalse(d.vsync);
            Assert.AreEqual(TierChoices.Auto, d.graphicsTier);
            Assert.AreEqual(WindowModes.Borderless, d.display.mode, "ProjectSettings fullscreenMode 1 = FullScreenWindow");
            Assert.IsTrue(d.display.UsesNativeResolution);
            Assert.AreEqual(SpeedUnits.Metric, d.speedUnits);
            Assert.AreEqual(1f, d.hudScale);
            Assert.AreEqual(1f, d.volumes.master); Assert.AreEqual(1f, d.volumes.engine);
            Assert.AreEqual(1f, d.volumes.ambient); Assert.AreEqual(1f, d.volumes.ui);
            var fixedFields = new List<string>();
            d.Sanitize(fixedFields);
            Assert.IsEmpty(fixedFields, "defaults are valid");
        }

        // ------------------------------------------------------------------ round trip

        [Test]
        public void Json_RoundTrip_KeepsEveryField()
        {
            var a = Custom();
            var report = new PcSettingsLoadReport();
            var b = PcSettingsJson.TryParse(PcSettingsJson.ToJson(a), report);
            Assert.IsNotNull(b);
            Assert.IsTrue(a.SameAs(b));
            Assert.AreEqual(144000, b.display.refreshNumerator);
            Assert.IsFalse(report.Migrated);
            Assert.IsEmpty(report.FixedFields);
        }

        [Test]
        public void Store_SaveLoad_RoundTrip_AndAtomicFiles()
        {
            var store = new PcSettingsStore(m_Dir);
            store.Save(Custom());
            Assert.IsTrue(File.Exists(store.FilePath));
            Assert.IsFalse(File.Exists(store.TempPath), "no .tmp left behind");
            var loaded = store.Load(out var report);
            Assert.AreEqual(PcSettingsLoadReport.Origin.File, report.Source);
            Assert.IsTrue(Custom().SameAs(loaded));

            var second = Custom(); second.fpsCap = 30;
            store.Save(second);
            Assert.IsTrue(File.Exists(store.BackupPath), "previous version kept as .bak");
            Assert.AreEqual(30, store.Load(out _).fpsCap);
            Assert.AreEqual(144, PcSettingsJson.TryParse(File.ReadAllText(store.BackupPath), null).fpsCap);
        }

        [Test]
        public void Store_CorruptFile_FallsBackToBackup_AndKeepsBadCopy()
        {
            var store = new PcSettingsStore(m_Dir);
            store.Save(Custom());
            var newer = Custom(); newer.fpsCap = 75;
            store.Save(newer);                                   // .bak = Custom (144)
            File.WriteAllText(store.FilePath, "{ \"schemaVersion\": 1, \"fpsCap\": ");   // half-written file
            var loaded = store.Load(out var report);
            Assert.IsTrue(report.Corrupt);
            Assert.AreEqual(PcSettingsLoadReport.Origin.Backup, report.Source);
            Assert.AreEqual(144, loaded.fpsCap);
            Assert.IsTrue(File.Exists(store.CorruptPath), "unreadable file kept as .bad");
        }

        [Test]
        public void Store_CorruptFile_NoBackup_NoLegacy_GivesDefaults()
        {
            var store = new PcSettingsStore(m_Dir);
            File.WriteAllText(store.FilePath, "not json at all");
            var loaded = store.Load(out var report);
            Assert.AreEqual(PcSettingsLoadReport.Origin.Defaults, report.Source);
            Assert.IsTrue(loaded.SameAs(PcSettingsData.Defaults()));
        }

        [Test]
        public void Store_Save_SanitizesWhatItWrites()
        {
            var store = new PcSettingsStore(m_Dir);
            var bad = Custom(); bad.volumes.master = 7f; bad.fpsCap = 59;
            store.Save(bad);
            var loaded = store.Load(out var report);
            Assert.AreEqual(1f, loaded.volumes.master);
            Assert.AreEqual(PcSettingsData.DefaultFpsCap, loaded.fpsCap);
            Assert.IsEmpty(report.FixedFields, "the file on disk is already clean");
        }

        // ------------------------------------------------------------------ migration

        [Test]
        public void Migration_FromLegacyPlayerPrefs()
        {
            var legacy = new DictLegacy();
            legacy.Values[PcSettingsJson.LegacyTierKey] = "Medium";
            legacy.Values[PcSettingsJson.LegacyFpsKey] = 30;
            legacy.Values[PcSettingsJson.HudScaleKey] = 1.3f;
            var store = new PcSettingsStore(m_Dir, legacy);
            var d = store.Load(out var report);
            Assert.AreEqual(PcSettingsLoadReport.Origin.Legacy, report.Source);
            Assert.IsTrue(report.Migrated);
            Assert.AreEqual(0, report.FileSchemaVersion);
            Assert.AreEqual("medium", d.graphicsTier);
            Assert.AreEqual(30, d.fpsCap);
            Assert.AreEqual(1.3f, d.hudScale, 1e-5f);
            Assert.AreEqual(PcSettingsData.CurrentSchemaVersion, d.schemaVersion);
        }

        [Test]
        public void Migration_FromLegacy_InvalidValuesBecomeDefaults()
        {
            var legacy = new DictLegacy();
            legacy.Values[PcSettingsJson.LegacyTierKey] = "Epic";
            legacy.Values[PcSettingsJson.LegacyFpsKey] = 50;          // not an offered cap
            legacy.Values[PcSettingsJson.HudScaleKey] = 9f;
            var d = new PcSettingsStore(m_Dir, legacy).Load(out var report);
            Assert.AreEqual(TierChoices.Auto, d.graphicsTier);
            Assert.AreEqual(PcSettingsData.DefaultFpsCap, d.fpsCap);
            Assert.AreEqual(1f, d.hudScale);
            CollectionAssert.Contains(report.FixedFields, "hudScale");
        }

        [Test]
        public void Migration_FileWinsOverLegacy()
        {
            var legacy = new DictLegacy();
            legacy.Values[PcSettingsJson.LegacyFpsKey] = 30;
            var store = new PcSettingsStore(m_Dir, legacy);
            store.Save(Custom());
            Assert.AreEqual(144, store.Load(out var report).fpsCap);
            Assert.AreEqual(PcSettingsLoadReport.Origin.File, report.Source);
        }

        [Test]
        public void Migration_SchemaZero_MissingFieldsKeepDefaults()
        {
            // Pre-release file: no schemaVersion, no volumes block, no hudScale.
            const string json = "{ \"display\": { \"width\": 1920, \"height\": 1080, \"refreshNumerator\": 60, \"refreshDenominator\": 1, \"mode\": \"windowed\" }, \"vsync\": true, \"fpsCap\": 120 }";
            var report = new PcSettingsLoadReport();
            var d = PcSettingsJson.TryParse(json, report);
            Assert.IsNotNull(d);
            Assert.IsTrue(report.Migrated);
            Assert.AreEqual(0, report.FileSchemaVersion);
            Assert.AreEqual(PcSettingsData.CurrentSchemaVersion, d.schemaVersion);
            Assert.AreEqual(1920, d.display.width);
            Assert.AreEqual(WindowModes.Windowed, d.display.mode);
            Assert.IsTrue(d.vsync);
            Assert.AreEqual(120, d.fpsCap);
            Assert.AreEqual(1f, d.volumes.master);
            Assert.AreEqual(1f, d.hudScale);
            Assert.AreEqual(TierChoices.Auto, d.graphicsTier);
        }

        [Test]
        public void Migration_NewerSchema_ReadsKnownFields_AndSaysSo()
        {
            const string json = "{ \"schemaVersion\": 99, \"fpsCap\": 75, \"futureField\": 3 }";
            var report = new PcSettingsLoadReport();
            var d = PcSettingsJson.TryParse(json, report);
            Assert.IsNotNull(d);
            Assert.IsTrue(report.FromNewerVersion);
            Assert.IsFalse(report.Migrated);
            Assert.AreEqual(75, d.fpsCap);
            Assert.AreEqual(PcSettingsData.CurrentSchemaVersion, d.schemaVersion);
        }

        [Test]
        public void Parse_RejectsNonObjects()
        {
            Assert.IsNull(PcSettingsJson.TryParse(null, null));
            Assert.IsNull(PcSettingsJson.TryParse("   ", null));
            Assert.IsNull(PcSettingsJson.TryParse("[1,2]", null));
            Assert.IsNull(PcSettingsJson.TryParse("{ broken", null));
        }

        // ------------------------------------------------------------------ out of range -> defaults

        [Test]
        public void Sanitize_OutOfRange_BecomesDefault()
        {
            var d = Custom();
            d.display.width = 10; d.display.height = 10;
            d.display.mode = "fullscreen";
            d.fpsCap = 77; d.graphicsTier = "epic"; d.hudScale = 3f; d.speedUnits = "knots";
            d.volumes.master = 1.5f; d.volumes.engine = -0.1f; d.volumes.ambient = float.NaN; d.volumes.ui = float.PositiveInfinity;
            var fixedFields = new List<string>();
            d.Sanitize(fixedFields);
            var def = PcSettingsData.Defaults();
            Assert.IsTrue(d.display.UsesNativeResolution);
            Assert.AreEqual(0, d.display.refreshNumerator, "size reset also drops the refresh of that size");
            Assert.AreEqual(def.display.mode, d.display.mode);
            Assert.AreEqual(def.fpsCap, d.fpsCap);
            Assert.AreEqual(def.graphicsTier, d.graphicsTier);
            Assert.AreEqual(def.hudScale, d.hudScale);
            Assert.AreEqual(def.speedUnits, d.speedUnits);
            Assert.AreEqual(1f, d.volumes.master); Assert.AreEqual(1f, d.volumes.engine);
            Assert.AreEqual(1f, d.volumes.ambient); Assert.AreEqual(1f, d.volumes.ui);
            Assert.IsTrue(d.vsync, "valid fields stay");
            CollectionAssert.IsSubsetOf(new[] { "display.size", "display.mode", "fpsCap", "graphicsTier", "hudScale", "speedUnits",
                "volumes.master", "volumes.engine", "volumes.ambient", "volumes.ui" }, fixedFields);
        }

        [Test]
        public void Sanitize_BoundsAreInside_AndBadRefreshIsDropped()
        {
            var d = PcSettingsData.Defaults();
            d.hudScale = PcSettingsData.HudScaleMin; d.volumes.master = 0f; d.volumes.ui = 1f;
            d.display.width = 1280; d.display.height = 720; d.display.refreshNumerator = 5; d.display.refreshDenominator = 1;   // 5 Hz
            var fixedFields = new List<string>();
            d.Sanitize(fixedFields);
            Assert.AreEqual(PcSettingsData.HudScaleMin, d.hudScale);
            Assert.AreEqual(0f, d.volumes.master, "0 % is a valid choice");
            Assert.AreEqual(1280, d.display.width);
            Assert.AreEqual(0, d.display.refreshDenominator);
            CollectionAssert.AreEqual(new[] { "display.refresh" }, fixedFields);
        }

        [Test]
        public void Sanitize_NullBlocks_AreRebuilt()
        {
            var d = PcSettingsData.Defaults();
            d.display = null; d.volumes = null;
            d.Sanitize();
            Assert.IsNotNull(d.display); Assert.IsNotNull(d.volumes);
        }

        [Test]
        public void Step_ClampsAndDoesNotDrift()
        {
            float v = 1f;
            for (int i = 0; i < 40; i++) v = PcSettingsData.Step(v, -1, PcSettingsData.VolumeStep, 0f, 1f);
            Assert.AreEqual(0f, v);
            for (int i = 0; i < 7; i++) v = PcSettingsData.Step(v, +1, PcSettingsData.VolumeStep, 0f, 1f);
            Assert.AreEqual(0.35f, v, 1e-6f);
            Assert.AreEqual(PcSettingsData.HudScaleMax, PcSettingsData.Step(1.4f, +1, 0.1f, PcSettingsData.HudScaleMin, PcSettingsData.HudScaleMax));
            Assert.AreEqual(0, PcSettingsData.StepIndex(0, -1, 6));
            Assert.AreEqual(5, PcSettingsData.StepIndex(5, +1, 6));
            Assert.AreEqual(-1, PcSettingsData.StepIndex(0, 1, 0));
        }

        [Test]
        public void TierChoices_MapToQualityLevels()
        {
            Assert.AreEqual("high", TierChoices.FromQualityLevel("High"));
            Assert.AreEqual("low", TierChoices.FromQualityLevel("LOW"));
            Assert.IsNull(TierChoices.FromQualityLevel("Epic"));
            Assert.AreEqual("Ultra", TierChoices.ToQualityLevel("ultra"));
            Assert.IsNull(TierChoices.ToQualityLevel(TierChoices.Auto));
        }

        // ------------------------------------------------------------------ resolutions

        static DisplayMode M(int w, int h, uint n, uint d = 1) => new DisplayMode(w, h, n, d);

        [Test]
        public void Resolutions_Deduplicated_Filtered_Sorted()
        {
            var raw = new[]
            {
                M(1920, 1080, 60), M(1280, 720, 60), M(1920, 1080, 60000, 1000), M(1920, 1080, 144),
                M(1920, 1080, 6000, 100), M(0, 0, 60), M(1280, 720, 60), M(1920, 1080, 60000, 1001), M(1600, 900, 60),
            };
            var list = ResolutionList.Build(raw);
            Assert.AreEqual(5, list.Count);
            Assert.AreEqual(M(1280, 720, 60), list[0]);
            Assert.AreEqual(M(1600, 900, 60), list[1]);
            Assert.AreEqual(5994, list[2].RefreshCentiHz, "59.94 Hz kept apart from 60 Hz");
            Assert.AreEqual(6000, list[3].RefreshCentiHz);
            Assert.AreEqual(14400, list[4].RefreshCentiHz);
            Assert.IsEmpty(ResolutionList.Build(null));
        }

        [Test]
        public void Resolutions_IndexOf_ExactNearestRefreshAndFallback()
        {
            var list = ResolutionList.Build(new[] { M(1280, 720, 60), M(1920, 1080, 60), M(1920, 1080, 144), M(2560, 1440, 165) });
            Assert.AreEqual(2, ResolutionList.IndexOf(list, 1920, 1080, 144.0));
            Assert.AreEqual(1, ResolutionList.IndexOf(list, 1920, 1080, 59.94), "closest refresh of the same size");
            Assert.AreEqual(2, ResolutionList.IndexOf(list, 1920, 1080, 0.0), "unknown refresh: the highest");
            Assert.AreEqual(3, ResolutionList.IndexOf(list, 2560, 1600, 60.0), "size gone (monitor swap): closest pixel count");
            Assert.AreEqual(-1, ResolutionList.IndexOf(new List<DisplayMode>(), 1920, 1080, 60.0));
        }

        [Test]
        public void Resolutions_Label_PolishDecimalComma()
        {
            Assert.AreEqual("1920 × 1080 · 60 Hz", M(1920, 1080, 60).Label());
            Assert.AreEqual("1920 × 1080 · 59,94 Hz", M(1920, 1080, 60000, 1001).Label());
            Assert.AreEqual("800 × 600", M(800, 600, 0, 0).Label());
        }

        // ------------------------------------------------------------------ frame pacing

        [Test]
        public void FramePacing_MapsCapAndVsync()
        {
            FramePacing.Map(false, 60, out int vs, out int fps);
            Assert.AreEqual(0, vs); Assert.AreEqual(60, fps);
            FramePacing.Map(false, 144, out vs, out fps);
            Assert.AreEqual(0, vs); Assert.AreEqual(144, fps);
            FramePacing.Map(false, 0, out vs, out fps);
            Assert.AreEqual(0, vs); Assert.AreEqual(-1, fps, "no cap");
            FramePacing.Map(true, 30, out vs, out fps);
            Assert.AreEqual(1, vs); Assert.AreEqual(-1, fps, "vsync: Unity ignores targetFrameRate on desktop");
            foreach (int cap in PcSettingsData.FpsCaps)
            {
                FramePacing.Map(false, cap, out vs, out fps);
                FramePacing.FromRuntime(vs, fps, 60, out bool backVsync, out int backCap);
                Assert.IsFalse(backVsync); Assert.AreEqual(cap, backCap, "round trip cap " + cap);
            }
        }

        [Test]
        public void FramePacing_FromRuntime_UnknownRateKeepsFallback()
        {
            FramePacing.FromRuntime(0, 50, 120, out bool vsync, out int cap);
            Assert.IsFalse(vsync); Assert.AreEqual(120, cap);
            FramePacing.FromRuntime(1, -1, 75, out vsync, out cap);
            Assert.IsTrue(vsync); Assert.AreEqual(75, cap, "vsync keeps the stored cap for when it is switched off");
        }

        [Test]
        public void FpsCaps_ContainAdr0270List()
        {
            CollectionAssert.AreEqual(new[] { 30, 60, 75, 120, 144, 0 }, PcSettingsData.FpsCaps);
        }

        // ------------------------------------------------------------------ keep / revert countdown

        [Test]
        public void ConfirmTimer_ExpiresOnce_AndReverts()
        {
            var t = new DisplayConfirmTimer();
            Assert.IsFalse(t.Tick(1f), "idle does nothing");
            t.Start(15f);
            Assert.AreEqual(15, t.SecondsLeft);
            Assert.IsFalse(t.Tick(14.2f));
            Assert.AreEqual(1, t.SecondsLeft);
            Assert.IsTrue(t.Tick(1f));
            Assert.AreEqual(DisplayConfirmTimer.State.Reverted, t.Current);
            Assert.IsFalse(t.Tick(1f), "fires exactly once");
        }

        [Test]
        public void ConfirmTimer_KeepStopsTheCountdown()
        {
            var t = new DisplayConfirmTimer();
            t.Start();
            Assert.AreEqual(DisplayConfirmTimer.DefaultSeconds, t.Seconds);
            t.Tick(3f);
            t.Keep();
            Assert.AreEqual(DisplayConfirmTimer.State.Kept, t.Current);
            Assert.IsFalse(t.Tick(100f));
            t.Start(0f);
            Assert.AreEqual(DisplayConfirmTimer.DefaultSeconds, t.Seconds, "non-positive duration falls back");
            t.Revert();
            Assert.AreEqual(DisplayConfirmTimer.State.Reverted, t.Current);
        }

        // ------------------------------------------------------------------ startup display policy

        [Test]
        public void StartupDisplay_OnlyFromFile_AndNotAgainstWindowArguments()
        {
            Assert.IsFalse(StartupDisplayPolicy.ShouldApply(false, new[] { "Kamion.exe" }), "first launch keeps ProjectSettings");
            Assert.IsTrue(StartupDisplayPolicy.ShouldApply(true, new[] { "Kamion.exe", "-scene", "knyszyn-w" }));
            Assert.IsFalse(StartupDisplayPolicy.ShouldApply(true, new[] { "Kamion.exe", "-screen-fullscreen", "0", "-screen-width", "1600" }),
                "build-windows.ps1 evidence window (ADR 0261)");
            Assert.IsFalse(StartupDisplayPolicy.ShouldApply(true, new[] { "Kamion.exe", "-popupwindow" }));
            Assert.IsTrue(StartupDisplayPolicy.ShouldApply(true, null));
        }

        // ------------------------------------------------------------------ audio levels

        [Test]
        public void AudioMixLevels_ClampAndVersion()
        {
            AudioMixLevels.Set(1f, 1f, 1f, 1f);
            int v0 = AudioMixLevels.Version;
            AudioMixLevels.Set(1f, 1f, 1f, 1f);
            Assert.AreEqual(v0, AudioMixLevels.Version, "no change, no version bump");
            AudioMixLevels.Set(2f, 0.5f, -1f, 0.25f);
            Assert.AreEqual(v0 + 1, AudioMixLevels.Version);
            Assert.AreEqual(1f, AudioMixLevels.Master); Assert.AreEqual(0.5f, AudioMixLevels.Engine);
            Assert.AreEqual(0f, AudioMixLevels.Ambient); Assert.AreEqual(0.25f, AudioMixLevels.Ui);
            AudioMixLevels.Set(1f, 1f, 1f, 1f);   // leave the process-wide levels as found
        }
    }
}
