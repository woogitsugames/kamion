// ADR 0298 (knyszyn-p2-s24, review 2026-11-18 N1/N3): the farmland mosaic is computed per pixel from the EPSG:2180
// position, not baked into the terrain vertex colours.
// ADR 0334 (fields-s24, critic build #5 pt 3 "pola i łąki to jedna zielona płaszczyzna"): the 0298 palette was an
// albedo MULTIPLIER on the green grass texture - a straw stubble tint of (1.16, 1.08, 0.80) x grass is still green, so
// every use read as one more shade of green. Now every strip has a USE (crop / stage) with its own linear albedo, which
// REPLACES the grass colour by a cover weight (the grass texture keeps its luminance detail), plus the structure that
// gives the use away from the cab: tramlines in standing cereal, straw windrows on stubble, hay windrows on a mown
// meadow, crop rows, disc stripes, weedy patches on fallow and pasture, headlands at the strip ends and baulks
// (miedze) 1-2.6 m wide between strips.
//
// Why per pixel. ADR 0295 wrote one dryness level per field into COLOR_0.b at the 1 m mask grid, but the High terrain
// band keeps 1 m vertices only near the roads (8 m elsewhere) and the Low terrain is 2 m: the 2 m baulks vanished and
// the strips read as "faint diagonal smudges"; the apron outside the tile could not carry the mosaic at all. A pure
// function of the map position gives the same field on both sides of any seam - neighbouring tile, apron or far ring.
//
// Contract. Terrain COLOR_0.b >= ~0.86 flags farmland (BDOT10k OT_PTTR_A; tools/worldgen/streetscape/vegetation.py):
// 0.90 grassland ("roślinność trawiasta"), 1.00 arable ("uprawa na gruntach ornych"); every other ground keeps B <= 0.80.
// local = region-local E/N (object space of the world chunk meshes and the apron); origin = EPSG:2180 of the region
// origin (_RegionOriginEN.xy, whole metres -> exact in fp32), so lattice positions are formed relative to the origin
// and the strip coordinate keeps cm precision 700 km from the CRS origin.
// Python mirror: vegetation.field_layout / field_use (props on baulks, samosiew on fallow) - keep the salts, lattice
// and use thresholds in step (tests/gis/test_fields_0334.py reads this file).
//
// Season (owner D68: summer everywhere, light of ~15 August). Late July / mid-August in Podlasie: the cereal harvest is
// under way (part standing ripe, part stubble with straw windrows or baled), rape harvested, maize and potatoes green,
// meadows between the 2nd and 3rd cut (regrowth, fresh windrows, hay drying, uncut), pastures, some fallow.
// Shares WORKING_VALUE (podlaskie: cereals ~55 % and fodder maize ~20 % of the arable land, rape and root crops small,
// GUS structure read as an order of magnitude, not a survey of these tiles); albedos WORKING_VALUE, linear, judged on
// the visual-qa renders against open-licence summer photos of Podlasie fields (artifacts/fields-s24/refs).
#ifndef KAMION_FIELD_MOSAIC_INCLUDED
#define KAMION_FIELD_MOSAIC_INCLUDED

#define KF_DISTRICT_M 1600.0  // WORKING_VALUE: area of one strip direction (a village's fields)
#define KF_STRETCH 3.0        // WORKING_VALUE: blocks 3x longer along the strips than across
#define KF_BLOCK_M 300.0
#define KF_BLOCK_HASH_OFS 4096  // block indices in the district frame are signed; hashed as index + this
#define KF_STRIP_MIN_M 16.0
#define KF_STRIP_SPAN_M 24.0
#define KF_TRAM_M 18.0          // WORKING_VALUE: tramline spacing (sprayer boom 18 m), two wheel tracks 1.8 m apart
#define KF_OWN_SHARE 0.55      // Podlasie strip farms: neighbouring strips are separate holdings (own crop)
#define KF_HEADLAND_M 9.0      // WORKING_VALUE: headland (uwrocie) at the strip end, ~ one sprayer pass
#define KF_BAULK_MIN_M 1.0     // WORKING_VALUE: baulk (miedza) width range, per strip edge
#define KF_BAULK_SPAN_M 1.6

