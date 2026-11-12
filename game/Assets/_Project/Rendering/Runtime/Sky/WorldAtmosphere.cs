using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// World atmosphere and look globals of ADR 0080 (KamionAtmosphere.hlsl, Kamion/Sky): ground haze layer, cloud deck,
    /// wet-surface and lawn-variation parameters, and the tone toe of the tiers without post-processing. Pushed by
    /// <see cref="EnvironmentLighting"/> before every frame (follows floating-origin shifts, tier and preset switches and
    /// the cloud drift; a handful of SetGlobal calls, no allocation). Unset globals are 0 = off, so scenes without an
    /// EnvironmentLighting keep their look.
    /// </summary>
    public static class WorldAtmosphere
    {
        // ---- owner A/B overrides (launch args / visual QA -Rq; RenderOverrides): not defaults
        /// <summary>rq_look: -1 = the preset's toe; 0 = none (variant A), 1..4 = variants B..E.</summary>
        public static int LookVariant = -1;
        /// <summary>rq_wet: wetness 0..1 (null = the preset's).</summary>
        public static float? WetOverride;
        /// <summary>rq_clouds: -1 = flat dome, 0..2 = quality (null = the tier's).</summary>
        public static int? CloudOverride;
        /// <summary>rq_clearcover: clear cloud coverage ablation (null = preset).</summary>
        public static float? ClearCloudCoverOverride;
        public static bool? HeadlampsOverride;
        /// <summary>rq_haze: false = uniform fog only (null = the tier's).</summary>
        public static bool? HazeOverride;
        /// <summary>rq_grassvar: lawn variation strength 0..1 (null = the preset's).</summary>
        public static float? GrassOverride;
        /// <summary>rq_hazegf (r11 A/B): ground haze layer factor (null = the preset's).</summary>
        public static float? HazeFactorOverride;
        /// <summary>rq_hazeh (r11 A/B): ground haze scale height in m (null = the preset's).</summary>
        public static float? HazeHeightOverride;
        /// <summary>rq_leafamb (r11 A/B): 0 = no sky light through the leaves and no leaf sheen (the r10 foliage ambient), null / 1 = on.</summary>
        public static float? LeafAmbientOverride;

        /// <summary>Contrast variants for the owner's decision (ADR 0080 §exposure): toe strength, half-point, pivot, EV bias.</summary>
        public static readonly Vector4[] LookVariants =
        {
            new Vector4(0f, 0.12f, 0.30f, 0f),        // A: D23 curve unchanged
            new Vector4(0.5f, 0.12f, 0.30f, 0f),      // B: moderate toe, 0.30 held
            new Vector4(0.7f, 0.15f, 0.35f, 0f),      // C: strong toe, 0.35 held
            new Vector4(0.8f, 0.30f, 0.50f, 0f),      // D: broad toe, 0.50 held (mid-tones down too)
            new Vector4(0.9f, 0.40f, 0.60f, 0f),      // E: ~gamma 1.45 about the sky value 0.60 (photo p10 / p50 match)
        };

        public static void ResolveLook(LightingPreset p, out float toe, out float toeP, out float pivot)
        {
            toe = p.lookToe; toeP = p.lookToeP; pivot = p.lookTonePivot;
            if (LookVariant >= 0 && LookVariant < LookVariants.Length)
            {
                var v = LookVariants[LookVariant];
                toe = v.x; toeP = v.y; pivot = v.z;
            }
        }

        /// <summary>
        /// r11: share of the ambient (sky + ground) radiance mirrored by leaf and needle surfaces (Kamion/Vegetation).
        /// A dielectric cuticle reflects ~4 % at normal incidence and more at grazing angles; part of that is already in
        /// the measured albedo textures. WORKING_VALUE, set so the crowns of the control cameras match the vegetation
        /// tones of the overcast reference photos (scripts/road-sky-metrics.py).
        /// </summary>
        public const float LeafSheen = 0.02f;

        static readonly int k_Haze = Shader.PropertyToID("_KamionHaze"), k_HazeColor = Shader.PropertyToID("_KamionHazeColor"),
            k_Tone = Shader.PropertyToID("_KamionTone"), k_Wet = Shader.PropertyToID("_KamionWet"),
            k_Cloud = Shader.PropertyToID("_KamionCloud"), k_CloudWind = Shader.PropertyToID("_KamionCloudWind"),
            k_CloudSun = Shader.PropertyToID("_KamionCloudSun"), k_CloudTex = Shader.PropertyToID("_KamionCloudTex"),
            k_ClearCloudCover = Shader.PropertyToID("_KamionClearCloudCover"),
            k_ClearSkySaturation = Shader.PropertyToID("_KamionClearSkySaturation"),
            k_SkyDisplay = Shader.PropertyToID("_KamionSkyDisplay"),
            k_ClearCloudPhoto = Shader.PropertyToID("_KamionClearCloudPhoto"),
            k_ClearCloudTex = Shader.PropertyToID("_KamionClearCloudTex"),
            k_ClearCloudRotation = Shader.PropertyToID("_KamionClearCloudRotation"),
            k_ClearCloudSourceLimits = Shader.PropertyToID("_KamionClearCloudSourceLimits"),
            k_LeafAmb = Shader.PropertyToID("_KamionLeafAmbient");

        /// <summary>Ground haze: extinction at height y = beta (1 + a exp(-(y - y0) / H)). Mirror of KamionFogTau.</summary>
        public static float FogTau(float beta, float a, float scaleHeightM, float y0, float cameraY, float pointY, float viewDepth)
        {
            float inv = 1f / Mathf.Max(scaleHeightM, 1f);
            float hc = Mathf.Max((cameraY - y0) * inv, -1f), hp = Mathf.Max((pointY - y0) * inv, -1f);
            float dh = hp - hc, ec = Mathf.Exp(-hc);
            float m = Mathf.Abs(dh) > 0.02f ? (ec - Mathf.Exp(-hp)) / dh : ec;
            return beta * Mathf.Max(viewDepth, 0f) * (1f + a * m);
        }

        /// <summary>Same presentation grade as the sky shader, also applied to fog so the horizon keeps one colour.
        /// This does not change the model's illuminance, SH, sun intensity or scene exposure.</summary>
        public static Color DisplaySkyFog(LightingPreset p, Color physical)
        {
            float gain = SkyDisplayGain(p), desaturation = Mathf.Clamp01(p.skyDisplayDesaturation);
            if (gain == 1f && desaturation == 0f) return physical;
            float y = physical.r*0.2126f+physical.g*0.7152f+physical.b*0.0722f;
            var display = Color.Lerp(physical, new Color(y, y, y, physical.a), desaturation)*gain;
            display.a = physical.a;
            return display;
        }

        // Zero is reserved for legacy serialized assets that predate this optional field.
        static float SkyDisplayGain(LightingPreset p) => p.skyDisplayGain > 0f ? Mathf.Clamp(p.skyDisplayGain, 0.001f, 1f) : 1f;

        public static void Push(EnvironmentLighting env, Color fogExposed)
        {
            var p = env.Active;
            if (p == null) { KamionHeadlamps.Reset(); KamionWetReflections.Reset(); return; }
            bool hasTier = QualityProfileApplier.HasCurrent;
            var t = hasTier ? QualityProfileApplier.Current : default;
            KamionHeadlamps.Push(env.Model, HeadlampsOverride ?? p.projectedHeadlamps, p.projectedHeadlampPeakCd, env.gameObject.scene);
            float skyGain = SkyDisplayGain(p), skyDesat = Mathf.Clamp01(p.skyDisplayDesaturation);
            Shader.SetGlobalVector(k_SkyDisplay, new Vector4(skyGain, skyDesat,
                skyGain < 1f || skyDesat > 0f ? 1f : 0f, 0f));

            // ---- haze
            bool layer = HazeOverride ?? !(hasTier && t.groundHazeOff);
            float beta = RenderSettings.fogDensity;
            float y0 = 0f;
            var gi = WorldSkyVisibility.Active;
            if (gi != null) y0 = gi.transform.TransformPoint(new Vector3(0f, gi.heightBase + 127f * gi.heightStep, 0f)).y;
            Shader.SetGlobalVector(k_Haze, new Vector4(beta, layer ? HazeFactorOverride ?? p.hazeGroundFactor : 0f,
                1f / Mathf.Max(HazeHeightOverride ?? p.hazeScaleHeightM, 1f), y0));
            // r11: diffuse sky light transmitted through the leaves (Kamion/Vegetation; per vertex, no fragment cost)
            float leaf = Mathf.Clamp01(LeafAmbientOverride ?? 1f);
            Shader.SetGlobalVector(k_LeafAmb, new Vector4(leaf, leaf * LeafSheen, 0f, 0f));
            var displayFog = DisplaySkyFog(p, fogExposed);
            Shader.SetGlobalVector(k_HazeColor, new Vector4(Mathf.Min(displayFog.r, 1f), Mathf.Min(displayFog.g, 1f), Mathf.Min(displayFog.b, 1f), 1f));

            // ---- tone toe in the shaders: only where no grading LUT runs
            ResolveLook(p, out float toe, out float toeP, out float pivot);
            bool post = hasTier && t.postProcessing;
            Shader.SetGlobalVector(k_Tone, post || toe <= 0f ? Vector4.zero : new Vector4(toe, toeP, LookGrading.ToeGain(toe, toeP, pivot) - 1f, 0f));

            // ---- wet surfaces, lawn variation
            Shader.SetGlobalVector(k_Wet, new Vector4(Mathf.Clamp01(WetOverride ?? p.wetness), p.puddles, Mathf.Clamp01(GrassOverride ?? p.grassVariation),
                p.wetFilmSmoothness > 0f ? Mathf.Clamp(p.wetFilmSmoothness, 0.01f, 0.8f) : 0f));
            KamionWetReflections.Push(p.wetLocalReflections);

            // ---- cloud deck
            int q = CloudOverride ?? (hasTier ? (t.cloudsOff ? -1 : t.cloudQuality) : 1);
            float contrast = q < 0 ? 0f : p.cloudContrast;
            // Clear clouds share the existing noise texture and sky pass. A zero coverage keeps the legacy dome.
            float clearCover = q < 0 ? 0f : Mathf.Clamp01(ClearCloudCoverOverride ?? p.clearCloudCover);
            Shader.SetGlobalFloat(k_ClearCloudCover, clearCover);
            Shader.SetGlobalFloat(k_ClearSkySaturation, Mathf.Clamp(p.clearSkySaturation, 1f, 4f));
            bool photo = clearCover > 0f && PhotographicClouds.TryGet(out _, out _);
            Shader.SetGlobalFloat(k_ClearCloudPhoto, photo ? 1f : 0f);
            float sourceMinElevation = Mathf.Clamp(p.clearCloudSourceMinElevationDeg, 0f, 5f);
            Shader.SetGlobalVector(k_ClearCloudSourceLimits,
                new Vector4(0.5f + sourceMinElevation/180f, sourceMinElevation > 0f ? 1f : 0f, 0f, 0f));
            if (photo && PhotographicClouds.TryGet(out var texture, out var sourceSun))
            {
                Shader.SetGlobalTexture(k_ClearCloudTex, texture);
                Vector3 sun = env.Model != null ? env.Model.SunDirection : Vector3.up;
                Shader.SetGlobalMatrix(k_ClearCloudRotation, Matrix4x4.Rotate(PhotographicClouds.SourceRotation(sun, sourceSun)));
            }
            Shader.SetGlobalVector(k_Cloud, new Vector4(contrast, Mathf.Max(q, 0), p.cloudScale, 5f));
            if (contrast > 0f || (clearCover > 0f && !photo))
            {
                Shader.SetGlobalTexture(k_CloudTex, CloudNoise.Texture);
                float time = Application.isPlaying ? Time.time : 0f;
                Vector2 o = p.cloudWind * (time * p.cloudScale);
                Shader.SetGlobalVector(k_CloudWind, new Vector4(o.x % 1f, o.y % 1f, (o.x * 1.7f) % 1f + 0.37f, (o.y * 1.7f) % 1f + 0.11f));
                Vector3 s = env.Model != null ? env.Model.SunDirection : Vector3.up;
                var az = new Vector2(s.x, s.z);
                az = az.sqrMagnitude > 1e-6f ? az.normalized : Vector2.right;
                Shader.SetGlobalVector(k_CloudSun, new Vector4(az.x, az.y, 1.6f, 0.035f));
            }
        }
    }

    /// <summary>CC0 photographic cloud opacity and self-shadowing. Cached once; no frame allocations.</summary>
    public static class PhotographicClouds
    {
        [System.Serializable] sealed class Source { public Vector3 sunDirection = Vector3.zero; }
        static bool s_Loaded;
        static Texture2D s_Texture;
        static Vector3 s_Sun;

        public static void ResetCache() { s_Loaded = false; s_Texture = null; }

        /// <summary>Align azimuth first, then elevation. A single minimum-angle rotation between suns can roll
        /// the entire sky by tens of degrees when their azimuths differ, despite similar sun altitudes.</summary>
        public static Quaternion SourceRotation(Vector3 sun, Vector3 sourceSun)
        {
            float azimuth = Mathf.Atan2(sun.x, sun.z) * Mathf.Rad2Deg;
            float sourceAzimuth = Mathf.Atan2(sourceSun.x, sourceSun.z) * Mathf.Rad2Deg;
            var yaw = Quaternion.AngleAxis(sourceAzimuth - azimuth, Vector3.up);
            return Quaternion.FromToRotation(yaw * sun, sourceSun) * yaw;
        }

        public static bool TryGet(out Texture2D texture, out Vector3 sunDirection)
        {
            if (!s_Loaded)
            {
                s_Loaded = true;
                s_Texture = Resources.Load<Texture2D>("Sky/T_ClearClouds");
                var metadata = Resources.Load<TextAsset>("Sky/ClearCloudsSource");
                var source = metadata != null ? JsonUtility.FromJson<Source>(metadata.text) : null;
                s_Sun = source != null ? source.sunDirection.normalized : Vector3.zero;
                if (s_Texture == null || s_Sun.sqrMagnitude < 0.9f)
                {
                    s_Texture = null;
                    Debug.LogWarning("[SKY_CLOUDS] Missing photographic cloud map/source axis; using the procedural diagnostic fallback.");
                }
            }
            texture = s_Texture;
            sunDirection = s_Sun;
            return texture != null;
        }
    }

    /// <summary>
    /// Tileable cloud noise for the sky's cloud deck (ADR 0080), generated once in memory (256², RGBA32 linear, mips):
    /// R billows (period 4, 4 octaves), G medium (period 5, 4 octaves), B fine detail (period 16, 3 octaves),
    /// A large sheets (period 2, 3 octaves). Every channel is stretched to mean 0.5 and 2.2 sigma of range, so the deck
    /// modulation has mean 1. Deterministic (fixed seeds): the same sky on every device and in every QA render.
    /// </summary>
    public static class CloudNoise
    {
        public const int Size = 256;
        static Texture2D s_Tex;

        public static Texture2D Texture
        {
            get
            {
                if (s_Tex == null) s_Tex = Build();
                return s_Tex;
            }
        }

        static float Hash(int x, int y, int seed)
        {
            unchecked
            {
                uint h = (uint)(x * 374761393 + y * 668265263 + seed * 362437);
                h = (h ^ (h >> 13)) * 1274126177u;
                h ^= h >> 16;
                return (h & 0xFFFFFF) / 16777215f;
            }
        }

        // Periodic value noise (quintic fade), period in cells.
        static float Value(float x, float y, int period, int seed)
        {
            int xi = Mathf.FloorToInt(x), yi = Mathf.FloorToInt(y);
            float fx = x - xi, fy = y - yi;
            fx = fx * fx * fx * (fx * (fx * 6f - 15f) + 10f);
            fy = fy * fy * fy * (fy * (fy * 6f - 15f) + 10f);
            int x0 = ((xi % period) + period) % period, y0 = ((yi % period) + period) % period;
            int x1 = (x0 + 1) % period, y1 = (y0 + 1) % period;
            float a = Hash(x0, y0, seed), b = Hash(x1, y0, seed), c = Hash(x0, y1, seed), d = Hash(x1, y1, seed);
            return Mathf.Lerp(Mathf.Lerp(a, b, fx), Mathf.Lerp(c, d, fx), fy);
        }

        public static float Fbm(float u, float v, int period, int octaves, int seed)
        {
            float sum = 0f, amp = 1f, norm = 0f;
            for (int o = 0; o < octaves; o++)
            {
                sum += amp * Value(u * period, v * period, period, seed + o * 17);
                norm += amp;
                amp *= 0.5f;
                period *= 2;
            }
            return sum / norm;
        }

        static Texture2D Build()
        {
            int n = Size;
            var ch = new float[4][];
            int[] period = { 4, 5, 16, 2 }, oct = { 4, 4, 3, 3 }, seed = { 11, 53, 97, 151 };
            for (int c = 0; c < 4; c++)
            {
                var a = new float[n * n];
                double mean = 0, sq = 0;
                for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float f = Fbm((x + 0.5f) / n, (y + 0.5f) / n, period[c], oct[c], seed[c]);
                    a[y * n + x] = f; mean += f; sq += f * f;
                }
                mean /= a.Length;
                float sigma = Mathf.Sqrt(Mathf.Max((float)(sq / a.Length - mean * mean), 1e-8f));
                for (int i = 0; i < a.Length; i++) a[i] = Mathf.Clamp01(0.5f + (a[i] - (float)mean) / (4.4f * sigma));
                ch[c] = a;
            }
            var px = new Color32[n * n];
            for (int i = 0; i < px.Length; i++)
                px[i] = new Color32((byte)(ch[0][i] * 255f + 0.5f), (byte)(ch[1][i] * 255f + 0.5f), (byte)(ch[2][i] * 255f + 0.5f), (byte)(ch[3][i] * 255f + 0.5f));
            var t = new Texture2D(n, n, TextureFormat.RGBA32, true, true)
            { name = "KamionCloudNoise", wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Trilinear, anisoLevel = 4, hideFlags = HideFlags.DontSave };
            t.SetPixels32(px);
            t.Apply(true, true);
            return t;
        }
    }
}
