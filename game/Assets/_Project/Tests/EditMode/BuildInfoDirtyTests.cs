using System;
using Game.Editor.Build;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>build-fix-s24: the "-dirty" stamp follows the build script's pre-build tree state when it is given.</summary>
    public class BuildInfoDirtyTests
    {
        string m_Saved;

        [SetUp] public void SetUp() => m_Saved = Environment.GetEnvironmentVariable(BuildInfoWriter.DirtyEnv);
        [TearDown] public void TearDown() => Environment.SetEnvironmentVariable(BuildInfoWriter.DirtyEnv, m_Saved);

        [Test]
        public void PreBuildState_FromEnv_WinsOverGitStatus()
        {
            Environment.SetEnvironmentVariable(BuildInfoWriter.DirtyEnv, "0");
            Assert.IsFalse(BuildInfoWriter.GitDirty());
            Environment.SetEnvironmentVariable(BuildInfoWriter.DirtyEnv, "1");
            Assert.IsTrue(BuildInfoWriter.GitDirty());
        }
    }
}
