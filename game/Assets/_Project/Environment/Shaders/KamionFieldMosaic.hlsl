// ADR 0298 (knyszyn-p2-s24, review 2026-11-18 N1/N3): the farmland mosaic is computed per pixel from the EPSG:2180
// position, not baked into the terrain vertex colours.
//
// Why. ADR 0295 wrote one dryness level per field into COLOR_0.b at the 1 m mask grid, but the High terrain band keeps
// 1 m vertices only near the roads (8 m elsewhere) and the Low terrain is 2 m: the 2 m baulks vanished and the strips
// read as "faint diagonal smudges" (review N3); the apron outside the tile (WorldEdgeBuilder, 30-600 m rings) could not
// carry the mosaic at all, so every tile edge showed a hard seam (review N1). A pure function of the map position gives
// the same field on both sides of any seam - neighbouring tile, apron or far ring - at full pixel resolution.
//
// Contract. Terrain COLOR_0.b >= ~0.86 flags farmland (BDOT10k OT_PTTR_A; tools/worldgen/streetscape/vegetation.py):
// 0.90 grassland ("roślinność trawiasta"), 1.00 arable ("uprawa na gruntach ornych"); every other ground keeps B <= 0.80.
// The apron flags arable land beyond the tile. Object space = region-local E/N (world chunk meshes, apron);
// _RegionOriginEN.xy = EPSG:2180 of the region origin (set per region material at import), z = 1 enables.
// Season: the world is summer (owner D68: light of ~15 August). Mid-August in Podlasie: cereals harvested (straw
// stubble), some fields disked brown, maize / potatoes / catch crops green, meadows green after the second cut, a few
// freshly mown or uncut hay strips. Shares and tints WORKING_VALUE, judged against owner drone photos 10/11 (May) and the
// GUGiK orthophoto 2025-05-27 for the strip layout only (no pixel of either reaches the game).
#ifndef KAMION_FIELD_MOSAIC_INCLUDED
#define KAMION_FIELD_MOSAIC_INCLUDED

#define KF_BLOCK_M 300.0
#define KF_STRIP_MIN_M 22.0
#define KF_STRIP_SPAN_M 24.0
#define KF_TRAM_M 18.0          // WORKING_VALUE: tramline spacing (sprayer boom 18 m), two wheel tracks 1.8 m apart
#define KF_OWN_SHARE 0.2

uint KFHash(int a, int b, uint salt)
{
    uint h = ((uint)a * 1597334677u) ^ ((uint)b * 3812015801u) ^ salt;
    h ^= h >> 16;
    h *= 2246822519u;
    h ^= h >> 13;
    return h;
}

float KFU01(uint h) { return (float)(h & 0xFFFFFFu) * (1.0 / 16777215.0); }

// use -> (dryness B, soil A, tint rgb, tramlines 0/1)
void KFUse(float r, bool arable, out half b, out half a, out half3 tint, out half tram)
{
    tram = 0.0h; a = 0.0h;
    if (arable)
    {
        if (r < 0.26)      { b = 0.70h; a = 0.06h; tint = half3(1.10h, 0.98h, 0.74h); tram = 1.0h; }  // cereal stubble, straw
        else if (r < 0.36) { b = 0.42h; a = 0.86h; tint = half3(1.00h, 0.98h, 0.96h); }                // disked / ploughed
        else if (r < 0.52) { b = 0.02h; a = 0.08h; tint = half3(0.74h, 0.96h, 0.62h); }                // maize
        else if (r < 0.62) { b = 0.10h; a = 0.18h; tint = half3(0.84h, 1.00h, 0.70h); }                // potatoes / beet
        else if (r < 0.76) { b = 0.18h; a = 0.26h; tint = half3(0.90h, 1.02h, 0.78h); tram = 1.0h; }  // catch crop on stubble
        else if (r < 0.88) { b = 0.05h; a = 0.0h;  tint = half3(0.84h, 1.06h, 0.76h); }                // clover / young rape
        else               { b = 0.12h; a = 0.0h;  tint = half3(0.90h, 1.05h, 0.80h); }                // grass ley
    }
    else
    {
        if (r < 0.45)      { b = 0.06h; tint = half3(0.88h, 1.06h, 0.78h); }   // meadow, regrowth after the 2nd cut
        else if (r < 0.70) { b = 0.14h; tint = half3(0.93h, 1.04h, 0.82h); }   // pasture
        else if (r < 0.85) { b = 0.38h; tint = half3(1.02h, 1.04h, 0.86h); }   // freshly mown
        else               { b = 0.60h; tint = half3(1.04h, 1.00h, 0.82h); }   // uncut hay
    }
}

