using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// crown-lod-s24 (critic build #10 TOP 3: stipple on the crown edges). Kamion/Vegetation leaf cards and impostors use
    /// alpha-to-coverage under MSAA. The GPU turns a fractional alpha into a sample mask with an ordered screen-space dither
    /// (NVIDIA, measured on the GTX 1070 dev PC: <c>artifacts/crown-lod-s24/</c>), so every pixel of partial coverage - the
    /// whole of a minified crown, where fwidth(alpha) spans the texel - becomes a fixed-pattern speckle of sky and leaf.
    /// Snapping the coverage alpha to whole samples (round(c * S) / S) leaves the hardware nothing to dither: each pixel
    /// keeps the same number of covered samples as before on average, without the pattern. The shader needs S, the MSAA
    /// sample count of the target the camera renders into (mirrors and the main view differ), set here per camera as the
    /// global <c>_KamionVegMsaa</c> (0 = unknown / quantisation off: the old hardware path).
    /// </summary>
    public static class VegetationCoverage
    {
        static readonly int k_Msaa = Shader.PropertyToID("_KamionVegMsaa");
        static bool s_Hooked;

        /// <summary>Quantisation on (shipping) unless the rq_a2cq 0 A/B override is given.</summary>
        public static bool Enabled => !RenderOverrides.LeafA2CQuant.HasValue || RenderOverrides.LeafA2CQuant.Value != 0;

        /// <summary>MSAA samples of the colour target a camera renders into (URP: camera target texture, else the asset's MSAA).</summary>
        public static int SamplesOf(Camera cam)
        {
            if (cam == null || !cam.allowMSAA) return 1;
            if (cam.targetTexture != null) return Mathf.Max(1, cam.targetTexture.antiAliasing);
            var asset = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            return asset != null ? Mathf.Max(1, asset.msaaSampleCount) : 1;
        }

        /// <summary>Value of _KamionVegMsaa for a sample count (0 = off).</summary>
        public static float ShaderValue(int samples, bool enabled) => enabled ? Mathf.Max(1, samples) : 0f;

        /// <summary>Coverage alpha after the shader's snap (CPU mirror of Vegetation.shader VegCoverageSnap, for tests).</summary>
        public static float Snap(float coverage, float samples)
        {
            if (samples < 0.5f) return coverage;
            return Mathf.Round(Mathf.Clamp01(coverage) * samples) / samples;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Hook()
        {
            if (s_Hooked) return;
            s_Hooked = true;
            RenderPipelineManager.beginCameraRendering += OnBeginCamera;
        }

#if UNITY_EDITOR
        [UnityEditor.InitializeOnLoadMethod]
        static void HookEditor() => Hook();   // visual QA renders in edit mode
#endif

        static void OnBeginCamera(ScriptableRenderContext ctx, Camera cam) =>
            Shader.SetGlobalFloat(k_Msaa, ShaderValue(SamplesOf(cam), Enabled));
    }
}
