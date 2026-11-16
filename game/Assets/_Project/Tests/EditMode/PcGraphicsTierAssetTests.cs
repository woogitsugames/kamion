using System.Collections.Generic;
using Game.Rendering;
using Game.Rendering.Editor;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Tests
{
    /// <summary>ADR 0269: the PC URP assets equal the PcTierTable, use only shader features some quality-level (mobile) asset
    /// already keeps in the build, and the mobile tiers / editor stay unchanged.</summary>
    public class PcGraphicsTierAssetTests
    {
        [TearDown]
        public void TearDown() => PcGraphicsTiers.ForceEnabled = null;

        [Test]
        public void PcAssets_LoadFromResourcesAndMatchTheTable()
        {
            foreach (PcTier t in System.Enum.GetValues(typeof(PcTier)))
            {
                var asset = PcGraphicsTiers.LoadAsset(t);
                Assert.IsNotNull(asset, $"Resources/{PcTierTable.Get(t).urpAsset}");
                Assert.AreEqual(PcTierAssetsSetup.AssetPath(t), AssetDatabase.GetAssetPath(asset));
                var diff = PcTierAssetsSetup.Diff(asset, PcTierTable.Get(t));
                Assert.IsEmpty(diff, $"{t}: " + string.Join("; ", diff) + " - run Game.Rendering.Editor.PcTierAssetsSetup.EnsureBatch");
            }
        }

        static List<UniversalRenderPipelineAsset> QualityLevelAssets()
        {
            var list = new List<UniversalRenderPipelineAsset>();
            for (int i = 0; i < QualitySettings.names.Length; i++)
                if (QualitySettings.GetRenderPipelineAssetAt(i) is UniversalRenderPipelineAsset a) list.Add(a);
            return list;
        }

        [Test]
        public void PcAssets_UseOnlyFeaturesTheQualityLevelAssetsKeepInTheBuild()
        {
            // Shader variant stripping looks at the quality-level assets only; a PC asset in Resources must not need more.
            var mobile = QualityLevelAssets();
            Assert.IsNotEmpty(mobile);
            var softQualities = new HashSet<int>();
            int maxCascades = 0, maxLights = 0; bool anySoft = false, anySsao = false;
            foreach (var m in mobile)
            {
                var so = new SerializedObject(m);
                if (m.supportsSoftShadows) { anySoft = true; softQualities.Add(so.FindProperty("m_SoftShadowQuality").intValue); }
                maxCascades = Mathf.Max(maxCascades, m.shadowCascadeCount);
                maxLights = Mathf.Max(maxLights, m.maxAdditionalLightsCount);
                foreach (var r in m.rendererDataList)
                    if (r != null) foreach (var f in r.rendererFeatures) if (f is ScreenSpaceAmbientOcclusion) anySsao = true;
            }
            foreach (PcTier t in System.Enum.GetValues(typeof(PcTier)))
            {
                var a = PcGraphicsTiers.LoadAsset(t);
                var s = PcTierTable.Get(t);
                if (s.softShadows)
                {
                    Assert.IsTrue(anySoft, $"{t}: soft shadows, no quality-level asset has them");
                    CollectionAssert.Contains(softQualities, s.softShadowQuality, $"{t}: soft shadow quality not kept by any quality level");
                }
                Assert.LessOrEqual(s.shadowCascades, maxCascades, $"{t}: cascades");
                if (s.ssao) Assert.IsTrue(anySsao, $"{t}: SSAO renderer feature not in any quality-level asset");
                var ma = new SerializedObject(a);
                var mm = new SerializedObject(mobile[0]);
                foreach (var p in new[] { "m_AdditionalLightsRenderingMode", "m_MainLightRenderingMode", "m_SupportsLightCookies", "m_SupportsLightLayers",
                                          "m_ReflectionProbeBlending", "m_ReflectionProbeBoxProjection", "m_AdditionalLightShadowsSupported" })
                    Assert.AreEqual(mm.FindProperty(p).intValue, ma.FindProperty(p).intValue, $"{t}: {p} differs from the mobile assets");
            }
        }

        [Test]
        public void PcSsaoRenderer_HasTheSameSettingsAsTheMobileOne()
        {
            var mobile = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(SsaoRendererSetup.SsaoRenderer);
            var pc = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(PcTierAssetsSetup.PcRendererSsao);
            Assert.IsNotNull(mobile); Assert.IsNotNull(pc);
            ScriptableRendererFeature Ssao(UniversalRendererData d) { foreach (var f in d.rendererFeatures) if (f is ScreenSpaceAmbientOcclusion) return f; return null; }
            var a = new SerializedObject(Ssao(mobile)).FindProperty("m_Settings");
            var b = new SerializedObject(Ssao(pc)).FindProperty("m_Settings");
            Assert.IsTrue(SerializedProperty.DataEquals(a, b), "SSAO keyword variants follow these settings (ADR 0269)");
            Assert.AreEqual(new SerializedObject(mobile).FindProperty("m_RenderingMode").intValue,
                            new SerializedObject(pc).FindProperty("m_RenderingMode").intValue, "rendering path");
        }

        [Test]
        public void Overlay_PutsPcValuesOnTheMobileTierAndKeepsTheRest()
        {
            var profile = QualityProfile.Load();
            Assert.IsNotNull(profile);
            foreach (PcTier t in System.Enum.GetValues(typeof(PcTier)))
            {
                Assert.IsTrue(profile.TryGet(t.ToString(), out var mobile), t.ToString());
                var o = PcGraphicsTiers.Overlay(mobile);
                var s = PcTierTable.Get(t);
                Assert.AreEqual(mobile.name, o.name);
                Assert.AreEqual(s.shadowDistance, o.shadowDistance);
                Assert.AreEqual(s.cameraFarClip, o.cameraFarClip);
                Assert.AreEqual(s.treeCullM, o.treeCullM);
                Assert.AreEqual(s.msaa, o.msaa);
                Assert.AreEqual(0f, o.adaptiveScaleMin, "fixed native resolution on PC");
                Assert.AreEqual(0, o.thermalFallbackFps);
                Assert.IsTrue(o.leafAlphaToCoverage);
                Assert.AreEqual(mobile.clearCoat, o.clearCoat, "vehicle look follows the mobile tier");
                Assert.AreEqual(mobile.cabShadowLift, o.cabShadowLift);
                Assert.AreEqual(mobile.worldMipBias, o.worldMipBias);
                Assert.AreNotEqual(TonemappingMode.None, o.tonemapping);
            }
        }

        [Test]
        public void EditorAndPhones_AreNotSwitchedToPcTiers()
        {
            Assert.IsFalse(PcGraphicsTiers.Enabled, "editor: PC tiers only with ForceEnabled");
            Assert.IsTrue(PcGraphicsTiers.IsDesktopPlayer(RuntimePlatform.WindowsPlayer));
            Assert.IsFalse(PcGraphicsTiers.IsDesktopPlayer(RuntimePlatform.Android));
            Assert.IsFalse(PcGraphicsTiers.IsDesktopPlayer(RuntimePlatform.WindowsEditor));
            CollectionAssert.AreEqual(QualityTiers.Names, new[] { "Low", "Medium", "High", "Ultra" });
            foreach (var n in QualityTiers.Names) Assert.IsTrue(PcTierTable.TryParse(n, out _), n);
        }

        [Test]
        public void EditorPreview_AppliesAndRestoresQualitySettings()
        {
            int level = QualitySettings.GetQualityLevel();
            var pipeline = QualitySettings.renderPipeline;
            float lodBias = QualitySettings.lodBias;
            int mip = QualitySettings.globalTextureMipmapLimit;
            try
            {
                PcGraphicsTiers.ForceEnabled = true;
                Assert.IsTrue(PcGraphicsTiers.Apply(PcTier.Low));
                Assert.AreEqual(PcTier.Low, PcGraphicsTiers.Current);
                Assert.AreSame(PcGraphicsTiers.LoadAsset(PcTier.Low), QualitySettings.renderPipeline);
                Assert.AreEqual(PcTierTable.Get(PcTier.Low).lodBias, QualitySettings.lodBias, 1e-5f);
                Assert.AreEqual(PcTierTable.Get(PcTier.Low).textureMipmapLimit, QualitySettings.globalTextureMipmapLimit);
            }
            finally
            {
                PcGraphicsTiers.RestoreEditorState();
                PcGraphicsTiers.ForceEnabled = null;
                QualitySettings.SetQualityLevel(level, false);
            }
            Assert.AreSame(pipeline, QualitySettings.renderPipeline, "quality level pipeline restored");
            Assert.AreEqual(lodBias, QualitySettings.lodBias, 1e-5f);
            Assert.AreEqual(mip, QualitySettings.globalTextureMipmapLimit);
        }
    }
}
