using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// Worn touch points of the cab interior (ADR 0044 addendum r8): C# mirror of the wear branch of CabInterior.shader
    /// (keep both in sync; EditMode CabInteriorWearTests evaluates this on the exported rim data) and the per-slot material
    /// values TruckAssetBuilder writes.
    /// Black leather / PU and black plastic do not get paler paint where hands rub them: the pigmented finish is burnished
    /// (smoother, a satin sheen instead of the grain's matt) and thinned, so the spot goes slightly lighter and greyer,
    /// i.e. towards a neutral grey, never towards the sun colour (review r6 C-N5: the old x2.7 lift on the warm tint read
    /// beige at low sun). WORKING_VALUE: no measured albedo of worn black automotive leather in the repo; 0.085 linear
    /// (sRGB 81) is a worn, not worn-through, black finish (new black leather 0.02-0.04, review r7 N-11), inside the docs/06
    /// corridor. Upper bound from D33: 0.15 put the sunlit rim at R-B 6.0-6.9 % at low sun (ADR 0044 r8).
    /// </summary>
    public static class CabWearModel
    {
        /// <summary>Linear albedo a fully worn black part (mean tint below ~0.1) goes to, neutral grey (x detail variation).</summary>
        public const float WornBlackAlbedo = 0.085f;
        /// <summary>Roughness floor of a worn spot, per slot: hand-polished leather is glossy but not lacquer (0.08); a
        /// thumb-polished ABS knob or key may go to 0.08. 0.30 (satin) was measured weaker (ADR 0044 r8).</summary>
        public const float WornRoughMinLeather = 0.12f;
        public const float WornRoughMinOther = 0.08f;

        public static float RoughMinFor(string slot) => slot == "Leather" ? WornRoughMinLeather : WornRoughMinOther;

        /// <summary>Shaped wear (shader wk). detR = detail R (variation), mixD = 1 when the slot has detail.</summary>
        public static float Shape(float wear, float detR, float mixD) =>
            Mathf.Clamp01(wear * 2.4f * (0.55f + 0.9f * detR * mixD + 0.45f * (1f - mixD)));

        /// <summary>Albedo (linear) before the deep-AO darkening. tint = linear vertex tint, base = tint x detail.</summary>
        public static Vector3 Albedo(Vector3 tint, Vector3 baseCol, float wear, float wk, float detR, float mixD)
        {
            Vector3 worn = baseCol * (1f + 1.5f * wear + 1.3f * wk);
            float dark = 1f - Mathf.Clamp01((tint.x + tint.y + tint.z) / 3f * 8f);
            float mean = (baseCol.x + baseCol.y + baseCol.z) / 3f;
            float target = Mathf.Max(mean, WornBlackAlbedo * (0.85f + 0.3f * (detR * mixD + 0.5f * (1f - mixD))));
            Vector3 wornDark = Vector3.Lerp(baseCol, new Vector3(target, target, target), wk);
            return Vector3.Lerp(worn, wornDark, dark);
        }

        public static float Roughness(float baseRough, float detB, float mixD, float wear, float wk, float roughMin)
        {
            float r = baseRough + (detB - 0.5f) * 0.6f * mixD;
            float worn = Mathf.Max(r - 0.25f * wear - 0.3f * wk, roughMin);
            return Mathf.Clamp(Mathf.Min(r, worn), 0.08f, 1f);
        }
    }
}