// uses: arable 0..10, grassland 11..15 (vegetation.FIELD_USES)
#define KF_CEREAL_RIPE 0
#define KF_CEREAL_PALE 1
#define KF_STUBBLE 2
#define KF_STUBBLE_BALED 3
#define KF_RAPE_STUBBLE 4
#define KF_MAIZE 5
#define KF_ROOTS 6
#define KF_DISKED 7
#define KF_CATCH 8
#define KF_LEY 9
#define KF_FALLOW 10
#define KF_REGROWTH 11
#define KF_PASTURE 12
#define KF_MOWN 13
#define KF_HAY 14
#define KF_UNCUT 15

uint KFHash(int a, int b, uint salt)
{
    uint h = ((uint)a * 1597334677u) ^ ((uint)b * 3812015801u) ^ salt;
    h ^= h >> 16;
    h *= 2246822519u;
    h ^= h >> 13;
    return h;
}

float KFU01(uint h) { return (float)(h & 0xFFFFFFu) * (1.0 / 16777215.0); }

// r in 0..1 -> use (cumulative shares; vegetation.FIELD_USES)
int KFUse(float r, bool arable)
{
    if (arable)
    {
        if (r < 0.18) return KF_CEREAL_RIPE;
        if (r < 0.26) return KF_CEREAL_PALE;
        if (r < 0.44) return KF_STUBBLE;
        if (r < 0.50) return KF_STUBBLE_BALED;
        if (r < 0.54) return KF_RAPE_STUBBLE;
        if (r < 0.74) return KF_MAIZE;
        if (r < 0.78) return KF_ROOTS;
        if (r < 0.86) return KF_DISKED;
        if (r < 0.90) return KF_CATCH;
        if (r < 0.96) return KF_LEY;
        return KF_FALLOW;
    }
    if (r < 0.30) return KF_REGROWTH;
    if (r < 0.50) return KF_PASTURE;
    if (r < 0.62) return KF_MOWN;
    if (r < 0.72) return KF_HAY;
    return KF_UNCUT;
}

// use -> linear albedo (rgb) and cover weight over the grass (a); dryness for the ground rules (b)
void KFLook(int u, out half4 alb, out half b)
{
    b = 0.15h;
    switch (u)
    {
        case KF_CEREAL_RIPE:   alb = half4(0.330h, 0.240h, 0.095h, 0.92h); b = 0.20h; break;   // wheat / triticale, golden
        case KF_CEREAL_PALE:   alb = half4(0.290h, 0.262h, 0.130h, 0.92h); b = 0.20h; break;   // barley / rye / oats, pale
        case KF_STUBBLE:       alb = half4(0.285h, 0.228h, 0.125h, 0.92h); b = 0.25h; break;   // cereal stubble, straw left
        case KF_STUBBLE_BALED: alb = half4(0.250h, 0.212h, 0.135h, 0.92h); b = 0.25h; break;   // stubble, straw baled off
        case KF_RAPE_STUBBLE:  alb = half4(0.165h, 0.145h, 0.095h, 0.92h); b = 0.25h; break;   // rape stubble, grey-brown
        case KF_MAIZE:         alb = half4(0.036h, 0.078h, 0.020h, 0.88h); break;              // fodder maize, dark
        case KF_ROOTS:         alb = half4(0.050h, 0.096h, 0.026h, 0.88h); break;              // potatoes / beet
        case KF_DISKED:        alb = half4(0.150h, 0.112h, 0.072h, 0.95h); b = 0.30h; break;   // disked, light sandy soil
        case KF_CATCH:         alb = half4(0.085h, 0.150h, 0.034h, 0.80h); break;              // catch crop on stubble
        case KF_LEY:           alb = half4(0.068h, 0.132h, 0.030h, 0.70h); break;              // grass / clover ley
        case KF_FALLOW:        alb = half4(0.120h, 0.128h, 0.050h, 0.80h); b = 0.35h; break;   // fallow, weeds and seedlings
        case KF_REGROWTH:      alb = half4(0.070h, 0.140h, 0.030h, 0.65h); break;              // meadow regrowth after a cut
        case KF_PASTURE:       alb = half4(0.060h, 0.108h, 0.027h, 0.70h); break;              // pasture, grazed
        case KF_MOWN:          alb = half4(0.125h, 0.160h, 0.050h, 0.80h); b = 0.25h; break;   // freshly mown, windrows
        case KF_HAY:           alb = half4(0.190h, 0.178h, 0.078h, 0.85h); b = 0.35h; break;   // hay drying on the ground
        default:               alb = half4(0.112h, 0.126h, 0.052h, 0.75h); b = 0.30h; break;   // uncut, seed heads
    }
}

