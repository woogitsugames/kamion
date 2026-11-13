#ifndef KAMION_LAMP_LENS_INCLUDED
#define KAMION_LAMP_LENS_INCLUDED
// ADR 0181: procedural lamp-lens optics for the Lights slot of Kamion/Truck Exterior (tractor + trailer).
// The export writes a lens-local frame into uv1 (the 'Decal' channel, unused outside the Paint slot; TexCoord1 is not
// in the player's vertex compression mask, so it stays float32 on the phone):
//     uv1.x = W_mm + u',  uv1.y = style * 256 + H_mm + v',   u', v' = 0.02 + 0.96 * (0..1 across the lens)
// W / H = lens size in whole millimetres, constant over the lens (survives interpolation and LOD decimation);
// floor(uv1.x) == 0 -> not a lens (plain emission as before). Styles = a6_export.LENS_STYLES:
//   1 PILLOW  multi-LED chamber behind pillow optics (indicator / tail / stop): emitters on a ~30 mm grid, 3.5 mm pillows
//   2 FLUTE   marker lamp: a row of emitters along the long axis behind 2.2 mm flutes
//   3 FRESNEL reverse / rear fog: one emitter cluster behind 3 mm Fresnel rings
//   4 REFLEX  retro-reflector: 3 mm corner-cube array (surface only, never emits)
//   5 PLATE   number plate lit by the plate lamp above it (emission = albedo x lamp x falloff, see the shader)
// Outputs are in two domains on purpose. `hdr` scales the exposed lamp radiance BEFORE the ADR 0178 hue limit: the
// space between emitters is ~5 % of the emitter luminance, so by day a lit lamp is a set of points, as on a photo.
// At dusk the whole chamber is far above the display range and the limiter flattens it; `disp` is applied AFTER the
// limit and keeps a 2:1 emitter / surround contrast there (what a camera keeps of an over-exposed LED lamp).
// Every feature fades to its mean once it is smaller than a pixel (fwidth of the millimetre coordinate), so a lamp at
// distance is a steady patch, not shimmer. All sizes WORKING_VALUE (generic LED lamp, no manufacturer's part).
struct KamionLens
{
    half style;     // 0 = none
    half shade;     // albedo multiplier (gasket, optics relief, emitter cups)
    half2 slope;    // tangent-space normal offset of the optics relief
    half hdr;       // emission scale before the hue limit
    half disp;      // emission scale after the hue limit
    half plate;     // PLATE: illumination falloff 0..1
};

// Review s20 P1-1: full contrast only from >= 4 px per period, zero at <= 2 px (Nyquist); the old 2 - 3 fw / p kept full
// contrast down to 3 px and ~50 % at 2 px (pixel chequerboard on High at 2 m, moire on Low).
half KamionLensFade(float fw, float pitch) { return (half)saturate(pitch / (2.0 * fw) - 1.0); }

// Review s20 P1-2: the lens chambers of a combination lamp are adjacent texels in one atlas island; on the Low atlas
// (1/4 of High) bilinear filtering pulled the neighbouring chamber's colour into the chamber (red wedge in the amber
// chamber, beige patch in the reverse lamp). The lens frame (uv1) and uv0 are both affine over a planar lens, so the
// Jacobian d(uv0)/d(q) follows from screen derivatives: the atlas lookup is clamped to the chamber, inset by 1.5 texels
// of the sampled mip. Not for the plate (its text must stay where it is) and not where q jumps (2x2 quad on a lens edge).
float2 KamionLensInsetUV(float2 uv0, float2 uv1, float2 texSize)
{
    float W = floor(uv1.x);
    if (W < 0.5 || floor(uv1.y) >= 5.0 * 256.0) return uv0;
    float2 q = (frac(uv1) - 0.02) / 0.96;
    float2 dqx = ddx(q), dqy = ddy(q);
    if (max(max(abs(dqx.x), abs(dqx.y)), max(abs(dqy.x), abs(dqy.y))) > 0.25) return uv0;
    float det = dqx.x * dqy.y - dqx.y * dqy.x;
    if (abs(det) < 1e-10) return uv0;
    float2 dux = ddx(uv0), duy = ddy(uv0);
    float2 ju = (dux * dqy.y - duy * dqx.y) / det;     // d uv0 / d q.x
    float2 jv = (duy * dqx.x - dux * dqy.x) / det;     // d uv0 / d q.y
    float foot = max(max(length(dux * texSize), length(duy * texSize)), 1.0);   // texels per pixel (mip footprint)
    float2 m = min(1.5 * foot / max(float2(length(ju * texSize), length(jv * texSize)), 1e-3), 0.45);
    float2 qc = clamp(q, m, 1.0 - m);
    return uv0 + ju * (qc.x - q.x) + jv * (qc.y - q.y);
}

