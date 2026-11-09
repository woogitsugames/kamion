using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// 1€ filter (Casiez, Roussel, Vogel, "1€ Filter: A Simple Speed-based Low-pass Filter for Noisy Input in
    /// Interactive Systems", CHI 2012): a first-order low-pass whose cutoff rises with the signal's speed, so slow
    /// motion is smoothed (jitter) and fast motion has little lag. Allocation-free.
    /// </summary>
    public sealed class OneEuroFilter
    {
        /// <summary>Minimum cutoff [Hz] (jitter at rest).</summary>
        public float MinCutoff;
        /// <summary>Speed coefficient (lag during fast motion), units: Hz per (signal unit / s).</summary>
        public float Beta;
        /// <summary>Cutoff for the derivative estimate [Hz].</summary>
        public float DerivativeCutoff;

        float m_X, m_Dx;
        bool m_Has;

        public OneEuroFilter(float minCutoff = 1f, float beta = 0.02f, float derivativeCutoff = 1f)
        {
            MinCutoff = minCutoff; Beta = beta; DerivativeCutoff = derivativeCutoff;
        }

        public void Reset() { m_Has = false; m_X = 0; m_Dx = 0; }

        public float Value => m_X;

        public float Filter(float x, float dt)
        {
            if (!m_Has || dt <= 0f)
            {
                if (!m_Has) { m_X = x; m_Dx = 0f; m_Has = true; }
                return m_X;
            }
            float dx = (x - m_X) / dt;
            m_Dx = Mathf.Lerp(m_Dx, dx, Alpha(dt, DerivativeCutoff));
            float cutoff = MinCutoff + Beta * Mathf.Abs(m_Dx);
            m_X = Mathf.Lerp(m_X, x, Alpha(dt, cutoff));
            return m_X;
        }

        static float Alpha(float dt, float cutoff)
        {
            float tau = 1f / (2f * Mathf.PI * Mathf.Max(cutoff, 1e-4f));
            return 1f / (1f + tau / dt);
        }
    }
}
