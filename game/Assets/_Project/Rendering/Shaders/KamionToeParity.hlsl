// Display parity of the cab view on the tiers without post-processing (ADR 0044 addendum r7).
// High / Ultra map the scene through the D23 master curve (LookGrading: black floor 1.5 %, toe 0.0025 -> 3.8 %,
// 0.01 -> 11.5 %); Low has no LUT and writes plain sRGB (0 -> 0 %, 0.0025 -> 3.2 %, 0.01 -> 10 %), so the same lower dash
// read 9 % "black < 3 %" on Low and 2 % on High at dusk (High with post off: 9.5 %). Here the cab surfaces write the
// linear value whose plain sRGB equals the D23 display: c' = c (1 + a k / (c + k)) + f k2 / (c + k2), per channel like the
// LUT. Fit to LookGrading (black 0.015, clip 0.7): <= 0.45 display points for c <= 0.2 (EditMode CabToeParityTests).
// _KamionToeParity = 0 (identity) outside the cab view and on the post-processing tiers (CabInteriorLighting).
#ifndef KAMION_TOE_PARITY_INCLUDED
#define KAMION_TOE_PARITY_INCLUDED

float4 _KamionToeParity;   // a, k, f, k2

half3 KamionToeParity(half3 c)
{
    float4 p = _KamionToeParity;
    if (p.y <= 0.0) return c;
    float3 x = max((float3)c, 0.0);
    return (half3)(x * (1.0 + p.x * p.y / (x + p.y)) + p.z * p.w / (x + p.w));
}

// ADR 0080 addendum (owner variant 3): the world contrast toe c' = g c (c + (1 - s) p) / (c + p) (LUT on the post tiers,
// KamionTone on Low) pulled the cab interior close to black (toe gain -> g (1 - s) = 0.16 near 0). In the cab view the
// interior keeps its ADR 0044 display (a phone lifts a backlit interior locally): the cab surfaces write the toe's
// pre-image, blended by w. Closed form of the inverse (quadratic in c). Zero vector = identity (outside the cab view,
// presets without a toe).
float4 _KamionCabToeInv;          // s, p, g, strength - Kamion/Cab Interior (every tier: LUT or KamionTone follows)
float4 _KamionCabToeInvDisplay;   // same for Kamion/Cab Display (post tiers only: no KamionTone in that shader)

half3 KamionCabToeInverse(half3 c, float4 t)
{
    if (t.x <= 0.0 || t.w <= 0.0) return c;
    float3 y = max((float3)c, 0.0);
    float3 b = y - t.z * (1.0 - t.x) * t.y;
    float3 inv = (b + sqrt(b * b + 4.0 * t.z * t.y * y)) / (2.0 * t.z);
    return (half3)lerp(y, inv, t.w);
}

#endif
