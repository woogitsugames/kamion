using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Pure, allocation-free mirror refresh schedule (ADR 0042, addendum ADR 0046): which mirrors render this frame under a
    /// shared per-frame cap. Every candidate (glass visible) accrues its weight as debt; the largest debts render and are
    /// reset; ties go to the lower phase.
    /// <para>
    /// <c>mainSlots</c> reserves that many of the <c>cap</c> slots for main mirrors (UN R46 class II) and gives the remaining
    /// slots to the convex mirrors (classes IV-VI) first, falling back to any candidate. With mainSlots 0 this is the plain
    /// weighted round-robin of ADR 0042. High uses cap 2 / mainSlots 1: one slot alternates the two class II mirrors
    /// (each every 2nd frame, steady 30 Hz at 60 FPS; every frame when only one is on screen), the other rotates the four
    /// convex mirrors (each every 4th frame).
    /// </para>
    /// </summary>
    public static class MirrorRefreshSchedule
    {
        public struct Entry
        {
            public float debt;
            public float weight;
            public int phase;
            public bool main;
            public bool candidate;
            /// <summary>Due-based schedule (ADR 0068): target render interval in frames (debt grows 1/interval per frame).</summary>
            public float interval;
            /// <summary>Due-based schedule: may take a spare slot (classes II and IV while driving).</summary>
            public bool fill;
            /// <summary>Due-based schedule state: candidate since an earlier frame (stagger offset applied).</summary>
            public bool started;
            /// <summary>Output: render this frame.</summary>
            public bool selected;
        }

        const byte AnyMirror = 0, MainOnly = 1, ConvexOnly = 2;

        /// <summary>Advances one frame for <paramref name="count"/> entries; returns the number selected (&lt;= cap).</summary>
        public static int Step(Entry[] e, int count, int cap, int mainSlots)
        {
            if (cap < 1) cap = 1;
            if (mainSlots < 0) mainSlots = 0;
            if (mainSlots > cap) mainSlots = cap;
            for (int i = 0; i < count; i++)
            {
                e[i].debt = e[i].candidate ? e[i].debt + (e[i].weight > 0.05f ? e[i].weight : 0.05f) : 0f;
                e[i].selected = false;
            }
            int n = 0;
            while (n < mainSlots && Pick(e, count, MainOnly)) n++;
            if (mainSlots > 0) while (n < cap && Pick(e, count, ConvexOnly)) n++;
            while (n < cap && Pick(e, count, AnyMirror)) n++;
            return n;
        }

        /// <summary>
        /// Due-based step (ADR 0068): every candidate accrues 1/interval per frame and is due at a debt of 1; at most
        /// <paramref name="cap"/> due mirrors render, most overdue first (ties: lower phase), and a rendered mirror keeps the
        /// remainder (debt - 1), so cadences stay steady. A mirror that becomes a candidate starts at an offset of
        /// (phase mod interval) / interval: mirrors with the same interval are staggered and the per-frame load is even
        /// (High, all six on screen: II L/R alternate, one convex per frame = 2 every frame, as ADR 0046).
        /// Unlike <see cref="Step"/> the cap is a limit, not a quota: when <paramref name="fillSpare"/> is false a frame where
        /// nothing is due renders nothing, so longer intervals (parked truck) really save renders. With
        /// <paramref name="fillSpare"/> the slots left go to candidates marked <see cref="Entry.fill"/> (classes II, IV) by debt,
        /// which keeps the ADR 0046 behaviour while driving (one side on screen: its II and IV every frame).
        /// Debt is capped at 2 (no burst of catch-up renders). Returns the number selected. No allocation.
        /// </summary>
        public static int StepDue(Entry[] e, int count, int cap, bool fillSpare)
        {
            if (cap < 1) cap = 1;
            for (int i = 0; i < count; i++)
            {
                e[i].selected = false;
                if (!e[i].candidate) { e[i].debt = 0f; e[i].started = false; continue; }
                float iv = e[i].interval >= 1f ? e[i].interval : 1f;
                if (!e[i].started)
                {
                    int k = Mathf.Max(1, Mathf.RoundToInt(iv));
                    e[i].debt = (e[i].phase % k) / (float)k;
                    e[i].started = true;
                }
                e[i].debt = Mathf.Min(e[i].debt + 1f / iv, 2f);
            }
            int n = 0;
            while (n < cap && PickDue(e, count, 1f - 1e-4f, false)) n++;
            if (fillSpare) while (n < cap && PickDue(e, count, float.NegativeInfinity, true)) n++;
            return n;
        }

        static bool PickDue(Entry[] e, int count, float minDebt, bool fillOnly)
        {
            int best = -1;
            for (int i = 0; i < count; i++)
            {
                if (!e[i].candidate || e[i].selected || e[i].debt < minDebt || fillOnly && !e[i].fill) continue;
                if (best < 0 || e[i].debt > e[best].debt + 1e-5f || Mathf.Abs(e[i].debt - e[best].debt) <= 1e-5f && e[i].phase < e[best].phase) best = i;
            }
            if (best < 0) return false;
            e[best].selected = true;
            e[best].debt = Mathf.Max(0f, e[best].debt - 1f);
            return true;
        }

        static bool Pick(Entry[] e, int count, byte filter)
        {
            int best = -1;
            for (int i = 0; i < count; i++)
            {
                if (!e[i].candidate || e[i].selected) continue;
                if (filter == MainOnly && !e[i].main || filter == ConvexOnly && e[i].main) continue;
                if (best < 0 || e[i].debt > e[best].debt || e[i].debt == e[best].debt && e[i].phase < e[best].phase) best = i;
            }
            if (best < 0) return false;
            e[best].selected = true;
            e[best].debt = 0f;
            return true;
        }
    }
}
