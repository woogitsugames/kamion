using System;
using System.IO;
using System.Reflection;
using Game.Rendering;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0239 fallback, review s23 P1 (REVIEW-2026-11-16-s23-code-fence-mesh-forward): a fence shader that is found but
    /// does not compile must count as missing, so the importer keeps URP Lit and the coverage-preserving mips instead of
    /// a magenta fence. The importer assembly is not referenced by the test assembly - reached by reflection.
    /// </summary>
    public class FenceShaderFallbackTests
    {
        const string ImportDir = "Assets/_Project/World/Import/";

        static MethodInfo Method(string name)
        {
            var type = Type.GetType("Game.World.Import.InstanceImporter, Game.World.Import.Editor");
            Assert.NotNull(type, "Game.World.Import.InstanceImporter");
            var m = type.GetMethod(name, BindingFlags.Public | BindingFlags.Static);
            Assert.NotNull(m, name);
            return m;
        }

        static Shader Usable(Shader s) => (Shader)Method("UsableShaderOrNull").Invoke(null, new object[] { s });

        [Test]
        public void MissingShader_IsNull()
        {
            Assert.IsNull(Usable(null));
        }

        [Test]
        public void CompilingFenceShader_IsReturned()
        {
            var fence = Shader.Find(FenceMeshCoverage.ShaderName);
            Assert.NotNull(fence, FenceMeshCoverage.ShaderName);
            Assert.AreSame(fence, Usable(fence));
            Assert.AreSame(fence, (Shader)Method("FenceShaderOrNull").Invoke(null, null));
        }

        [Test]
        public void ShaderWithAnError_CountsAsMissing_AndTheTextureKeepsItsCoverageMips()
        {
            LogAssert.ignoreFailingMessages = true;      // the broken source logs a shader error on purpose
            Shader broken = null;
            try
            {
                broken = ShaderUtil.CreateShaderAsset(
                    "Shader \"Hidden/Kamion/Tests/BrokenFence\" { SubShader { Pass { this is not shaderlab } } }", false);
                Assert.NotNull(broken);
                Assert.IsTrue(ShaderUtil.ShaderHasError(broken), "the test shader must be one with an error");
                Assert.IsNull(Usable(broken));
                // what the importer does with that answer (InstanceImporter.ImportTexture / RegionImporter.LitMaterial)
                Assert.IsTrue(FenceMeshCoverage.PreserveCoverageMips(FenceMeshCoverage.TextureFile, true, Usable(broken) != null));
                var lit = Shader.Find("Universal Render Pipeline/Lit");
                var mat = new Material(lit);
                try
                {
                    Assert.IsFalse(FenceMeshCoverage.Apply(mat, Usable(broken)));
                    Assert.AreSame(lit, mat.shader);
                }
                finally { UnityEngine.Object.DestroyImmediate(mat); }
            }
            finally
            {
                if (broken != null) UnityEngine.Object.DestroyImmediate(broken);
                LogAssert.ignoreFailingMessages = false;
            }
        }

        [TestCase("RegionImporter.cs")]
        [TestCase("InstanceImporter.cs")]
        public void Importers_LookTheFenceShaderUpThroughTheHelperOnly(string file)
        {
            string src = File.ReadAllText(ImportDir + file);
            StringAssert.Contains("FenceShaderOrNull()", src);
            // one raw lookup is allowed: the body of the helper itself (InstanceImporter.cs)
            int raw = src.Split(new[] { "Shader.Find(Game.Rendering.FenceMeshCoverage.ShaderName)" }, StringSplitOptions.None).Length - 1;
            Assert.AreEqual(file == "InstanceImporter.cs" ? 1 : 0, raw, file);
            if (file == "InstanceImporter.cs") StringAssert.Contains("ShaderUtil.ShaderHasError(shader)", src);
        }
    }
}