// periodic band of width bw (m) every period p (m) at coordinate x, box-filtered by the pixel footprint fp; 0 once
// the period shrinks below ~3 px (no moire towards the horizon)
half KFBand(float x, float p, float bw, float fp)
{
    float q = frac(x / p) * p;
    float d = min(q, p - q);
    return (half)(saturate((0.5 * bw - d) / fp + 0.5) * saturate(p / (3.0 * fp) - 0.5));
}

// value noise on a cell lattice, cell size s (m), lattice formed relative to the region origin (exact)
half KFNoise(float2 local, float2 origin, float s, uint salt)
{
    float2 ga = floor((local + origin) / s);
    float2 f = (local - (ga * s - origin)) / s;
    f = f * f * (3.0 - 2.0 * f);
    int2 g = int2(ga);
    half a = (half)KFU01(KFHash(g.x, g.y, salt)), bb = (half)KFU01(KFHash(g.x + 1, g.y, salt));
    half c = (half)KFU01(KFHash(g.x, g.y + 1, salt)), d = (half)KFU01(KFHash(g.x + 1, g.y + 1, salt));
    return lerp(lerp(a, bb, (half)f.x), lerp(c, d, (half)f.x), (half)f.y);
}

// local: region-local E/N (m); origin: EPSG:2180 of the region origin (whole metres); footprint: metres per pixel;
// driftN: 0..1 low-frequency noise (macro map). m: terrain masks (in/out). field: linear albedo of the field (rgb)
// and its cover weight over the grass (a), applied after the ground-mask colouring.
void KamionFieldMosaic(float2 local, float2 origin, float footprint, half driftN, inout half4 m, out half4 field)
{
    field = half4(0.0h, 0.0h, 0.0h, 0.0h);
    half farm = smoothstep(0.84h, 0.88h, m.b);
    if (farm <= 0.0h) return;
    bool arable = m.b > 0.95h;

    // ADR 0334 layout. District (KF_DISTRICT_M jittered lattice): one long-axis direction for all its strips (a Podlasie
    // village's strips run side by side, all the same way). Inside it, blocks are the Voronoi cells of a KF_BLOCK_M
    // lattice in a frame stretched KF_STRETCH times along that axis, so a block is ~3x longer than wide and holds a run
    // of narrow parallel strips (wąskie, podłużne działki). Every lattice point is formed relative to the origin /
    // district seed, so the strip coordinate keeps cm precision in fp32.
    float2 cD = floor((local + origin) / KF_DISTRICT_M);
    float e1 = 1e20, e2 = 1e20;
    float2 sD = 0, sD2 = 0;
    int2 dIJ = 0;
    [unroll] for (int dj0 = -1; dj0 <= 1; dj0++)
    [unroll] for (int di0 = -1; di0 <= 1; di0++)
    {
        int2 ij = int2(cD) + int2(di0, dj0);
        float2 s = float2(ij) * KF_DISTRICT_M - origin
                 + (0.15 + 0.7 * float2(KFU01(KFHash(ij.x, ij.y, 971u)), KFU01(KFHash(ij.x, ij.y, 973u)))) * KF_DISTRICT_M;
        float2 v = local - s;
        float dd = dot(v, v);
        if (dd < e1) { e2 = e1; sD2 = sD; e1 = dd; sD = s; dIJ = ij; }
        else if (dd < e2) { e2 = dd; sD2 = s; }
    }
    float districtEdge = (e2 - e1) / max(2.0 * length(sD2 - sD), 1e-3);
    uint dsalt = KFHash(dIJ.x, dIJ.y, 977u);
    float thD = PI * KFU01(KFHash(dIJ.x, dIJ.y, 975u));
    float2 aD = float2(cos(thD), sin(thD));       // long axis of the strips
    float2 nD = float2(-aD.y, aD.x);
    float2 r0 = local - sD;
    float2 q = float2(dot(r0, aD) / KF_STRETCH, dot(r0, nD));

    // block of parallel strips: nearest jittered seed of the KF_BLOCK_M lattice in the stretched frame, distance to the
    // block border measured in metres (the bisector of the affine Voronoi mapped back to the ground)
    float2 c = floor(q / KF_BLOCK_M);
    float d1 = 1e20, d2 = 1e20;
    float2 s1 = 0, s2 = 0;
    int2 b1 = 0;
    [unroll] for (int dj = -1; dj <= 1; dj++)
    [unroll] for (int di = -1; di <= 1; di++)
    {
        int2 ij = int2(c) + int2(di, dj);
        int2 hb = ij + KF_BLOCK_HASH_OFS;     // KFHash(i, j) == KFHash(-i, -j): keep the hashed indices positive
        float2 s = (float2(ij) + 0.15 + 0.7 * float2(KFU01(KFHash(hb.x, hb.y, 911u ^ dsalt)), KFU01(KFHash(hb.x, hb.y, 913u ^ dsalt)))) * KF_BLOCK_M;
        float2 v = q - s;
        float dd = dot(v, v);
        if (dd < d1) { d2 = d1; s2 = s1; d1 = dd; s1 = s; b1 = hb; }
        else if (dd < d2) { d2 = dd; s2 = s; }
    }
    float2 nq = (s2 - s1) / max(length(s2 - s1), 1e-3);
    float blockEdge = (d2 - d1) / max(2.0 * length(s2 - s1), 1e-3) / length(float2(nq.x / KF_STRETCH, nq.y));
    blockEdge = min(blockEdge, districtEdge);
    float th = thD + 0.5 * PI + (KFU01(KFHash(b1.x, b1.y, 917u ^ dsalt)) - 0.5) * 0.2;   // strip normal, +-5.7 deg per block
    float w = KF_STRIP_MIN_M + KF_STRIP_SPAN_M * KFU01(KFHash(b1.x, b1.y, 919u ^ dsalt));
    float2 dir = float2(cos(th), sin(th));
    float2 seed = sD + aD * (s1.x * KF_STRETCH) + nD * s1.y;
    float2 rel = local - seed;
    float t = dot(rel, dir) / w;                  // across the strips, relative to the block seed (fp32-safe)
    float along = dot(rel, float2(-dir.y, dir.x)); // along the strip (m)
    float k = floor(t);
    float across = (t - k) * w;                   // metres from the strip's lower edge
    uint bid = KFHash(b1.x, b1.y, 923u ^ dsalt);
    uint fid = KFHash((int)bid, (int)k, 929u);
    bool own = KFU01(KFHash((int)fid, 0, 931u)) < KF_OWN_SHARE;
    float r = own ? KFU01(KFHash((int)fid, 0, 937u)) : KFU01(KFHash((int)bid, 0, 939u));
    int u = KFUse(r, arable);
    // a strip of a block differs a little from its neighbours (same use, own tone)
    half dev = (half)(KFU01(KFHash((int)fid, 0, 943u)) - 0.5);

    half4 alb; half fb;
    KFLook(u, alb, fb);
    half3 col = alb.rgb * (1.0h + dev * 0.12h) * (1.0h + (driftN - 0.5h) * 0.16h);
    half fa = 0.0h;

    float fp = max(footprint, 1e-3);
    half n5 = KFNoise(local, origin, 5.0, 951u);
    half n17 = KFNoise(local, origin, 17.0, 953u);

    // ---- structure of the use (all bands parallel to the strip, i.e. periodic in `across`)
    if (u <= KF_CEREAL_PALE || u == KF_CATCH)
    {
        // tramlines: two wheel tracks 1.8 m apart every 18 m, 0.45 m wide - bare soil in a standing crop
        float q = frac((across - 0.5 * KF_TRAM_M) / KF_TRAM_M) * KF_TRAM_M;
        float dc = min(q, KF_TRAM_M - q);
        half track = (half)(saturate((0.225 - abs(dc - 0.9)) / fp + 0.5) * saturate(0.9 / fp - 0.5));
        col = lerp(col, half3(0.150h, 0.112h, 0.072h), track * 0.75h);
        // lodged / thinner patches (wind, wet hollows): darker and duller
        col *= 1.0h - 0.12h * smoothstep(0.62h, 0.80h, n17);
    }
    else if (u <= KF_RAPE_STUBBLE)
    {
        // straw windrows behind the combine (7.5 m header) - only where the straw is still on the field; baled stubble
        // keeps the paler ghosts of the swaths; fine stubble rows near the cab
        float wp = u == KF_RAPE_STUBBLE ? 6.0 : 7.5;
        half row = KFBand(across + 1.7, wp, u == KF_STUBBLE ? 1.5 : 2.6, fp);
        half3 straw = u == KF_RAPE_STUBBLE ? half3(0.210h, 0.185h, 0.120h) : half3(0.400h, 0.345h, 0.215h);
        col = lerp(col, straw, row * (u == KF_STUBBLE ? 0.85h : 0.35h));
        half fine = KFBand(across, 0.16, 0.06, fp);
        col *= 1.0h - 0.16h * fine;
        // weeds / volunteer cereal greening the stubble in patches
        col = lerp(col, half3(0.085h, 0.130h, 0.040h), 0.30h * smoothstep(0.55h, 0.85h, n5 * 0.6h + n17 * 0.4h));
    }
    else if (u <= KF_ROOTS)
    {
        // crop rows 0.75 m (maize / potatoes), soil between the rows seen only close by
        half gap = KFBand(across + 0.375, 0.75, 0.30, fp);
        col = lerp(col, half3(0.120h, 0.095h, 0.062h), gap * 0.45h);
        col *= 1.0h + 0.10h * (n5 - 0.5h);
    }
    else if (u == KF_DISKED)
    {
        // disc harrow passes (3 m) and a little straw still on the surface
        col *= 1.0h + 0.10h * (KFBand(across, 3.0, 1.5, fp) - 0.5h);
        col = lerp(col, half3(0.260h, 0.220h, 0.140h), 0.15h * smoothstep(0.5h, 0.9h, n5));
        fa = 0.0h;
    }
    else if (u == KF_FALLOW || u == KF_PASTURE || u == KF_UNCUT)
    {
        // weedy / grazed / flowering patches 5-17 m
        half p = smoothstep(0.35h, 0.75h, n5 * 0.55h + n17 * 0.45h);
        half3 other = u == KF_FALLOW ? half3(0.170h, 0.160h, 0.060h)      // yellow flowering weeds, dry stalks
                    : u == KF_PASTURE ? half3(0.090h, 0.140h, 0.035h)     // rank tufts left by the cattle
                    : half3(0.150h, 0.140h, 0.080h);                      // seed heads, sorrel-brown
        col = lerp(col, other, p * 0.6h);
    }
    else if (u == KF_MOWN || u == KF_HAY)
    {
        // windrows of cut grass every 6 m (tedder / rake), lighter and yellower than the cut sward between them
        half row = KFBand(across + 2.0, 6.0, 1.3, fp);
        col = lerp(col, u == KF_MOWN ? half3(0.170h, 0.185h, 0.070h) : half3(0.250h, 0.225h, 0.105h), row * 0.8h);
    }

    // ---- headland (uwrocie) at the strip end on arable land: the turning passes, compacted and a pass behind the rest
    if (arable)
    {
        half head = (half)(saturate((KF_HEADLAND_M - blockEdge) / fp + 0.5) * saturate(blockEdge / max(fp, 0.5)));
        half3 hc = u <= KF_RAPE_STUBBLE ? col * half3(0.86h, 0.90h, 0.98h) : lerp(col, half3(0.11h, 0.095h, 0.065h), 0.25h);
        col = lerp(col, hc, head * 0.8h);
    }

    // ---- baulk (miedza): rough unmown grass 1-2.6 m wide between two strips (width per strip edge), 2.4 m along the
    // block border; box-filtered by the pixel footprint, kept as a thin line far away (it gives the strips away), but
    // never under one pixel at full strength (no grid painted over the horizon)
    float kEdge = across < 0.5 * w ? k : k + 1.0;
    float bw = KF_BAULK_MIN_M + KF_BAULK_SPAN_M * KFU01(KFHash((int)bid, (int)kEdge, 947u));
    float e = min(across, w - across);
    half baulk = (half)(saturate((0.5 * bw - e) / fp + 0.5) * saturate(bw / fp));
    half bblock = (half)(saturate((1.2 - blockEdge) / fp + 0.5) * saturate(2.4 / fp));
    baulk = max(baulk, bblock);
    half3 bc = lerp(half3(0.072h, 0.112h, 0.036h), half3(0.150h, 0.140h, 0.072h), smoothstep(0.45h, 0.8h, n5));
    col = lerp(col, bc, baulk * 0.9h);
    fb = lerp(fb, 0.50h, baulk);

    m.b = lerp(m.b, fb, farm);
    m.a = lerp(m.a, fa, farm);
    field = half4(col, alb.a * farm);
}

#endif
