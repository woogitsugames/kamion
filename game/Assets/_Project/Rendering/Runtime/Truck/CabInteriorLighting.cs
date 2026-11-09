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
        [Tooltip("Cab-view lift in stops (phone local tone mapping, D23)")] public float cabViewEv = 0.3f;
        [Tooltip("Extra fill scale (1 = physical estimate)")] public float fillScale = 1f;
        [Tooltip("Colour of the bounce (warm: dash, koniak, floor mat)")] public Color bounceTint = new Color(1f, 0.93f, 0.85f);

        /// <summary>Windows in the cab frame: outward normal and daylight-opening area (m^2).</summary>
        static readonly Vector3[] k_WinN =
        {
            new Vector3(0f, 0.3256f, 0.9455f),  // windscreen, rake 19 deg (glass_interface.json)
            new Vector3(-1f, 0f, 0.05f),        // driver door glass
            new Vector3(1f, 0f, 0.05f),         // passenger door glass
        };
        static readonly float[] k_WinA = { 1.85f, 0.62f, 0.62f };

        static readonly int k_Fill = Shader.PropertyToID("_CabFill"), k_Gain = Shader.PropertyToID("_CabGain");

        public Vector3 LastFill { get; private set; }
        public float LastGain { get; private set; } = 1f;
        public Camera viewCamera;

        void OnDisable()
        {
            Shader.SetGlobalVector(k_Fill, Vector4.zero);
            Shader.SetGlobalFloat(k_Gain, 1f);
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
                float flux = 0f;
                for (int i = 0; i < k_WinN.Length; i++)
                {
                    float cos = Mathf.Max(0f, Vector3.Dot(k_WinN[i].normalized, sLocal));
                    flux += k_WinA[i] * (m.SunNormalIlluminanceLux * cos + eSky);
                }
                flux *= glassTransmittance;
                float rho = Mathf.Clamp(meanAlbedo, 0.01f, 0.9f);
                float eBounce = flux * rho / (interiorArea * (1f - rho));
                float k = m.Exposure / Mathf.PI * fillScale;
                Color c = m.SunColor * bounceTint;
                fill = new Vector3(c.r, c.g, c.b) * (eBounce * k);
            }
            float gain = 1f;
            if (cam != null && interiorBounds.Contains(t.InverseTransformPoint(cam.transform.position)))
                gain = Mathf.Pow(2f, cabViewEv);
            LastFill = fill;
            LastGain = gain;
            Shader.SetGlobalVector(k_Fill, new Vector4(fill.x, fill.y, fill.z, 0f));
            Shader.SetGlobalFloat(k_Gain, gain);
        }
    }
}
