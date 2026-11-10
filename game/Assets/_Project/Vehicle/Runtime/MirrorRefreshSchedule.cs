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
