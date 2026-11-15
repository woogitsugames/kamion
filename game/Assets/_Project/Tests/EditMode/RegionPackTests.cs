using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Game.Editor.Build;
using Game.World.Packs;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>Region packs (ADR 0234): manifest parsing, sha256/version checks, state resolution, install, paths, bundle plan.</summary>
    public class RegionPackTests
    {
        const string Unity = "6000.3.28f1";
        static readonly RegionPackAppIdentity App = new RegionPackAppIdentity(500, Unity, "Android");

        // ------------------------------------------------------------------ helpers

        static RegionPackEntry Entry(string id, string region, string tier, byte[] bytes, params string[] deps) => new RegionPackEntry
        {
            id = id, region = region, tier = tier, file = id + ".bundle",
            sizeBytes = bytes.Length, sha256 = RegionPackHash.Sha256Bytes(bytes),
            scenes = string.IsNullOrEmpty(tier) ? Array.Empty<string>() : new[] { "World_" + region + (tier == "High" ? "_High" : "") },
            dependencies = deps,
        };

        static readonly byte[] CommonBytes = Encoding.ASCII.GetBytes("common-bundle-bytes");
        static readonly byte[] DkBytes = Encoding.ASCII.GetBytes("dk65-06 low bundle bytes");
        static readonly byte[] DkHighBytes = Encoding.ASCII.GetBytes("dk65-06 HIGH bundle bytes, longer");

        static RegionPackManifest Set(string version = "0.1.0-abc1234567", int min = 400, int max = 0) => new RegionPackManifest
        {
            schema = RegionPackManifest.SchemaId, packSetVersion = version, unityVersion = Unity, buildTarget = "Android",
            minAppVersionCode = min, maxAppVersionCode = max, gitSha = "abc1234567", createdUtc = "2026-11-15T12:00:00Z",
            packs = new[]
            {
                Entry("common", "", "", CommonBytes),
                Entry("dk65-06", "dk65-06", "Low", DkBytes, "common"),
                Entry("dk65-06-high", "dk65-06", "High", DkHighBytes, "common"),
            },
        };

        /// <summary>In-memory files: path → bytes.</summary>
        sealed class FakeFiles : IRegionPackFiles
        {
            public readonly Dictionary<string, byte[]> Files = new Dictionary<string, byte[]>();
            public int Hashes;
            public long Size(string path) => path != null && Files.TryGetValue(path, out var b) ? b.Length : -1;
            public string Sha256(string path) { Hashes++; return RegionPackHash.Sha256Bytes(Files[path]); }
        }

        static readonly RegionPackPaths FakePaths = new RegionPackPaths("/data/kamion");

        static FakeFiles Installed(params (string file, byte[] bytes)[] files)
        {
            var f = new FakeFiles();
            foreach (var (file, bytes) in files) f.Files[FakePaths.Installed(file)] = bytes;
            return f;
        }

        // ------------------------------------------------------------------ manifest

        [Test]
        public void Manifest_RoundTripsThroughJsonUtility()
        {
            string json = JsonUtility.ToJson(Set(), true);
            Assert.IsTrue(RegionPackManifest.TryParse(json, out var m, out string err), err);
            Assert.AreEqual("0.1.0-abc1234567", m.packSetVersion);
            Assert.AreEqual(3, m.packs.Length);
            Assert.AreEqual("dk65-06-high", m.FindRegion("dk65-06", "High").id);
            Assert.AreEqual("dk65-06", m.FindRegion("dk65-06", "Low").id);
            Assert.AreEqual("dk65-06", m.FindRegion("dk65-06", null).id, "empty tier = Low");
            Assert.IsNull(m.FindRegion("knyszyn", "Low"));
            Assert.IsNull(m.FindRegion("", "Low"), "common is not a scene pack");
            Assert.AreEqual(CommonBytes.Length + DkBytes.Length, m.SizeWithDependencies(m.Find("dk65-06")));
        }

        [Test]
        public void Manifest_ParsesHandWrittenJson()
        {
            string sha = new string('a', 64);
            string json = "{\"schema\":\"truck-sim-pl/region-packs/1\",\"packSetVersion\":\"0.1.0-x\",\"unityVersion\":\"" + Unity +
                          "\",\"buildTarget\":\"Android\",\"minAppVersionCode\":1,\"packs\":[" +
                          "{\"id\":\"common\",\"file\":\"common.bundle\",\"sizeBytes\":10,\"sha256\":\"" + sha + "\"}," +
                          "{\"id\":\"knyszyn\",\"region\":\"knyszyn\",\"tier\":\"Low\",\"file\":\"knyszyn.bundle\",\"sizeBytes\":20,\"sha256\":\"" + sha +
                          "\",\"crc\":4294967295,\"scenes\":[\"World_knyszyn\"],\"dependencies\":[\"common\"]}]}";
            Assert.IsTrue(RegionPackManifest.TryParse(json, out var m, out string err), err);
            Assert.AreEqual(0, m.maxAppVersionCode, "missing field keeps the default");
            Assert.AreEqual(uint.MaxValue, m.Find("knyszyn").crc);
            Assert.AreEqual(0, m.Find("common").dependencies.Length);
        }

        [TestCase(null, "empty")]
        [TestCase("not json", "JSON")]
        [TestCase("{\"schema\":\"other/1\"}", "schema")]
        public void Manifest_RejectsGarbage(string json, string expected)
        {
            Assert.IsFalse(RegionPackManifest.TryParse(json, out var m, out string err));
            Assert.IsNull(m);
            StringAssert.Contains(expected, err);
        }

        static void AssertInvalid(Action<RegionPackManifest> breakIt, string expected)
        {
            var m = Set();
            breakIt(m);
            Assert.IsFalse(RegionPackManifest.Validate(m, out string err), "expected: " + expected);
            StringAssert.Contains(expected, err);
        }

        [Test]
        public void Manifest_ValidationCatchesBrokenEntries()
        {
            AssertInvalid(m => m.packs[1].sha256 = "ABC", "sha256");
            AssertInvalid(m => m.packs[1].sha256 = new string('A', 64), "sha256");   // uppercase not accepted
            AssertInvalid(m => m.packs[1].sizeBytes = 0, "sizeBytes");
            AssertInvalid(m => m.packs[1].file = "../evil.bundle", "file name");
            AssertInvalid(m => m.packs[1].file = "dk65-06.zip", "file name");
            AssertInvalid(m => m.packs[2].file = "dk65-06.bundle", "listed twice");
            AssertInvalid(m => m.packs[2].id = "dk65-06", "duplicate");
            AssertInvalid(m => m.packs[1].dependencies = new[] { "nope" }, "unknown dependency");
            AssertInvalid(m => m.packs[1].dependencies = new[] { "dk65-06" }, "itself");
            AssertInvalid(m => m.packs[1].dependencies = new[] { "dk65-06-high" }, "scene pack");
            AssertInvalid(m => m.packs[1].tier = "Medium", "tier");
            AssertInvalid(m => m.packs[1].region = "", "without region");
            AssertInvalid(m => m.packs[0].dependencies = new[] { "dk65-06" }, "scene pack");
            AssertInvalid(m => m.unityVersion = "", "unityVersion");
            AssertInvalid(m => m.packSetVersion = "", "packSetVersion");
            AssertInvalid(m => { m.minAppVersionCode = 10; m.maxAppVersionCode = 5; }, "range");
            AssertInvalid(m => m.packs = new RegionPackEntry[0], "no packs");
        }

        [Test]
        public void Manifest_RegionDataChain_MustBeClosedAndLoadsCommonFirst()
        {
            var m = Set();
            var data = Encoding.ASCII.GetBytes("dk65-06 data: collision + instances");
            m.packs = new[]
            {
                m.packs[0],
                Entry("dk65-06-data", "dk65-06", "", data, "common"),
                Entry("dk65-06", "dk65-06", "Low", DkBytes, "dk65-06-data", "common"),
                Entry("dk65-06-high", "dk65-06", "High", DkHighBytes, "common", "dk65-06-data"),
            };
            m.packs[1].region = "dk65-06";
            Assert.IsTrue(RegionPackManifest.Validate(m, out string err), err);
            Assert.IsFalse(m.Find("dk65-06-data").IsScenePack, "data pack is not a scene pack");
            Assert.AreEqual("dk65-06", m.FindRegion("dk65-06", "Low").id);
            var order = m.LoadOrder(m.Find("dk65-06"));
            Assert.AreEqual("common", order[0].id);
            Assert.AreEqual("dk65-06-data", order[1].id);
            Assert.AreEqual(CommonBytes.Length + data.Length + DkBytes.Length, m.SizeWithDependencies(m.Find("dk65-06")));

            m.packs[2].dependencies = new[] { "dk65-06-data" };   // misses common, which the data pack needs
            Assert.IsFalse(RegionPackManifest.Validate(m, out err));
            StringAssert.Contains("not closed", err);
            m.packs[2].dependencies = new[] { "dk65-06-data", "common" };
            m.packs[0].dependencies = new[] { "dk65-06-data" };      // cycle common <-> data
            Assert.IsFalse(RegionPackManifest.Validate(m, out err));
        }

        // ------------------------------------------------------------------ hash + paths

        [Test]
        public void Sha256_KnownVectorAndFileMatchBytes()
        {
            Assert.AreEqual("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", RegionPackHash.Sha256Bytes(Encoding.ASCII.GetBytes("abc")));
            string tmp = Path.Combine(Path.GetTempPath(), "rp-hash-" + Guid.NewGuid().ToString("N"));
            try
            {
                var big = new byte[3 * 1024 * 1024 + 17];   // crosses the 1 MB read buffer
                for (int i = 0; i < big.Length; i++) big[i] = (byte)(i * 31);
                File.WriteAllBytes(tmp, big);
                Assert.AreEqual(RegionPackHash.Sha256Bytes(big), RegionPackHash.Sha256File(tmp));
            }
            finally { File.Delete(tmp); }
            Assert.IsTrue(RegionPackHash.IsSha256Hex(new string('0', 64)));
            Assert.IsFalse(RegionPackHash.IsSha256Hex(new string('g', 64)));
            Assert.IsFalse(RegionPackHash.IsSha256Hex(null));
        }

        [TestCase("dk65-06.bundle", true)]
        [TestCase("bialystok-dojlidy-high.bundle", true)]
        [TestCase("common.bundle", true)]
        [TestCase("0.1.0-abc.bundle", true)]
        [TestCase("../common.bundle", false)]
        [TestCase("a/b.bundle", false)]
        [TestCase("a\\b.bundle", false)]
        [TestCase("Common.bundle", false)]
        [TestCase(".hidden.bundle", false)]
        [TestCase("x..y.bundle", false)]
        [TestCase("dk65-06.bundle.part", false)]
        [TestCase(".bundle", false)]
        [TestCase("", false)]
        [TestCase(null, false)]
        public void Paths_BundleFileNamesAreSanitised(string file, bool ok)
        {
            Assert.AreEqual(ok, RegionPackPaths.IsSafeBundleFileName(file));
            Assert.AreEqual(ok, FakePaths.Installed(file) != null);
        }

        [Test]
        public void Paths_LayoutUnderPersistentDataPath()
        {
            var p = new RegionPackPaths("/root");
            Assert.AreEqual(Path.Combine("/root", "regionpacks"), p.Root);
            Assert.AreEqual(Path.Combine("/root", "regionpacks", "incoming"), p.Incoming);
            Assert.AreEqual(Path.Combine(p.Root, "regionpacks.json"), p.InstalledManifest);
            Assert.AreEqual(Path.Combine(p.Incoming, "regionpacks.json"), p.IncomingManifest);
            Assert.AreEqual(Path.Combine(p.Incoming, "a.bundle.part"), p.IncomingPart("a.bundle"));
            Assert.AreEqual("https://h/p/a.bundle", RegionPackPaths.Url("https://h/p", "a.bundle"));
            Assert.AreEqual("https://h/p/a.bundle", RegionPackPaths.Url(" https://h/p/ ", "a.bundle"));
            Assert.IsNull(RegionPackPaths.Url("", "a.bundle"), "no URL configured = no download");
            Assert.IsNull(RegionPackPaths.Url(null, "a.bundle"));
        }

        // ------------------------------------------------------------------ compatibility

        [Test]
        public void Compatibility_UnityVersionTargetAndAppRange()
        {
            Assert.IsNull(RegionPackResolver.CompatibilityProblem(Set(), App));
            StringAssert.Contains("Unity", RegionPackResolver.CompatibilityProblem(Set(), new RegionPackAppIdentity(500, "6000.3.29f1", "Android")));
            StringAssert.Contains("built for", RegionPackResolver.CompatibilityProblem(Set(), new RegionPackAppIdentity(500, Unity, "IPhonePlayer")));
            StringAssert.Contains(">= 400", RegionPackResolver.CompatibilityProblem(Set(), new RegionPackAppIdentity(399, Unity, "Android")));
            Assert.IsNull(RegionPackResolver.CompatibilityProblem(Set(), new RegionPackAppIdentity(400, Unity, "Android")), "min is inclusive");
            StringAssert.Contains("<= 450", RegionPackResolver.CompatibilityProblem(Set(max: 450), App));
            Assert.IsNull(RegionPackResolver.CompatibilityProblem(Set(max: 500), App), "max is inclusive");
            Assert.IsNotNull(RegionPackResolver.CompatibilityProblem(null, App));
        }

        // ------------------------------------------------------------------ state resolution

        static RegionPackInfo Resolve(RegionPackManifest m, FakeFiles f, bool deep, string tier = "Low", RegionPackAppIdentity? app = null) =>
            RegionPackResolver.Resolve(m, "dk65-06", tier, app ?? App, FakePaths, f, deep);

        [Test]
        public void Resolve_NoSet_IsNotInstalled()
        {
            Assert.AreEqual(RegionPackState.NotInstalled, Resolve(null, new FakeFiles(), false).State);
        }

        [Test]
        public void Resolve_RegionMissingFromSet_IsNotInstalled()
        {
            var info = RegionPackResolver.Resolve(Set(), "knyszyn", "Low", App, FakePaths, new FakeFiles(), false);
            Assert.AreEqual(RegionPackState.NotInstalled, info.State);
            Assert.AreEqual(0, info.SizeBytes);
        }

        [Test]
        public void Resolve_FilesMissing_IsNotInstalledWithBytesToFetch()
        {
            var info = Resolve(Set(), new FakeFiles(), false);
            Assert.AreEqual(RegionPackState.NotInstalled, info.State);
            Assert.AreEqual(CommonBytes.Length + DkBytes.Length, info.SizeBytes);
            var withCommon = Resolve(Set(), Installed(("common.bundle", CommonBytes)), false);
            Assert.AreEqual(DkBytes.Length, withCommon.SizeBytes, "common already installed is not fetched again");
        }

        [Test]
        public void Resolve_AllIntact_IsInstalled_ShallowDoesNotHash()
        {
            var f = Installed(("common.bundle", CommonBytes), ("dk65-06.bundle", DkBytes));
            var info = Resolve(Set(), f, false);
            Assert.AreEqual(RegionPackState.Installed, info.State, info.ToString());
            Assert.IsTrue(info.CanStart);
            Assert.AreEqual(0, f.Hashes, "the menu check reads sizes only");
            Assert.AreEqual(RegionPackState.Installed, Resolve(Set(), f, true).State);
            Assert.AreEqual(2, f.Hashes, "deep check hashes the pack and its dependency");
        }

        [Test]
        public void Resolve_SizeMismatch_IsCorrupt()
        {
            var f = Installed(("common.bundle", CommonBytes), ("dk65-06.bundle", new byte[3]));
            var info = Resolve(Set(), f, false);
            Assert.AreEqual(RegionPackState.Corrupt, info.State);
            Assert.IsFalse(info.CanStart);
        }

        [Test]
        public void Resolve_SameSizeOtherBytes_IsCorruptOnlyWhenDeep()
        {
            var tampered = (byte[])DkBytes.Clone();
            tampered[0] ^= 0xFF;
            var f = Installed(("common.bundle", CommonBytes), ("dk65-06.bundle", tampered));
            Assert.AreEqual(RegionPackState.Installed, Resolve(Set(), f, false).State, "shallow check cannot see it");
            Assert.AreEqual(RegionPackState.Corrupt, Resolve(Set(), f, true).State, "the check before loading does");
        }

        [Test]
        public void Resolve_CommonMissingOrBroken_IsMissingDependency()
        {
            var noCommon = Resolve(Set(), Installed(("dk65-06.bundle", DkBytes)), false);
            Assert.AreEqual(RegionPackState.MissingDependency, noCommon.State);
            StringAssert.Contains("common", noCommon.Reason);
            Assert.AreEqual(CommonBytes.Length, noCommon.SizeBytes);
            var badCommon = (byte[])CommonBytes.Clone();
            badCommon[1] ^= 1;
            var deep = Resolve(Set(), Installed(("common.bundle", badCommon), ("dk65-06.bundle", DkBytes)), true);
            Assert.AreEqual(RegionPackState.MissingDependency, deep.State);
            StringAssert.Contains("corrupt", deep.Reason);
        }

        [Test]
        public void Resolve_IncompatibleSet_WinsOverFiles()
        {
            var f = Installed(("common.bundle", CommonBytes), ("dk65-06.bundle", DkBytes));
            var old = Resolve(Set(), f, false, app: new RegionPackAppIdentity(100, Unity, "Android"));
            Assert.AreEqual(RegionPackState.Incompatible, old.State);
            Assert.IsFalse(old.CanStart);
            Assert.AreEqual(RegionPackState.Incompatible, Resolve(Set(), f, false, app: new RegionPackAppIdentity(500, "6000.4.0f1", "Android")).State);
        }

        [Test]
        public void Resolve_HighTierIsSeparatePack()
        {
            var f = Installed(("common.bundle", CommonBytes), ("dk65-06.bundle", DkBytes));
            Assert.AreEqual(RegionPackState.NotInstalled, Resolve(Set(), f, false, "High").State);
            Assert.AreEqual("High", RegionPackResolver.PreferredTier("Ultra", true));
            Assert.AreEqual("Low", RegionPackResolver.PreferredTier("High", false));
            Assert.AreEqual("Low", RegionPackResolver.PreferredTier("Medium", true));
        }

        // ------------------------------------------------------------------ labels

        [Test]
        public void Labels_PolishTextsPerState()
        {
            long mb52 = 52L * 1048576 + 314573;   // 52.3 MB
            Assert.AreEqual("52 MB", RegionPackLabels.Megabytes(mb52));
            Assert.AreEqual("3,5 MB", RegionPackLabels.Megabytes(3670016));
            Assert.AreEqual("w APK", RegionPackLabels.Detail(new RegionPackInfo(RegionPackState.InBase, "", 0), false));
            Assert.AreEqual("paczka pobrana · 52 MB", RegionPackLabels.Detail(new RegionPackInfo(RegionPackState.Installed, "", mb52), false));
            Assert.AreEqual("do pobrania · 52 MB", RegionPackLabels.Detail(new RegionPackInfo(RegionPackState.NotInstalled, "", mb52), true));
            Assert.AreEqual("brak paczki (wgraj przez adb)", RegionPackLabels.Detail(new RegionPackInfo(RegionPackState.NotInstalled, "", mb52), false));
            Assert.AreEqual("pobieranie 37 % · 52 MB", RegionPackLabels.Detail(new RegionPackInfo(RegionPackState.Downloading, "", mb52, 0.37f), true));

            var missing = new RegionPackInfo(RegionPackState.NotInstalled, "", mb52);
            Assert.AreEqual(RegionPackLabels.DownloadLabel, RegionPackLabels.Action(missing, true));
            Assert.IsTrue(RegionPackLabels.ActionDownloads(missing, true));
            Assert.AreEqual(RegionPackLabels.UnavailableLabel, RegionPackLabels.Action(missing, false));
            Assert.IsFalse(RegionPackLabels.ActionDownloads(missing, false), "no URL: never download");
            var installed = new RegionPackInfo(RegionPackState.Installed, "", mb52);
            Assert.AreEqual(RegionPackLabels.StartLabel, RegionPackLabels.Action(installed, true));
            Assert.IsFalse(RegionPackLabels.ActionDownloads(installed, true));
            var incompatible = new RegionPackInfo(RegionPackState.Incompatible, "x", mb52);
            Assert.AreEqual(RegionPackLabels.IncompatibleLabel, RegionPackLabels.Action(incompatible, true));
            Assert.IsFalse(RegionPackLabels.ActionDownloads(incompatible, true));
            Assert.AreEqual(RegionPackLabels.RetryLabel, RegionPackLabels.Action(new RegionPackInfo(RegionPackState.Corrupt, "", mb52), true));
        }

        // ------------------------------------------------------------------ install from incoming/ (real files)

        string m_Tmp;
        RegionPackPaths m_Paths;

        [SetUp]
        public void SetUp()
        {
            m_Tmp = Path.Combine(Path.GetTempPath(), "rp-test-" + Guid.NewGuid().ToString("N"));
            m_Paths = new RegionPackPaths(m_Tmp);
            Directory.CreateDirectory(m_Paths.Incoming);
        }

        [TearDown]
        public void TearDown()
        {
            if (Directory.Exists(m_Tmp)) Directory.Delete(m_Tmp, true);
        }

        void Push(RegionPackManifest m, params (string file, byte[] bytes)[] files)
        {
            File.WriteAllText(m_Paths.IncomingManifest, JsonUtility.ToJson(m, true));
            foreach (var (file, bytes) in files) File.WriteAllBytes(m_Paths.IncomingFile(file), bytes);
        }

        RegionPackInfo DiskResolve(string tier = "Low")
        {
            RegionPackManifest.TryParse(File.ReadAllText(m_Paths.InstalledManifest), out var m, out _);
            return RegionPackResolver.Resolve(m, "dk65-06", tier, App, m_Paths, RegionPackDiskFiles.Instance, true);
        }

        [Test]
        public void Install_NothingIncoming_DoesNothing()
        {
            var r = RegionPackInstaller.InstallIncoming(m_Paths, App, RegionPackDiskFiles.Instance);
            Assert.IsFalse(r.Attempted);
            Assert.IsFalse(File.Exists(m_Paths.InstalledManifest));
        }

        [Test]
        public void Install_AdbPushedSet_MovesVerifiedBundles()
        {
            Push(Set(), ("common.bundle", CommonBytes), ("dk65-06.bundle", DkBytes));
            var r = RegionPackInstaller.InstallIncoming(m_Paths, App, RegionPackDiskFiles.Instance);
            Assert.IsTrue(r.Ok, r.ToString());
            CollectionAssert.AreEquivalent(new[] { "common", "dk65-06" }, r.Installed);
            Assert.IsTrue(File.Exists(m_Paths.Installed("dk65-06.bundle")));
            Assert.IsFalse(File.Exists(m_Paths.IncomingFile("dk65-06.bundle")));
            Assert.IsFalse(File.Exists(m_Paths.IncomingManifest));
            Assert.AreEqual(RegionPackState.Installed, DiskResolve().State);
            Assert.AreEqual(RegionPackState.NotInstalled, DiskResolve("High").State, "High was not pushed");
        }

        [Test]
        public void Install_BadBundle_IsDeletedAndReported()
        {
            var bad = (byte[])DkBytes.Clone();
            bad[2] ^= 0x40;
            Push(Set(), ("common.bundle", CommonBytes), ("dk65-06.bundle", bad));
            var r = RegionPackInstaller.InstallIncoming(m_Paths, App, RegionPackDiskFiles.Instance);
            Assert.IsTrue(r.Ok);
            CollectionAssert.AreEqual(new[] { "dk65-06" }, r.Rejected);
            Assert.IsFalse(File.Exists(m_Paths.IncomingFile("dk65-06.bundle")));
            Assert.IsFalse(File.Exists(m_Paths.Installed("dk65-06.bundle")));
            Assert.AreEqual(RegionPackState.NotInstalled, DiskResolve().State);
        }

        [Test]
        public void Install_IncompatibleSet_IsRejectedWithoutTouchingInstalled()
        {
            Push(Set(), ("common.bundle", CommonBytes), ("dk65-06.bundle", DkBytes));
            Assert.IsTrue(RegionPackInstaller.InstallIncoming(m_Paths, App, RegionPackDiskFiles.Instance).Ok);
            Push(Set("0.2.0-def", min: 900), ("dk65-06.bundle", DkHighBytes));
            var r = RegionPackInstaller.InstallIncoming(m_Paths, App, RegionPackDiskFiles.Instance);
            Assert.IsTrue(r.Attempted);
            StringAssert.Contains("incompatible", r.Error);
            Assert.IsTrue(File.Exists(m_Paths.IncomingManifest + RegionPackInstaller.RejectedSuffix), "renamed so it is not retried");
            Assert.AreEqual(RegionPackState.Installed, DiskResolve().State, "old set still usable");
        }

        [Test]
        public void Install_InvalidManifest_IsRejected()
        {
            File.WriteAllText(m_Paths.IncomingManifest, "{\"schema\":\"truck-sim-pl/region-packs/1\"}");
            var r = RegionPackInstaller.InstallIncoming(m_Paths, App, RegionPackDiskFiles.Instance);
            StringAssert.Contains("invalid", r.Error);
            Assert.IsFalse(File.Exists(m_Paths.InstalledManifest));
        }

        [Test]
        public void Install_NewSet_KeepsIdenticalBundlesAndRemovesStaleOnes()
        {
            Push(Set(), ("common.bundle", CommonBytes), ("dk65-06.bundle", DkBytes));
            RegionPackInstaller.InstallIncoming(m_Paths, App, RegionPackDiskFiles.Instance);
            File.WriteAllBytes(m_Paths.Installed("orphan.bundle"), new byte[] { 1, 2, 3 });

            // New set: common rebuilt (other bytes), dk65-06 identical, only the new common is pushed.
            var newCommon = Encoding.ASCII.GetBytes("common-bundle-bytes v2");
            var next = Set("0.1.1-fff");
            next.packs[0] = Entry("common", "", "", newCommon);
            Push(next, ("common.bundle", newCommon));
            var r = RegionPackInstaller.InstallIncoming(m_Paths, App, RegionPackDiskFiles.Instance);
            Assert.IsTrue(r.Ok, r.ToString());
            CollectionAssert.AreEqual(new[] { "common" }, r.Installed);
            CollectionAssert.AreEqual(new[] { "dk65-06" }, r.Kept);
            CollectionAssert.Contains(r.Removed, "orphan.bundle");
            Assert.AreEqual(RegionPackState.Installed, DiskResolve().State);

            // Next set rebuilds dk65-06 but the owner pushes only the manifest: the old bytes must not survive.
            var third = Set("0.1.2-aaa");
            third.packs[0] = Entry("common", "", "", newCommon);
            third.packs[1] = Entry("dk65-06", "dk65-06", "Low", Encoding.ASCII.GetBytes("dk65-06 low bundle bytes v3"), "common");
            Push(third);
            r = RegionPackInstaller.InstallIncoming(m_Paths, App, RegionPackDiskFiles.Instance);
            CollectionAssert.Contains(r.Removed, "dk65-06");
            Assert.AreEqual(RegionPackState.NotInstalled, DiskResolve().State);
        }

        // ------------------------------------------------------------------ bundle plan (editor)

        static readonly Dictionary<string, string[]> Deps = new Dictionary<string, string[]>
        {
            ["Assets/_Generated/World/dk65-06/World_dk65-06.unity"] = new[]
            {
                "Assets/_Generated/World/dk65-06/World_dk65-06.unity",
                "Assets/_Generated/World/dk65-06/Meshes/Low/chunk_0_0.asset",
                "Assets/_Generated/World/dk65-06/Collision/col_0_0.asset",
                "Assets/_Generated/Truck/TRAKT.prefab",
                "Assets/_Project/Rendering/Shaders/WorldSurface.shader",
                "Assets/_Project/World/Runtime/WorldRoute.cs",
                "Assets/_Project/Editor/Thing.asset",
            },
            ["Assets/_Generated/World/dk65-06/World_dk65-06_High.unity"] = new[]
            {
                "Assets/_Generated/World/dk65-06/Meshes/High/chunk_0_0.asset",
                "Assets/_Generated/World/dk65-06/Collision/col_0_0.asset",
                "Assets/_Generated/Truck/TRAKT.prefab",
            },
            ["Assets/_Generated/World/knyszyn/World_knyszyn.unity"] = new[]
            {
                "Assets/_Generated/World/knyszyn/Meshes/Low/chunk_0_0.asset",
                "Assets/_Generated/Truck/TRAKT.prefab",
                "Assets/_Generated/World/dk65-06/Shared/odd.asset",   // another region's asset: common
            },
        };

        [Test]
        public void Plan_SplitsCommonRegionDataAndImplicit()
        {
            var scenes = new List<RegionPackScene>
            {
                new RegionPackScene("dk65-06", "dk65-06", "Low", RegionPackPlanner.ScenePath("dk65-06", "Low")),
                new RegionPackScene("dk65-06-high", "dk65-06", "High", RegionPackPlanner.ScenePath("dk65-06", "High")),
                new RegionPackScene("knyszyn", "knyszyn", "Low", RegionPackPlanner.ScenePath("knyszyn", "Low")),
            };
            var plan = RegionPackPlanner.Build(scenes, p => Deps[p]);
            CollectionAssert.AreEqual(new[]
            {
                "Assets/_Generated/Truck/TRAKT.prefab",
                "Assets/_Generated/World/dk65-06/Shared/odd.asset",
                "Assets/_Project/Rendering/Shaders/WorldSurface.shader",
            }, plan.Common);
            CollectionAssert.AreEqual(new[] { "Assets/_Generated/World/dk65-06/Collision/col_0_0.asset" }, plan.RegionData["dk65-06"]);
            CollectionAssert.AreEqual(new[] { "Assets/_Generated/World/dk65-06/Meshes/Low/chunk_0_0.asset" }, plan.Unique["dk65-06"]);
            CollectionAssert.AreEqual(new[] { "Assets/_Generated/World/knyszyn/Meshes/Low/chunk_0_0.asset" }, plan.Unique["knyszyn"]);
            CollectionAssert.Contains(plan.Skipped, "Assets/_Project/World/Runtime/WorldRoute.cs");
            CollectionAssert.Contains(plan.Skipped, "Assets/_Project/Editor/Thing.asset");
            Assert.IsFalse(plan.Common.Exists(a => a.EndsWith(".unity")), "scenes never go to common");
        }

        [Test]
        public void Plan_LowOnly_KeepsRegionAssetsImplicit()
        {
            var scenes = new List<RegionPackScene> { new RegionPackScene("dk65-06", "dk65-06", "Low", RegionPackPlanner.ScenePath("dk65-06", "Low")) };
            var plan = RegionPackPlanner.Build(scenes, p => Deps[p]);
            Assert.AreEqual(0, plan.RegionData.Count);
            Assert.AreEqual(2, plan.Unique["dk65-06"].Count);
            CollectionAssert.AreEqual(new[] { "Assets/_Generated/Truck/TRAKT.prefab", "Assets/_Project/Rendering/Shaders/WorldSurface.shader" }, plan.Common);
        }

        [Test]
        public void Plan_RegionTokensAndNames()
        {
            var available = new[] { "bialystok-dojlidy", "bialystok-industrial-c", "dk65-01", "knyszyn" };
            var all = RegionPackPlanner.ResolveRegions("all", available, "bialystok-industrial-c", out var unknown);
            CollectionAssert.AreEqual(new[] { "bialystok-dojlidy", "dk65-01", "knyszyn" }, all, "region C stays in the base APK");
            Assert.AreEqual(0, unknown.Count);
            var some = RegionPackPlanner.ResolveRegions("dojlidy, knyszyn;nope dk65-01 knyszyn", available, "bialystok-industrial-c", out unknown);
            CollectionAssert.AreEqual(new[] { "bialystok-dojlidy", "knyszyn", "dk65-01" }, some);
            CollectionAssert.AreEqual(new[] { "nope" }, unknown);
            CollectionAssert.AreEqual(new[] { "bialystok-industrial-c" },
                RegionPackPlanner.ResolveRegions("bialystok-industrial-c", available, "bialystok-industrial-c", out _), "C only when named");
            Assert.AreEqual("World_knyszyn", RegionPackPlanner.SceneName("knyszyn", "Low"));
            Assert.AreEqual("WorldC_High", RegionPackPlanner.SceneName("bialystok-industrial-c", "High"));
            Assert.AreEqual("Assets/_Generated/World/dk65-06/World_dk65-06_High.unity", RegionPackPlanner.ScenePath("dk65-06", "High"));
            Assert.AreEqual("dk65-06-high", RegionPackPlanner.PackId("dk65-06", "High"));
            Assert.AreEqual("dk65-06-data", RegionPackPlanner.DataPackId("dk65-06"));
            Assert.IsTrue(RegionPackPlanner.IsExcluded("Assets/X/Foo.cs"));
            Assert.IsTrue(RegionPackPlanner.IsExcluded("Packages/com.x/Editor/Foo.asset"));
            Assert.IsFalse(RegionPackPlanner.IsExcluded("Packages/com.unity.render-pipelines.universal/Shaders/Lit.shader"));
        }

        // ------------------------------------------------------------------ ADR 0273: tile scenes in packs, leases, targets

        static readonly Dictionary<string, string[]> DepsWithTile = new Dictionary<string, string[]>
        {
            ["Assets/_Generated/World/dk65-06/World_dk65-06.unity"] = new[]
            {
                "Assets/_Generated/World/dk65-06/Meshes/Low/chunk_0_0.asset",
                "Assets/_Generated/World/dk65-06/Lights/sun.asset",                 // full scene only
                "Assets/_Generated/Truck/TRAKT.prefab",
            },
            ["Assets/_Generated/World/dk65-06/World_dk65-06_Tile.unity"] = new[]
            {
                "Assets/_Generated/World/dk65-06/World_dk65-06_Tile.unity",
                "Assets/_Generated/World/dk65-06/Meshes/Low/chunk_0_0.asset",       // shared by both scenes of the bundle
                "Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/tile_graph.json",
            },
        };

        [Test]
        public void Plan_TileSceneSharesTheSceneBundle_NotRegionData()
        {
            var s = new RegionPackScene("dk65-06", "dk65-06", "Low", RegionPackPlanner.ScenePath("dk65-06", "Low"), RegionPackPlanner.TileScenePath("dk65-06", "Low"));
            CollectionAssert.AreEqual(new[]
            {
                "Assets/_Generated/World/dk65-06/World_dk65-06.unity",
                "Assets/_Generated/World/dk65-06/World_dk65-06_Tile.unity",
            }, s.ScenePaths);
            CollectionAssert.AreEqual(new[] { "World_dk65-06", "World_dk65-06_Tile" }, s.SceneNames);
            var plan = RegionPackPlanner.Build(new List<RegionPackScene> { s }, p => DepsWithTile[p]);
            Assert.AreEqual(0, plan.RegionData.Count, "full + tile scene of one pack are one user: no data bundle");
            CollectionAssert.AreEqual(new[]
            {
                "Assets/_Generated/World/dk65-06/Lights/sun.asset",
                "Assets/_Generated/World/dk65-06/Meshes/Low/chunk_0_0.asset",
            }, plan.Unique["dk65-06"]);
            CollectionAssert.AreEqual(new[]
            {
                "Assets/_Generated/Truck/TRAKT.prefab",
                "Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/tile_graph.json",
            }, plan.Common);
            CollectionAssert.AreEqual(new[] { "Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/tile_graph.json" },
                plan.ResourcesCopies, "Resources/ assets are listed as second copies (review P2-4)");
        }

        [Test]
        public void Plan_NoTileScene_KeepsOneScene()
        {
            var s = new RegionPackScene("dk65-06", "dk65-06", "Low", RegionPackPlanner.ScenePath("dk65-06", "Low"), "");
            Assert.IsNull(s.TileScenePath);
            Assert.AreEqual(1, s.ScenePaths.Length);
            CollectionAssert.AreEqual(new[] { "World_dk65-06" }, s.SceneNames);
        }

        [Test]
        public void Names_DelegateToRegionScenes()
        {
            Assert.AreEqual(Game.World.RegionScenes.SceneNameFor("knyszyn", "High"), RegionPackPlanner.SceneName("knyszyn", "High"));
            Assert.AreEqual("World_knyszyn_High_Tile", RegionPackPlanner.TileSceneName("knyszyn", "High"));
            Assert.AreEqual("WorldC_Tile", RegionPackPlanner.TileSceneName("bialystok-industrial-c", "Low"));
            Assert.AreEqual("Assets/_Generated/World/dk65-06/World_dk65-06_Tile.unity", RegionPackPlanner.TileScenePath("dk65-06", "Low"));
            Assert.IsTrue(RegionPackLoadResult.IsTileScene("World_dk65-06_High_Tile"));
            Assert.IsFalse(RegionPackLoadResult.IsTileScene("World_dk65-06_High"));
            Assert.IsFalse(RegionPackLoadResult.IsTileScene(null));
            Assert.IsTrue(RegionPackPlanner.IsUnderResources("Assets/_Project/Gameplay/Resources/Regions/region_catalog.json"));
            Assert.IsFalse(RegionPackPlanner.IsUnderResources("Assets/_Generated/World/dk65-06/Meshes/Low/chunk_0_0.asset"));
        }

        [Test]
        public void Target_NamesMatchTheRunningPlatform()
        {
            Assert.AreEqual("Android", RegionPackManifest.TargetFor(RuntimePlatform.Android));
            Assert.AreEqual("Win64", RegionPackManifest.TargetFor(RuntimePlatform.WindowsPlayer));
            Assert.AreEqual("Win64", RegionPackManifest.TargetFor(RuntimePlatform.WindowsEditor));
            var m = new RegionPackManifest { schema = RegionPackManifest.SchemaId, unityVersion = Unity, buildTarget = "Win64", minAppVersionCode = 1 };
            Assert.IsNull(RegionPackResolver.CompatibilityProblem(m, new RegionPackAppIdentity(500, Unity, "Win64")));
            Assert.IsNotNull(RegionPackResolver.CompatibilityProblem(m, App), "a Windows set never loads on Android");
        }

        [Test]
        public void Leases_TwoRegionsAtOnce_CommonStaysUntilTheLast()
        {
            var l = new RegionPackLeases();
            string a = RegionPackLeases.Key("dk65-06", "Low"), b = RegionPackLeases.Key("dk65-07", "Low");
            CollectionAssert.AreEqual(new[] { "common", "dk65-06" }, l.Acquire(a, new[] { "common", "dk65-06" }));
            CollectionAssert.AreEqual(new[] { "dk65-07" }, l.Acquire(b, new[] { "common", "dk65-07" }), "common already loaded");
            Assert.AreEqual(2, l.BundleRefs("common"));
            // Releasing A must not touch B (the old Prepare unloaded every other region: review s22 #112 P1-2).
            CollectionAssert.AreEqual(new[] { "dk65-06" }, l.Release(a));
            Assert.IsTrue(l.IsHeld(b));
            Assert.AreEqual(1, l.BundleRefs("common"));
            CollectionAssert.AreEqual(new[] { "dk65-07", "common" }, l.Release(b), "reverse load order, common last");
            Assert.AreEqual(0, l.LoadedBundleCount);
            Assert.AreEqual(0, l.HeldKeyCount);
        }

        [Test]
        public void Leases_SameRegionTwice_MenuAndStreamer()
        {
            var l = new RegionPackLeases();
            string k = RegionPackLeases.Key("knyszyn", "High");
            Assert.AreEqual(3, l.Acquire(k, new[] { "common", "knyszyn-data", "knyszyn-high" }).Count);
            Assert.AreEqual(0, l.Acquire(k, null).Count, "second holder only counts");
            Assert.AreEqual(2, l.LeaseCount(k));
            Assert.AreEqual(0, l.Release(k).Count, "one holder left: nothing unloads");
            CollectionAssert.AreEqual(new[] { "knyszyn-high", "knyszyn-data", "common" }, l.Release(k));
            Assert.AreEqual(0, l.Release(k).Count, "releasing a key that is not held is a no-op");
        }

        [Test]
        public void Leases_DuplicateIdsAndClear()
        {
            var l = new RegionPackLeases();
            CollectionAssert.AreEqual(new[] { "common", "x" }, l.Acquire("x|Low", new[] { "common", "common", "", null, "x" }));
            l.Acquire("y|Low", new[] { "common", "y" });
            var all = l.Clear();
            Assert.AreEqual(3, all.Count);
            Assert.AreEqual(0, l.LoadedBundleCount);
            Assert.Throws<ArgumentException>(() => l.Acquire("", new[] { "a" }));
        }
    }
}