KamionLens KamionLensEval(float2 uv1)
{
    KamionLens L;
    L.style = 0; L.shade = 1; L.slope = 0; L.hdr = 1; L.disp = 1; L.plate = 0;
    float W = floor(uv1.x);
    if (W < 0.5) return L;
    float yi = floor(uv1.y);
    float style = floor(yi / 256.0);
    float H = yi - style * 256.0;
    float2 size = float2(W, max(H, 1.0));
    float2 q = saturate((frac(uv1) - 0.02) / 0.96);
    float2 hs = 0.5 * size;
    float2 p = (q - 0.5) * size;                       // millimetres from the lens centre
    float fw = max(length(float2(fwidth(p.x), fwidth(p.y))), 1e-4);   // pixel footprint in millimetres (skew-safe)
    float S = min(hs.x, hs.y);
    L.style = (half)style;

    if (style > 4.5)
    {
        // Plate lamp = a strip over the top edge covering ~44 % of the plate width, 15 mm above it. WORKING_VALUE:
        // soft inverse-square-like falloff, top centre : far bottom corner ~ 4.7 : 1.
        float x = max(abs(p.x) - 0.22 * W, 0.0);
        float y = hs.y - p.y + 15.0;
        L.plate = (half)(1.0 / (1.0 + (x * x + y * y) / (100.0 * 100.0)));
        return L;
    }

    // Chamber gasket / partition wall: the outer 3 mm of a lens neither transmits nor shows the optics.
    float edge = min(hs.x - abs(p.x), hs.y - abs(p.y));
    float bw = min(3.0, 0.3 * S);
    half fB = KamionLensFade(fw, 2.0 * bw);
    half border = lerp(1.0, (half)smoothstep(-0.5 * fw, bw + 0.5 * fw, edge), fB);   // edge widened by the footprint

    if (style > 3.5)
    {
        // Corner-cube array: offset rows of 3 x 2.6 mm cells, each with three facets of different brightness.
        float2 g = float2(p.x / 3.0 + 0.5 * floor(p.y / 2.6), p.y / 2.6);
        float2 m = frac(g) - 0.5;
        half f = KamionLensFade(fw, 2.6);
        half cube = 1.0 - 2.0 * (half)max(abs(m.x), abs(m.y));
        half facet = 0.82 + 0.24 * (half)step(0.0, m.x) + 0.12 * (half)step(0.0, m.y);
        L.shade = lerp(1.0, (0.60 + 0.55 * cube) * facet, f) * lerp(0.45, 1.0, border);
        L.slope = (half2)m * (0.5 * f);
        L.hdr = 0; L.disp = 0;
        return L;
    }

    half s, far;
    if (style > 2.5)
    {
        // Fresnel: emitter cluster on the axis, 3 mm rings.
        float r = length(p);
        // Triangle wave, not the true sawtooth: the sawtooth's step is a harmonic series that stepped into concentric moire
        // even when the 3 mm period itself was resolved (review s20 P1-1).
        half ring = (half)(1.0 - abs(2.0 * frac(r / 3.0) - 1.0));
        half fR = KamionLensFade(fw, 3.0);
        half fH = KamionLensFade(fw, S);
        float sig = 0.30 * S;
        half hot = (half)exp(-r * r / (2.0 * sig * sig));
        s = lerp(0.26, 0.14 + 0.86 * hot, fH) * lerp(1.0, 0.65 + 0.60 * ring, fR);
        L.slope = (half2)(p / max(r, 1e-3)) * ((ring - 0.5) * 0.25 * fR);
        // Centre boss of the Fresnel lens fades with the rings (review s20 P1-2: a bright dot stayed after the rings were gone).
        L.shade = 0.85 * lerp(1.0, 0.78 + 0.38 * ring, fR) * (1.0 + 0.35 * fR * (half)exp(-r * r / (2.0 * 2.5 * 2.5)));
        far = 1.0 - fH;
    }
    else if (style > 1.5)
    {
        // Flutes across the long axis, emitters in a row along it.
        bool wide = W >= H;
        float la = wide ? p.x : p.y, lb = wide ? p.y : p.x;
        float len = max(W, H);
        float n = max(round(len / 24.0), 1.0);
        float cl = len / n;
        float c = (frac(la / cl + 0.5 * n) - 0.5) * cl;
        float sig = clamp(0.6 * S, 2.0, 5.0);
        half led = (half)exp(-(c * c + lb * lb) / (2.0 * sig * sig));
        half fL = KamionLensFade(fw, min(cl, 4.0 * sig));
        float t = frac(la / 2.2) - 0.5;
        half fl = (half)(1.0 - 4.0 * t * t);
        half fF = KamionLensFade(fw, 2.2);
        s = lerp(0.30, 0.12 + 0.88 * led, fL) * lerp(1.0, 0.70 + 0.45 * fl, fF);
        half2 axis = wide ? half2(1, 0) : half2(0, 1);
        L.slope = axis * (half)(-8.0 * t * 0.07) * fF;
        half fD = KamionLensFade(fw, 6.0);              // the 1.5 mm die needs ~4 px of its own
        L.shade = lerp(1.0, 0.80 + 0.30 * fl, fF) * (1.0 + 0.4 * fL * fD * (half)exp(-(c * c + lb * lb) / (2.0 * 1.5 * 1.5)));
        far = 1.0 - fL;
    }
    else
    {
        // Pillow optics over an emitter grid: cells ~30 mm, one LED in a round reflector cup per cell.
        float2 n = max(round(size / 30.0), 1.0);
        float2 cs = size / n;
        float2 c = (frac(q * n) - 0.5) * cs;
        float r = length(c);
        float rc = 0.46 * min(cs.x, cs.y);                       // cup radius
        half fD = KamionLensFade(fw, 6.4);                       // the 1.6 mm die needs ~4 px of its own
        half led = (half)(0.75 * exp(-r * r / (2.0 * 4.5 * 4.5)) + 0.25 * fD * exp(-r * r / (2.0 * 1.6 * 1.6)));
        half fL = KamionLensFade(fw, min(cs.x, cs.y));
        // Cup rim widened by the pixel footprint: a sharper rim than a pixel stepped into lumpy 'egg' cups on Low.
        half cup = 1.0 - (half)smoothstep(rc - 1.5 - fw, rc + 1.0 + fw, r);  // 1 inside the cup, 0 on the carrier
        half dish = (half)saturate(1.0 - r / rc);                  // 0 rim .. 1 emitter
        float2 m = frac(p / 3.5) - 0.5;
        float2 pm = 1.0 - 4.0 * m * m;
        half pil = (half)(pm.x * pm.y);
        half fP = KamionLensFade(fw, 3.5);
        s = lerp(0.24, (0.10 + 0.90 * led) * lerp(0.75, 1.0, cup), fL) * lerp(1.0, 0.72 + 0.50 * pil, fP);
        L.slope = (half2)(-8.0 * m * pm.yx) * (0.06 * fP);
        // Unlit: metallised cups read lighter towards the rim (they mirror the sky), the carrier darker, the die a dot.
        L.shade = lerp(1.0, 0.80 + 0.36 * pil, fP) * lerp(1.0, lerp(0.80, 1.08 - 0.16 * dish, cup), fL)
                * (1.0 + 0.5 * fL * fD * (half)exp(-r * r / (2.0 * 1.6 * 1.6)));
        far = 1.0 - fL;
    }
    s = saturate(s);
    L.hdr = lerp(0.05, 1.0, s) * lerp(0.15, 1.0, border);
    // Far away (structure below a pixel) the lamp reads as one patch near the emitter level, not the surround level.
    L.disp = lerp(lerp(0.50, 1.0, s), 0.85, far) * lerp(0.40, 1.0, border);
    L.shade *= lerp(0.40, 1.0, border);
    return L;
}
#endif
