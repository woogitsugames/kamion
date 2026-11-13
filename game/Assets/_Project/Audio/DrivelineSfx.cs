namespace TruckSim.Audio
{
    /// <summary>
    /// ADR 0176: driveline one-shot events from physics telemetry, as a pure value type (no scene objects, no allocation,
    /// unit-tested). The controller feeds it once per audio update and plays the clips of the returned flags.
    /// <list type="bullet">
    /// <item>AMT phases (numeric values of <c>Game.Vehicle.Physics.AmtState</c>): entering ShiftNeutral = the sliding
    /// sleeve leaves the dog teeth (<see cref="AmtDisengage"/>); entering ShiftEngage = dog clutch engages
    /// (<see cref="AmtEngage"/>); leaving ShiftEngage = the clutch is closed again and its actuator vents
    /// (<see cref="AmtClutchClosed"/>).</item>
    /// <item>Exhaust-flap engine brake from the actuator state <c>Engine.EngineBrakeState</c> (first-order, 0..1):
    /// engage when the state rises 0.12 above its last minimum, release when it falls below 0.88 of its maximum since
    /// engaging (the flap starts to open ~30 ms after the lever, independent of the command shape). The detector is frozen
    /// during AMT shifts: the upshift synchronisation brake (ADR 0134) and the shift's own cut are not lever events. After a
    /// shift it re-arms from the current state: still requested = stays on (release later from the new maximum), no longer
    /// requested = off without a sound (the flap opening was masked by the shift).</item>
    /// </list>
    /// </summary>
    public struct DrivelineSfx
    {
        public const int AmtShiftTorqueRamp = 3, AmtShiftNeutral = 4, AmtShiftSync = 5, AmtShiftEngage = 6;
        public const float EngageRise = 0.12f, ReleaseRatio = 0.88f;

        public const int AmtDisengage = 1, AmtEngage = 2, AmtClutchClosed = 4, EbrakeEngage = 8, EbrakeRelease = 16;

        int m_PrevAmt;
        bool m_Init, m_EbOn, m_WasShifting;
        float m_EbMin, m_EbMax;

        /// <summary>Peak actuator state of the engine-brake application that just released (0..1): scales the dump level.</summary>
        public float LastReleaseDepth { get; private set; }

        public bool EngineBrakeOn => m_EbOn;

        public static bool IsShifting(int amtState) => amtState >= AmtShiftTorqueRamp && amtState <= AmtShiftEngage;

        /// <summary>Forget the history (respawn, teleport): the next step only initialises, no events.</summary>
        public void Reset() { m_Init = false; m_EbOn = false; m_WasShifting = false; LastReleaseDepth = 0f; }

        /// <summary>One update. Returns a bit set of the event constants above (0 = nothing).</summary>
        /// <param name="amtState">Numeric <c>AmtState</c>.</param>
        /// <param name="engineBrakeState">Actuator state 0..1 (<c>Engine.EngineBrakeState</c>).</param>
        /// <param name="engineBrakeRequested">The driver's lever asks for the engine brake (<c>EngineBrakeCommand &gt; 0</c>).</param>
        public int Step(int amtState, float engineBrakeState, bool engineBrakeRequested)
        {
            float s = engineBrakeState < 0f ? 0f : engineBrakeState > 1f ? 1f : engineBrakeState;
            if (!m_Init)
            {
                m_Init = true;
                m_PrevAmt = amtState;
                m_EbOn = s > 0.5f;
                m_EbMin = s;
                m_EbMax = s;
                return 0;
            }
            int ev = 0;
            if (amtState != m_PrevAmt)
            {
                if (amtState == AmtShiftNeutral) ev |= AmtDisengage;
                if (amtState == AmtShiftEngage) ev |= AmtEngage;
                if (m_PrevAmt == AmtShiftEngage && !IsShifting(amtState)) ev |= AmtClutchClosed;
                m_PrevAmt = amtState;
            }
            if (IsShifting(amtState))
            {
                m_WasShifting = true;
                return ev; // frozen: keep the lever state across the shift
            }
            if (m_WasShifting)
            {
                m_WasShifting = false;
                if (m_EbOn && !engineBrakeRequested) m_EbOn = false;
                m_EbMin = s;
                m_EbMax = s;
                return ev;
            }
            if (!m_EbOn)
            {
                if (s < m_EbMin) m_EbMin = s;
                if (s > m_EbMin + EngageRise)
                {
                    m_EbOn = true;
                    m_EbMax = s;
                    ev |= EbrakeEngage;
                }
            }
            else
            {
                if (s > m_EbMax) m_EbMax = s;
                if (s < m_EbMax * ReleaseRatio)
                {
                    m_EbOn = false;
                    m_EbMin = s;
                    LastReleaseDepth = m_EbMax;
                    ev |= EbrakeRelease;
                }
            }
            return ev;
        }
    }
}
