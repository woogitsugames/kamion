using Game.Core;
using Game.Platform;
using NUnit.Framework;

namespace Game.Tests
{
    public class BuildInfoTests
    {
        [Test]
        public void Parse_ReadsBakedFields()
        {
            var info = BuildInfo.Parse("{\"version\":\"0.1.0\",\"gitSha\":\"abc1234\",\"gitDirty\":true,\"versionCode\":7}");
            Assert.AreEqual("0.1.0", info.version);
            Assert.AreEqual(7, info.versionCode);
            Assert.AreEqual("0.1.0 (abc1234-dirty)", info.ShortLabel);
        }

        [Test]
        public void Parse_GarbageFallsBack()
        {
            Assert.AreEqual("editor", BuildInfo.Parse("not json").gitSha);
            Assert.AreEqual("editor", BuildInfo.Parse(null).gitSha);
        }

        // ---- ADR 0276: content hash of the player data, read from build-id.json next to the exe

        [Test]
        public void ContentHash_ParsedFromBuildIdFile()
        {
            const string file = "{\n \"schema\": \"kamion/build-id/1\",\n \"gitSha\": \"e28533ca31\",\n \"contentHash\": \"0A1b2C3d4E5f\",\n \"contentSha256\": \"" +
                                "0a1b2c3d4e5f00000000000000000000000000000000000000000000000000ff\"\n}";
            Assert.AreEqual("0a1b2c3d4e5f", BuildInfo.ParseContentHash(file));
        }

        [TestCase(null)]
        [TestCase("")]
        [TestCase("not json")]
        [TestCase("{\"contentHash\": \"0a1b2c3d4e\"}")]                       // too short
        [TestCase("{\"contentHash\": \"0a1b2c3d4e5f6\"}")]                    // too long
        [TestCase("{\"contentHash\": \"0a1b2c3d4e5g\"}")]                     // not hex
        [TestCase("{\"contentSha256\": \"0a1b2c3d4e5f\"}")]                   // other key
        public void ContentHash_AnythingElse_IsEmpty(string json)
        {
            Assert.AreEqual("", BuildInfo.ParseContentHash(json));
        }

        [Test]
        public void IdentityLabel_AddsContentHash_OnlyWhenKnown()
        {
            var info = BuildInfo.Parse("{\"version\":\"0.1.0\",\"gitSha\":\"abc1234\",\"gitDirty\":false,\"versionCode\":7}");
            Assert.AreEqual("0.1.0 (abc1234)", info.IdentityLabel, "no build-id.json: same as ShortLabel");
            info.contentHash = "0a1b2c3d4e5f";
            Assert.AreEqual("0.1.0 (abc1234) · dane 0a1b2c3d4e5f", info.IdentityLabel);
            Assert.AreEqual("0.1.0 (abc1234)", info.ShortLabel, "ShortLabel (telemetry, pcperf) unchanged");
            // The hash is never baked into build_info.json (it cannot be known before the build).
            StringAssert.DoesNotContain("contentHash", UnityEngine.JsonUtility.ToJson(info));
        }

        [Test]
        public void BuildIdFile_LivesNextToTheExe_OutsideTheDataFolder()
        {
            string p = BuildInfo.BuildIdPathFor("C:/Games/kamion-0.1.0-abc/Kamion_Data");
            Assert.AreEqual(System.IO.Path.Combine("C:/Games/kamion-0.1.0-abc", "build-id.json"), p);
            Assert.AreEqual(p, BuildInfo.BuildIdPathFor("C:/Games/kamion-0.1.0-abc/Kamion_Data/"));
            Assert.IsNull(BuildInfo.BuildIdPathFor(null));
            Assert.AreEqual("", BuildInfo.ReadContentHash(System.IO.Path.Combine(System.IO.Path.GetTempPath(), System.IO.Path.GetRandomFileName(), "Kamion_Data")),
                "missing file: empty, no exception");
        }

        [Test]
        public void ContentHash_RoundTripThroughFile()
        {
            string dir = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "kamion-build-id-" + System.IO.Path.GetRandomFileName());
            try
            {
                System.IO.Directory.CreateDirectory(System.IO.Path.Combine(dir, "Kamion_Data"));
                System.IO.File.WriteAllText(System.IO.Path.Combine(dir, BuildInfo.BuildIdFileName), "{\"contentHash\": \"fedcba987654\"}");
                Assert.AreEqual("fedcba987654", BuildInfo.ReadContentHash(System.IO.Path.Combine(dir, "Kamion_Data")));
            }
            finally { if (System.IO.Directory.Exists(dir)) System.IO.Directory.Delete(dir, true); }
        }

        [Test]
        public void ThermalNames_CoverAndroidRange()
        {
            Assert.AreEqual("none", ThermalStatusNames.Get(0));
            Assert.AreEqual("shutdown", ThermalStatusNames.Get(6));
            Assert.AreEqual("n/a", ThermalStatusNames.Get(null));
        }
    }
}
