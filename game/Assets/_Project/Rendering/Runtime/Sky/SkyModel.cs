using System;
using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// Analytic daylight model used for the sky dome, the ambient SH, the reflection cubemap, the sun light and the fog
    /// colour, so all five agree (docs/adr/0010-look-development-sky-exposure-tonemapping.md).
    ///
    /// Clear sky luminance: Preetham, Shirley, Smits, "A Practical Analytic Model for Daylight" (SIGGRAPH 1999), Perez
    /// distribution as a function of turbidity T. Clear sky colour (chromaticity only, luminance 1): spectral (12-band) scattering
    /// in a spherical Rayleigh + Mie + ozone atmosphere (coefficients of Bruneton 2017 / Hillaire 2020, aerosol
    /// optical depth from T through Ångström β = 0.04 (T − 1), α = 1.3), baked per sun position into a 64×32 LUT
    /// (angle to the sun × zenith angle). Preetham's own xy fit is biased toward magenta below ~30° elevation (the
    /// "slate" sky of the first Unity renders, docs/reports/visual/unity-look-v2); the scattering colour is greener-blue
    /// and whiter toward the horizon. Higher orders: one isotropic second-order term (mean sky + ground radiance) refills the long horizontal paths; the zenith stays within
    /// measured clear-sky zenith CCTs of 10 000–25 000 K. Overcast: CIE standard overcast sky (Moon and Spencer 1942,
    /// CIE S 011/E:2003 type 1): L(θ) = Lz (1 + 2 cos θ) / 3, achromatic D65.
    /// Absolute levels are NOT taken from Preetham's zenith formula; the dome is normalised so that its horizontal
    /// illuminance equals the daylight-availability fits of the IESNA Lighting Handbook (9th ed., ch. 8):
    ///   extraterrestrial illuminance 127.5 klx, direct normal E_dn = 127.5 exp(-c m), c = 0.21 (clear),
    ///   clear-sky diffuse E_kh = 0.8 + 15.5 sin(h)^0.5 klx, overcast E_kh = 0.3 + 21.0 sin(h) klx,
    ///   m = relative air mass (Kasten and Young 1989).
    /// The handbook coefficients are quoted from memory of the published fits: WORKING_VALUE until checked against the
    /// handbook text. All radiometry is photometric (cd/m², lx) times a camera exposure factor k (see <see cref="Exposure"/>),
    /// i.e. "exposed units": a Lambertian surface of albedo ρ under illuminance E is displayed at ρ·E·k/π.
    /// </summary>
    public sealed class SkyModel
    {
        public const float SolarIlluminanceExtraterrestrialLux = 127500f;
        public const float SunSolidAngleSr = 6.8e-5f;           // 0.53° disc
        public const float ClearExtinctionC = 0.21f;
        public const float ChromaMaxZenithRad = 84f * Mathf.Deg2Rad;

        public readonly Vector3 SunDirection;   // towards the sun, world space (Y up)
        public readonly float SunElevationDeg;
        public readonly float Turbidity;
        public readonly float Overcast;         // 0 = clear (Preetham), 1 = CIE overcast; in between = linear blend
        public readonly float SunNormalIlluminanceLux;   // direct normal (0 when overcast = 1)
        public readonly float SkyHorizontalIlluminanceLux;
        public readonly Color SunColor;          // linear Rec.709, luminance 1
        public readonly float Exposure;          // k: display value per cd/m²
        public readonly float WhiteBalanceAdaptation;   // 0 = fixed daylight WB (default); ADR 0043 option (c)
        public readonly Color AdaptedWhite;      // colour of a neutral (overcast / ground) radiance after the WB adaptation, luminance 1
        /// <summary>Requested sun altitude (may be below the horizon, ≥ <see cref="MinTwilightElevationDeg"/>); the sky shape
        /// uses <see cref="SunElevationDeg"/> (clamped to 0.5°). Street lamps, exposure and the sun light follow this one.</summary>
        public readonly float TrueSunElevationDeg;
        /// <summary>Towards the true sun (below the horizon in twilight): sun light transform and the cab clock.</summary>
        public readonly Vector3 TrueSunDirection;
        /// <summary>Sky luminance factor relative to the sun at 0.5° (1 above it; ADR 0062 civil twilight).</summary>
        public readonly float TwilightFactor;
        /// <summary>ADR 0080: overcast dome brightening toward the sun, L x (1 + s cos²γ) for γ &lt; 90°, renormalised to
        /// the same horizontal illuminance (thinner cloud / forward scattering toward the sun; 0 = CIE standard overcast).</summary>
        public readonly float OvercastDirectional;
        /// <summary>ADR 0080: share of the clear-sky direct beam that passes a thin overcast as a directional component
        /// (soft form shading and faint shadows). Taken out of the overcast diffuse, so the total horizontal illuminance
        /// (and the exposure) stays at the handbook overcast value.</summary>
        public readonly float OvercastSunLeak;
        /// <summary>ADR 0080 r11: correlated colour temperature of the overcast dome (K; 0 = achromatic D65, the CIE
        /// standard overcast). The camera's white balance is fixed daylight (D65), so a dome above 6500 K reads slightly
        /// cool, as in the reference photos (sky B - R +7..+16 at 190-225, review 2026-11-10 B4).</summary>
        public readonly float OvercastCctK;

        // ---------------------------------------------------------------- twilight (ADR 0062)
        public const float MinTwilightElevationDeg = -8f;
        /// <summary>Horizontal illuminance at the end of civil twilight (sun −6°), clear sky. Commonly quoted ~3.4 lx
        /// (UNVERIFIED: from memory of the twilight illuminance tables, e.g. Bond and Henderson 1963).</summary>
        public const float CivilTwilightEndLux = 3.4f;
        /// <summary>
        /// Twilight sky luminance factor for a sun below 0.5°: log-linear from 1 at 0.5° (the dome's own clear-sky diffuse
        /// illuminance there, ≈ 2.25 klx) to <see cref="CivilTwilightEndLux"/> at −6°, i.e. ~0.37× per degree. The sky
        /// keeps its 0.5° shape and colour (afterglow toward the sun's azimuth). WORKING_VALUE.
        /// </summary>
        public static float TwilightFactorAt(float sunElevationDeg)
        {
            if (sunElevationDeg >= 0.5f) return 1f;
            float e05 = (0.8f + 15.5f * Mathf.Sqrt(Mathf.Sin(0.5f * Mathf.Deg2Rad))) * 1000f;
            float el = Mathf.Max(sunElevationDeg, MinTwilightElevationDeg);
            return Mathf.Exp(Mathf.Log(CivilTwilightEndLux / e05) * (0.5f - el) / 6.5f);
        }

        // Perez coefficients (A..E) for Y, x, y and zenith values (clear part).
        readonly float[] m_PY = new float[5], m_Px = new float[5], m_Py = new float[5];
        readonly float m_Zx, m_Zy, m_ThetaS;
        readonly float m_ClearScale;     // cd/m² per unit of normalised Preetham luminance
        readonly float m_OvercastZenith; // cd/m²

        public const int ChromaWidth = 64, ChromaHeight = 32;   // u = γ/π (angle to the sun), v = sqrt(cos θ)
        readonly Color[] m_Chroma = new Color[ChromaWidth * ChromaHeight];

        /// <param name="sunElevationDeg">sun altitude above the horizon</param>
        /// <param name="sunAzimuthDeg">compass azimuth (0 = north, 90 = east), world X = east, Z = north</param>
        /// <param name="turbidity">Linke-like turbidity of the Preetham model, 2 (very clear) … 6 (hazy)</param>
        /// <param name="overcast">0 clear … 1 fully overcast (CIE)</param>
        /// <param name="ev100">exposure value at ISO 100; k = 1 / (1.2 · 2^EV100) (Lagarde and de Rousiers 2014)</param>
        /// <param name="wbAdaptation">0 = fixed daylight white balance (default, all presets). &gt; 0: phone-style partial
        /// white-balance adaptation (Bradford von Kries, degree D) toward the scene illuminant (sun + sky on a horizontal
        /// plane), applied to sun, sky, ambient, fog and reflections alike. Option (c) of ADR 0043: owner A/B only.</param>
        public SkyModel(float sunElevationDeg, float sunAzimuthDeg, float turbidity, float overcast, float ev100, float wbAdaptation = 0f,
            float overcastDirectional = 0f, float overcastSunLeak = 0f, float overcastCctK = 0f)
        {
            OvercastCctK = overcastCctK;
            OvercastDirectional = Mathf.Clamp(overcastDirectional, 0f, 2f);
            OvercastSunLeak = Mathf.Clamp(overcastSunLeak, 0f, 0.3f);
            SunElevationDeg = Mathf.Clamp(sunElevationDeg, 0.5f, 89.5f);
            TrueSunElevationDeg = Mathf.Clamp(sunElevationDeg, MinTwilightElevationDeg, 89.5f);
            TwilightFactor = TwilightFactorAt(TrueSunElevationDeg);
            Turbidity = Mathf.Clamp(turbidity, 1.7f, 10f);
            Overcast = Mathf.Clamp01(overcast);
            float el = SunElevationDeg * Mathf.Deg2Rad, az = sunAzimuthDeg * Mathf.Deg2Rad;
            SunDirection = new Vector3(Mathf.Cos(el) * Mathf.Sin(az), Mathf.Sin(el), Mathf.Cos(el) * Mathf.Cos(az)).normalized;
            float elT = TrueSunElevationDeg * Mathf.Deg2Rad;
            TrueSunDirection = new Vector3(Mathf.Cos(elT) * Mathf.Sin(az), Mathf.Sin(elT), Mathf.Cos(elT) * Mathf.Cos(az)).normalized;
            Exposure = ExposureFromEv100(ev100);

            float sinH = Mathf.Sin(el);
            float m = AirMass(SunElevationDeg);
            float clearDn = SolarIlluminanceExtraterrestrialLux * Mathf.Exp(-ClearExtinctionC * m);
            // Twilight (ADR 0062): the sun is below the horizon - no direct light, the dome dims by TwilightFactor.
            float clearKh = (0.8f + 15.5f * Mathf.Sqrt(sinH)) * 1000f * TwilightFactor;
            float overKh = (0.3f + 21.0f * sinH) * 1000f * TwilightFactor;
            // ADR 0080: a thin overcast passes part of the beam; what it passes is not scattered into the dome.
            float leakDn = TrueSunElevationDeg < 0f ? 0f : clearDn * OvercastSunLeak * Overcast;
            float leakKh = Mathf.Min(leakDn * sinH, overKh * 0.5f);
            leakDn = sinH > 1e-4f ? leakKh / sinH : 0f;
            overKh -= leakKh;
            SunNormalIlluminanceLux = TrueSunElevationDeg < 0f ? 0f : clearDn * (1f - Overcast) + leakDn;
            SkyHorizontalIlluminanceLux = Mathf.Lerp(clearKh, overKh, Overcast);

            // ---- Preetham coefficients ----
            float T = Turbidity;
            m_ThetaS = Mathf.PI * 0.5f - el;
            Set(m_PY, 0.1787f * T - 1.4630f, -0.3554f * T + 0.4275f, -0.0227f * T + 5.3251f, 0.1206f * T - 2.5771f, -0.0670f * T + 0.3703f);
            Set(m_Px, -0.0193f * T - 0.2592f, -0.0665f * T + 0.0008f, -0.0004f * T + 0.2125f, -0.0641f * T - 0.8989f, -0.0033f * T + 0.0452f);
            Set(m_Py, -0.0167f * T - 0.2608f, -0.0950f * T + 0.0092f, -0.0079f * T + 0.2102f, -0.0441f * T - 1.6537f, -0.0109f * T + 0.0529f);
            float t = m_ThetaS, t2 = t * t, t3 = t2 * t;
            m_Zx = T * T * (0.00166f * t3 - 0.00375f * t2 + 0.00209f * t) + T * (-0.02903f * t3 + 0.06377f * t2 - 0.03202f * t + 0.00394f) + (0.11693f * t3 - 0.21196f * t2 + 0.06052f * t + 0.25886f);
            m_Zy = T * T * (0.00275f * t3 - 0.00610f * t2 + 0.00317f * t) + T * (-0.04214f * t3 + 0.08970f * t2 - 0.04153f * t + 0.00516f) + (0.15346f * t3 - 0.26756f * t2 + 0.06670f * t + 0.26688f);

            // Normalise the clear dome to the handbook horizontal illuminance: E_h = Σ L cosθ dω.
            m_ClearScale = 1f;
            float eUnit = IntegrateHorizontal(ClearLuminanceRelative);
            m_ClearScale = eUnit > 0f ? clearKh / eUnit : 0f;
            // CIE overcast: E_h = 7π/9 · Lz; with the directional term the integral is numeric.
            m_OvercastZenith = overKh * 9f / (7f * Mathf.PI);
            if (OvercastDirectional > 0f)
            {
                float e1 = IntegrateHorizontal(OvercastRelative);
                m_OvercastZenith = e1 > 0f ? overKh / e1 : 0f;
            }

            SunColor = SunColorFromTurbidity(T, m);
            // r11: the overcast share of the "neutral" radiance (dome, the ground it lights, fog) takes the dome's colour.
            AdaptedWhite = OvercastCctK > 0f ? NormaliseLum(Color.LerpUnclamped(Color.white, DaylightRgb(OvercastCctK), Overcast)) : Color.white;
            if (Overcast < 1f) { BuildChroma(); ApplyTwilightChroma(); }
            WhiteBalanceAdaptation = Mathf.Clamp01(wbAdaptation);
            if (WhiteBalanceAdaptation > 0f)
            {
                var A = AdaptationMatrix(SceneIlluminantRgb(), WhiteBalanceAdaptation);
                SunColor = NormaliseLum(Mul(A, SunColor));
                AdaptedWhite = NormaliseLum(Mul(A, AdaptedWhite));
                for (int i = 0; i < m_Chroma.Length; i++) m_Chroma[i] = NormaliseLum(Mul(A, m_Chroma[i]));
            }
        }

        /// <summary>
        /// Linear Rec.709 colour (luminance 1, D65 = white) of a CIE daylight illuminant of the given correlated colour
        /// temperature (4000-25000 K): chromaticity from the CIE daylight locus (CIE 015:2004, eq. 3.3-3.4; Wyszecki and
        /// Stiles 1982), xyY -> XYZ -> Rec.709.
        /// </summary>
        public static Color DaylightRgb(float cctK)
        {
            double T = Mathf.Clamp(cctK, 4000f, 25000f);
            double x = T <= 7000.0
                ? -4.6070e9 / (T * T * T) + 2.9678e6 / (T * T) + 0.09911e3 / T + 0.244063
                : -2.0064e9 / (T * T * T) + 1.9018e6 / (T * T) + 0.24748e3 / T + 0.237040;
            double y = -3.000 * x * x + 2.870 * x - 0.275;
            double X = x / y, Z = (1.0 - x - y) / y;
            var c = new Color(
                (float)(3.2404542 * X - 1.5371385 - 0.4985314 * Z),
                (float)(-0.9692660 * X + 1.8760108 + 0.0415560 * Z),
                (float)(0.0556434 * X - 0.2040259 + 1.0572252 * Z), 1f);
            return NormaliseLum(c);
        }

        public static float ExposureFromEv100(float ev100) => 1f / (1.2f * Mathf.Pow(2f, ev100));

        /// <summary>EV100 that an incident-light meter (C = 250) gives for a horizontal illuminance: EV = log2(E / 2.5).</summary>
        public static float IncidentEv100(float illuminanceLux) => Mathf.Log(Mathf.Max(illuminanceLux, 1f) / 2.5f, 2f);

        /// <summary>Kasten and Young (1989) relative optical air mass.</summary>
        public static float AirMass(float elevationDeg)
        {
            float h = Mathf.Max(elevationDeg, 0f);
            return 1f / (Mathf.Sin(h * Mathf.Deg2Rad) + 0.50572f * Mathf.Pow(h + 6.07995f, -1.6364f));
        }

        /// <summary>Total illuminance on a horizontal plane (direct + sky), lux.</summary>
        public float HorizontalIlluminanceLux => SunNormalIlluminanceLux * Mathf.Max(SunDirection.y, 0f) + SkyHorizontalIlluminanceLux;

        /// <summary>Unity directional-light intensity (exposed units, Unity's Lambert has no 1/π).</summary>
        public float SunLightIntensity => SunNormalIlluminanceLux * Exposure / Mathf.PI;

        /// <summary>Sky radiance (cd/m² per channel, linear Rec.709, luminance-weighted) for a direction above the horizon.</summary>
        public Color Radiance(Vector3 dir)
        {
            dir.Normalize();
            if (dir.y < 0.001f) dir = new Vector3(dir.x, 0.001f, dir.z).normalized;
            Color c = Color.black;
            if (Overcast < 1f)
            {
                float theta = Mathf.Acos(Mathf.Clamp(dir.y, -1f, 1f));
                float gamma = Mathf.Acos(Mathf.Clamp(Vector3.Dot(dir, SunDirection), -1f, 1f));
                float Y = Perez(m_PY, theta, gamma) / Perez(m_PY, 0f, m_ThetaS) * m_ClearScale;
                c += ChromaAt(dir.y, gamma) * (Y * (1f - Overcast));
            }
            if (Overcast > 0f)
            {
                float L = m_OvercastZenith * OvercastRelative(dir);
                c += AdaptedWhite * (L * Overcast);
            }
            return c;
        }

        /// <summary>Exposed radiance (display units before tonemapping).</summary>
        public Color ExposedRadiance(Vector3 dir) => Radiance(dir) * Exposure;

        /// <summary>Mean sky radiance in a thin band just above the horizon (fog / aerial-perspective colour), exposed.</summary>
        public Color HorizonColorExposed()
        {
            Color sum = Color.black;
            const int n = 32;
            for (int i = 0; i < n; i++)
            {
                float a = i * Mathf.PI * 2f / n;
                sum += Radiance(new Vector3(Mathf.Sin(a), 0.05f, Mathf.Cos(a)));
            }
            return sum * (Exposure / n);
        }

        // ---------------------------------------------------------------- shader parameters
        public void GetShaderParameters(out Vector4 perezY0, out Vector4 perezX0, out Vector4 perezy0, out Vector4 perezE,
            out Vector4 zenith, out Vector4 misc)
        {
            perezY0 = new Vector4(m_PY[0], m_PY[1], m_PY[2], m_PY[3]);
            perezX0 = new Vector4(m_Px[0], m_Px[1], m_Px[2], m_Px[3]);
            perezy0 = new Vector4(m_Py[0], m_Py[1], m_Py[2], m_Py[3]);
            perezE = new Vector4(m_PY[4], m_Px[4], m_Py[4], 0f);
            // Zenith chromaticity, clear scale relative to Perez(0, θs) and exposure folded in.
            float fY0 = Perez(m_PY, 0f, m_ThetaS), fx0 = Perez(m_Px, 0f, m_ThetaS), fy0 = Perez(m_Py, 0f, m_ThetaS);
            zenith = new Vector4(m_Zx / fx0, m_Zy / fy0, m_ClearScale * Exposure / fY0, m_OvercastZenith * Exposure);
            misc = new Vector4(Overcast, SunNormalIlluminanceLux * Exposure / SunSolidAngleSr, OvercastDirectional, 0f);
        }

        // ---------------------------------------------------------------- SH and cubemap
        /// <summary>
        /// Projects the exposed sky (upper hemisphere) plus a Lambertian ground (lower hemisphere, albedo × horizontal
        /// illuminance / π) into Unity's L2 ambient probe. Each sample acts as a directional light of intensity L·k·dω/π,
        /// which reproduces the irradiance E(n)·k/π a Unity Lambert surface expects. The sun is NOT included (real light).
        /// </summary>
        /// <param name="lowSunCool">Review r4 L2 (olive low-sun shade): 0..1 share of the low-sun sky samples whose chroma is
        /// taken from the zenith instead of their own (luminance kept). Faded in below 15 deg sun elevation (full at 5 deg),
        /// clear part only. A shadow at low sun is lit by the whole blue dome, but the L2 probe is dominated by the bright warm
        /// aureole/horizon band next to the sun, which turned the plaza shade olive (R-B +9). Only the directional sun stays
        /// warm. 0 = the plain analytic sky (tests).</param>
        public UnityEngine.Rendering.SphericalHarmonicsL2 AmbientProbe(Color groundAlbedo, int resolution = 24, float skySaturation = 1f,
            float lowSunCool = 0f)
        {
            var sh = new UnityEngine.Rendering.SphericalHarmonicsL2();
            Color ground = groundAlbedo * AdaptedWhite * (HorizontalIlluminanceLux * Exposure / Mathf.PI);
            float cool = Mathf.Clamp01(lowSunCool) * Mathf.Clamp01((15f - SunElevationDeg) / 10f) * (1f - Overcast);
            Color zc = ExposedRadiance(Vector3.up);
            float zy = 0.2126f * zc.r + 0.7152f * zc.g + 0.0722f * zc.b;
            zc = zy > 1e-8f ? zc / zy : Color.white;
            // Equal-area sampling: rows in z = cosθ, columns in φ.
            int rows = resolution * 2, cols = resolution * 4;
            float dOmega = 4f * Mathf.PI / (rows * cols);
            for (int r = 0; r < rows; r++)
            {
                float z = 1f - 2f * (r + 0.5f) / rows;
                float s = Mathf.Sqrt(Mathf.Max(0f, 1f - z * z));
                for (int c = 0; c < cols; c++)
                {
                    float phi = 2f * Mathf.PI * (c + 0.5f) / cols;
                    var d = new Vector3(s * Mathf.Cos(phi), z, s * Mathf.Sin(phi));
                    Color L = ground;
                    if (z > 0f)
                    {
                        L = ExposedRadiance(d);
                        if (cool > 0f)
                        {
                            float y = 0.2126f * L.r + 0.7152f * L.g + 0.0722f * L.b;
                            L = Color.LerpUnclamped(L, zc * y, cool);
                        }
                        // r11: the cut models missing inter-reflections under a blue clear sky; the overcast dome's own
                        // (slight) colour is the colour of the light and stays.
                        L = Desaturate(L, Mathf.Lerp(skySaturation, 1f, Overcast));
                    }
                    sh.AddDirectionalLight(d, L, dOmega / Mathf.PI);
                }
            }
            return sh * ShConventionScale(resolution);
        }

        /// <summary>Lerp toward the Rec.709 luminance (keeps luminance, scales chroma).</summary>
        public static Color Desaturate(Color c, float saturation)
        {
            if (saturation >= 1f) return c;
            float y = 0.2126f * c.r + 0.7152f * c.g + 0.0722f * c.b;
            return Color.LerpUnclamped(new Color(y, y, y, c.a), c, saturation);
        }

        static float s_ShScale;
        static int s_ShScaleRes;

        /// <summary>
        /// Unity's <c>AddDirectionalLight</c> folds its own normalisation into the probe (measured: a uniform unit-radiance
        /// sphere evaluates to ~1.89 instead of 1 = E/π). Calibrate once with that uniform sphere so the probe returns
        /// exactly irradiance/π (test SkyModelTests.AmbientProbe_ReproducesSkyIrradiance).
        /// </summary>
        static float ShConventionScale(int resolution)
        {
            if (s_ShScaleRes == resolution && s_ShScale > 0f) return s_ShScale;
            var sh = new UnityEngine.Rendering.SphericalHarmonicsL2();
            int rows = resolution * 2, cols = resolution * 4;
            float dOmega = 4f * Mathf.PI / (rows * cols);
            for (int r = 0; r < rows; r++)
            {
                float z = 1f - 2f * (r + 0.5f) / rows;
                float s = Mathf.Sqrt(Mathf.Max(0f, 1f - z * z));
                for (int c = 0; c < cols; c++)
                {
                    float phi = 2f * Mathf.PI * (c + 0.5f) / cols;
                    sh.AddDirectionalLight(new Vector3(s * Mathf.Cos(phi), z, s * Mathf.Sin(phi)), Color.white, dOmega / Mathf.PI);
                }
            }
            var res = new Color[1];
            sh.Evaluate(new[] { Vector3.up }, res);
            s_ShScale = res[0].g > 1e-6f ? 1f / res[0].g : 1f;
            s_ShScaleRes = resolution;
            return s_ShScale;
        }

        /// <summary>Exposed irradiance/π (what <c>SampleSH(up)</c> should return) of sky + ground for a normal.</summary>
        public Color ExpectedAmbient(Vector3 n, Color groundAlbedo, int resolution = 48)
        {
            Color ground = groundAlbedo * AdaptedWhite * (HorizontalIlluminanceLux * Exposure / Mathf.PI);
            int rows = resolution * 2, cols = resolution * 4;
            float dOmega = 4f * Mathf.PI / (rows * cols);
            Color sum = Color.black;
            for (int r = 0; r < rows; r++)
            {
                float z = 1f - 2f * (r + 0.5f) / rows;
                float s = Mathf.Sqrt(Mathf.Max(0f, 1f - z * z));
                for (int c = 0; c < cols; c++)
                {
                    float phi = 2f * Mathf.PI * (c + 0.5f) / cols;
                    var d = new Vector3(s * Mathf.Cos(phi), z, s * Mathf.Sin(phi));
                    float cosT = Vector3.Dot(d, n);
                    if (cosT <= 0f) continue;
                    sum += (z > 0f ? ExposedRadiance(d) : ground) * (cosT * dOmega);
                }
            }
            return sum / Mathf.PI;
        }

        /// <summary>Exposed radiance cubemap (sky + ground + no sun) for specular environment reflections.</summary>
        public Cubemap ReflectionCubemap(Color groundAlbedo, int size = 64, System.Func<Color, Color> skyPresentation = null)
        {
            var cube = new Cubemap(size, TextureFormat.RGBAHalf, true) { name = "SkyReflection", filterMode = FilterMode.Trilinear, wrapMode = TextureWrapMode.Clamp };
            Color ground = groundAlbedo * AdaptedWhite * (HorizontalIlluminanceLux * Exposure / Mathf.PI);
            Color horizon = HorizonColorExposed();
            // Optional appearance mapping affects reflected sky/horizon only, never analytic SH or ground irradiance.
            if (skyPresentation != null) horizon = skyPresentation(horizon);
            var px = new Color[size * size];
            for (int f = 0; f < 6; f++)
            {
                var face = (CubemapFace)f;
                for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                    Vector3 d = FaceDirection(face, u, v).normalized;
                    Color c;
                    if (d.y >= 0f) {
                        c = ExposedRadiance(d);
                        if (skyPresentation != null) c = skyPresentation(c);
                    }
                    else c = Color.Lerp(horizon, ground, Mathf.SmoothStep(0f, 1f, -d.y * 4f));
                    c.a = 1f;
                    px[y * size + x] = c;
                }
                cube.SetPixels(px, face);
            }
            cube.Apply(true, false);
            return cube;
        }

        // Unity cubemap face orientation (as SetPixels expects: row 0 = top of the face).
        static Vector3 FaceDirection(CubemapFace f, float u, float v)
        {
            switch (f)
            {
                case CubemapFace.PositiveX: return new Vector3(1f, -v, -u);
                case CubemapFace.NegativeX: return new Vector3(-1f, -v, u);
                case CubemapFace.PositiveY: return new Vector3(u, 1f, v);
                case CubemapFace.NegativeY: return new Vector3(u, -1f, -v);
                case CubemapFace.PositiveZ: return new Vector3(u, -v, 1f);
                default: return new Vector3(-u, -v, -1f);
            }
        }

        // ---------------------------------------------------------------- internals
        static void Set(float[] a, float A, float B, float C, float D, float E) { a[0] = A; a[1] = B; a[2] = C; a[3] = D; a[4] = E; }

        static float Perez(float[] p, float theta, float gamma)
        {
            float ct = Mathf.Max(Mathf.Cos(theta), 0.01f);
            float cg = Mathf.Cos(gamma);
            return (1f + p[0] * Mathf.Exp(p[1] / ct)) * (1f + p[2] * Mathf.Exp(p[3] * gamma) + p[4] * cg * cg);
        }

        /// <summary>Overcast luminance relative to the zenith constant: CIE (1 + 2 cos θ) / 3 × the directional term.</summary>
        float OvercastRelative(Vector3 dir)
        {
            float cg = Mathf.Max(Vector3.Dot(dir, SunDirection), 0f);
            return (1f + 2f * Mathf.Max(dir.y, 0f)) / 3f * (1f + OvercastDirectional * cg * cg);
        }

        float ClearLuminanceRelative(Vector3 dir)
        {
            float theta = Mathf.Acos(Mathf.Clamp(dir.y, -1f, 1f));
            float gamma = Mathf.Acos(Mathf.Clamp(Vector3.Dot(dir, SunDirection), -1f, 1f));
            return m_ClearScale * Perez(m_PY, theta, gamma) / Perez(m_PY, 0f, m_ThetaS);
        }

        /// <summary>Preetham CIE xy chromaticity (kept for comparison in tests; the sky uses <see cref="ChromaAt"/>).</summary>
        public void PreethamXy(Vector3 dir, out float x, out float y)
        {
            float theta = Mathf.Min(Mathf.Acos(Mathf.Clamp(dir.y, -1f, 1f)), ChromaMaxZenithRad);
            float gamma = Mathf.Acos(Mathf.Clamp(Vector3.Dot(dir, SunDirection), -1f, 1f));
            x = m_Zx * Perez(m_Px, theta, gamma) / Perez(m_Px, 0f, m_ThetaS);
            y = m_Zy * Perez(m_Py, theta, gamma) / Perez(m_Py, 0f, m_ThetaS);
        }

        // ---------------------------------------------------------------- scattering chromaticity (spectral)
        const float EarthR = 6360e3f, AtmosphereR = 6460e3f, ObserverH = 150f, RayleighH = 8000f, MieH = 1200f;
        const float MieG = 0.76f, MieExtinctionPerScattering = 1.11f;
        const int Bands = 12;                   // 410 … 696 nm, 26 nm apart
        static float BandNm(int k) => 410f + 26f * k;
        // Rayleigh scattering at sea level, 33.1e-6 m⁻¹ at 440 nm (Bruneton 2017), ∝ λ⁻⁴.
        static float RayleighAt(float nm) => 33.1e-6f * Mathf.Pow(440f / nm, 4f);
        // Ozone absorption (Chappuis band), linear through Bruneton's 440/550/680 nm values; tent profile 10–40 km.
        static float OzoneAt(float nm) => nm < 550f ? Mathf.Lerp(0.085e-6f, 1.881e-6f, Mathf.InverseLerp(440f, 550f, nm))
                                                     : Mathf.Lerp(1.881e-6f, 0.650e-6f, Mathf.InverseLerp(550f, 680f, nm));
        static float OzoneDensity(float h) => Mathf.Max(0f, 1f - Mathf.Abs(h - 25000f) / 15000f);
        // Extraterrestrial solar spectrum ≈ black body 5778 K (relative).
        static float SolarAt(float nm) { float l = nm * 1e-9f; return 1f / (Mathf.Pow(l, 5f) * (Mathf.Exp(1.4388e-2f / (l * 5778f)) - 1f)); }
        static float Lobe(float x, float mu, float s1, float s2) { float t = (x - mu) / (x < mu ? s1 : s2); return Mathf.Exp(-0.5f * t * t); }
        // CIE 1931 2° colour-matching functions, multi-lobe fit of Wyman, Sloan and Shirley (JCGT 2013).
        static Vector3 Cmf(float nm) => new Vector3(
            1.056f * Lobe(nm, 599.8f, 37.9f, 31.0f) + 0.362f * Lobe(nm, 442.0f, 16.0f, 26.7f) - 0.065f * Lobe(nm, 501.1f, 20.4f, 26.2f),
            0.821f * Lobe(nm, 568.8f, 46.9f, 40.5f) + 0.286f * Lobe(nm, 530.9f, 16.3f, 31.1f),
            1.217f * Lobe(nm, 437.0f, 11.8f, 36.0f) + 0.681f * Lobe(nm, 459.0f, 26.0f, 13.8f));

        static float RayLengthToTop(float r, float mu) => -r * mu + Mathf.Sqrt(Mathf.Max(0f, r * r * (mu * mu - 1f) + AtmosphereR * AtmosphereR));

        /// <summary>
        /// Spectral (12 bands) single scattering + one isotropic second-order term (mean sky and ground radiance as the
        /// source), integrated to CIE XYZ and converted to Rec.709, normalised to luminance 1. Three "RGB wavelengths"
        /// (the usual real-time shortcut) gave a green-grey horizon and a beige haze in the first v2 renders.
        /// </summary>
        void BuildChroma()
        {
            float beta = 0.04f * (Turbidity - 1f);
            var ray = new float[Bands]; var mie = new float[Bands]; var oz = new float[Bands]; var sol = new float[Bands]; var cmf = new Vector3[Bands];
            for (int k = 0; k < Bands; k++)
            {
                float nm = BandNm(k);
                ray[k] = RayleighAt(nm); mie[k] = beta * Mathf.Pow(nm / 1000f, -1.3f) / MieH; oz[k] = OzoneAt(nm); sol[k] = SolarAt(nm); cmf[k] = Cmf(nm);
            }
            float solMax = 0f; foreach (var v in sol) solMax = Mathf.Max(solMax, v);
            for (int k = 0; k < Bands; k++) sol[k] /= solMax;

            // Optical depth towards the sun per band as a function of height (the sun's local zenith angle is taken as
            // constant along the view ray: < 3° change over the 300 km of a horizontal ray).
            const int nh = 64;
            var sunOd = new float[nh, Bands];
            float muS = Mathf.Max(SunDirection.y, 0.02f);
            for (int a = 0; a < nh; a++)
            {
                float hk = 60000f * (a / (float)(nh - 1)) * (a / (float)(nh - 1));
                float r0 = EarthR + hk, len = RayLengthToTop(r0, muS);
                const int ns = 24;
                for (int i = 0; i < ns; i++)
                {
                    float t = len * ((i + 0.5f) / ns) * ((i + 0.5f) / ns), dt = len * (2f * i + 1f) / (ns * ns);
                    float h = Mathf.Sqrt(r0 * r0 + t * t + 2f * r0 * t * muS) - EarthR;
                    float dR = Mathf.Exp(-h / RayleighH), dM = Mathf.Exp(-h / MieH) * MieExtinctionPerScattering, dO = OzoneDensity(h);
                    for (int k = 0; k < Bands; k++) sunOd[a, k] += (ray[k] * dR + mie[k] * dM + oz[k] * dO) * dt;
                }
            }
            float SunOd(float h, int k)
            {
                float f = Mathf.Sqrt(Mathf.Clamp(h, 0f, 60000f) / 60000f) * (nh - 1);
                int a = Mathf.Min((int)f, nh - 2);
                return Mathf.Lerp(sunOd[a, k], sunOd[a + 1, k], f - a);
            }

            float sinS = Mathf.Sqrt(1f - SunDirection.y * SunDirection.y), cosS = SunDirection.y;
            float r0v = EarthR + ObserverH;
            var sdir = new Vector3(sinS, cosS, 0f);
            var odv = new float[Bands];

            void March(Vector3 d, float[] ambient, float[] L, bool rayleighOnly = false)
            {
                float cosT = d.y, mu = Vector3.Dot(d, sdir);
                float pR = 3f / (16f * Mathf.PI) * (1f + mu * mu);
                float pM = 3f / (8f * Mathf.PI) * (1f - MieG * MieG) * (1f + mu * mu) / ((2f + MieG * MieG) * Mathf.Pow(1f + MieG * MieG - 2f * MieG * mu, 1.5f));
                float len = RayLengthToTop(r0v, cosT);
                const int n = 32;
                System.Array.Clear(odv, 0, Bands);
                System.Array.Clear(L, 0, Bands);
                float prev = 0f;
                for (int s2 = 0; s2 < n; s2++)
                {
                    float t1 = len * ((s2 + 1f) / n) * ((s2 + 1f) / n), dt = t1 - prev, tm = 0.5f * (prev + t1);
                    prev = t1;
                    float h = Mathf.Sqrt(r0v * r0v + tm * tm + 2f * r0v * tm * cosT) - EarthR;
                    float dR = Mathf.Exp(-h / RayleighH), dM = Mathf.Exp(-h / MieH), dO = OzoneDensity(h);
                    for (int k = 0; k < Bands; k++)
                    {
                        float e = (ray[k] * dR + mie[k] * dM * MieExtinctionPerScattering + oz[k] * dO) * dt;
                        float mid = odv[k] + 0.5f * e;
                        float sc = ray[k] * dR, sm = mie[k] * dM;
                        L[k] += Mathf.Exp(-mid - SunOd(h, k)) * sol[k] * (sc * pR + (rayleighOnly ? 0f : sm * pM)) * dt;
                        if (ambient != null) L[k] += Mathf.Exp(-mid) * (sc + sm) * ambient[k] * 0.5f * dt;
                        odv[k] += e;
                    }
                }
            }

            // Second-order source: mean single-scattered sky radiance over the upper hemisphere + Lambertian ground
            // (albedo 0.2) lit by the attenuated sun and that sky; isotropic phase over each hemisphere (½ each).
            var amb = new float[Bands];
            var tmp = new float[Bands];
            const int ar = 6, ac = 12;
            for (int a = 0; a < ar; a++)
            for (int b = 0; b < ac; b++)
            {
                float z = (a + 0.5f) / ar, sz = Mathf.Sqrt(1f - z * z), phi = (b + 0.5f) * 2f * Mathf.PI / ac;
                // Rayleigh only: the Mie aureole (g = 0.76) is a narrow forward lobe that keeps travelling away from the
                // observer; counted as an isotropic source it painted the whole low-sun horizon orange (review r4 L2:
                // khaki sky 154/140/114, anti-sun horizon R > B at 9 deg).
                March(new Vector3(sz * Mathf.Cos(phi), z, sz * Mathf.Sin(phi)), null, tmp, true);
                for (int k = 0; k < Bands; k++) amb[k] += tmp[k] / (ar * ac);
            }
            for (int k = 0; k < Bands; k++)
                amb[k] += 0.2f * (sol[k] * Mathf.Exp(-SunOd(ObserverH, k)) * Mathf.Max(cosS, 0f) / Mathf.PI + amb[k]);

            // Orders ≥ 3 (ADR 0043): Hillaire, "A Scalable and Production Ready Sky and Atmosphere Rendering Technique"
            // (EGSR 2020, §5.5): with an isotropic phase the higher orders form a geometric series, Ψ_ms = L_2nd / (1 − f_ms),
            // f_ms = (1/4π) ∫_sphere ∫ σ_s T dt dω = the share of isotropic light a point re-scatters back to itself.
            // Evaluated once at the observer (bottom of the atmosphere, where f_ms is largest); ground rays end at the
            // ground 150 m below. f_ms ≈ 0.40 (410 nm) … 0.20 (696 nm) at T 3, so the higher orders are bluer.
            var fms = MultipleScatteringFraction(ray, mie, oz);
            for (int k = 0; k < Bands; k++) amb[k] /= 1f - Mathf.Min(fms[k], 0.9f);

            // White balance: the extraterrestrial sun maps to the same near-white (0.98, 1, 0.96) the sun light uses
            // (SunColorFromTurbidity), so sky and sunlight share one reference white - like a camera on daylight WB.
            Vector3 sunXyz = Vector3.zero;
            for (int k = 0; k < Bands; k++) sunXyz += cmf[k] * sol[k];
            var sunRgb = new Vector3(3.2404542f * sunXyz.x - 1.5371385f * sunXyz.y - 0.4985314f * sunXyz.z,
                -0.9692660f * sunXyz.x + 1.8760108f * sunXyz.y + 0.0415560f * sunXyz.z,
                0.0556434f * sunXyz.x - 0.2040259f * sunXyz.y + 1.0572252f * sunXyz.z);
            var wb = new Vector3(0.98f / sunRgb.x, 1f / sunRgb.y, 0.96f / sunRgb.z);

            for (int j = 0; j < ChromaHeight; j++)
            for (int i = 0; i < ChromaWidth; i++)
            {
                float v = j / (float)(ChromaHeight - 1), u = i / (float)(ChromaWidth - 1);
                float cosT = Mathf.Max(v * v, 0.0005f), sinT = Mathf.Sqrt(1f - cosT * cosT);
                float gamma = u * Mathf.PI, cosG = Mathf.Cos(gamma);
                // Direction with zenith angle θ and angle γ to the sun (sun at azimuth 0); clamp unreachable γ.
                float cosPhi = sinT * sinS > 1e-5f ? Mathf.Clamp((cosG - cosT * cosS) / (sinT * sinS), -1f, 1f) : 1f;
                March(new Vector3(sinT * cosPhi, cosT, sinT * Mathf.Sqrt(1f - cosPhi * cosPhi)), amb, tmp);
                Vector3 xyz = Vector3.zero;
                for (int k = 0; k < Bands; k++) xyz += cmf[k] * tmp[k];
                var c = new Color(
                    Mathf.Max(0f, 3.2404542f * xyz.x - 1.5371385f * xyz.y - 0.4985314f * xyz.z) * wb.x,
                    Mathf.Max(0f, -0.9692660f * xyz.x + 1.8760108f * xyz.y + 0.0415560f * xyz.z) * wb.y,
                    Mathf.Max(0f, 0.0556434f * xyz.x - 0.2040259f * xyz.y + 1.0572252f * xyz.z) * wb.z);
                float lum = 0.2126f * c.r + 0.7152f * c.g + 0.0722f * c.b;
                m_Chroma[j * ChromaWidth + i] = lum > 0f ? new Color(c.r / lum, c.g / lum, c.b / lum, 1f) : Color.white;
            }
        }

        // ---------------------------------------------------------------- white-balance adaptation (option c, ADR 0043)
        static readonly Matrix4x4 s_ToXyz = Rows(0.4124564f, 0.3575761f, 0.1804375f, 0.2126729f, 0.7151522f, 0.0721750f, 0.0193339f, 0.1191920f, 0.9503041f);
        // Bradford cone response (Lam 1985; CIECAM97s / ICC v4).
        static readonly Matrix4x4 s_Bradford = Rows(0.8951f, 0.2664f, -0.1614f, -0.7502f, 1.7135f, 0.0367f, 0.0389f, -0.0685f, 1.0296f);
        static Matrix4x4 Rows(float a, float b, float c, float d, float e, float f, float g, float h, float i)
        {
            var m = Matrix4x4.identity;
            m.SetRow(0, new Vector4(a, b, c, 0f)); m.SetRow(1, new Vector4(d, e, f, 0f)); m.SetRow(2, new Vector4(g, h, i, 0f));
            return m;
        }
        static Color Mul(Matrix4x4 m, Color c) { Vector3 v = m.MultiplyVector(new Vector3(c.r, c.g, c.b)); return new Color(v.x, v.y, v.z, c.a); }
        static Color NormaliseLum(Color c)
        {
            c = new Color(Mathf.Max(c.r, 0f), Mathf.Max(c.g, 0f), Mathf.Max(c.b, 0f), 1f);
            float y = 0.2126f * c.r + 0.7152f * c.g + 0.0722f * c.b;
            return y > 1e-8f ? c / y : Color.white;
        }

        /// <summary>Horizontal illuminance colour (direct sun + sky dome), linear Rec.709, before adaptation.</summary>
        Color SceneIlluminantRgb()
        {
            Color sky = Color.black;
            const int rows = 12, cols = 24;
            for (int r = 0; r < rows; r++)
            {
                float z = (r + 0.5f) / rows, s = Mathf.Sqrt(1f - z * z);
                for (int c = 0; c < cols; c++)
                {
                    float phi = (c + 0.5f) * 2f * Mathf.PI / cols;
                    sky += Radiance(new Vector3(s * Mathf.Cos(phi), z, s * Mathf.Sin(phi))) * (z / rows * 2f * Mathf.PI / cols);
                }
            }
            return SunColor * (SunNormalIlluminanceLux * Mathf.Max(SunDirection.y, 0f)) + sky;
        }

        /// <summary>Von Kries in Bradford space, degree D: illuminant → D65 white, luminance of the illuminant kept.</summary>
        static Matrix4x4 AdaptationMatrix(Color illuminant, float D)
        {
            Matrix4x4 toCone = s_Bradford * s_ToXyz;
            Vector3 w = toCone.MultiplyVector(new Vector3(illuminant.r, illuminant.g, illuminant.b) / Mathf.Max(1e-6f,
                0.2126f * illuminant.r + 0.7152f * illuminant.g + 0.0722f * illuminant.b));
            Vector3 n = toCone.MultiplyVector(Vector3.one);
            var g = Matrix4x4.identity;
            g.m00 = 1f + D * (n.x / w.x - 1f); g.m11 = 1f + D * (n.y / w.y - 1f); g.m22 = 1f + D * (n.z / w.z - 1f);
            return toCone.inverse * g * toCone;
        }

        /// <summary>Hillaire 2020 f_ms per band at the observer (16 zenith bands over the sphere, 32 steps per ray).</summary>
        static float[] MultipleScatteringFraction(float[] ray, float[] mie, float[] oz)
        {
            var f = new float[Bands];
            var od = new float[Bands];
            const int zr = 16, n = 32;
            float r0 = EarthR + ObserverH;
            for (int a = 0; a < zr; a++)
            {
                float z = -1f + 2f * (a + 0.5f) / zr;
                float len = z >= 0f ? RayLengthToTop(r0, z) : ObserverH / -z;
                // The ray integral depends on z only (equal-area bands in z), so azimuth needs no samples.
                System.Array.Clear(od, 0, Bands);
                float prev = 0f;
                for (int i = 0; i < n; i++)
                {
                    float t1 = len * ((i + 1f) / n) * ((i + 1f) / n), dt = t1 - prev, tm = 0.5f * (prev + t1);
                    prev = t1;
                    float h = Mathf.Max(0f, Mathf.Sqrt(r0 * r0 + tm * tm + 2f * r0 * tm * z) - EarthR);
                    float dR = Mathf.Exp(-h / RayleighH), dM = Mathf.Exp(-h / MieH), dO = OzoneDensity(h);
                    for (int k = 0; k < Bands; k++)
                    {
                        float e = (ray[k] * dR + mie[k] * dM * MieExtinctionPerScattering + oz[k] * dO) * dt;
                        f[k] += Mathf.Exp(-od[k] - 0.5f * e) * (ray[k] * dR + mie[k] * dM) * dt / zr;
                        od[k] += e;
                    }
                }
            }
            return f;
        }

        /// <summary>
        /// ADR 0182: twilight colour of the clear dome for a sun below the horizon. The chroma LUT is computed for the sun at
        /// 0.5° (shape kept, ADR 0062), which gives a sunset palette (warm, pale) over the whole dome. After sunset the sky
        /// away from the low glow is lit by sunlight that grazed the upper atmosphere through the ozone layer; Chappuis-band
        /// absorption removes the yellow-red and the zenith turns deep blue ("blue hour"; Hulburt 1953, J. Opt. Soc. Am.
        /// 43, 113). The warm glow stays only low toward the sun's azimuth. Strength ramps from 0 at 0.5° to full at -3.5°.
        /// Target colour: the CIE daylight locus at 25 000 K pushed 1.8× further from white (deeper than any daylight
        /// CCT, as twilight zenith colours are). Luminance unchanged. WORKING_VALUE (to be compared with owner photos).
        /// </summary>
        void ApplyTwilightChroma()
        {
            float t = Mathf.Clamp01((0.5f - TrueSunElevationDeg) / 4f);
            if (t <= 0f) return;
            Color w = Color.white, blue = NormaliseLum(w + (DaylightRgb(25000f) - w) * TwilightBlueStretch);
            blue.a = 1f;
            for (int j = 0; j < ChromaHeight; j++)
            {
                float v = j / (float)(ChromaHeight - 1);                 // sqrt(cos θ): 0 horizon, 1 zenith
                for (int i = 0; i < ChromaWidth; i++)
                {
                    float gammaDeg = i / (float)(ChromaWidth - 1) * 180f;
                    float glow = (1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(15f, 75f, gammaDeg)))
                               * (1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.15f, 0.6f, v)));
                    float k = t * TwilightBlueAmount * (1f - glow);
                    int idx = j * ChromaWidth + i;
                    var c = Color.LerpUnclamped(m_Chroma[idx], blue, k);
                    // r5 (review s19 P2-7): the lowest band toward the sun read salmon-magenta; at the end of civil twilight
                    // it is orange-yellowish (B well below G). -15 % B there. WORKING_VALUE.
                    float lowBand = 1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.05f, 0.3f, v));
                    float towardSun = 1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(20f, 90f, gammaDeg));
                    c.b *= 1f - 0.15f * t * lowBand * towardSun;
                    c = SuppressTwilightMagenta(c, t * lowBand * towardSun, t);
                    c = NormaliseLum(c);
                    c.a = 1f;
                    m_Chroma[idx] = c;
                }
            }
        }

        /// <summary>
        /// ADR 0192 (review s19 0182 P2-7, still open after r5: horizon toward the sun (143, 119, 137) sRGB, B > G):
        /// a linear mix of the warm sunset LUT colour (R high) with the deep twilight blue (B high) passes through magenta
        /// - a hue the clear twilight sky does not take in the low band toward the sun, where the glow runs orange to
        /// yellow to a pale green-white before the blue (the "green" band of the twilight arch). Where both R and B exceed
        /// G (magenta excess m = min(R, B) - G): in the low band toward the sun (weight `warm`) B is pulled below G
        /// (B ≤ 0.85 G, orange-yellow); elsewhere R is pulled toward G (blue-violet instead of pink; the faint purple
        /// light high toward the sun keeps 30 % of its excess). WORKING_VALUE, luminance restored by the caller.
        /// </summary>
        public static Color SuppressTwilightMagenta(Color c, float warm, float t)
        {
            float m = Mathf.Min(c.r, c.b) - c.g;
            if (m <= 0f || t <= 0f) return c;
            float bWarm = Mathf.Min(c.b, 0.85f * c.g);
            c.b = Mathf.Lerp(c.b, bWarm, Mathf.Clamp01(warm * 1.6f));
            m = Mathf.Min(c.r, c.b) - c.g;
            if (m > 0f) c.r -= 0.7f * m * t;
            return c;
        }

        /// <summary>ADR 0182 twilight chroma: how far past the 25 000 K daylight colour the blue target sits, and the
        /// share of the dome colour it replaces away from the glow. WORKING_VALUE.</summary>
        public const float TwilightBlueStretch = 1.8f, TwilightBlueAmount = 0.85f;

        /// <summary>Clear-sky colour of luminance 1 (linear Rec.709) for a view direction (y = cos θ) and angle to the sun.</summary>
        public Color ChromaAt(float cosTheta, float gamma)
        {
            float u = Mathf.Clamp01(gamma / Mathf.PI) * (ChromaWidth - 1), v = Mathf.Sqrt(Mathf.Clamp01(cosTheta)) * (ChromaHeight - 1);
            int i = Mathf.Min((int)u, ChromaWidth - 2), j = Mathf.Min((int)v, ChromaHeight - 2);
            float fu = u - i, fv = v - j;
            Color a = Color.Lerp(m_Chroma[j * ChromaWidth + i], m_Chroma[j * ChromaWidth + i + 1], fu);
            Color b = Color.Lerp(m_Chroma[(j + 1) * ChromaWidth + i], m_Chroma[(j + 1) * ChromaWidth + i + 1], fu);
            return Color.Lerp(a, b, fv);
        }

        /// <summary>The chromaticity LUT as a texture for Kamion/Sky (RGBAHalf, bilinear, clamp).</summary>
        public Texture2D CreateChromaTexture()
        {
            var t = new Texture2D(ChromaWidth, ChromaHeight, TextureFormat.RGBAHalf, false, true)
            { name = "SkyChroma", wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear, hideFlags = HideFlags.DontSave };
            t.SetPixels(m_Chroma);
            t.Apply(false, false);
            return t;
        }

        static float IntegrateHorizontal(Func<Vector3, float> L)
        {
            const int rows = 48, cols = 96;
            float sum = 0f;
            float dz = 1f / rows, dphi = 2f * Mathf.PI / cols;
            for (int r = 0; r < rows; r++)
            {
                float z = (r + 0.5f) * dz;      // cosθ, upper hemisphere
                float s = Mathf.Sqrt(1f - z * z);
                for (int c = 0; c < cols; c++)
                {
                    float phi = (c + 0.5f) * dphi;
                    sum += L(new Vector3(s * Mathf.Cos(phi), z, s * Mathf.Sin(phi))) * z * dz * dphi;
                }
            }
            return sum;
        }

        /// <summary>CIE xyY → linear Rec.709 (sRGB primaries, D65).</summary>
        public static Color XyYToRec709(float x, float y, float Y)
        {
            y = Mathf.Max(y, 1e-4f);
            float X = x / y * Y, Z = (1f - x - y) / y * Y;
            return new Color(
                Mathf.Max(0f, 3.2404542f * X - 1.5371385f * Y - 0.4985314f * Z),
                Mathf.Max(0f, -0.9692660f * X + 1.8760108f * Y + 0.0415560f * Z),
                Mathf.Max(0f, 0.0556434f * X - 0.2040259f * Y + 1.0572252f * Z));
        }

        /// <summary>
        /// Direct-sun colour after Rayleigh + aerosol attenuation along the air mass (normalised to luminance 1).
        /// Rayleigh optical depth at sea level ≈ 0.0960 (450 nm), 0.0505 (550), 0.0242 (650); aerosol Ångström
        /// β = 0.04 (T − 1) WORKING_VALUE, α = 1.3. Produces ~5000–5800 K at 20–60° elevation for T 2–4.
        /// </summary>
        static Color SunColorFromTurbidity(float T, float airMass)
        {
            float beta = 0.04f * (T - 1f);
            float Tr(float tauR, float lambdaUm) => Mathf.Exp(-airMass * (tauR + beta * Mathf.Pow(lambdaUm, -1.3f)));
            // Solar spectrum outside the atmosphere is roughly flat (slightly blue-deficient) in these three bands.
            var c = new Color(Tr(0.0242f, 0.65f) * 0.98f, Tr(0.0505f, 0.55f), Tr(0.0960f, 0.45f) * 0.96f);
            float lum = 0.2126f * c.r + 0.7152f * c.g + 0.0722f * c.b;
            return c / Mathf.Max(lum, 1e-4f);
        }
    }
}
