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
        [Tooltip("Enclosure for every view from outside the cab (review r5 E2 'aquarium windscreen': from outside the interior " +
                 "was ~3x too bright against the sky). Physical share of the open-sky ambient the cab blocks: glazing ~4.3 m^2 " +
                 "of ~26 m^2 interior, transmittance 0.75, so the interior sees ~10-15 % of the open sky; the first bounce comes " +
                 "from _CabFill. The lower in-cab value above is part of the cab-view local tone mapping (ADR 0029). WORKING_VALUE")]
        [Range(0f, 1f)] public float exteriorEnclosure = 0.88f;
        [Tooltip("Desaturation of the lifted share of deep shade in the cab view (review r5 L2: black plastics went brown)")]
        [Range(0f, 1f)] public float shadowLiftNeutral = 0.8f;
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
        [Tooltip("D84: cab-view lift (stops) left at night; the day lift fades to it between twilightStartSunDeg and " +
            "twilightFullSunDeg so the wheel is not brighter than the world outside. WORKING_VALUE")] public float nightViewEv = 0.45f;
        [Tooltip("True sun elevation where the twilight fade starts / is complete [deg]")] public float twilightStartSunDeg = 3f;
        public float twilightFullSunDeg = -5f;
        [Tooltip("D84: warm spill of backlit legends / cluster / courtesy light on the trim at night (display-referred " +
            "radiance per unit albedo; 0 = off). WORKING_VALUE")] public float panelGlow = 0.07f;
        public Color panelGlowColor = new Color(1f, 0.80f, 0.58f);

        // Interior ambient key of the overcast reference preset (computed once; no per-frame allocation).
        static float s_RefKey = -1f;

        static readonly int k_Fill = Shader.PropertyToID("_CabFill"), k_Gain = Shader.PropertyToID("_CabGain"),
            k_BacklightEnvironment = Shader.PropertyToID("_CabBacklightEnvironment"),
            k_Lift = Shader.PropertyToID("_CabShadowLift"), k_Enclosure = Shader.PropertyToID("_CabEnclosure"),
            k_Parity = Shader.PropertyToID("_KamionToeParity"),
            k_CamOutside = Shader.PropertyToID("_KamionCamOutside"),
            k_ToeInv = Shader.PropertyToID("_KamionCabToeInv"), k_ToeInvDisplay = Shader.PropertyToID("_KamionCabToeInvDisplay");

        [Tooltip("ADR 0080: share (0..1) of the world contrast toe (LightingPreset.lookToe, overcast variant 3) that the cab " +
                 "view undoes on the interior and the cluster, so the dash, wheel and gauges keep their ADR 0044 display " +
                 "instead of falling close to black. 0 = interior takes the full world curve. WORKING_VALUE")]
        [Range(0f, 1f)] public float toeCompensation = 1f;

        [Tooltip("Cab view on the tiers without post-processing: write the D23 toe in the cab shaders (KamionToeParity.hlsl, " +
                 "ADR 0044 addendum r7); off = plain sRGB toe on Low (A/B)")]
        public bool toeParity = true;

        [Tooltip("ADR 0072: views from outside the cab on the tiers without post-processing also write the D23 toe in the truck " +
                 "shaders (Kamion/Truck Exterior, cab interior through the glass), so the shaded TRAKT front reads on Low as on " +
                 "High (Low lowsun: louvre faces 1.2 display points under High). Off = plain sRGB outside the cab view (A/B)")]
        public bool exteriorToeParity = true;

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
                p.exposureCompensation = 0f;   // ADR 0080: the reference stays the table exposure (variant 3 biases the preset by -0.2 EV)
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

        /// <summary>D84: 0 by day (sun at or above <paramref name="startDeg"/>, e.g. LP_LowSun 9 deg), 1 at night (at or
        /// below <paramref name="fullDeg"/>, e.g. LP_Dusk -6 deg), smooth in between. Mirror: CabTwilightTests.</summary>
        public static float NightFactor(float sunElevationDeg, float startDeg, float fullDeg) =>
            1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(fullDeg, startDeg, sunElevationDeg));

        /// <summary>D84: cab-view lift in stops: the day lift fades to min(nightStops, cabViewStops) with the night factor.</summary>
        public static float CabViewStops(float dayStops, float cabViewStops, float nightStops, float night) =>
            Mathf.Lerp(dayStops, Mathf.Min(nightStops, cabViewStops), Mathf.Clamp01(night));

        public float LastMeterEv { get; private set; }
        public Vector3 LastFill { get; private set; }
        public float LastGain { get; private set; } = 1f;
        public Camera viewCamera;

        /// <summary>ADR 0244: cabs between OnEnable and OnDisable (KamionHeadlamps binding recheck without FindObjectsOfTypeAll).</summary>
        public static System.Collections.Generic.IReadOnlyList<CabInteriorLighting> Enabled => s_Enabled;
        internal static readonly System.Collections.Generic.List<CabInteriorLighting> s_Enabled = new System.Collections.Generic.List<CabInteriorLighting>(4);

        void OnEnable()
        {
            if (!s_Enabled.Contains(this)) s_Enabled.Add(this);
        }

        void OnDisable()
        {
            s_Enabled.Remove(this);
            Shader.SetGlobalVector(k_BacklightEnvironment, Vector4.zero);
            Shader.SetGlobalVector(k_Fill, Vector4.zero);
            Shader.SetGlobalFloat(k_Gain, 1f);
            Shader.SetGlobalVector(k_Lift, Vector4.zero);
            Shader.SetGlobalFloat(k_Enclosure, 0f);
            Shader.SetGlobalVector(k_Parity, Vector4.zero);
            Shader.SetGlobalFloat(k_CamOutside, 0f);
            Shader.SetGlobalVector(k_ToeInv, Vector4.zero);
            Shader.SetGlobalVector(k_ToeInvDisplay, Vector4.zero);
        }

        void LateUpdate() => RefreshForView();

        /// <summary>
        /// Per-frame path: the view camera is resolved with <see cref="ViewCameraResolver"/>, never plain Camera.main
        /// (ADR 0044 addendum r9: under the on-device control camera Camera.main was null, the cab view state was never
        /// applied and the phone cab-dash frames were 25-44 % black against ~1.5 % in the editor).
        /// </summary>
        public void RefreshForView()
        {
            var cam = ViewCameraResolver.Resolve(viewCamera);
            Refresh(cam);
            bool inCab = LastGain > 1f;
            if (cam != m_LoggedCam || inCab != m_LoggedInCab)
            {
                m_LoggedCam = cam; m_LoggedInCab = inCab;
                if (Application.isPlaying)
                    Debug.Log($"[CAB] view camera {(cam != null ? cam.name : "none")} cabView={inCab} gain {LastGain:F2} meter {LastMeterEv:F2} EV");
            }
        }

        Camera m_LoggedCam;
        bool m_LoggedInCab;

        EnvironmentLighting m_FallbackEnv;
        float m_NextEnvSearch = float.NegativeInfinity;
        /// <summary>Scene searches made by <see cref="FallbackEnvironment"/> (tests).</summary>
        public int EnvironmentSearches { get; private set; }
        /// <summary>Play mode: at most one scene search per this many seconds while no EnvironmentLighting is enabled.</summary>
        public const float EnvironmentSearchIntervalS = 1f;

        /// <summary>
        /// EnvironmentLighting when <see cref="EnvironmentLighting.Instance"/> is null (none enabled, e.g. DrivingLab, which
        /// has no sky rig). ADR 0244: in play mode the FindAnyObjectByType scene search ran every LateUpdate there; it is now
        /// throttled to <see cref="EnvironmentSearchIntervalS"/> (the same pattern as FurnitureRetroSource, ADR 0131) and
        /// the result is kept while it lives. Edit mode (visual QA calls Refresh per control camera) searches every call,
        /// as before.
        /// </summary>
        EnvironmentLighting FallbackEnvironment()
        {
            if (Application.isPlaying)
            {
                if (m_FallbackEnv != null) return m_FallbackEnv;
                float now = Time.unscaledTime;
                if (now < m_NextEnvSearch) return null;
                m_NextEnvSearch = now + EnvironmentSearchIntervalS;
            }
            EnvironmentSearches++;
            m_FallbackEnv = FindAnyObjectByType<EnvironmentLighting>();
            return m_FallbackEnv;
        }

        /// <summary>Recomputes the fill (visual QA calls it per control camera).</summary>
        public void Refresh(Camera cam)
        {
            var env = EnvironmentLighting.Instance;
            if (env == null) env = FallbackEnvironment();
            var m = env != null ? env.Model : null;
            // ADR 0112 r3: physical panel emission follows exposure, independently of ambient/AO and cab-view lift.
            // z is validity: an unset/missing environment must never turn legends on accidentally.
            Shader.SetGlobalVector(k_BacklightEnvironment, m != null
                ? new Vector4(m.TrueSunElevationDeg, m.Exposure, 1f, 0f) : Vector4.zero);
            Transform t = cab != null ? cab : transform;
            Vector3 fill = Vector3.zero;
            float night = 0f;
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
                // Neutral = the adapted white of the preset: with the phone-style WB of LP_LowSun (ADR 0043) the sun and
                // the sky are adapted, plain white daylight was not (review r6 C-N5).
                Color c = (m.SunColor * fluxSun + m.AdaptedWhite * fluxSky) * bounceTint * bounce;
                // D84 polish (review P1-3 "no warm ambient at dusk"): spill of the backlit switch legends, cluster and
                // footwell courtesy light on the surrounding trim. Display-referred like the legend cap of ADR 0112
                // (exposure-independent, so it does not blow up with the night exposure), added to the bounce fill:
                // the shader multiplies it by the albedo and the baked AO. WORKING_VALUE, no photometry.
                night = NightFactor(m.TrueSunElevationDeg, twilightStartSunDeg, twilightFullSunDeg);
                c += panelGlowColor * (Mathf.Max(0f, panelGlow) * night);
                fill = new Vector3(c.r, c.g, c.b);
            }
            float gain = 1f, lift = 0f, enc = exteriorEnclosure, outside = 1f;
            Vector4 toeInv = Vector4.zero;
            bool post = QualityProfileApplier.HasCurrent && QualityProfileApplier.Current.postProcessing;
            // ADR 0072: outside the cab the truck shaders write the D23 toe too (the world keeps plain sRGB on Low).
            Vector4 parity = !post && exteriorToeParity ? LookGrading.NoPostToeParity : Vector4.zero;
            if (cam != null && interiorBounds.Contains(t.InverseTransformPoint(cam.transform.position)))
            {
                // Tiers without the D23 LUT (Low): the cab surfaces write the D23 toe themselves (ADR 0044 addendum r7),
                // so the cab view reads the same on Low and High (review r6: Low dusk black < 3 % 8.4 % vs High 1.8 %).
                parity = !post && toeParity ? LookGrading.NoPostToeParity : Vector4.zero;
                // D84 polish (review P1-3): after sunset the day-time phone lift (up to cabViewEv + cabMeterMaxEv =
                // 2.5 stops) made the rim and hub brighter than the road outside. A driver's eye is adapted to the
                // dark world; the lift fades to nightViewEv through twilight.
                gain = Mathf.Pow(2f, CabViewStops(cabViewEv + CabMeterEv(m, fill), cabViewEv, nightViewEv, night));
                outside = 0f;
                float comp = Mathf.Clamp01(RenderOverrides.CabToe ?? toeCompensation);
                if (env != null && env.Active != null && comp > 0f)
                {
                    WorldAtmosphere.ResolveLook(env.Active, out float toe, out float toeP, out float pivot);
                    if (toe > 0f) toeInv = new Vector4(toe, toeP, LookGrading.ToeGain(toe, toeP, pivot), comp);
                }
                enc = enclosure;
                // Phone-like local tone mapping of the cab view (review r4 L1): only the interior surfaces, only in the
                // cab view, strongest in the deepest shade - the sky through the glass and the lit dash are untouched.
                lift = shadowLift >= 0f ? shadowLift : QualityProfileApplier.HasCurrent ? QualityProfileApplier.Current.cabShadowLift : 8f;
            }
            LastMeterEv = Mathf.Log(gain, 2f) - (gain > 1f ? cabViewEv : 0f);
            LastFill = fill;
            LastGain = gain;
            // w: glass transmittance of the direct sun on the interior (every sunlit cab surface is lit through the glazing;
            // the glass casts no shadow, so the shader applies it; review r6 C-N5).
            Shader.SetGlobalVector(k_Fill, new Vector4(fill.x, fill.y, fill.z, Mathf.Clamp01(glassTransmittance)));
            Shader.SetGlobalFloat(k_Gain, gain);
            Shader.SetGlobalVector(k_Lift, new Vector4(lift, Mathf.Max(1e-4f, shadowLiftKnee), Mathf.Clamp01(shadowLiftNeutral), 0f));
            Shader.SetGlobalFloat(k_Enclosure, Mathf.Clamp01(enc));
            Shader.SetGlobalVector(k_Parity, parity);
            Shader.SetGlobalVector(k_ToeInv, toeInv);
            Shader.SetGlobalVector(k_ToeInvDisplay, post ? toeInv : Vector4.zero);
            // ADR 0059: Kamion/Truck Glass dims the far pane of the see-through path only for views from outside the cab.
            Shader.SetGlobalFloat(k_CamOutside, outside);
        }
    }
}
