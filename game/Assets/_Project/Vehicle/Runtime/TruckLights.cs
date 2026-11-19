using Game.Vehicle.Physics;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Lamp state of the art truck (track A7): writes the 32 x 1 light-state texture read by the Lights slot of
    /// Kamion/Truck Exterior (texel = light group id from the manifest light_groups; RGB = lamp luminance / NitsPerEncodedUnit, the
    /// shader decodes the nits scale before applying scene exposure; A = limiter reference, ADR 0197). State from the solver input: DRL on, low beam + tail lamps with the
    /// automatic light sensor (sun below <see cref="autoLowBeamSunDeg"/>), brake lamps from the service brake pedal, reverse
    /// lamps with the selector in R. Luminances are WORKING_VALUE display calibrations, not measured lamp photometry.
    /// One global 32 x 1 texture, updated only when the state changes, no lights: Low safe. One player truck per scene
    /// (traffic trucks will need per-instance state).
    /// </summary>
    [ExecuteAlways]
    public sealed class TruckLights : MonoBehaviour
    {
        public VehicleBody body;
        [Tooltip("Sun elevation (deg) below which the automatic low beam switches on")] public float autoLowBeamSunDeg = 6f;
        public bool forceLowBeam;
        public bool highBeam;
        // ADR 0178 visual QA: stop lamps lit without a vehicle input (KAMION_QA_LAMPS=brake). Not serialized, never set in play.
        [System.NonSerialized] public bool forceBrake;
        // ADR 0299 visual QA: reversing lamps lit without a gear selector (KAMION_QA_LAMPS=reverse). Not serialized, never set in play.
        [System.NonSerialized] public bool forceReverse;
        [Tooltip("Turn-signal lever: 0 off, -1 left, +1 right, 2 hazard (set by the gameplay layer from the stalk)")] public int indicatorLever;
        [Tooltip("Flasher relay contact closed (lamps lit); phase from the stalk's 1.5 Hz flasher")] public bool flasherLit;
        [Tooltip("Rear fog lamps (tractor: one lamp on the left; trailer: one per combination lamp). ADR 0175, light group 14")] public bool rearFog;

        // Group ids (manifest shader_contract.light_groups) = LampPhotometry (ADR 0197: 16 TAIL / 17 STOP, trailer chambers).
        const int DRL = LampPhotometry.Drl, LOW = LampPhotometry.LowBeam, HIGH = LampPhotometry.HighBeam, IND_L = LampPhotometry.IndL,
            IND_R = LampPhotometry.IndR, TAIL_BRAKE = LampPhotometry.TailBrake, REVERSE = LampPhotometry.Reverse,
            MARKER_F = LampPhotometry.MarkerFront, MARKER_S = LampPhotometry.MarkerSide, MARKER_R = LampPhotometry.MarkerRear,
            PLATE = LampPhotometry.Plate, FOG_REAR = LampPhotometry.FogRear, TAIL = LampPhotometry.Tail, STOP = LampPhotometry.Stop;
        // Raw cd/m^2 WORKING_VALUEs retained from ADR 0087 (LampPhotometry). ADR 0115 calibrates the displayed DRL highlight in
        // the shader. Day/night ratio remains 1 / 0.35; the source values are not measured lamp photometry.
        const float DrlNits = LampPhotometry.DrlNits, LowNits = LampPhotometry.LowNits, HighNits = LampPhotometry.HighNits,
            TailNits = LampPhotometry.TailNits, BrakeNits = LampPhotometry.BrakeNits, ReverseNits = LampPhotometry.ReverseNits,
            MarkerNits = LampPhotometry.MarkerNits, IndicatorNits = LampPhotometry.IndicatorNits, RearFogNits = LampPhotometry.RearFogNits;
        // Linear sRGB emitter colours (LampPhotometry, ADR 0197). The R48 red and amber areas both lie outside the sRGB gamut:
        // red (1, 0, 0) x 0.640 y 0.330 is the nearest reachable point (yellow limit met, purple limit 0.010 short);
        // amber (1, 0.22, 0) x 0.542 y 0.408 meets the green and red limits, 0.016 xy from the area (white limit unreachable).
        // Display limit of the radiance: TruckExterior.shader TruckLampHueLimitRef.
        public static readonly Color White = ToColor(LampPhotometry.WhiteLinear), Red = ToColor(LampPhotometry.RedLinear),
            Amber = ToColor(LampPhotometry.AmberLinear);
        static Color ToColor(float[] c) => new Color(c[0], c[1], c[2]);

        // Encode luminance before RGBAHalf storage: DRL160000 and high80000 exceed65504.
        // Shader decodes in float after combining this scale with scene exposure. No photometric calibration implied.
        public const float NitsPerEncodedUnit = 1000f;
        static readonly int k_NitsScale = Shader.PropertyToID("_TruckLightNitsScale");
        static readonly int k_State = Shader.PropertyToID("_TruckLightState");
        Texture2D m_Tex;
        readonly Color[] m_Px = new Color[LampPhotometry.StateTexels];
        uint m_LastHash;

        public Texture2D StateTexture => m_Tex;

        void OnEnable()
        {
            if (m_Tex == null)
            {
                m_Tex = new Texture2D(LampPhotometry.StateTexels, 1, TextureFormat.RGBAHalf, false, true)
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
            float brake = forceBrake ? 1f : body != null ? (float)body.Input.Brake : 0f;
            bool reverse = forceReverse || (body != null && body.Input.Selector == GearSelector.Reverse);
            bool indL = flasherLit && (indicatorLever == -1 || indicatorLever == 2);
            bool indR = flasherLit && (indicatorLever == 1 || indicatorLever == 2);
            uint hash = (low ? 1u : 0u) | (highBeam ? 2u : 0u) | (reverse ? 4u : 0u) | ((uint)(Mathf.Clamp01(brake) * 31f) << 3)
                        | (indL ? 256u : 0u) | (indR ? 512u : 0u) | (rearFog ? 1024u : 0u);
            if (hash == m_LastHash) return;
            m_LastHash = hash;

            for (int i = 0; i < m_Px.Length; i++) m_Px[i] = Color.clear;
            m_Px[DRL] = White * (low ? DrlNits * 0.35f : DrlNits);   // DRL dims to position-lamp level with the low beam
            m_Px[LOW] = low ? White * LowNits : Color.clear;
            m_Px[HIGH] = highBeam ? White * HighNits : Color.clear;
            m_Px[MARKER_F] = low ? White * MarkerNits : Color.clear;
            m_Px[MARKER_S] = low ? Amber * MarkerNits : Color.clear;
            m_Px[MARKER_R] = low ? Red * MarkerNits : Color.clear;
            m_Px[PLATE] = low ? White * MarkerNits : Color.clear;   // trailer plate lamp (trailer manifest group 13), with the position lamps
            float tail = low ? TailNits : 0f;
            bool braking = brake > 0.05f;
            m_Px[TAIL_BRAKE] = Red * Mathf.Max(tail, braking ? BrakeNits : 0f);   // tractor: one chamber, tail + stop
            m_Px[TAIL] = Red * tail;                                               // trailer: tail chamber (ADR 0197)
            m_Px[STOP] = braking ? Red * BrakeNits : Color.clear;                  // trailer: stop chamber (ADR 0197)
            // Indicators: one global texture feeds the tractor and the trailer lamps (same group ids 4 / 5 in both manifests).
            m_Px[IND_L] = indL ? Amber * IndicatorNits : Color.clear;
            m_Px[IND_R] = indR ? Amber * IndicatorNits : Color.clear;
            m_Px[REVERSE] = reverse ? White * ReverseNits : Color.clear;
            // Rear fog lamps (UN R48 6.11): red, only with the dipped beam / front fog on (6.11.7.1); WORKING_VALUE luminance.
            m_Px[FOG_REAR] = rearFog && low ? Red * RearFogNits : Color.clear;
            // Alpha = limiter reference (ADR 0197): the shader limits every state of a group at the gain of its brightest
            // state, so tail : stop survives the ADR 0178 limiter (UN R148 4.8.11 >= 5 : 1). 0 = per-pixel limit (ADR 0178).
            for (int i = 0; i < m_Px.Length; i++) m_Px[i].a = LampPhotometry.LimiterReferenceNits(i);
            for (int i = 0; i < m_Px.Length; i++) m_Px[i] *= 1f / NitsPerEncodedUnit;
            m_Tex.SetPixels(m_Px);
            m_Tex.Apply(false);
            // Global, not a property block: a property block would take the lamps out of the SRP batcher.
            Shader.SetGlobalFloat(k_NitsScale, NitsPerEncodedUnit);
            Shader.SetGlobalTexture(k_State, m_Tex);
        }
    }
}
