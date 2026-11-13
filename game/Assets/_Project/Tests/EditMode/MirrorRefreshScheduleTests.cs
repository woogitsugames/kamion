using System.Collections.Generic;
using Game.Vehicle.Runtime;
using NUnit.Framework;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// Mirror refresh schedule (ADR 0042, ADR 0046 addendum): per-frame cap, steady class II refresh on High, Low unchanged,
    /// no starvation of the convex mirrors, no allocation in the per-frame step.
    /// Order as built by TruckAssetBuilder: MainL, MainR (class II), WideL, WideR (IV), Kerb (V), Front (VI).
    /// </summary>
    public class MirrorRefreshScheduleTests
    {
        static MirrorRefreshSchedule.Entry[] Six(params bool[] visible)
        {
            var e = new MirrorRefreshSchedule.Entry[6];
            for (int i = 0; i < 6; i++)
                e[i] = new MirrorRefreshSchedule.Entry { phase = i, main = i < 2, weight = i < 2 ? 1f : 0.5f, candidate = visible.Length == 0 || visible[i] };
            return e;
        }

        /// <summary>Runs warm-up + measured frames; returns the set of render intervals (frames) per mirror and the max renders per frame.</summary>
        static (HashSet<int>[] intervals, int maxPerFrame) Run(MirrorRefreshSchedule.Entry[] e, int cap, int mainSlots, int frames = 96, int warmup = 16)
        {
            var last = new int[e.Length];
            var iv = new HashSet<int>[e.Length];
            for (int i = 0; i < e.Length; i++) { last[i] = -1; iv[i] = new HashSet<int>(); }
            int maxN = 0;
            for (int f = 0; f < warmup + frames; f++)
            {
                int n = MirrorRefreshSchedule.Step(e, e.Length, cap, mainSlots);
                int counted = 0;
                for (int i = 0; i < e.Length; i++)
                {
                    if (!e[i].selected) continue;
                    counted++;
                    Assert.IsTrue(e[i].candidate, $"mirror {i} rendered while not a candidate");
                    if (f >= warmup && last[i] >= 0) iv[i].Add(f - last[i]);
                    last[i] = f;
                }
                Assert.AreEqual(counted, n);
                if (n > maxN) maxN = n;
            }
            return (iv, maxN);
        }

        static void AssertEvery(HashSet<int>[] iv, int mirror, int frames)
        {
            CollectionAssert.AreEquivalent(new[] { frames }, iv[mirror], $"mirror {mirror}: intervals {string.Join(",", iv[mirror])}, expected a steady {frames}");
        }

        [Test]
        public void High_AllSix_ClassII_Every2ndFrameSteady_Convex_Every4th_CapTwo()
        {
            var (iv, maxN) = Run(Six(), cap: 2, mainSlots: 1);
            Assert.AreEqual(2, maxN);
            AssertEvery(iv, 0, 2); AssertEvery(iv, 1, 2);
            for (int i = 2; i < 6; i++) AssertEvery(iv, i, 4);
        }

        [Test]
        public void High_OneSideOnScreen_MainAndWide_EveryFrame()
        {
            var (iv, _) = Run(Six(true, false, true, false, false, false), cap: 2, mainSlots: 1);
            AssertEvery(iv, 0, 1); AssertEvery(iv, 2, 1);
            // Right side: main every frame, wide / kerb / front share the second slot.
            (iv, _) = Run(Six(false, true, false, true, true, true), cap: 2, mainSlots: 1);
            AssertEvery(iv, 1, 1);
            for (int i = 3; i < 6; i++) AssertEvery(iv, i, 3);
        }

        [Test]
        public void High_NoConvexOnScreen_SecondSlotGoesToMain()
        {
            var (iv, maxN) = Run(Six(true, true, false, false, false, false), cap: 2, mainSlots: 1);
            Assert.AreEqual(2, maxN);
            AssertEvery(iv, 0, 1); AssertEvery(iv, 1, 1);
        }

        [Test]
        public void Low_Unchanged_OneRenderPerFrame_Main4th_Convex8th()
        {
            var (iv, maxN) = Run(Six(), cap: 1, mainSlots: 0);
            Assert.AreEqual(1, maxN);
            AssertEvery(iv, 0, 4); AssertEvery(iv, 1, 4);
            for (int i = 2; i < 6; i++) AssertEvery(iv, i, 8);
        }

        [Test]
        public void Medium_Unchanged_Main2nd_Convex4th()
        {
            var (iv, maxN) = Run(Six(), cap: 2, mainSlots: 0);
            Assert.AreEqual(2, maxN);
            AssertEvery(iv, 0, 2); AssertEvery(iv, 1, 2);
            for (int i = 2; i < 6; i++) AssertEvery(iv, i, 4);
        }

        [Test]
        public void Budget_PerTier_MatchesAdr0046()
        {
            int[] cap = { 1, 2, 2, 6 }, reserved = { 0, 0, 1, 0 };
            for (int lvl = 0; lvl < 4; lvl++)
            {
                Assert.AreEqual(cap[lvl], VehicleCameraBudget.MirrorsPerFrameFor(lvl), $"level {lvl} MirrorsPerFrame");
                Assert.AreEqual(reserved[lvl], VehicleCameraBudget.MainMirrorSlotsFor(lvl), $"level {lvl} MainMirrorSlots");
            }
        }

        [Test]
        public void Step_DoesNotAllocate()
        {
            var e = Six();
            Game.Tests.GcAllocCounter.AssertZero(
                () => { for (int f = 0; f < 1000; f++) MirrorRefreshSchedule.Step(e, 6, 2, 1); },
                warmup: () => { for (int f = 0; f < 32; f++) MirrorRefreshSchedule.Step(e, 6, 2, 1); },
                message: "MirrorRefreshSchedule.Step must not allocate");
        }
    }
}
