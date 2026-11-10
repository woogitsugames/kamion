using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// Cab interior fill for Kamion/Cab Interior (track A7, visual review r2 A6 #1 P0: at low sun the cab was black).
    /// URP gives the interior only the open-sky SH (x baked AO) and the direct sun patches. A real cab is also lit by the
    /// light that enters through the glass and bounces off the dash, floor and seats. That first bounce is estimated once
    /// per frame with the integrating-sphere formula on the cab's glazing:
    ///   flux in   = tau * sum_w A_w * (E_sun_normal * max(0, n_w . s) + E_sky_w)
    ///   E_bounce  = flux * rho / (A_cab * (1 - rho))
    /// and passed as _CabFill = E_bounce * exposure / pi (exposed radiance per unit albedo, the convention of SH ambient).
    /// E_sky_w is the sky illuminance on a vertical window (~0.5 of the horizontal sky illuminance), so the fill follows
    /// the sun direction relative to the truck: sun through the windscreen fills the cab, sun from behind barely does.
    /// _CabGain is the cab-view part of D23 (owner: "like a phone photo"): a phone exposes a backlit interior up with local
    /// tone mapping, so when the camera is inside the cab the interior is lifted by <see cref="cabViewEv"/> stops.
    /// All constants are WORKING_VALUE (cab geometry from glass_interface.json / door_interface.json, albedo from the
    /// koniak trim table); acceptance: lower dash and door card above 8 % display value at 9 deg sun (review r2).
    /// Cost: a few dozen flops on the CPU and one SH-add in the shader; no light, no pass, every tier.
    /// </summary>
    [ExecuteAlways]
    public sealed class CabInteriorLighting : MonoBehaviour
    {
        [Tooltip("Cab frame (CAB_MOUNT_REF): +Z forward, +Y up")] public Transform cab;
        [Tooltip("Cab interior bounds in the cab frame (camera inside = cab view)")]
        public Bounds interiorBounds = new Bounds(new Vector3(0f, 1.4f, 0f), new Vector3(2.4f, 2.6f, 2.4f));
        [Tooltip("Glass transmittance (laminated windscreen ~0.75, side glass ~0.8)")] public float glassTransmittance = 0.75f;
        [Tooltip("Mean interior albedo for the bounce (koniak inserts, grey headliner, dark dash)")] public float meanAlbedo = 0.22f;
        [Tooltip("Interior surface area (m^2)")] public float interiorArea = 26f;
        [Tooltip("Cab-view lift in stops (phone local tone mapping, D23; A8: 1.0 with the enclosure below, review r4 L1 '+0.7-1.0 EV')")] public float cabViewEv = 1.0f;
        [Tooltip("Share of the open-sky ambient (SH) blocked by the cab roof and walls (A8, review r4 E2: from outside the " +
                 "interior was lit like an open terrace, so the windscreen read as clear glass). Glazing ~4.3 m^2 of ~26 m^2. WORKING_VALUE")]
        public float enclosure = 0.6f;
        [Tooltip("Extra fill scale (1 = physical estimate)")] public float fillScale = 1f;
        [Tooltip("Colour of the bounce (dash, koniak, floor mat). Mild: review r3 C2 - a strongly warm tint on top of the sun " +
                 "colour turned the black plastics beige at low sun")] public Color bounceTint = new Color(1f, 0.97f, 0.93f);

        /// <summary>Windows in the cab frame: outward normal and daylight-opening area (m^2).</summary>
        static readonly Vector3[] k_WinN =
        {
            new Vector3(0f, 0.3256f, 0.9455f),  // windscreen, rake 19 deg (glass_interface.json)
            new Vector3(-1f, 0f, 0.05f),        // driver door glass
            new Vector3(1f, 0f, 0.05f),         // passenger door glass
        };
        static readonly float[] k_WinA = { 1.85f, 0.62f, 0.62f };

        [Tooltip("Cab-view local shadow lift (review r4 L1): k in gain = 1 + k (k0 / (Y + k0))^3 on the interior; -1 = from the " +
                 "quality tier (QualityProfile.cabShadowLift)")] public float shadowLift = -1f;
        [Tooltip("Knee of the shadow lift (exposed linear luminance; 0.004 = ~6 % display)")] public float shadowLiftKnee = 0.004f;

        [Tooltip("Cab metering (review r4 L1 at low sun / dusk): share (0..1) of the drop of the interior ambient level below the " +
                 "overcast reference that the cab view compensates, like a phone metering a backlit cab. The exposure table " +
                 "(ADR 0016) exposes low sun for the sunlit walls, so the cab - lit by the sky only - fell 2-3 EV below its " +
                 "overcast level (lower dash and footwell < 3 %). 0 = fixed cabViewEv only. WORKING_VALUE")]
        [Range(0f, 1f)] public float cabMeterStrength = 0.6f;
        [Tooltip("Maximum extra cab-view lift from the cab metering (stops); dusk must still read darker than day")] public float cabMeterMaxEv = 1.5f;

        // Interior ambient key of the overcast reference preset (computed once; no per-frame allocation).
        static float s_RefKey = -1f;

        static readonly int k_Fill = Shader.PropertyToID("_CabFill"), k_Gain = Shader.PropertyToID("_CabGain"),
            k_Lift = Shader.PropertyToID("_CabShadowLift"), k_Enclosure = Shader.PropertyToID("_CabEnclosure");

        /// <summary>Interior ambient key: open-sky SH on an upward normal through the enclosure + first-bounce fill (exposed).</summary>
        float Key(SkyModel m, Vector3 fill) =>
            (1f - Mathf.Clamp01(enclosure)) * m.SkyHorizontalIlluminanceLux * m.Exposure / Mathf.PI + (0.2126f * fill.x + 0.7152f * fill.y + 0.0722f * fill.z);

        /// <summary>Extra cab-view stops (0..cabMeterMaxEv) compensating the interior key below the overcast reference.</summary>
        public float CabMeterEv(SkyModel m, Vector3 fill)
        {
            if (m == null || cabMeterStrength <= 0f) return 0f;
            if (s_RefKey < 0f)
            {
                var p = LightingPreset.CreateOvercast();
                var rm = p.CreateModel();
                float eSky = rm.SkyHorizontalIlluminanceLux * 0.5f, flux = 0f;
                for (int i = 0; i < k_WinA.Length; i++) flux += k_WinA[i] * eSky;
                float rho = Mathf.Clamp(meanAlbedo, 0.01f, 0.9f);
                float f = flux * glassTransmittance * rho / (interiorArea * (1f - rho)) * rm.Exposure / Mathf.PI * fillScale;
                s_RefKey = Key(rm, new Vector3(f, f, f));
                if (Application.isPlaying) Destroy(p); else DestroyImmediate(p);
            }
            float key = Key(m, fill);
            if (key <= 1e-6f || s_RefKey <= 0f) return 0f;
            return Mathf.Clamp(cabMeterStrength * Mathf.Log(s_RefKey / key, 2f), 0f, Mathf.Max(0f, cabMeterMaxEv));
        }

        public float LastMeterEv { get; private set; }
        public Vector3 LastFill { get; private set; }
        public float LastGain { get; private set; } = 1f;
        public Camera viewCamera;

        void OnDisable()
        {
            Shader.SetGlobalVector(k_Fill, Vector4.zero);
            Shader.SetGlobalFloat(k_Gain, 1f);
            Shader.SetGlobalVector(k_Lift, Vector4.zero);
            Shader.SetGlobalFloat(k_Enclosure, 0f);
        }

        void LateUpdate() => Refresh(viewCamera != null ? viewCamera : Camera.main);

        /// <summary>Recomputes the fill (visual QA calls it per control camera).</summary>
        public void Refresh(Camera cam)
        {
            var env = EnvironmentLighting.Instance;
            if (env == null) env = FindAnyObjectByType<EnvironmentLighting>();
            var m = env != null ? env.Model : null;
            Transform t = cab != null ? cab : transform;
            Vector3 fill = Vector3.zero;
            if (m != null)
            {
                Vector3 sLocal = t.InverseTransformDirection(m.SunDirection);
                float eSky = m.SkyHorizontalIlluminanceLux * 0.5f;
                float fluxSun = 0f, fluxSky = 0f;
                for (int i = 0; i < k_WinN.Length; i++)
                {
                    float cos = Mathf.Max(0f, Vector3.Dot(k_WinN[i].normalized, sLocal));
                    fluxSun += k_WinA[i] * m.SunNormalIlluminanceLux * cos;
                    fluxSky += k_WinA[i] * eSky;
                }
                float rho = Mathf.Clamp(meanAlbedo, 0.01f, 0.9f);
                float bounce = glassTransmittance * rho / (interiorArea * (1f - rho)) * m.Exposure / Mathf.PI * fillScale;
                // Sun part in the sun's colour, sky part neutral (overcast-grey daylight through the glass; review r3 C2).
                Color c = (m.SunColor * fluxSun + Color.white * fluxSky) * bounceTint * bounce;
                fill = new Vector3(c.r, c.g, c.b);
            }
            float gain = 1f, lift = 0f;
            if (cam != null && interiorBounds.Contains(t.InverseTransformPoint(cam.transform.position)))
            {
                gain = Mathf.Pow(2f, cabViewEv + CabMeterEv(m, fill));
                // Phone-like local tone mapping of the cab view (review r4 L1): only the interior surfaces, only in the
                // cab view, strongest in the deepest shade - the sky through the glass and the lit dash are untouched.
                lift = shadowLift >= 0f ? shadowLift : QualityProfileApplier.HasCurrent ? QualityProfileApplier.Current.cabShadowLift : 8f;
            }
            LastMeterEv = Mathf.Log(gain, 2f) - (gain > 1f ? cabViewEv : 0f);
            LastFill = fill;
            LastGain = gain;
            Shader.SetGlobalVector(k_Fill, new Vector4(fill.x, fill.y, fill.z, 0f));
            Shader.SetGlobalFloat(k_Gain, gain);
            Shader.SetGlobalVector(k_Lift, new Vector4(lift, Mathf.Max(1e-4f, shadowLiftKnee), 0f, 0f));
            Shader.SetGlobalFloat(k_Enclosure, Mathf.Clamp01(enclosure));
        }
    }
}
