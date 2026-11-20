using System;
using Game.Core;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>ADR 0311: look-ahead peak limiter of the listener bus - transparent under the ceiling, no sample over it,
    /// no gain step (click).</summary>
    public sealed class BusLimiterTests
    {
        const int Rate = 48000, Ch = 2, Block = 512;

        static float[] Sine(int frames, float amp, float hz, int ch = Ch)
        {
            var d = new float[frames * ch];
            for (int f = 0; f < frames; f++)
                for (int c = 0; c < ch; c++) d[f * ch + c] = amp * (float)Math.Sin(2 * Math.PI * hz * f / Rate);
            return d;
        }

        static float[] Run(BusLimiter lim, float[] src, int ch = Ch)
        {
            var outp = (float[])src.Clone();
            var block = new float[Block * ch];
            for (int i = 0; i + block.Length <= outp.Length; i += block.Length)
            {
                Array.Copy(outp, i, block, 0, block.Length);
                lim.Process(block, ch, Rate);
                Array.Copy(block, 0, outp, i, block.Length);
            }
            return outp;
        }

        [Test]
        public void UnderTheCeiling_IsADelayedBitExactCopy()
        {
            var src = Sine(Block * 20, 0.5f, 110f);
            var lim = new BusLimiter();
            var o = Run(lim, src);
            int d = (BusLimiter.LookaheadFrames - 1) * Ch;
            for (int i = d; i < src.Length; i++) Assert.AreEqual(src[i - d], o[i], "sample " + i);
            Assert.AreEqual(1f, lim.MinGain);
            Assert.AreEqual(0, lim.LimitedFrames);
        }

        [Test]
        public void OverTheCeiling_NoSampleLeavesAboveIt()
        {
            float ceiling = (float)Math.Pow(10, BusLimiter.CeilingDb / 20.0);
            // quiet bed with loud bursts (horn-like 400 Hz at +6 dBFS) and a single-sample spike
            var src = Sine(Block * 40, 0.3f, 90f);
            for (int f = Block * 10; f < Block * 14; f++)
                for (int c = 0; c < Ch; c++) src[f * Ch + c] += 1.7f * (float)Math.Sin(2 * Math.PI * 400 * f / Rate);
            src[Block * 25 * Ch] = 3f;
            var lim = new BusLimiter();
            var o = Run(lim, src);
            float max = 0f;
            foreach (float v in o) max = Math.Max(max, Math.Abs(v));
            Assert.LessOrEqual(max, ceiling * 1.0001f);
            Assert.Less(lim.MinGain, 0.6f, "the bursts were limited");
        }

        [Test]
        public void GainCurve_HasNoStep()
        {
            // DC 0.5 (under the ceiling), then DC 2.0. While the loud part is in the look-ahead window the output is still
            // the quiet part times the falling gain: that gain must ramp (box average over the window), not jump.
            const int L = BusLimiter.LookaheadFrames;
            int frames = Block * 8, onset = frames / 2;
            var src = new float[frames * Ch];
            for (int f = 0; f < frames; f++) for (int c = 0; c < Ch; c++) src[f * Ch + c] = f < onset ? 0.5f : 2f;
            var o = Run(new BusLimiter(), src);
            float ceiling = (float)Math.Pow(10, BusLimiter.CeilingDb / 20.0);
            float full = 0.5f * (1f - ceiling / 2f);   // total fall of the quiet output during the attack
            float maxStep = 0f;
            for (int f = onset; f < onset + L - 1; f++) maxStep = Math.Max(maxStep, Math.Abs(o[f * Ch] - o[(f - 1) * Ch]));
            Assert.Less(maxStep, full / L * 1.05f, "attack spread over the look-ahead window");
            Assert.LessOrEqual(o[(onset + L - 1) * Ch], ceiling + 1e-4f, "the first loud frame leaves at the ceiling");
            Assert.AreEqual(ceiling, o[(frames - 1) * Ch], 1e-4f, "settles on the ceiling");
        }

        [Test]
        public void ChannelCountChange_ResetsWithoutThrowing()
        {
            var lim = new BusLimiter();
            lim.Process(Sine(Block, 0.2f, 100f), 2, Rate);
            lim.Process(Sine(Block, 0.2f, 100f, 6), 6, Rate);
            lim.Process(new float[16], 9, Rate);   // more than MaxChannels: ignored
            lim.Process(null, 2, Rate);
            Assert.Pass();
        }
    }
}
