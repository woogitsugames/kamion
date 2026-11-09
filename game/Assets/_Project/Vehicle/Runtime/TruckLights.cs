using Game.Vehicle.Physics;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Lamp state of the art truck (track A7): writes the 16 x 1 light-state texture read by the Lights slot of
    /// Kamion/Truck Exterior (texel = light group id from the manifest light_groups; RGB = lamp luminance in cd/m^2, the
    /// shader multiplies by the scene exposure). State from the solver input: DRL on, low beam + tail lamps with the
    /// automatic light sensor (sun below <see cref="autoLowBeamSunDeg"/>), brake lamps from the service brake pedal, reverse
    /// lamps with the selector in R. Luminances are WORKING_VALUE (LED signal lamps: ECE R7/R87 intensity over the lens
    /// area), to be replaced by measured values. One global 16 x 1 texture, updated only when the state changes, no lights: Low safe. One player truck per scene
    /// (traffic trucks will need per-instance state).
    /// </summary>
    [ExecuteAlways]
    public sealed class TruckLights : MonoBehaviour
    {
        public VehicleBody body;
        [Tooltip("Sun elevation (deg) below which the automatic low beam switches on")] public float autoLowBeamSunDeg = 6f;
        public bool forceLowBeam;
        public bool highBeam;

        // Group ids (truck_exterior_manifest.json shader_contract.light_groups).
        const int DRL = 1, LOW = 2, HIGH = 3, IND_L = 4, IND_R = 5, TAIL_BRAKE = 6, REVERSE = 7, MARKER_F = 8, MARKER_S = 9, MARKER_R = 10, FOG = 11, WORK = 12;
        // cd/m^2 (WORKING_VALUE): LED DRL ~ 400 cd over ~25 cm^2; low beam lens apparent ~ 5e4; tail 8 cd / brake 120 cd over ~60 cm^2.
        const float DrlNits = 1.6e5f, LowNits = 5e4f, HighNits = 8e4f, TailNits = 1.3e3f, BrakeNits = 2.0e4f, ReverseNits = 3e4f, MarkerNits = 2e3f;
        static readonly Color White = new Color(1f, 0.97f, 0.92f), Red = new Color(1f, 0.03f, 0.01f), Amber = new Color(1f, 0.42f, 0.02f);

        static readonly int k_State = Shader.PropertyToID("_TruckLightState");
        Texture2D m_Tex;
        readonly Color[] m_Px = new Color[16];
        uint m_LastHash;

        public Texture2D StateTexture => m_Tex;

        void OnEnable()
        {
            if (m_Tex == null)
            {
                m_Tex = new Texture2D(16, 1, TextureFormat.RGBAHalf, false, true)
                    { name = "TruckLightState", filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp, hideFlags = HideFlags.DontSave };
            }
            m_LastHash = uint.MaxValue;
            Refresh();
        }

        void OnDisable()
        {
            if (m_Tex != null) { if (Application.isPlaying) Destroy(m_Tex); else DestroyImmediate(m_Tex); m_Tex = null; }
        }

        void LateUpdate() => Refresh();

        public bool LowBeamOn
        {
            get
            {
                if (forceLowBeam) return true;
                var sun = RenderSettings.sun;
                if (sun == null) return false;
                float elev = Mathf.Asin(Mathf.Clamp(-sun.transform.forward.y, -1f, 1f)) * Mathf.Rad2Deg;
                return !sun.enabled || elev < autoLowBeamSunDeg;
            }
        }

        public void Refresh()
        {
            if (m_Tex == null) return;
            bool low = LowBeamOn;
            float brake = body != null ? (float)body.Input.Brake : 0f;
            bool reverse = body != null && body.Input.Selector == GearSelector.Reverse;
            uint hash = (low ? 1u : 0u) | (highBeam ? 2u : 0u) | (reverse ? 4u : 0u) | ((uint)(Mathf.Clamp01(brake) * 31f) << 3);
            if (hash == m_LastHash) return;
            m_LastHash = hash;

            for (int i = 0; i < 16; i++) m_Px[i] = Color.clear;
            m_Px[DRL] = White * (low ? DrlNits * 0.35f : DrlNits);   // DRL dims to position-lamp level with the low beam
            m_Px[LOW] = low ? White * LowNits : Color.clear;
            m_Px[HIGH] = highBeam ? White * HighNits : Color.clear;
            m_Px[MARKER_F] = low ? White * MarkerNits : Color.clear;
            m_Px[MARKER_S] = low ? Amber * MarkerNits : Color.clear;
            m_Px[MARKER_R] = low ? Red * MarkerNits : Color.clear;
            float tail = low ? TailNits : 0f;
            m_Px[TAIL_BRAKE] = Red * Mathf.Max(tail, brake > 0.05f ? BrakeNits : 0f);
            m_Px[REVERSE] = reverse ? White * ReverseNits : Color.clear;
            m_Tex.SetPixels(m_Px);
            m_Tex.Apply(false);
            // Global, not a property block: a property block would take the lamps out of the SRP batcher.
            Shader.SetGlobalTexture(k_State, m_Tex);
        }
    }
}
