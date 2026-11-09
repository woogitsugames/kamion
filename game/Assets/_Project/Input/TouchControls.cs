using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Touch pedals + buttons (logic; uGUI widgets write into it). Pedal values are the finger position along the
    /// pedal (0 bottom .. 1 top) and are shaped by a progressive curve (x^exponent) for fine modulation at small
    /// openings. Buttons queue one-shot commands that are emitted on the next <see cref="Sample"/>.
    /// </summary>
    public sealed class TouchControls : IDriverInput
    {
        public string Name => "dotyk";
        public bool Enabled { get; set; } = true;

        public float ThrottleExponent = 1.6f;
        public float BrakeExponent = 1.4f;

        /// <summary>Raw pedal positions 0..1 written by the widgets.</summary>
        public float ThrottleRaw, BrakeRaw;

        SelectorRequest m_Selector;
        int m_Shift, m_Retarder;
        bool m_Park, m_Manual, m_Couple, m_Legs, m_Cruise, m_RevCam;

        public void RequestSelector(SelectorRequest s) => m_Selector = s;
        public void RequestShift(int delta) => m_Shift += delta;
        public void RequestParkingToggle() => m_Park = true;
        public void RequestManualToggle() => m_Manual = true;
        public void RequestRetarderStep(int delta) => m_Retarder += delta;
        public void RequestCouplingToggle() => m_Couple = true;
        public void RequestLandingGearToggle() => m_Legs = true;
        public void RequestBrakeCruiseToggle() => m_Cruise = true;
        public void RequestReverseCameraToggle() => m_RevCam = true;

        public static float Shape(float raw, float exponent) => Mathf.Pow(Mathf.Clamp01(raw), Mathf.Max(0.1f, exponent));

        public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
        {
            intent.SteerActive = false;
            intent.Throttle = Shape(ThrottleRaw, ThrottleExponent);
            intent.Brake = Shape(BrakeRaw, BrakeExponent);
            intent.Selector = m_Selector;
            intent.ShiftDelta = m_Shift;
            intent.ToggleParkingBrake = m_Park;
            intent.ToggleManual = m_Manual;
            intent.RetarderDelta = m_Retarder;
            intent.ToggleCoupling = m_Couple;
            intent.ToggleLandingGear = m_Legs;
            intent.ToggleBrakeCruise = m_Cruise;
            intent.ToggleReverseCamera = m_RevCam;
            m_Selector = SelectorRequest.None; m_Shift = 0; m_Park = false; m_Manual = false;
            m_Retarder = 0; m_Couple = false; m_Legs = false; m_Cruise = false; m_RevCam = false;
        }
    }
}
