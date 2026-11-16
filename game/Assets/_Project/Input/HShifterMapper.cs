using System;

namespace Game.Controls
{
    /// <summary>
    /// H-pattern shifter → truck gearbox commands (ADR 0263). The truck has a 12-speed AMT (docs/04 §2.7): an H-shifter
    /// with N gates (6 by default) plus a range switch (low/high) addresses gears 1..2N; reverse is its own gate.
    /// The shifter is absolute, the current vehicle interface is relative (<see cref="DriverIntent.ShiftDelta"/>,
    /// <see cref="DriverIntent.Selector"/>), so this class remembers the last engaged gear and emits:
    /// - reverse gate → <see cref="SelectorRequest.Reverse"/>;
    /// - a forward gate after N/R → <see cref="SelectorRequest.Drive"/> (+ the delta from the AMT start gear is the
    ///   AMT's business, documented limitation);
    /// - a forward gate after another forward gate → <see cref="DriverIntent.ShiftDelta"/> = new − old gear, and
    ///   <see cref="DriverIntent.TargetGear"/> = the absolute gear (for an absolute AMT request, proposal in ADR 0263);
    /// - neutral only when the lever stays out of every gate for <see cref="NeutralHoldS"/> (moving 3 → 4 passes
    ///   through neutral, which must not drop the AMT to N between shifts).
    /// Pure, allocation-free, unit-tested.
    /// </summary>
    public sealed class HShifterMapper
    {
        /// <summary>Forward gates of the shifter (6 for a 6+R shifter).</summary>
        public int GatesPerRange = 6;
        /// <summary>The range switch (splitter button / toggle) adds <see cref="GatesPerRange"/> to the gate number.</summary>
        public bool UseRange = true;
        /// <summary>Time out of every gate before neutral is requested [s]. WORKING_VALUE (a quick H-shift takes ~0.2-0.4 s, UNVERIFIED).</summary>
        public float NeutralHoldS = 0.6f;

        /// <summary>Last engaged gear: -1 = R, 0 = N, 1.. forward.</summary>
        public int EngagedGear { get; private set; }
        float m_OutOfGateS;

        /// <summary>Gate from the button states: the first pressed forward gate (1-based), -1 for reverse, 0 = none.</summary>
        public static int Slot(bool[] forwardGates, int count, bool reverseGate)
        {
            if (reverseGate) return -1;
            if (forwardGates == null) return 0;
            int n = Math.Min(count, forwardGates.Length);
            for (int i = 0; i < n; i++) if (forwardGates[i]) return i + 1;
            return 0;
        }

        /// <summary>Absolute gear for a gate and range position.</summary>
        public int Gear(int slot, bool rangeHigh) => slot > 0 && UseRange && rangeHigh ? slot + GatesPerRange : slot;

        public void Reset(int engagedGear = 0) { EngagedGear = engagedGear; m_OutOfGateS = 0f; }

        /// <summary>Feeds the current gate/range; writes one-shot commands into <paramref name="intent"/> on a change.</summary>
        public void Update(float dt, int slot, bool rangeHigh, ref DriverIntent intent)
        {
            if (slot == 0)
            {
                m_OutOfGateS += Math.Max(0f, dt);
                if (EngagedGear != 0 && m_OutOfGateS >= NeutralHoldS)
                {
                    EngagedGear = 0;
                    intent.Selector = SelectorRequest.Neutral;
                }
                return;
            }
            m_OutOfGateS = 0f;
            int gear = Gear(slot, rangeHigh);
            if (gear == EngagedGear) return;
            if (gear < 0) intent.Selector = SelectorRequest.Reverse;
            else if (EngagedGear <= 0) intent.Selector = SelectorRequest.Drive;
            else intent.ShiftDelta += gear - EngagedGear;
            if (gear > 0) { intent.TargetGear = gear; }
            EngagedGear = gear;
        }
    }

    /// <summary>Rising-edge detector for a fixed set of buttons (paddles, mapped actions). Allocation-free after construction.</summary>
    public sealed class ButtonEdges
    {
        readonly bool[] m_Prev;
        public ButtonEdges(int count) { m_Prev = new bool[Math.Max(0, count)]; }
        public int Count => m_Prev.Length;

        /// <summary>True only on the frame the button goes down.</summary>
        public bool Pressed(int index, bool down)
        {
            if ((uint)index >= (uint)m_Prev.Length) return false;
            bool edge = down && !m_Prev[index];
            m_Prev[index] = down;
            return edge;
        }

        public void Clear() { Array.Clear(m_Prev, 0, m_Prev.Length); }
    }
}
