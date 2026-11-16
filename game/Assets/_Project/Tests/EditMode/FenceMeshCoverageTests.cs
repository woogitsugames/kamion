using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0239 (B-082): welded fence mesh - import policy, material swap, shader constants and coverage maths.</summary>
    public class FenceMeshCoverageTests
    {
        const string ShaderDir = "Assets/_Project/Rendering/Shaders/";

        [TestCase("fence_mesh.png", true, true, false)]      // plain box mips for the coverage shader
        [TestCase("fence_mesh.png", true, false, true)]      // shader missing: the s20 behaviour (mesh visible, moire)
        [TestCase("Assets/_Generated/World/x/Textures/fence_mesh.png", true, true, false)]
        [TestCase("fence_concrete_albedo.png", true, true, true)]
        [TestCase("leaves_linden.png", true, true, true)]
        [TestCase("plot_kit.png", true, true, true)]
        [TestCase("bark_pine.png", false, true, false)]
        public void OnlyTheFenceMeshLosesCoveragePreservingMips(string file, bool alphaTested, bool shader, bool expected)
        {
            Assert.AreEqual(expected, FenceMeshCoverage.PreserveCoverageMips(file, alphaTested, shader));
        }

        [Test]
        public void ShaderConstants_MirrorTheCSharpPolicy()
        {
            string src = File.ReadAllText(ShaderDir + "FenceMeshCoverage.hlsl");
            float Def(string name)
            {
                var m = Regex.Match(src, @"#define\s+" + name + @"\s+([0-9.]+)");
                Assert.IsTrue(m.Success, name);
                return float.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture);
            }
            Assert.AreEqual(FenceMeshCoverage.FadeNearM, Def("FENCE_MESH_FADE_NEAR_M"), 1e-7f);
            Assert.AreEqual(FenceMeshCoverage.FadeFarM, Def("FENCE_MESH_FADE_FAR_M"), 1e-7f);
            Assert.AreEqual(FenceMeshCoverage.FarGain, Def("FENCE_MESH_FAR_GAIN"), 1e-7f);
            Assert.AreEqual(FenceMeshCoverage.A2CLevels, Def("FENCE_MESH_A2C_LEVELS"), 1e-7f);
            StringAssert.Contains("52.9829189", src);
            StringAssert.Contains("float2(0.06711056, 0.00583715)", src);
        }

        [Test]
        public void Shader_CompilesAndKeepsTheLitContract()
        {
            var shader = Shader.Find(FenceMeshCoverage.ShaderName);
            Assert.NotNull(shader, FenceMeshCoverage.ShaderName);
            Assert.IsTrue(shader.isSupported);
            Assert.IsFalse(UnityEditor.ShaderUtil.ShaderHasError(shader));
            foreach (var p in new[] { "_BaseMap", "_BaseColor", "_Cutoff", "_Cull", "_AlphaToMask", "_Smoothness", "_Metallic" })
                Assert.GreaterOrEqual(shader.FindPropertyIndex(p), 0, p);
            string text = File.ReadAllText(ShaderDir + "WorldFenceMesh.shader");
            StringAssert.Contains("AlphaToMask[_AlphaToMask]", text);
            StringAssert.Contains("\"LightMode\" = \"DepthOnly\"", text);
            // the colour pass must not compile URP Lit's own cutoff (it would discard the far veil)
            StringAssert.DoesNotContain("shader_feature_local_fragment _ALPHATEST_ON", text);
        }

        [Test]
        public void Apply_SwapsTheShaderAndKeepsTheLitState()
        {
            var lit = Shader.Find("Universal Render Pipeline/Lit");
            var fence = Shader.Find(FenceMeshCoverage.ShaderName);
            Assert.NotNull(lit); Assert.NotNull(fence);
            var tex = new Texture2D(2, 2);
            var mat = new Material(lit);
            try
            {
                var colour = new Color(0.2f, 0.33f, 0.25f, 1f);
                mat.SetColor("_BaseColor", colour);
                mat.SetTexture("_BaseMap", tex);
                mat.SetFloat("_Cutoff", 0.5f); mat.SetFloat("_Cull", 0f); mat.SetFloat("_Smoothness", 0.5f);
                mat.EnableKeyword("_ALPHATEST_ON");
                mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.AlphaTest;
                mat.enableInstancing = true;
                var stored = mat.GetColor("_BaseColor");

                Assert.IsTrue(FenceMeshCoverage.Apply(mat, fence));

                Assert.AreEqual(FenceMeshCoverage.ShaderName, mat.shader.name);
                Assert.AreEqual(stored, mat.GetColor("_BaseColor"));
                Assert.AreSame(tex, mat.GetTexture("_BaseMap"));
                Assert.AreEqual(0.5f, mat.GetFloat("_Cutoff"), 1e-6f);
                Assert.AreEqual(0f, mat.GetFloat("_Cull"), 1e-6f);
                Assert.AreEqual(0.5f, mat.GetFloat("_Smoothness"), 1e-6f);
                Assert.AreEqual(1f, mat.GetFloat("_AlphaToMask"), 1e-6f);
                Assert.AreEqual((int)UnityEngine.Rendering.RenderQueue.AlphaTest, mat.renderQueue);
                Assert.IsTrue(mat.enableInstancing);
                Assert.AreEqual(FenceMeshCoverage.CastsShadow, mat.GetShaderPassEnabled("ShadowCaster"));
                Assert.IsTrue(mat.GetShaderPassEnabled("UniversalForward"));
            }
            finally { Object.DestroyImmediate(mat); Object.DestroyImmediate(tex); }
        }

        [Test]
        public void Apply_WithoutTheShaderLeavesTheMaterialAlone()
        {
            var lit = Shader.Find("Universal Render Pipeline/Lit");
            var mat = new Material(lit);
            try
            {
                Assert.IsFalse(FenceMeshCoverage.Apply(mat, null));
                Assert.AreSame(lit, mat.shader);
                Assert.IsTrue(mat.GetShaderPassEnabled("ShadowCaster"));
                Assert.IsFalse(FenceMeshCoverage.Apply(null, lit));
            }
            finally { Object.DestroyImmediate(mat); }
        }

        // Tier render heights at a 1080 px tall screen (QualityProfile.Defaults renderScale 0.75 / 1.0), 60 deg vertical FOV.
        [TestCase(1.5f, 810f, 0f)]       // Low: wires resolved, sharp cutoff
        [TestCase(10f, 810f, 1f)]        // Low: where the s20 cutoff lost the mesh - pure coverage now
        [TestCase(3f, 1080f, 0f)]        // High
        [TestCase(12f, 1080f, 1f)]
        public void Fade_SwitchesFromCutoffToCoverageWhereTheWireGoesSubPixel(float distanceM, float heightPx, float expected)
        {
            Assert.AreEqual(expected, FenceMeshCoverage.Fade(FenceMeshCoverage.FootprintM(distanceM, 60f, heightPx)), 1e-6f);
        }

        [Test]
        public void Fade_IsMonotonic()
        {
            float last = -1f;
            for (float f = 0f; f < 0.02f; f += 0.0002f)
            {
                float t = FenceMeshCoverage.Fade(f);
                Assert.GreaterOrEqual(t, last);
                Assert.That(t, Is.InRange(0f, 1f));
                last = t;
            }
        }

        [Test]
        public void Near_IsTheClassicCutoff()
        {
            // fade 0, no MSAA: the sharpened edge thresholded at 0.5 = alpha >= cutoff, whatever the noise says
            foreach (float noise in new[] { 0f, 0.3f, 0.99f })
            {
                Assert.AreEqual(0f, FenceMeshCoverage.Alpha(0.49f, 0.2f, 0f, noise, false));
                Assert.AreEqual(1f, FenceMeshCoverage.Alpha(0.51f, 0.9f, 0f, noise, false));
                // alpha-to-coverage: the edge value goes out unchanged (URP Lit's SharpenAlpha behaviour)
                Assert.AreEqual(0.3f, FenceMeshCoverage.Alpha(0.3f, 0.45f, 0f, noise, true), 1e-6f);
                Assert.AreEqual(0f, FenceMeshCoverage.Alpha(0f, 0.1f, 0f, noise, true));
            }
        }

        [TestCase(0.05f)]
        [TestCase(0.152f)]     // mean alpha of fence_mesh.png (20 x 3 px + 5 x 4 px wires of 512)
        [TestCase(0.35f)]
        [TestCase(0.8f)]
        public void Far_MeanCoverageEqualsAlpha_WithAndWithoutMsaa(float alpha)
        {
            foreach (bool a2c in new[] { false, true })
            {
                double sum = 0;
                const int n = 128;
                for (int y = 0; y < n; y++)
                    for (int x = 0; x < n; x++)
                    {
                        float a = FenceMeshCoverage.Alpha(0f, alpha, 1f, FenceMeshCoverage.Noise(x + 0.5f, y + 0.5f), a2c);
                        if (a2c) Assert.That(a, Is.EqualTo(0f).Or.EqualTo(0.5f).Or.EqualTo(1f));
                        else Assert.That(a, Is.EqualTo(0f).Or.EqualTo(1f));
                        sum += a;
                    }
                Assert.AreEqual(alpha, sum / (n * n), 0.02, a2c ? "alpha-to-coverage" : "no MSAA");
            }
        }

        [Test]
        public void Far_NothingIsDrawnWhereTheTextureIsEmpty_AndSolidStaysSolid()
        {
            for (int i = 0; i < 4096; i++)
            {
                float noise = FenceMeshCoverage.Noise(i % 64 + 0.5f, i / 64 + 0.5f);
                Assert.That(noise, Is.InRange(0f, 0.999999f));
                foreach (bool a2c in new[] { false, true })
                {
                    Assert.AreEqual(0f, FenceMeshCoverage.Alpha(0f, 0f, 1f, noise, a2c));
                    Assert.AreEqual(1f, FenceMeshCoverage.Alpha(1f, 1f, 1f, noise, a2c));
                }
            }
        }

        [Test]
        public void EveryTierHasMsaa_SoAlphaToCoverageIsTheShippedPath()
        {
            // ADR 0239: the noise-only branch is the fallback (mirrors / targets without MSAA), not a tier's main path.
            foreach (var tier in QualityProfile.Defaults())
                Assert.GreaterOrEqual(tier.msaa, 2, tier.name);
        }
    }
}