// en: EPSG:2180 metres; footprint: metres per pixel; driftN: 0..1 low-frequency noise (macro map, no extra fetch).
// m: terrain masks (in/out). tint: albedo multiplier to apply after the ground-mask colouring.
void KamionFieldMosaic(float2 en, float footprint, half driftN, inout half4 m, out half3 tint)
{
    tint = half3(1.0h, 1.0h, 1.0h);
    half farm = smoothstep(0.84h, 0.88h, m.b);
    if (farm <= 0.0h) return;
    bool arable = m.b > 0.95h;

    // block of parallel strips: nearest jittered seed of the 300 m lattice, distance to the block border (bisector)
    float2 c = floor(en / KF_BLOCK_M);
    float d1 = 1e20, d2 = 1e20;
    float2 s1 = 0, s2 = 0;
    int2 b1 = 0;
    [unroll] for (int dj = -1; dj <= 1; dj++)
    [unroll] for (int di = -1; di <= 1; di++)
    {
        int2 ij = int2(c) + int2(di, dj);
        float2 s = (float2(ij) + 0.15 + 0.7 * float2(KFU01(KFHash(ij.x, ij.y, 911u)), KFU01(KFHash(ij.x, ij.y, 913u)))) * KF_BLOCK_M;
        float2 v = en - s;
        float dd = dot(v, v);
        if (dd < d1) { d2 = d1; s2 = s1; d1 = dd; s1 = s; b1 = ij; }
        else if (dd < d2) { d2 = dd; s2 = s; }
    }
    float blockEdge = (d2 - d1) / max(2.0 * length(s2 - s1), 1e-3);
    float th = PI * KFU01(KFHash(b1.x, b1.y, 917u));
    float w = KF_STRIP_MIN_M + KF_STRIP_SPAN_M * KFU01(KFHash(b1.x, b1.y, 919u));
    float2 dir = float2(cos(th), sin(th));
    float t = dot(en - s1, dir) / w;              // across the strips, relative to the seed (fp32-safe)
    float k = floor(t);
    float across = (t - k) * w;                   // metres from the strip's lower edge
    float stripEdge = min(across, w - across);
    uint bid = KFHash(b1.x, b1.y, 923u);
    uint fid = KFHash((int)bid, (int)k, 929u);
    bool own = KFU01(KFHash((int)fid, 0, 931u)) < KF_OWN_SHARE;
    float r = own ? KFU01(KFHash((int)fid, 0, 937u)) : KFU01(KFHash((int)bid, 0, 939u));
    // a strip of a block differs a little from its neighbours (same use, own tone)
    half dev = (half)(KFU01(KFHash((int)fid, 0, 943u)) - 0.5);

    half fb, fa, tram; half3 ft;
    KFUse(r, arable, fb, fa, ft, tram);
    fb = saturate(fb + dev * 0.06h + (driftN - 0.5h) * 0.06h);
    ft *= 1.0h + dev * 0.06h;

    float fp = max(footprint, 1e-3);
    // tramlines: two wheel tracks 1.8 m apart every 18 m, parallel to the strip, 0.4 m wide; faded once sub-pixel
    if (tram > 0.0h)
    {
        float q = frac((across - 0.5 * KF_TRAM_M) / KF_TRAM_M) * KF_TRAM_M;
        float dc = min(q, KF_TRAM_M - q);
        float dt = abs(dc - 0.9);
        half track = (half)(saturate((0.2 - dt) / fp + 0.5) * saturate(0.6 / fp));
        fa = lerp(fa, 0.55h, track * 0.8h);
        fb = lerp(fb, 0.30h, track * 0.5h);
    }
    // baulk (miedza): rough grass line 2 m wide between two fields, box-filtered by the pixel footprint
    float e = min(stripEdge, blockEdge);
    half baulk = (half)(saturate((1.0 - e) / fp + 0.5) * saturate(2.0 / fp + 0.25));
    fb = lerp(fb, 0.56h, baulk);
    fa = lerp(fa, 0.0h, baulk);
    ft = lerp(ft, half3(0.98h, 1.03h, 0.84h), baulk);

    m.b = lerp(m.b, fb, farm);
    m.a = lerp(m.a, fa, farm);
    tint = lerp(half3(1.0h, 1.0h, 1.0h), ft, farm);
}

#endif
