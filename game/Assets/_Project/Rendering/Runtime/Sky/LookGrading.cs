using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// The D23 "phone photo" tone curve (ADR 0016), applied through the URP HDR grading LUT with tonemapping None:
    /// a master curve (ColorCurves, evaluated by LutBuilderHdr in FastTonemap space u = x / (1 + x)) maps the exposed
    /// scene value to the display value directly. It replaces Neutral + contrast + lift (ADR 0010, D23 v1), which
    /// gave a 21 % black and an 80-85 % white ceiling ("milk", review r3 G1).
    ///
    /// Shape (scene linear → display sRGB, WORKING_VALUE, judged against the CC0 phone photos of review r3 §0):
    /// black floor <c>black</c> (≤ 2 %, the "lift after tonemapping"), a toe close to plain sRGB (0.01 → 11.5 %), mid-grey
    /// 0.18 → 48.5 % (ADR 0010 calibration kept), bright highlights (0.5 → 79 %) and a hard clip at <c>whiteClip</c>
    /// (default 0.7): the overcast sky (≥ 0.7 above ~5° at the exposure table) and lit white paint reach 100 % like on a
    /// phone (review r3: the reference photos clip 2-20 % of the sky). Low (no post-processing) is the
    /// plain sRGB clip at 1.0 - the same mid-grey and toe, so the tiers stay close.
    /// </summary>
    public static class LookGrading
    {
        // Scene linear x → display sRGB. The first (black) and last (white clip) points come from the preset.
        static readonly float[] k_X = { 0f, 0.0025f, 0.01f, 0.03f, 0.09f, 0.18f, 0.33f, 0.5f };
        static readonly float[] k_S = { 0f, 0.038f, 0.115f, 0.21f, 0.355f, 0.485f, 0.62f, 0.79f };

        public static float LinearToSrgb(float x)
        {
            x = Mathf.Clamp01(x);
            return x <= 0.0031308f ? 12.92f * x : 1.055f * Mathf.Pow(x, 1f / 2.4f) - 0.055f;
        }

        public static float SrgbToLinear(float s) => s <= 0.04045f ? s / 12.92f : Mathf.Pow((s + 0.055f) / 1.055f, 2.4f);

        static float U(float x) => x / (1f + x);           // URP FastTonemap (grey)
        static float V(float y) => y / (1f + y);

        /// <summary>Master-curve keys (FastTonemap domain) with monotone (Fritsch-Carlson) tangents: no overshoot.</summary>
        public static Keyframe[] MasterCurveKeys(float blackSrgb, float whiteClip)
        {
            int n = k_X.Length + 2;
            var u = new float[n];
            var v = new float[n];
            for (int i = 0; i < k_X.Length; i++)
            {
                u[i] = U(k_X[i]);
                float s = i == 0 ? blackSrgb : Mathf.Max(k_S[i], blackSrgb);
                v[i] = V(SrgbToLinear(s));
            }
            float clip = Mathf.Max(whiteClip, k_X[k_X.Length - 1] + 0.05f);
            u[n - 2] = U(clip); v[n - 2] = V(1f);
            u[n - 1] = 1f; v[n - 1] = V(1f);
            var d = new float[n - 1];
            for (int i = 0; i < n - 1; i++) d[i] = (v[i + 1] - v[i]) / (u[i + 1] - u[i]);
            var m = new float[n];
            m[0] = d[0]; m[n - 1] = 0f;
            for (int i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0f ? 0f : (d[i - 1] + d[i]) * 0.5f;
            for (int i = 0; i < n - 1; i++)
            {
                if (d[i] == 0f) { m[i] = m[i + 1] = 0f; continue; }
                float a = m[i] / d[i], b = m[i + 1] / d[i], h = a * a + b * b;
                if (h > 9f) { float t = 3f / Mathf.Sqrt(h); m[i] = t * a * d[i]; m[i + 1] = t * b * d[i]; }
            }
            var keys = new Keyframe[n];
            for (int i = 0; i < n; i++) keys[i] = new Keyframe(u[i], v[i], m[i], m[i]);
            return keys;
        }

        // ---------------------------------------------------------------- contrast toe (ADR 0080)
        /// <summary>Gain that keeps <paramref name="pivot"/> fixed under the toe.</summary>
        public static float ToeGain(float s, float p, float pivot) => s <= 0f ? 1f : (pivot + p) / (pivot + (1f - s) * p);

        /// <summary>
        /// Contrast toe c' = g c (c + (1 - s) p) / (c + p): shadows scaled toward (1 - s) g, values far above p by g, the
        /// pivot unchanged. Monotone for s &lt; 1. The same function runs in KamionAtmosphere.hlsl on the tiers without
        /// post-processing; the post tiers compose it into the master curve (<see cref="MasterCurveKeys(float,float,float,float,float)"/>).
        /// </summary>
        public static float Toe(float c, float s, float p, float pivot)
        {
            c = Mathf.Max(c, 0f);
            return s <= 0f ? c : c * ToeGain(s, p, pivot) * (c + (1f - s) * p) / (c + p);
        }

        /// <summary>Scene value whose toe output is <paramref name="y"/> (bisection).</summary>
        public static float InverseToe(float y, float s, float p, float pivot)
        {
            if (s <= 0f) return y;
            float lo = 0f, hi = Mathf.Max(y, 1e-4f) * 2f + p;
            for (int i = 0; i < 48; i++)
            {
                float mid = 0.5f * (lo + hi);
                if (Toe(mid, s, p, pivot) < y) lo = mid; else hi = mid;
            }
            return 0.5f * (lo + hi);
        }

        static readonly float[] k_ToeX = { 0f, 0.0025f, 0.005f, 0.01f, 0.02f, 0.03f, 0.045f, 0.065f, 0.09f, 0.12f, 0.15f, 0.18f, 0.22f, 0.27f, 0.33f, 0.4f, 0.5f };

        /// <summary>The D23 master curve of the scene value after the contrast toe: display = D23(Toe(x)). s = 0 returns
        /// the plain D23 keys.</summary>
        public static Keyframe[] MasterCurveKeys(float blackSrgb, float whiteClip, float toe, float toeP, float pivot)
        {
            if (toe <= 0f) return MasterCurveKeys(blackSrgb, whiteClip);
            var d23 = new AnimationCurve(MasterCurveKeys(blackSrgb, whiteClip));
            float clip = Mathf.Max(whiteClip, k_X[k_X.Length - 1] + 0.05f);
            float xClip = InverseToe(clip, toe, toeP, pivot);
            var us = new System.Collections.Generic.List<float>();
            var vs = new System.Collections.Generic.List<float>();
            foreach (float x in k_ToeX)
            {
                if (x >= xClip * 0.97f) break;
                us.Add(U(x));
                vs.Add(d23.Evaluate(U(Toe(x, toe, toeP, pivot))));
            }
            us.Add(U(xClip)); vs.Add(V(1f));
            us.Add(1f); vs.Add(V(1f));
            return Monotone(us.ToArray(), vs.ToArray());
        }

        static Keyframe[] Monotone(float[] u, float[] v)
        {
            int n = u.Length;
            var d = new float[n - 1];
            for (int i = 0; i < n - 1; i++) d[i] = (v[i + 1] - v[i]) / (u[i + 1] - u[i]);
            var m = new float[n];
            m[0] = d[0]; m[n - 1] = 0f;
            for (int i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0f ? 0f : (d[i - 1] + d[i]) * 0.5f;
            for (int i = 0; i < n - 1; i++)
            {
                if (d[i] == 0f) { m[i] = m[i + 1] = 0f; continue; }
                float a = m[i] / d[i], b = m[i + 1] / d[i], h = a * a + b * b;
                if (h > 9f) { float t = 3f / Mathf.Sqrt(h); m[i] = t * a * d[i]; m[i + 1] = t * b * d[i]; }
            }
            var keys = new Keyframe[n];
            for (int i = 0; i < n; i++) keys[i] = new Keyframe(u[i], v[i], m[i], m[i]);
            return keys;
        }

        /// <summary>Display sRGB of an exposed scene value through the master curve (grey; what the LUT does).</summary>
        public static float Display(AnimationCurve master, float x)
        {
            float v = Mathf.Clamp(master.Evaluate(U(Mathf.Max(x, 0f))), 0f, 0.999f);
            return LinearToSrgb(v / (1f - v));
        }

        /// <summary>
        /// Cab-view display parity of the tiers without post-processing (KamionToeParity.hlsl, ADR 0044 addendum r7):
        /// (a, k, f, k2) of c' = c (1 + a k / (c + k)) + f k2 / (c + k2), the linear value whose plain sRGB equals the
        /// master curve's display of c (black 0.015, white clip 0.7, the values of every LP_* preset). Least-squares fit
        /// (relative error, 0..0.5): within 0.45 display points for c &lt;= 0.2 (CabToeParityTests).
        /// </summary>
        public static readonly Vector4 NoPostToeParity = new Vector4(0.21129f, 0.206849f, 0.001319f, 0.000598f);

        public static float ToeParity(Vector4 p, float c)
        {
            c = Mathf.Max(c, 0f);
            return c * (1f + p.x * p.y / (c + p.y)) + p.z * p.w / (c + p.w);
        }

        /// <summary>Lum-vs-saturation keys (0.5 = unchanged): desaturate towards white above ~0.6 of the clip.</summary>
        public static Keyframe[] HighlightDesaturationKeys(float amount, float whiteClip)
        {
            float a = Mathf.Clamp01(whiteClip * 0.45f), b = Mathf.Clamp(whiteClip * 0.75f, a + 0.05f, 1f);
            return new[] { new Keyframe(0f, 0.5f, 0f, 0f), new Keyframe(a, 0.5f, 0f, 0f), new Keyframe(b, 0.5f * (1f - amount), 0f, 0f) };
        }
    }
}
