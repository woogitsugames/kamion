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

        [Test]
        public void ThermalNames_CoverAndroidRange()
        {
            Assert.AreEqual("none", ThermalStatusNames.Get(0));
            Assert.AreEqual("shutdown", ThermalStatusNames.Get(6));
            Assert.AreEqual("n/a", ThermalStatusNames.Get(null));
        }
    }
}
