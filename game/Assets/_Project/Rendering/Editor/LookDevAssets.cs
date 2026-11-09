using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering.Editor
{
    /// <summary>
    /// Creates (if missing) the look-development assets shared by world scenes: lighting presets (clear / overcast),
    /// the analytic sky material, the world post-processing volume profile (tonemapping only, ADR 0010) and the
    /// <see cref="QualityProfile"/> resource. Existing assets are kept (they may be tuned by hand) except the parts that
    /// are pure code contracts (shader on the sky material, tonemapper component present).
    /// Also the factory for world surface materials (<see cref="WorldMaterial"/>).
    /// </summary>
    public static class LookDevAssets
    {
        public const string LightingDir = "Assets/_Project/Rendering/Settings/Lighting";
        public const string ClearPreset = LightingDir + "/LP_Clear.asset";
        public const string OvercastPreset = LightingDir + "/LP_Overcast.asset";
        public const string SkyMaterial = LightingDir + "/M_Sky.mat";
        public const string WorldVolumeProfile = "Assets/_Project/Rendering/Settings/VP_World.asset";
        public const string QualityProfilePath = "Assets/_Project/Rendering/Resources/QualityProfile.asset";

        [MenuItem("Kamion/Rendering/Create look-dev assets")]
        public static void EnsureAll()
        {
            Directory.CreateDirectory(Path.Combine(ProjectRoot, LightingDir));
            Directory.CreateDirectory(Path.Combine(ProjectRoot, Path.GetDirectoryName(QualityProfilePath)));
            if (AssetDatabase.LoadAssetAtPath<LightingPreset>(ClearPreset) == null)
                AssetDatabase.CreateAsset(LightingPreset.CreateClear(), ClearPreset);
            if (AssetDatabase.LoadAssetAtPath<LightingPreset>(OvercastPreset) == null)
                AssetDatabase.CreateAsset(LightingPreset.CreateOvercast(), OvercastPreset);

            var shader = Shader.Find("Kamion/Sky");
            if (shader == null) throw new System.InvalidOperationException("Shader Kamion/Sky not found (compile error?)");
            var sky = AssetDatabase.LoadAssetAtPath<Material>(SkyMaterial);
            if (sky == null) { sky = new Material(shader) { name = "M_Sky" }; AssetDatabase.CreateAsset(sky, SkyMaterial); }
            sky.shader = shader;
            EditorUtility.SetDirty(sky);

            var vp = AssetDatabase.LoadAssetAtPath<VolumeProfile>(WorldVolumeProfile);
            if (vp == null) { vp = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(vp, WorldVolumeProfile); }
            if (!vp.TryGet(out Tonemapping tm))
            {
                tm = vp.Add<Tonemapping>(true);
                tm.name = "Tonemapping";
                AssetDatabase.AddObjectToAsset(tm, vp);
            }
            tm.mode.overrideState = true;
            tm.mode.value = TonemappingMode.Neutral;
            // Explicitly neutral: no bloom, no vignette, no grading (docs/06 §2: no "HDR look").
            if (!vp.TryGet(out Bloom bloom)) { bloom = vp.Add<Bloom>(true); bloom.name = "Bloom"; AssetDatabase.AddObjectToAsset(bloom, vp); }
            bloom.intensity.overrideState = true; bloom.intensity.value = 0f; bloom.active = false;
            if (!vp.TryGet(out Vignette vig)) { vig = vp.Add<Vignette>(true); vig.name = "Vignette"; AssetDatabase.AddObjectToAsset(vig, vp); }
            vig.intensity.overrideState = true; vig.intensity.value = 0f; vig.active = false;
            EditorUtility.SetDirty(vp);

            if (AssetDatabase.LoadAssetAtPath<QualityProfile>(QualityProfilePath) == null)
            {
                var qp = ScriptableObject.CreateInstance<QualityProfile>();
                qp.tiers = QualityProfile.Defaults();
                AssetDatabase.CreateAsset(qp, QualityProfilePath);
            }
            AssetDatabase.SaveAssets();
        }

        public static LightingPreset[] Presets() => new[]
        {
            AssetDatabase.LoadAssetAtPath<LightingPreset>(ClearPreset),
            AssetDatabase.LoadAssetAtPath<LightingPreset>(OvercastPreset),
        };

        public static QualityProfile LoadQualityProfile() => AssetDatabase.LoadAssetAtPath<QualityProfile>(QualityProfilePath);

        /// <summary>Visual style per surface kind (detail texture, tile size, macro variation, polish).</summary>
        public struct SurfaceStyle
        {
            public string texture;
            public float tile, detailScale, detailMix, macroSize, macroStrength, smoothnessVar;
            public Color macroTint;
        }

        public static SurfaceStyle StyleFor(string surface)
        {
            switch (surface)
            {
                case "grass":
                    // Dry, yellower patches where the macro noise is high: breaks the uniform lawn at distance.
                    return new SurfaceStyle { texture = WorldTextureGenerator.Grass, tile = 3.1f, detailScale = 3.3f, detailMix = 0.5f, macroSize = 47f, macroStrength = 0.3f, macroTint = new Color(1.25f, 1.12f, 0.85f) };
                case "asphalt":
                    return new SurfaceStyle { texture = WorldTextureGenerator.Asphalt, tile = 2.3f, detailScale = 2.71f, detailMix = 0.45f, macroSize = 37f, macroStrength = 0.22f, macroTint = Color.white, smoothnessVar = 0.08f };
                case "paving_stones":
                    return new SurfaceStyle { texture = WorldTextureGenerator.Paving, tile = 1.6f, detailScale = 1f, detailMix = 0f, macroSize = 23f, macroStrength = 0.18f, macroTint = Color.white };
                case "sett":
                    return new SurfaceStyle { texture = WorldTextureGenerator.Sett, tile = 1.6f, detailScale = 1f, detailMix = 0f, macroSize = 23f, macroStrength = 0.18f, macroTint = Color.white };
                case "gravel":
                    return new SurfaceStyle { texture = WorldTextureGenerator.Gravel, tile = 2f, detailScale = 2.9f, detailMix = 0.5f, macroSize = 29f, macroStrength = 0.2f, macroTint = Color.white };
                case "paint":
                    return new SurfaceStyle { texture = WorldTextureGenerator.Paint, tile = 1.7f, detailScale = 2.3f, detailMix = 0.4f, macroSize = 31f, macroStrength = 0.15f, macroTint = Color.white };
                default: // concrete, concrete_kerb, steel fallback
                    return new SurfaceStyle { texture = WorldTextureGenerator.Concrete, tile = 2f, detailScale = 2.6f, detailMix = 0.5f, macroSize = 19f, macroStrength = 0.2f, macroTint = Color.white };
            }
        }

        /// <summary>
        /// Creates or updates a world material. <paramref name="albedo"/> is the linear mean albedo (manifest colour);
        /// <paramref name="decal"/> = coplanar overlay (markings): polygon offset and a later queue.
        /// Metallic surfaces (steel barriers) use URP Lit.
        /// </summary>
        public static Material WorldMaterial(string path, string surface, Color albedo, float roughness, float metallic, bool decal, Color? decalBackground = null)
        {
            Directory.CreateDirectory(Path.Combine(ProjectRoot, Path.GetDirectoryName(path)));
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            bool metal = metallic > 0.5f;
            var shader = Shader.Find(metal ? "Universal Render Pipeline/Lit" : "Kamion/World Surface");
            if (shader == null) throw new System.InvalidOperationException("world shader missing");
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = shader;
            mat.enableInstancing = true;
            if (metal)
            {
                // Galvanised steel: base colour is specular F0 for metals, linear.
                mat.SetColor("_BaseColor", albedo.gamma);
                mat.SetFloat("_Metallic", metallic);
                mat.SetFloat("_Smoothness", 1f - roughness);
            }
            else
            {
                var st = StyleFor(surface);
                // Material colours are stored as sRGB and linearised for the GPU in a linear project: pass .gamma so the
                // shader receives the manifest's linear albedo exactly.
                mat.SetColor("_BaseColor", new Color(albedo.r, albedo.g, albedo.b, 1f).gamma);
                mat.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(st.texture));
                mat.SetTexture("_MacroMap", AssetDatabase.LoadAssetAtPath<Texture2D>(WorldTextureGenerator.Macro));
                mat.SetFloat("_TileSize", st.tile);
                mat.SetFloat("_DetailScale", st.detailScale);
                mat.SetFloat("_DetailMix", st.detailMix);
                mat.SetFloat("_MacroSize", st.macroSize);
                mat.SetFloat("_MacroStrength", st.macroStrength);
                mat.SetColor("_MacroTint", st.macroTint.gamma);
                mat.SetFloat("_Smoothness", Mathf.Clamp01(1f - roughness));
                mat.SetFloat("_SmoothnessVar", st.smoothnessVar);
                mat.SetFloat("_FadeWidth", decal ? 0.12f : 0f);   // P-1 line width, Dz.U. 2019 poz. 2311 zał. 2
                mat.SetColor("_FadeColor", (decalBackground ?? new Color(0.075f, 0.075f, 0.072f)).gamma);
                mat.SetFloat("_OffsetFactor", decal ? -1f : 0f);
                mat.SetFloat("_OffsetUnits", decal ? -4f : 0f);
                mat.renderQueue = decal ? (int)RenderQueue.Geometry + 10 : -1;
            }
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static string ProjectRoot => Path.GetDirectoryName(Application.dataPath);
    }
}
