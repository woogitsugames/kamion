using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// Welded panel fence mesh (ADR 0239, BACKLOG B-082): which texture / material it is, how its texture is imported and
    /// the C# mirror of Shaders/FenceMeshCoverage.hlsl (constants and the per-pixel decision; EditMode tests keep them in
    /// step). All distances are WORKING_VALUE until judged on the phone.
    /// </summary>
    public static class FenceMeshCoverage
    {
        public const string ShaderName = "Kamion/World FenceMesh";
        /// <summary>The generated wire texture (tools/worldgen/streetscape/export.py fence_mesh_png): 1 m tile, UV0 in metres.</summary>
        public const string TextureFile = "fence_mesh.png";
        /// <summary>Metres of fence per pixel where the sharp cutoff starts to give way to coverage (FENCE_MESH_FADE_NEAR_M).</summary>
        public const float FadeNearM = 0.0033f;
        /// <summary>Metres of fence per pixel from which alpha is pure coverage (FENCE_MESH_FADE_FAR_M).</summary>
        public const float FadeFarM = 0.0093f;
        /// <summary>Far coverage per unit of mean texture alpha (FENCE_MESH_FAR_GAIN); 1 = the wires' share of the pixel.</summary>
        public const float FarGain = 1f;
        /// <summary>Coverage steps per pixel under alpha-to-coverage (FENCE_MESH_A2C_LEVELS): 0, 1/2, 1 - exact at MSAA 2x and 4x.</summary>
        public const float A2CLevels = 2f;
        /// <summary>
        /// The mesh casts no shadow: its wire (5 mm) is narrower than a shadow-map texel on every tier (Low 35 m / 1024 px
        /// = 68 mm), so the caster drew aliased stripes or nothing (BACKLOG B-088), and the sun's 0.53 deg disc blurs a
        /// 5 mm wire away within ~0.5 m. Posts and plinth still cast. Set true to get URP Lit's cutoff caster back.
        /// </summary>
        public const bool CastsShadow = false;

        public static bool IsFenceMeshTexture(string file) =>
            file != null && string.Equals(System.IO.Path.GetFileName(file), TextureFile, System.StringComparison.OrdinalIgnoreCase);

        /// <summary>
        /// TextureImporter.mipMapsPreserveCoverage for a world texture. The fence mesh needs plain box mips (mean alpha =
        /// covered share, which the shader spends as coverage); without the shader (compile error) it keeps the
        /// coverage-preserving mips of every other alpha-tested texture - moire, but a visible mesh (s20 lead decision).
        /// </summary>
        public static bool PreserveCoverageMips(string file, bool alphaTested, bool fenceShaderAvailable) =>
            alphaTested && !(fenceShaderAvailable && IsFenceMeshTexture(file));

        /// <summary>0 = sharp cutoff, 1 = coverage (FenceMeshFade). footprintM: metres of fence across one pixel.</summary>
        public static float Fade(float footprintM) => Mathf.Clamp01((footprintM - FadeNearM) / (FadeFarM - FadeNearM));

        /// <summary>Metres of fence across one pixel for a fence facing the camera: distance × pixel angle (rad).</summary>
        public static float FootprintM(float distanceM, float verticalFovDeg, float renderHeightPx) =>
            distanceM * 2f * Mathf.Tan(verticalFovDeg * 0.5f * Mathf.Deg2Rad) / renderHeightPx;

        /// <summary>Interleaved gradient noise of FenceMeshNoise (pixel centre coordinates, e.g. 10.5), in [0, 1).</summary>
        public static float Noise(float pixelX, float pixelY)
        {
            double inner = pixelX * 0.06711056 + pixelY * 0.00583715;
            inner -= System.Math.Floor(inner);
            double v = 52.9829189 * inner;
            return (float)(v - System.Math.Floor(v));
        }

        /// <summary>
        /// FenceMeshAlpha without the derivatives: sharp = the 1-pixel cutoff edge (0..1), alpha = texture alpha,
        /// fade = Fade(), noise = Noise(). Returns the alpha written (0 = pixel discarded).
        /// </summary>
        public static float Alpha(float sharp, float alpha, float fade, float noise, bool alphaToCoverage)
        {
            float c = Mathf.Lerp(sharp, Mathf.Clamp01(alpha * FarGain), fade);
            float a = alphaToCoverage
                ? Mathf.Lerp(c, Mathf.Min(Mathf.Floor(c * A2CLevels + noise) / A2CLevels, 1f), fade)
                : (c >= Mathf.Lerp(0.5f, Mathf.Max(noise, 0.004f), fade) ? 1f : 0f);
            return a > 0.0001f ? a : 0f;
        }

        /// <summary>
        /// Turns the URP Lit material that RegionImporter.LitMaterial built for a fence mesh into Kamion/World FenceMesh
        /// (same properties and keywords). Returns false and leaves the material alone when the shader is missing.
        /// </summary>
        public static bool Apply(Material lit, Shader fenceShader)
        {
            if (lit == null || fenceShader == null) return false;
            int queue = lit.renderQueue;
            lit.shader = fenceShader;
            lit.renderQueue = queue;                       // AlphaTest, as set by LitMaterial
            lit.SetFloat("_AlphaToMask", 1f);              // the shader reads URP's _AlphaToMaskAvailable (MSAA target)
            lit.SetShaderPassEnabled("ShadowCaster", CastsShadow);
            return true;
        }
    }
}
