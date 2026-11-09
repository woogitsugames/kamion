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
    ///   heads nearest to the camera (re-chosen 4× a second, no allocation), so the road under the nearest lamps is lit.
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
        static int s_HeadCount;
        static float s_On;
        static readonly int k_On = Shader.PropertyToID("_KamionStreetLamps"), k_LightsOn = Shader.PropertyToID("_KamionLampLights"),
            k_Emission = Shader.PropertyToID("_Emission");

        /// <summary>0..1: lamps on (from the sun elevation of the active lighting preset).</summary>
        public static float On => s_On;

        public static string Diagnostics => $"lamps on {s_On:F2}, glass materials {s_Glass.Count}, heads {s_HeadCount}";

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

        /// <summary>Lamp head positions in world space (the world re-sends them after a floating-origin shift).</summary>
        public static void SetHeads(Vector3[] heads, int count)
        {
            s_Heads = heads ?? new Vector3[0];
            s_HeadCount = Mathf.Min(count, s_Heads.Length);
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
            Shader.SetGlobalFloat(k_LightsOn, 0f);
        }

        void LateUpdate()
        {
            if (Time.unscaledTime < m_NextPick) return;
            m_NextPick = Time.unscaledTime + 0.25f;
            RefreshLights(viewCamera != null ? viewCamera : Camera.main);
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
                l.transform.position = s_Heads[m_Pick[i]];
                l.intensity = DownIntensityCd * k / Mathf.PI * s_On;
            }
            Shader.SetGlobalFloat(k_LightsOn, n > 0 ? 1f : 0f);
        }

        void Rebuild()
        {
            OnDisable();
            int count = QualityProfileApplier.HasCurrent ? QualityProfileApplier.Current.streetLights : 0;
            m_Lights = new Light[count];
            m_Pick = new int[count];
            for (int i = 0; i < count; i++)
            {
                var go = new GameObject("StreetLampLight " + i) { hideFlags = HideFlags.DontSave };
                go.transform.SetParent(transform, false);
                var l = go.AddComponent<Light>();
                l.type = LightType.Point;
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
            // Small n (≤ 8): insertion into a fixed list, O(lamps · n), no allocation beyond the first call.
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
