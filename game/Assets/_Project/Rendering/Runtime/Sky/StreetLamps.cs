using System.Collections.Generic;
using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// Street lamps at dusk (review r4 L3). The world registers its lamp-glass materials and the lamp head positions
    /// (WorldInstances); this class
    /// - writes the lamp luminance into the glass materials (Kamion/World Surface _Emission, cd/m²) and the global switch
    ///   _KamionStreetLamps from the sun elevation (Polish municipal lighting runs on astronomical clocks / twilight
    ///   switches: on around sunset; here a fade from 3° to 1° elevation, WORKING_VALUE);
    /// - on tiers with <see cref="QualityProfile.Tier.streetLights"/> > 0 keeps that many real point lights at the lamp
    ///   heads nearest to the camera (re-chosen 4× a second, no allocation); since ADR 0062 they light vehicles and props
    ///   only (Kamion/World Surface ignores them and draws the analytic pools below, so nothing is lit twice);
    /// - ADR 0062 (review r8 N-20), every tier with <see cref="QualityProfile.Tier.lampPools"/> > 0: the heads nearest to a
    ///   focus 30 m ahead of the camera go to the world shader as a global array (_KamionLampPos, xyz + fade weight) and
    ///   Kamion/World Surface adds their inverse-square light with a full-cutoff luminaire shape (constant to 60° from the
    ///   nadir, zero at 75°) - the pools on the road at no light / shadow / per-object cost (Low has no point lights).
    ///   A lamp near the edge of the chosen set fades out over the last 25 % of the distance to the first lamp left out,
    ///   so re-choosing does not pop.
    /// - ADR 0191: each pool is one luminaire (not one column): its position on the arm, the arm direction and LED / sodium
    ///   come from the lamp prototypes (WorldInstances, <see cref="StreetLampOptics.LuminairesFromGlass"/>), and the shader
    ///   draws the asymmetric road-luminaire footprint of <see cref="StreetLampOptics"/> (long along the road, short
    ///   behind the column) instead of a round 60° disc; sodium luminaires tint their pool. Tiers with
    ///   <see cref="QualityProfile.Tier.lampPoolSpecular"/> add the GGX highlight of each lamp (the streak on asphalt).
    /// Photometry (WORKING_VALUE, typical LED road luminaire 8–12 klm): lens luminance 2·10⁵ cd/m² (clips to white, as on a
    /// phone), downward intensity ~2500 cd → Unity intensity = I·k/π in exposed units, range 30 m. Sodium (old
    /// luminaires, "_sodium" materials) 2000 K tint.
    /// </summary>
    [ExecuteAlways]
    public sealed class StreetLamps : MonoBehaviour
    {
        public const float LensLuminance = 2.0e5f;
        public const float DownIntensityCd = 2500f;
        static readonly Color k_Led = new Color(1f, 0.93f, 0.82f), k_Sodium = new Color(1f, 0.62f, 0.25f);

        static readonly List<Material> s_Glass = new List<Material>();
        static Vector3[] s_Heads = new Vector3[0];
        static Vector4[] s_Axes = new Vector4[0];
        static int s_HeadCount;
        static float s_On;
        static readonly int k_On = Shader.PropertyToID("_KamionStreetLamps"), k_LightsOn = Shader.PropertyToID("_KamionLampLights"),
            k_Emission = Shader.PropertyToID("_Emission"), k_PoolPos = Shader.PropertyToID("_KamionLampPos"),
            k_PoolCount = Shader.PropertyToID("_KamionLampCount"), k_PoolColor = Shader.PropertyToID("_KamionLampColor"),
            k_PoolAxis = Shader.PropertyToID("_KamionLampAxis"), k_PoolSodium = Shader.PropertyToID("_KamionLampSodium"),
            k_PoolSpec = Shader.PropertyToID("_KamionLampSpec"), k_PoolFloor = Shader.PropertyToID("_KamionLampFloor");
        /// <summary>
        /// s20 night-int (review 0191 P1-2, Mapillary night frames: the carriageway between columns is never black): horizontal
        /// illuminance near lamps from everything the analytic set leaves out - the lamps beyond the N nearest, light
        /// reflected by façades and paving, and the urban sky glow. ~2.5 % of the nadir of a 2500 cd lamp at 8 m (39 lx),
        /// under the EN 13201 minimum of a lit road (Uo 0.35-0.4 of ~10-15 lx average). WORKING_VALUE.
        /// </summary>
        public const float NightFloorLux = 1.0f;
        /// <summary>s20 night-int: the night floor fades to zero this far (horizontal, m) from the nearest chosen luminaire. WORKING_VALUE.</summary>
        public const float NightFloorReachM = 45f;
        /// <summary>
        /// s20 night-int (review 0191 P1-4): the High / Ultra lights are spots pointing down with the luminaire's cut-off
        /// (outer cone 150° = 75° from the nadir) instead of spheres - a sphere at the lens lit the arm and housing above it
        /// from 0.1-0.5 m ("neon" arms) and nearby thujas from the side. Inner cone = soft edge. WORKING_VALUE.
        /// </summary>
        public const float SpotOuterDeg = 150f, SpotInnerDeg = 110f;
        /// <summary>Upper limit of the analytic pools (size of the shader array).</summary>
        public const int MaxPools = 8;
        /// <summary>The pool focus sits this far ahead of the camera (horizontal), where the visible road is.</summary>
        public const float PoolFocusAheadM = 30f;
        static readonly Vector4[] s_PoolPos = new Vector4[MaxPools];
        static readonly Vector4[] s_PoolAxis = new Vector4[MaxPools];
        /// <summary>Number of analytic pools sent to the world shader in the last refresh (diagnostics / tests).</summary>
        public static int PoolCount { get; private set; }
        /// <summary>The pool array of the last refresh (xyz head, w fade weight); read-only use.</summary>
        public static Vector4[] PoolPositions => s_PoolPos;
        /// <summary>ADR 0191: the pool axes of the last refresh (arm x, arm z, sodium 0/1, road optic 0/1); read-only use.</summary>
        public static Vector4[] PoolAxes => s_PoolAxis;
        /// <summary>
        /// ADR 0191: sodium tint relative to the LED pool colour at equal luminance (Rec.709 Y) - the intensity in cd is
        /// photometric, so a sodium pool is as bright as an LED one, only orange. Applied per pool in the shader.
        /// </summary>
        public static Color SodiumTintRatio
        {
            get
            {
                float yl = 0.2126f * k_Led.r + 0.7152f * k_Led.g + 0.0722f * k_Led.b;
                float ys = 0.2126f * k_Sodium.r + 0.7152f * k_Sodium.g + 0.0722f * k_Sodium.b;
                float k = yl / ys;
                return new Color(k_Sodium.r * k / k_Led.r, k_Sodium.g * k / k_Led.g, k_Sodium.b * k / k_Led.b, 0f);
            }
        }

        /// <summary>0..1: lamps on (from the sun elevation of the active lighting preset).</summary>
        public static float On => s_On;

        public static string Diagnostics => $"lamps on {s_On:F2}, glass materials {s_Glass.Count}, heads {s_HeadCount}, pools {PoolCount}";

        /// <summary>ADR 0191: the chosen pools (head xyz, weight | arm x z, sodium, road optic) for QA logs. Allocates.</summary>
        public static string PoolDiagnostics
        {
            get
            {
                var sb = new System.Text.StringBuilder();
                for (int i = 0; i < PoolCount; i++)
                {
                    Vector4 p = s_PoolPos[i], a = s_PoolAxis[i];
                    sb.Append(System.FormattableString.Invariant($"[{p.x:F1} {p.y:F1} {p.z:F1} w{p.w:F2} | {a.x:F2} {a.y:F2} s{a.z:F0} r{a.w:F0}] "));
                }
                return sb.ToString();
            }
        }

        public static bool IsLampGlass(Material m) => m != null && m.name.StartsWith("M_lamp_glass");

        /// <summary>Called by the world for each lamp-glass material copy it draws with.</summary>
        public static void RegisterGlass(Material m)
        {
            if (m == null || s_Glass.Contains(m)) return;
            s_Glass.Add(m);
            bool sodium = m.name.Contains("sodium");
            Color c = (sodium ? k_Sodium : k_Led) * LensLuminance;
            m.SetVector(k_Emission, new Vector4(c.r, c.g, c.b, 0f));
            // tools/worldgen/streetscape/props.py lamp(): the glass quad's normal points up (into the housing), so it is
            // back-face culled from the street. Drawn double-sided until the generator flips it (world-builder).
            m.SetFloat("_Cull", 0f);
        }

        public static void UnregisterGlass(Material m) => s_Glass.Remove(m);

        /// <summary>Lamp head positions in world space (the world re-sends them after a floating-origin shift).
        /// Without axes every head is a symmetric LED luminaire.</summary>
        public static void SetHeads(Vector3[] heads, int count) => SetHeads(heads, null, count);

        /// <summary>ADR 0191: luminaire positions + axes (arm x, arm z, sodium 0/1, road optic 0/1) in world space.</summary>
        public static void SetHeads(Vector3[] heads, Vector4[] axes, int count)
        {
            s_Heads = heads ?? new Vector3[0];
            s_HeadCount = Mathf.Min(count, s_Heads.Length);
            s_Axes = axes ?? new Vector4[0];
            LampGlare.Invalidate();
        }

        /// <summary>EnvironmentLighting: lamps follow the sun elevation.</summary>
        public static void SetSunElevation(float elevationDeg)
        {
            s_On = Mathf.Clamp01(Mathf.InverseLerp(3f, 1f, elevationDeg));
            Shader.SetGlobalFloat(k_On, s_On);
        }

        // ---------------------------------------------------------------- point lights near the camera
        Light[] m_Lights = new Light[0];
        int[] m_Pick = new int[0];
        float m_NextPick;
        public Camera viewCamera;

        void OnDisable()
        {
            foreach (var l in m_Lights) if (l != null) { if (Application.isPlaying) Destroy(l.gameObject); else DestroyImmediate(l.gameObject); }
            m_Lights = new Light[0];
            LampGlare.Dispose();
            Shader.SetGlobalFloat(k_LightsOn, 0f);
            PoolCount = 0;
            Shader.SetGlobalFloat(k_PoolCount, 0f);
            Shader.SetGlobalVector(k_PoolFloor, Vector4.zero);
        }

        void LateUpdate()
        {
            if (Time.unscaledTime < m_NextPick) return;
            m_NextPick = Time.unscaledTime + 0.25f;
            RefreshLights(ViewCameraResolver.Resolve(viewCamera));   // not Camera.main: null under qacam (ADR 0044 r9)
        }

        /// <summary>Re-chooses the nearest lamps for the point lights (visual QA calls it per camera).</summary>
        public void RefreshLights(Camera cam)
        {
            int want = QualityProfileApplier.HasCurrent ? QualityProfileApplier.Current.streetLights : 0;
            if (s_On <= 0f || cam == null || s_HeadCount == 0) want = 0;
            if (m_Lights.Length != (QualityProfileApplier.HasCurrent ? QualityProfileApplier.Current.streetLights : 0)) Rebuild();
            var env = EnvironmentLighting.Instance;
            float k = env != null && env.Model != null ? env.Model.Exposure : 0f;
            int n = Mathf.Min(want, m_Lights.Length);
            if (n > 0) PickNearest(cam.transform.position, n);
            for (int i = 0; i < m_Lights.Length; i++)
            {
                var l = m_Lights[i];
                bool use = i < n && m_Pick[i] >= 0;
                l.enabled = use;
                if (!use) continue;
                int hi = m_Pick[i];
                l.transform.position = s_Heads[hi];
                l.color = hi < s_Axes.Length && s_Axes[hi].z > 0.5f ? SodiumLightColor : k_Led;
                l.intensity = DownIntensityCd * k / Mathf.PI * s_On;
            }
            Shader.SetGlobalFloat(k_LightsOn, n > 0 ? 1f : 0f);
            RefreshPools(cam, k);
            LampGlare.Sync(s_Heads, s_Axes, s_HeadCount, s_On, k, k_Led, SodiumLightColor);   // ADR 0192 lens glare, s20: colour per luminaire
        }

        /// <summary>ADR 0062: analytic pools on the world surfaces (all tiers with lampPools > 0).</summary>
        void RefreshPools(Camera cam, float exposure)
        {
            int want = QualityProfileApplier.HasCurrent ? Mathf.Min(QualityProfileApplier.Current.lampPools, MaxPools) : 0;
            if (s_On <= 0f || cam == null || s_HeadCount == 0 || want <= 0)
            {
                PoolCount = 0;
                Shader.SetGlobalFloat(k_PoolCount, 0f);
                Shader.SetGlobalVector(k_PoolFloor, Vector4.zero);
                return;
            }
            Vector3 fwd = cam.transform.forward; fwd.y = 0f;
            bool spec = QualityProfileApplier.HasCurrent && QualityProfileApplier.Current.lampPoolSpecular;
            Vector3 focus = cam.transform.position + (fwd.sqrMagnitude > 1e-6f ? fwd.normalized * PoolFocusAheadM : Vector3.zero);
            // n + 1 nearest: the first lamp left out sets the fade-out distance of the chosen ones.
            int n = Mathf.Min(want + 1, s_HeadCount);
            EnsurePick(n);
            PickNearest(focus, n);
            int used = Mathf.Min(want, n);
            float edge = n > want ? Mathf.Sqrt(m_Dist[want]) : float.MaxValue;
            for (int i = 0; i < MaxPools; i++)
            {
                if (i >= used || m_Pick[i] < 0) { s_PoolPos[i] = Vector4.zero; s_PoolAxis[i] = Vector4.zero; continue; }
                Vector3 h = s_Heads[m_Pick[i]];
                s_PoolAxis[i] = m_Pick[i] < s_Axes.Length ? s_Axes[m_Pick[i]] : Vector4.zero;
                float d = Mathf.Sqrt(m_Dist[i]);
                float w = edge < float.MaxValue ? Mathf.Clamp01((edge - d) / (0.25f * edge)) : 1f;
                s_PoolPos[i] = new Vector4(h.x, h.y, h.z, w);
            }
            PoolCount = used;
            Shader.SetGlobalVectorArray(k_PoolPos, s_PoolPos);
            Shader.SetGlobalVectorArray(k_PoolAxis, s_PoolAxis);
            Shader.SetGlobalVector(k_PoolSodium, SodiumTintRatio);
            Shader.SetGlobalFloat(k_PoolSpec, spec ? 1f : 0f);
            Shader.SetGlobalFloat(k_PoolCount, used);
            // Same photometry as the point lights: E = I cos / d², Unity display units I·k/π (Lambert without 1/π).
            Color c = k_Led * (DownIntensityCd * exposure / Mathf.PI * s_On);
            Shader.SetGlobalVector(k_PoolColor, new Vector4(c.r, c.g, c.b, 0f));
            bool floorOff = QualityProfileApplier.HasCurrent && QualityProfileApplier.Current.lampFloorOff;
            Color f = k_Led * (floorOff ? 0f : NightFloorLux * exposure / Mathf.PI * s_On);
            Shader.SetGlobalVector(k_PoolFloor, new Vector4(f.r, f.g, f.b, NightFloorReachM));
        }

        /// <summary>s20 night-int: colour of a sodium luminaire's light at the LED luminance (pools use the same ratio).</summary>
        public static Color SodiumLightColor
        {
            get { var r = SodiumTintRatio; return new Color(k_Led.r * r.r, k_Led.g * r.g, k_Led.b * r.b, 1f); }
        }

        void EnsurePick(int n)
        {
            if (m_Pick.Length < n) { m_Pick = new int[n]; m_Dist = new float[n]; }
        }

        void Rebuild()
        {
            OnDisable();
            int count = QualityProfileApplier.HasCurrent ? QualityProfileApplier.Current.streetLights : 0;
            m_Lights = new Light[count];
            EnsurePick(Mathf.Max(count, MaxPools + 1));
            for (int i = 0; i < count; i++)
            {
                var go = new GameObject("StreetLampLight " + i) { hideFlags = HideFlags.DontSave };
                go.transform.SetParent(transform, false);
                var l = go.AddComponent<Light>();
                l.type = LightType.Spot;
                l.spotAngle = SpotOuterDeg;
                l.innerSpotAngle = SpotInnerDeg;
                go.transform.rotation = Quaternion.LookRotation(Vector3.down, Vector3.forward);
                l.range = 30f;
                l.color = k_Led;
                l.shadows = LightShadows.None;
                l.renderMode = LightRenderMode.ForcePixel;
                l.enabled = false;
                m_Lights[i] = l;
            }
        }

        void PickNearest(Vector3 p, int n)
        {
            for (int i = 0; i < m_Pick.Length; i++) m_Pick[i] = -1;
            // Small n (≤ 9): insertion into a fixed list, O(lamps · n), no allocation beyond the first call.
            if (m_Dist.Length != m_Pick.Length) m_Dist = new float[m_Pick.Length];
            for (int i = 0; i < n; i++) m_Dist[i] = float.MaxValue;
            for (int h = 0; h < s_HeadCount; h++)
            {
                float d = (s_Heads[h] - p).sqrMagnitude;
                if (d >= m_Dist[n - 1]) continue;
                int j = n - 1;
                while (j > 0 && m_Dist[j - 1] > d) { m_Dist[j] = m_Dist[j - 1]; m_Pick[j] = m_Pick[j - 1]; j--; }
                m_Dist[j] = d; m_Pick[j] = h;
            }
        }
        float[] m_Dist = new float[0];
    }
}
