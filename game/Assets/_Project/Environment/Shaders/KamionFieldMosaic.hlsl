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
// ADR 0334 r2 (fields2-s24, critic build #8 P1#6): the strip edges meander - value noise of 71 / 17 / 5 m cells added
// to the strip coordinate (metres peak-to-peak). Python mirror: vegetation.field_wobble (salts 983, 953, 951).
#define KF_WOB_L_M 71.0
#define KF_WOB_AL 1.8
#define KF_WOB_A17 0.5
#define KF_WOB_A5 0.12

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
        case KF_CEREAL_RIPE:   alb = half4(0.350h, 0.240h, 0.085h, 0.92h); b = 0.20h; break;   // wheat / triticale, golden
        case KF_CEREAL_PALE:   alb = half4(0.315h, 0.262h, 0.120h, 0.92h); b = 0.20h; break;   // barley / rye / oats, pale
        case KF_STUBBLE:       alb = half4(0.300h, 0.212h, 0.095h, 0.92h); b = 0.25h; break;   // cereal stubble, straw left
        case KF_STUBBLE_BALED: alb = half4(0.265h, 0.205h, 0.110h, 0.92h); b = 0.25h; break;   // stubble, straw baled off
        case KF_RAPE_STUBBLE:  alb = half4(0.165h, 0.145h, 0.095h, 0.92h); b = 0.25h; break;   // rape stubble, grey-brown
        case KF_MAIZE:         alb = half4(0.036h, 0.078h, 0.020h, 0.88h); break;              // fodder maize, dark
        case KF_ROOTS:         alb = half4(0.050h, 0.096h, 0.026h, 0.88h); break;              // potatoes / beet
        case KF_DISKED:        alb = half4(0.150h, 0.112h, 0.072h, 0.95h); b = 0.30h; break;   // disked, light sandy soil
        case KF_CATCH:         alb = half4(0.085h, 0.150h, 0.034h, 0.80h); break;              // catch crop on stubble
        case KF_LEY:           alb = half4(0.068h, 0.132h, 0.030h, 0.70h); break;              // grass / clover ley
        case KF_FALLOW:        alb = half4(0.120h, 0.128h, 0.050h, 0.80h); b = 0.35h; break;   // fallow, weeds and seedlings
        case KF_REGROWTH:      alb = half4(0.068h, 0.148h, 0.030h, 0.72h); break;              // meadow regrowth after a cut
        case KF_PASTURE:       alb = half4(0.054h, 0.098h, 0.025h, 0.78h); break;              // pasture, grazed
        case KF_MOWN:          alb = half4(0.150h, 0.172h, 0.060h, 0.86h); b = 0.25h; break;   // freshly mown, windrows
        case KF_HAY:           alb = half4(0.225h, 0.195h, 0.085h, 0.90h); b = 0.35h; break;   // hay drying on the ground
        default:               alb = half4(0.128h, 0.124h, 0.060h, 0.84h); b = 0.30h; break;   // uncut, seed heads
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

// value noise in the strip frame: cells sa (across the rows) x sl (along the rows) metres - streaks along the rows
half KFNoiseSF(float a, float l, float sa, float sl, uint salt)
{
    float2 p = float2(a / sa, l / sl);
    float2 g0 = floor(p);
    float2 f = p - g0;
    f = f * f * (3.0 - 2.0 * f);
    int2 g = int2(g0) + KF_BLOCK_HASH_OFS * 4;
    half a0 = (half)KFU01(KFHash(g.x, g.y, salt)), b0 = (half)KFU01(KFHash(g.x + 1, g.y, salt));
    half c0 = (half)KFU01(KFHash(g.x, g.y + 1, salt)), d0 = (half)KFU01(KFHash(g.x + 1, g.y + 1, salt));
    return lerp(lerp(a0, b0, (half)f.x), lerp(c0, d0, (half)f.x), (half)f.y);
}

