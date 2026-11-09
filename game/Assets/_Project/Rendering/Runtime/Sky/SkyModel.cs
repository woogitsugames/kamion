using System;
using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// Analytic daylight model used for the sky dome, the ambient SH, the reflection cubemap, the sun light and the fog
    /// colour, so all five agree (docs/adr/0010-look-development-sky-exposure-tonemapping.md).
    ///
    /// Clear sky: Preetham, Shirley, Smits, "A Practical Analytic Model for Daylight" (SIGGRAPH 1999): Perez luminance
    /// distribution and CIE xy chromaticity as functions of turbidity T, converted to linear Rec.709. Overcast: CIE standard
    /// overcast sky (Moon and Spencer 1942, CIE S 011/E:2003 type 1): L(θ) = Lz (1 + 2 cos θ) / 3, achromatic D65.
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

        // Perez coefficients (A..E) for Y, x, y and zenith values (clear part).
        readonly float[] m_PY = new float[5], m_Px = new float[5], m_Py = new float[5];
        readonly float m_Zx, m_Zy, m_ThetaS;
        readonly float m_ClearScale;     // cd/m² per unit of normalised Preetham luminance
        readonly float m_OvercastZenith; // cd/m²

        /// <param name="sunElevationDeg">sun altitude above the horizon</param>
        /// <param name="sunAzimuthDeg">compass azimuth (0 = north, 90 = east), world X = east, Z = north</param>
        /// <param name="turbidity">Linke-like turbidity of the Preetham model, 2 (very clear) … 6 (hazy)</param>
        /// <param name="overcast">0 clear … 1 fully overcast (CIE)</param>
        /// <param name="ev100">exposure value at ISO 100; k = 1 / (1.2 · 2^EV100) (Lagarde and de Rousiers 2014)</param>
        public SkyModel(float sunElevationDeg, float sunAzimuthDeg, float turbidity, float overcast, float ev100)
        {
            SunElevationDeg = Mathf.Clamp(sunElevationDeg, 0.5f, 89.5f);
            Turbidity = Mathf.Clamp(turbidity, 1.7f, 10f);
            Overcast = Mathf.Clamp01(overcast);
            float el = SunElevationDeg * Mathf.Deg2Rad, az = sunAzimuthDeg * Mathf.Deg2Rad;
            SunDirection = new Vector3(Mathf.Cos(el) * Mathf.Sin(az), Mathf.Sin(el), Mathf.Cos(el) * Mathf.Cos(az)).normalized;
            Exposure = ExposureFromEv100(ev100);

            float sinH = Mathf.Sin(el);
            float m = AirMass(SunElevationDeg);
            float clearDn = SolarIlluminanceExtraterrestrialLux * Mathf.Exp(-ClearExtinctionC * m);
            float clearKh = (0.8f + 15.5f * Mathf.Sqrt(sinH)) * 1000f;
            float overKh = (0.3f + 21.0f * sinH) * 1000f;
            SunNormalIlluminanceLux = clearDn * (1f - Overcast);
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
            // CIE overcast: E_h = 7π/9 · Lz.
            m_OvercastZenith = overKh * 9f / (7f * Mathf.PI);

            SunColor = SunColorFromTurbidity(T, m);
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
                ClearXyY(dir, out float Y, out float x, out float y);
                c += XyYToRec709(x, y, Y * m_ClearScale) * (1f - Overcast);
            }
            if (Overcast > 0f)
            {
                float L = m_OvercastZenith * (1f + 2f * dir.y) / 3f;
                c += new Color(L, L, L) * Overcast;
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
            misc = new Vector4(Overcast, SunNormalIlluminanceLux * Exposure / SunSolidAngleSr, 0f, 0f);
        }

        // ---------------------------------------------------------------- SH and cubemap
        /// <summary>
        /// Projects the exposed sky (upper hemisphere) plus a Lambertian ground (lower hemisphere, albedo × horizontal
        /// illuminance / π) into Unity's L2 ambient probe. Each sample acts as a directional light of intensity L·k·dω/π,
        /// which reproduces the irradiance E(n)·k/π a Unity Lambert surface expects. The sun is NOT included (real light).
        /// </summary>
        public UnityEngine.Rendering.SphericalHarmonicsL2 AmbientProbe(Color groundAlbedo, int resolution = 24)
        {
            var sh = new UnityEngine.Rendering.SphericalHarmonicsL2();
            Color ground = groundAlbedo * (HorizontalIlluminanceLux * Exposure / Mathf.PI);
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
                    Color L = z > 0f ? ExposedRadiance(d) : ground;
                    sh.AddDirectionalLight(d, L, dOmega / Mathf.PI);
                }
            }
            return sh * ShConventionScale(resolution);
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
            Color ground = groundAlbedo * (HorizontalIlluminanceLux * Exposure / Mathf.PI);
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
        public Cubemap ReflectionCubemap(Color groundAlbedo, int size = 64)
        {
            var cube = new Cubemap(size, TextureFormat.RGBAHalf, true) { name = "SkyReflection", filterMode = FilterMode.Trilinear, wrapMode = TextureWrapMode.Clamp };
            Color ground = groundAlbedo * (HorizontalIlluminanceLux * Exposure / Mathf.PI);
            Color horizon = HorizonColorExposed();
            var px = new Color[size * size];
            for (int f = 0; f < 6; f++)
            {
                var face = (CubemapFace)f;
                for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                    Vector3 d = FaceDirection(face, u, v).normalized;
                    Color c = d.y >= 0f ? ExposedRadiance(d) : Color.Lerp(horizon, ground, Mathf.SmoothStep(0f, 1f, -d.y * 4f));
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

        float ClearLuminanceRelative(Vector3 dir)
        {
            float theta = Mathf.Acos(Mathf.Clamp(dir.y, -1f, 1f));
            float gamma = Mathf.Acos(Mathf.Clamp(Vector3.Dot(dir, SunDirection), -1f, 1f));
            return m_ClearScale * Perez(m_PY, theta, gamma) / Perez(m_PY, 0f, m_ThetaS);
        }

        void ClearXyY(Vector3 dir, out float Y, out float x, out float y)
        {
            float theta = Mathf.Acos(Mathf.Clamp(dir.y, -1f, 1f));
            float gamma = Mathf.Acos(Mathf.Clamp(Vector3.Dot(dir, SunDirection), -1f, 1f));
            Y = Perez(m_PY, theta, gamma) / Perez(m_PY, 0f, m_ThetaS);
            // Preetham's chromaticity turns magenta in the last few degrees above the horizon (known artefact of the
            // fit); evaluate chromaticity no lower than 6° elevation.
            float thetaC = Mathf.Min(theta, ChromaMaxZenithRad);
            x = m_Zx * Perez(m_Px, thetaC, gamma) / Perez(m_Px, 0f, m_ThetaS);
            y = m_Zy * Perez(m_Py, thetaC, gamma) / Perez(m_Py, 0f, m_ThetaS);
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