// local: region-local E/N (m); origin: EPSG:2180 of the region origin (whole metres); footprint: metres per pixel;
// enDx / enDy: screen-space derivatives of `local` (ddx, ddy - taken by the caller outside any branch): the row
// patterns are filtered by the footprint ACROSS the rows, so rows seen end-on stay visible far down the field.
// mbD: (ddx, ddy) of the farmland flag m.b - with enDx / enDy it gives the flag's ground gradient: the ramp between a
// field polygon and its neighbour (1 m of mesh beside the roads, 8 m elsewhere) becomes a ragged rough-grass margin.
// driftN: 0..1 low-frequency noise (macro map). m: terrain masks (in/out). field: linear albedo of the field (rgb)
// and its cover weight over the grass (a), applied after the ground-mask colouring. slopeEN: ground slope of the
// furrows / rows (dE, dN), added to the world normal by the caller.
void KamionFieldMosaic(float2 local, float2 origin, float footprint, float2 enDx, float2 enDy, half2 mbD, half driftN,
                       inout half4 m, out half4 field, out half2 slopeEN)
{
    field = half4(0.0h, 0.0h, 0.0h, 0.0h);
    slopeEN = half2(0.0h, 0.0h);
    half farm = smoothstep(0.84h, 0.88h, m.b);
    if (farm <= 0.0h) return;
    // r2: ground gradient of the flag (1 / m); > 0 only on the mesh cells that straddle a polygon border
    float det = enDx.x * enDy.y - enDx.y * enDy.x;
    float2 gB = abs(det) > 1e-12 ? float2(enDy.y * mbD.x - enDx.y * mbD.y, enDx.x * mbD.y - enDy.x * mbD.x) / det : float2(0.0, 0.0);
    float gl = length(gB);
    bool ramp = gl > 0.002;

    // ADR 0334 layout. District (KF_DISTRICT_M jittered lattice): one long-axis direction for all its strips (a Podlasie
    // village's strips run side by side, all the same way). Inside it, blocks are the Voronoi cells of a KF_BLOCK_M
    // lattice in a frame stretched KF_STRETCH times along that axis, so a block is ~3x longer than wide and holds a run
    // of narrow parallel strips (wąskie, podłużne działki). Every lattice point is formed relative to the origin /
    // district seed, so the strip coordinate keeps cm precision in fp32.
    float2 cD = floor((local + origin) / KF_DISTRICT_M);
    float e1 = 1e20, e2 = 1e20;
    float2 sD = 0, sD2 = 0;
    int2 dIJ = 0, dIJ2 = 0;
    [unroll] for (int dj0 = -1; dj0 <= 1; dj0++)
    [unroll] for (int di0 = -1; di0 <= 1; di0++)
    {
        int2 ij = int2(cD) + int2(di0, dj0);
        float2 s = float2(ij) * KF_DISTRICT_M - origin
                 + (0.15 + 0.7 * float2(KFU01(KFHash(ij.x, ij.y, 971u)), KFU01(KFHash(ij.x, ij.y, 973u)))) * KF_DISTRICT_M;
        float2 v = local - s;
        float dd = dot(v, v);
        if (dd < e1) { e2 = e1; sD2 = sD; dIJ2 = dIJ; e1 = dd; sD = s; dIJ = ij; }
        else if (dd < e2) { e2 = dd; sD2 = s; dIJ2 = ij; }
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
    int2 b1 = 0, b2 = 0;
    [unroll] for (int dj = -1; dj <= 1; dj++)
    [unroll] for (int di = -1; di <= 1; di++)
    {
        int2 ij = int2(c) + int2(di, dj);
        int2 hb = ij + KF_BLOCK_HASH_OFS;     // KFHash(i, j) == KFHash(-i, -j): keep the hashed indices positive
        float2 s = (float2(ij) + 0.15 + 0.7 * float2(KFU01(KFHash(hb.x, hb.y, 911u ^ dsalt)), KFU01(KFHash(hb.x, hb.y, 913u ^ dsalt)))) * KF_BLOCK_M;
        float2 v = q - s;
        float dd = dot(v, v);
        if (dd < d1) { d2 = d1; s2 = s1; b2 = b1; d1 = dd; s1 = s; b1 = hb; }
        else if (dd < d2) { d2 = dd; s2 = s; b2 = hb; }
    }
    float2 nq = (s2 - s1) / max(length(s2 - s1), 1e-3);
    float2 gq = float2(nq.x / KF_STRETCH, nq.y);          // border normal on the ground, district frame (a, n)
    float gql = max(length(gq), 1e-4);
    float blockEdge = (d2 - d1) / max(2.0 * length(s2 - s1), 1e-3) / gql;
    // r2: which border is the nearest - its ground normal (the rows of the headland run along it), whether it crosses
    // the strips (a strip END = headland) or runs beside them, and an id both of its sides agree on (field track or not)
    bool distr = districtEdge < blockEdge;
    float2 dW = (sD2 - sD) / max(length(sD2 - sD), 1e-3);
    float2 gW = distr ? dW : (aD * gq.x + nD * gq.y) / gql;
    half crossK = (half)saturate((abs(dot(gW, aD)) - 0.30) / 0.25);
    uint hBorder = distr ? KFHash(dIJ.x, dIJ.y, 991u) + KFHash(dIJ2.x, dIJ2.y, 991u)
                         : KFHash(b1.x, b1.y, 991u ^ dsalt) + KFHash(b2.x, b2.y, 991u ^ dsalt);
    bool fieldTrack = KFU01(KFHash((int)hBorder, 0, 993u)) < 0.40;       // WORKING_VALUE: share of borders with a field track
    blockEdge = min(blockEdge, districtEdge);
    float th = thD + 0.5 * PI + (KFU01(KFHash(b1.x, b1.y, 917u ^ dsalt)) - 0.5) * 0.2;   // strip normal, +-5.7 deg per block
    float w = KF_STRIP_MIN_M + KF_STRIP_SPAN_M * KFU01(KFHash(b1.x, b1.y, 919u ^ dsalt));
    float2 dir = float2(cos(th), sin(th));
    float2 seed = sD + aD * (s1.x * KF_STRETCH) + nD * s1.y;
    float2 rel = local - seed;

    float fp = max(footprint, 1e-3);
    half n5 = KFNoise(local, origin, 5.0, 951u);
    half n17 = KFNoise(local, origin, 17.0, 953u);
    half nL = KFNoise(local, origin, KF_WOB_L_M, 983u);
#if defined(_KAMION_WORLD_DETAIL)
    half n1 = KFNoise(local, origin, 1.7, 985u);
#else
    half n1 = 0.5h;
#endif
    // r2: the strip edge is not a ruled line - the strip coordinate meanders by up to +-1.2 m (gentle 71 m bows, a little
    // 17 m and 5 m wiggle - seen end-on from the cab the furrows must stay near-straight, r2 render review), so the colour seam, the baulk and every row parallel to the edge follow one ploughed-by-eye line
    // r2 polygon border: the flag passes 0.90 (the grassland code) on its way from arable 1.00 to the verge - that used
    // to draw a ruler-straight band of vivid meadow green around every arable polygon. Now the ramp below the arable
    // threshold is a margin of rough grass, and the threshold wanders by ~+-0.5 m of ground (ragged crop edge).
    float thA = 0.95 + (ramp ? clamp(((n1 - 0.5) + (n5 - 0.5) * 0.8) * 1.6 * gl, -0.04, 0.04) : 0.0);
    bool arable = m.b > thA;
    float dA = max(0.3 * gl, 0.004);
    half margin = ramp ? (half)saturate((thA + dA - m.b) / (2.0 * dA)) : 0.0h;
    float wob = (nL - 0.5) * KF_WOB_AL + (n17 - 0.5) * KF_WOB_A17 + (n5 - 0.5) * KF_WOB_A5;
    float t = (dot(rel, dir) + wob) / w;          // across the strips, relative to the block seed (fp32-safe)
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
    // r2: half of the "disked" strips are ploughed (orka / podorywka after the harvest): darker moist soil, furrows
    bool ploughed = u == KF_DISKED && KFU01(KFHash((int)fid, 0, 995u)) < 0.5;
    if (ploughed) alb.rgb = half3(0.105h, 0.079h, 0.054h);
    half3 col = alb.rgb * (1.0h + dev * 0.12h) * (1.0h + (driftN - 0.5h) * 0.16h);
    half fa = 0.0h;

    // ---- r2 headland (uwrocie): where the block border crosses the strips, the last KF_HEADLAND_M (x 0.65..1.35 per
    // block, wobbling) are worked ALONG the border - every row / windrow / furrow of the use turns by 90 deg there
    float Hd = KF_HEADLAND_M * (0.65 + 0.7 * KFU01(KFHash(b1.x, b1.y, 949u ^ dsalt))) + (n17 - 0.5) * 2.0;
    bool hrow = arable && crossK > 0.5h && blockEdge < Hd;
    float rc = hrow ? blockEdge : across;                 // coordinate across the rows (m)
    float rl = hrow ? t * w : along;                      // coordinate along the rows (m)
    float2 rdir = hrow ? gW : dir;
    float fpr = max(abs(dot(enDx, rdir)) + abs(dot(enDy, rdir)), 1e-4);   // footprint across the rows
    fpr = min(fpr, fp * 1.5);

    // streaks along the rows: every pass of a machine leaves its own tone (pass-wide) and fine drill / chaff lines
    half sf2 = KFNoiseSF(rc, rl, 2.6, 60.0, 987u) - 0.5h;
#if defined(_KAMION_WORLD_DETAIL)
    half sf1 = (KFNoiseSF(rc, rl, 0.55, 18.0, 989u) - 0.5h) * (half)saturate(0.55 / (1.5 * fpr) - 0.5);
#else
    half sf1 = 0.0h;
#endif
    half stA1 = 0.0h, stA2 = 0.0h;        // streak amplitudes (fine, pass-wide)
    float rowP = 0.0;                     // fine row / furrow period (m), 0 = none
    half rowD = 0.0h, rowS = 0.0h;        // furrow darkening, furrow slope

    // ---- structure of the use (all bands parallel to the rows, i.e. periodic in `rc`)
    if (u <= KF_CEREAL_PALE || u == KF_CATCH)
    {
        // tramlines: two wheel tracks 1.8 m apart every 18 m, 0.45 m wide - bare soil in a standing crop
        float qq = frac((rc - 0.5 * KF_TRAM_M) / KF_TRAM_M) * KF_TRAM_M;
        float dc = min(qq, KF_TRAM_M - qq);
        half track = (half)(saturate((0.225 - abs(dc - 0.9)) / fpr + 0.5) * saturate(0.9 / fpr - 0.5));
        col = lerp(col, half3(0.150h, 0.112h, 0.072h), track * 0.75h);
        // lodged / thinner patches (wind, wet hollows): darker and duller
        col *= 1.0h - 0.12h * smoothstep(0.62h, 0.80h, n17);
        stA1 = 0.06h; stA2 = 0.16h;
    }
    else if (u <= KF_RAPE_STUBBLE)
    {
        // straw windrows behind the combine (7.5 m header) - only where the straw is still on the field; baled stubble
        // keeps the paler ghosts of the swaths; stubble rows near the cab
        float wp = u == KF_RAPE_STUBBLE ? 6.0 : 7.5;
        half row = KFBand(rc + 1.7, wp, u == KF_STUBBLE ? 1.5 : 2.6, fpr);
        half3 straw = u == KF_RAPE_STUBBLE ? half3(0.210h, 0.185h, 0.120h) : half3(0.420h, 0.315h, 0.150h);
        col = lerp(col, straw, row * (u == KF_STUBBLE ? 0.85h : 0.35h));
        // combine wheelings: two compacted tracks per header pass, straw pressed flat, soil showing
        half wheel = KFBand(rc + 0.45, wp, 0.55, fpr) + KFBand(rc - 2.2, wp, 0.55, fpr);
        col *= 1.0h - 0.14h * wheel;
        // weeds / volunteer cereal greening the stubble in patches
        col = lerp(col, half3(0.085h, 0.130h, 0.040h), 0.30h * smoothstep(0.55h, 0.85h, n5 * 0.6h + n17 * 0.4h));
        rowP = u == KF_RAPE_STUBBLE ? 0.33 : 0.25;      // WORKING_VALUE: drill rows read as pairs from the cab
        rowD = 0.15h; rowS = 0.20h;
        stA1 = 0.26h; stA2 = 0.20h;
    }
    else if (u <= KF_ROOTS)
    {
        // crop rows 0.75 m (maize / potatoes), soil between the rows seen only close by
        half gap = KFBand(rc + 0.375, 0.75, 0.30, fpr);
        col = lerp(col, half3(0.120h, 0.095h, 0.062h), gap * 0.45h);
        col *= 1.0h + 0.10h * (n5 - 0.5h);
        rowP = 0.75; rowD = 0.0h; rowS = 0.12h;      // closed canopy in August: a hint of the rows, not ridges
        stA1 = 0.10h; stA2 = 0.12h;
    }
    else if (u == KF_DISKED)
    {
        if (ploughed)
        {
            // furrow slices 0.40 m (WORKING_VALUE: 14-16" plough bodies), lighter dried crests, plough passes 1.6 m
            col *= 1.0h + 0.06h * (KFBand(rc, 1.6, 0.8, fpr) - 0.5h);
            col = lerp(col, half3(0.175h, 0.140h, 0.098h), 0.22h * smoothstep(0.45h, 0.85h, n5));
            rowP = 0.40; rowD = 0.30h; rowS = 0.55h;
            stA1 = 0.30h; stA2 = 0.12h;
        }
        else
        {
            // disc harrow passes (3 m) and a little straw still on the surface
            col *= 1.0h + 0.16h * (KFBand(rc, 3.0, 1.5, fpr) - 0.5h);
            col = lerp(col, half3(0.260h, 0.220h, 0.140h), 0.18h * smoothstep(0.5h, 0.9h, n5));
            rowP = 0.22; rowD = 0.12h; rowS = 0.15h;
            stA1 = 0.26h; stA2 = 0.20h;
        }
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
        half row = KFBand(rc + 2.0, 6.0, 1.3, fpr);
        col = lerp(col, u == KF_MOWN ? half3(0.170h, 0.185h, 0.070h) : half3(0.250h, 0.225h, 0.105h), row * 0.8h);
        stA1 = 0.12h; stA2 = 0.14h;
    }
    else
    {
        // ley / meadow regrowth: mower passes 2.8 m laid alternately (light / dark stripes of the swath direction)
        col *= 1.0h + 0.07h * (KFBand(rc, 5.6, 2.8, fpr) - 0.5h);
        stA1 = 0.06h; stA2 = 0.10h;
    }
    col *= 1.0h + stA1 * sf1 + stA2 * sf2;
    if (rowP > 0.0)
    {
        // furrows / drill rows: darker bottoms (self-shadow, moist soil) and a slope for the light; once the period is
        // under ~3 px across the rows, the mean darkening stays (no tone pop) and the slope is gone
        // (render review r2: a pure sine read as corduroy - the furrow depth breaks up in 1.7 m / 5 m patches and the
        // line wanders by a fraction of its period, like clods and a hand on the wheel)
        float ph = frac(rc / rowP + (n1 - 0.5) * 0.25 + (n5 - 0.5) * 0.15) * 6.2831853;
        half fr = (half)saturate(rowP / (2.5 * fpr) - 0.8) * saturate(0.30h + 1.2h * n1) * (0.6h + 0.8h * n5);
        half sn, cs;
        sincos((half)ph, sn, cs);
        col *= 1.0h - rowD * lerp(0.5h, 0.5h - 0.5h * cs, fr);
        slopeEN = (half2)rdir * (sn * rowS * fr);
    }

    // ---- headland tone and the turning marks (kołowy ślad): each pass ends in a loop of two wheel tracks that swings
    // into the headland - a row of arcs along the headland line
    if (arable && crossK > 0.5h)
    {
        half head = (half)(saturate((Hd - blockEdge) / fp + 0.5) * saturate(blockEdge / max(fp, 0.5)));
        half3 hc = u <= KF_RAPE_STUBBLE ? col * half3(0.86h, 0.90h, 0.98h) : lerp(col, half3(0.11h, 0.095h, 0.065h), 0.25h);
        col = lerp(col, hc, head * 0.8h);
        float P = (u <= KF_CEREAL_PALE || u == KF_CATCH) ? 9.0 : (u <= KF_RAPE_STUBBLE ? 7.5 : 6.0);
        float ac = floor(across / P);
        float am = (across / P - ac) * P - 0.5 * P;
        float ua = KFU01(KFHash((int)fid, (int)ac, 997u));           // per loop: there or worked over, wider or tighter
        float dr = length(float2(am, blockEdge - (Hd - 0.6)));
        float ring = abs(abs(dr - (0.30 + 0.12 * ua) * P) - 0.9);
        half arc = (half)(saturate((0.22 - ring) / fp + 0.5) * saturate(0.9 / fp - 0.5)) * (blockEdge < Hd - 0.6 && ua < 0.7 ? 1.0h : 0.0h);
        arc *= 0.35h + 0.65h * n5;
        col = lerp(col, lerp(col * 0.72h, half3(0.150h, 0.112h, 0.072h), 0.40h), arc * 0.6h);
        slopeEN *= 1.0h - arc;
    }

    // ---- baulk (miedza): rough unmown grass between two strips of different holdings (two strips of one holding
    // share a seam only), 1-2.6 m wide per strip edge; r2: its width swells and pinches along the edge (5 m and
    // 1.7 m noise) and the crop thins out towards it over 1-4 m (weeds from the baulk, the drill lifted early), so the
    // seam is a soft, ragged band and not a ruled colour step. Box-filtered by the pixel footprint, kept as a thin
    // line far away (it gives the strips away), never under one pixel at full strength.
    bool upper = across >= 0.5 * w;
    float kEdge = upper ? k + 1.0 : k;
    uint fidN = KFHash((int)bid, (int)(upper ? k + 1.0 : k - 1.0), 929u);
    bool hasBaulk = own || KFU01(KFHash((int)fidN, 0, 931u)) < KF_OWN_SHARE;
    float bw = KF_BAULK_MIN_M + KF_BAULK_SPAN_M * KFU01(KFHash((int)bid, (int)kEdge, 947u));
    float e = min(across, w - across);
    float hw = max(0.5 * bw * (0.55 + 0.9 * n5) + (n1 - 0.5) * 0.35, 0.12);
    float fpe = max(fp, 0.30);     // a grass edge is never sharper than a few blades
    half baulk = hasBaulk ? (half)(saturate((hw - e) / fpe + 0.5) * saturate(2.0 * hw / fp)) : 0.0h;
    half thin = hasBaulk ? (half)saturate(1.0 - (e - hw) / (0.6 + 2.2 * n17)) : 0.0h;
    // block border: a wider grass strip, on some borders a field track (two sandy ruts 1.6 m apart in the grass)
    float hbw = (fieldTrack ? 1.9 : 1.2) + (n17 - 0.5) * 1.2 + (n5 - 0.5) * 0.5 + (n1 - 0.5) * 0.3;
    half bblock = (half)(saturate((hbw - blockEdge) / fpe + 0.5) * saturate(2.0 * hbw / fp));
    thin = max(thin, (half)saturate(1.0 - (blockEdge - hbw) / (0.6 + 2.2 * n17)));
    baulk = max(baulk, max(bblock, margin));
    if (ramp && arable) thin = max(thin, (half)saturate(1.0 - (m.b - thA) / max(2.5 * gl, 1e-3)));
    half3 bc = lerp(half3(0.072h, 0.112h, 0.036h), half3(0.150h, 0.140h, 0.072h), smoothstep(0.45h, 0.8h, n5));
    bc *= 0.85h + 0.30h * n1;
    col = lerp(col, lerp(col, bc, 0.55h), thin * thin * (0.25h + 0.70h * n5));
    half bstr = lerp(arable ? 0.92h : 0.35h, 0.92h, margin);     // between two meadows the baulk is only rougher grass
    col = lerp(col, bc, baulk * bstr);
    if (fieldTrack)
    {
        half rut = (half)(saturate((0.26 - abs(blockEdge - 0.8)) / fp + 0.5) * saturate(0.52 / fp));
        col = lerp(col, half3(0.215h, 0.180h, 0.120h) * (0.85h + 0.30h * n5), rut * (0.55h + 0.40h * n17));
    }
    slopeEN *= (1.0h - baulk) * farm * alb.a;
    fb = lerp(fb, 0.50h, baulk * bstr);

    m.b = lerp(m.b, fb, farm);
    m.a = lerp(m.a, fa, farm);
    field = half4(col, alb.a * farm);
}

#endif
