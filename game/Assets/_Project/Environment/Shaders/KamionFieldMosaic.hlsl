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
// ADR 0334 r3 (fields3-s24, critic wave10-pre 1): the whole LAYOUT (districts, blocks, strip seams) is looked up at a
// warped position - two octaves of 2D value noise, metres peak-to-peak per axis - so a field edge bows by several
// metres over 50-250 m and stops being a ruled line 300 m away, where the r2 wobble (+-1.2 m) is under a pixel. The
// ROWS keep the unwarped coordinate (r2 render review: rows that bend read as wood grain), so they run out obliquely
// at a bowed edge like drill rows at a real field margin. Python mirror: vegetation.field_warp (salts 1011..1017).
#define KF_WARP_L_M 230.0
#define KF_WARP_AL 10.0
#define KF_WARP_S_M 53.0
#define KF_WARP_AS 3.0
// ADR 0334 r4 (fields4-s24, critic s24 wave 11 pt 10 "pola w dali proste granice"): a third, wide octave - beyond
// ~300 m the 230 m / +-5 m bow is a few pixels, and a block border 400 m out was again a ruled line between two
// colours. 610 m cells, +-14 m per axis: a border bows by a visible angle at any distance, near the cab it is a gentle
// curve over half a kilometre. Python mirror: vegetation.FIELD_WARP_FAR (salts 1061, 1063).
#define KF_WARP_X_M 610.0
#define KF_WARP_AX 28.0
// r3 flag contract: grassland = COLOR_0.b <= KF_MEADOW_B0 (new tiles write 0.00), arable = 1.00, every other ground
// keeps 0.07 .. 0.80. With the r2 codes (grassland 0.90) the mesh ramp from arable 1.00 to a meadow could not be told
// from the ramp to a verge, and the margin rule (flag gradient, constant per triangle) painted the straddling terrain
// cells of the stair-stepped border as rough grass - hard-edged green rectangles of a few metres in the crop (critic
// P0, dk65-07 f2_obl_maize; cell-sized at the coarser terrain LODs). Now every ramp below the arable code leaves the
// farmland; tiles not rebuilt yet (grassland 0.90) keep the r2 behaviour.
#define KF_MEADOW_B0 0.020
#define KF_MEADOW_B1 0.050

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
// mott: 0..1 mottling of 0.5-4 m (macro map A) - r3: tone / hue patches inside one use (a sward is not one flat green).
void KamionFieldMosaic(float2 local, float2 origin, float footprint, float2 enDx, float2 enDy, half2 mbD, half driftN,
                       half mott, inout half4 m, out half4 field, out half2 slopeEN)
{
    field = half4(0.0h, 0.0h, 0.0h, 0.0h);
    slopeEN = half2(0.0h, 0.0h);
    half farmHi = smoothstep(0.84h, 0.88h, m.b);                               // arable 1.00 (r2 tiles: + grassland 0.90)
    half farm = max(farmHi, 1.0h - smoothstep(KF_MEADOW_B0, KF_MEADOW_B1, m.b));   // r3: grassland code 0.00
    if (farm <= 0.0h) return;
    // r3 layout warp (see KF_WARP_*): lw is used for the district / block / strip lookup only
    float2 lw = local + (float2(KFNoise(local, origin, KF_WARP_L_M, 1011u), KFNoise(local, origin, KF_WARP_L_M, 1013u)) - 0.5) * KF_WARP_AL
                      + (float2(KFNoise(local, origin, KF_WARP_S_M, 1015u), KFNoise(local, origin, KF_WARP_S_M, 1017u)) - 0.5) * KF_WARP_AS
                      + (float2(KFNoise(local, origin, KF_WARP_X_M, 1061u), KFNoise(local, origin, KF_WARP_X_M, 1063u)) - 0.5) * KF_WARP_AX;
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
    float2 cD = floor((lw + origin) / KF_DISTRICT_M);
    float e1 = 1e20, e2 = 1e20;
    float2 sD = 0, sD2 = 0;
    int2 dIJ = 0, dIJ2 = 0;
    [unroll] for (int dj0 = -1; dj0 <= 1; dj0++)
    [unroll] for (int di0 = -1; di0 <= 1; di0++)
    {
        int2 ij = int2(cD) + int2(di0, dj0);
        float2 s = float2(ij) * KF_DISTRICT_M - origin
                 + (0.15 + 0.7 * float2(KFU01(KFHash(ij.x, ij.y, 971u)), KFU01(KFHash(ij.x, ij.y, 973u)))) * KF_DISTRICT_M;
        float2 v = lw - s;
        float dd = dot(v, v);
        if (dd < e1) { e2 = e1; sD2 = sD; dIJ2 = dIJ; e1 = dd; sD = s; dIJ = ij; }
        else if (dd < e2) { e2 = dd; sD2 = s; dIJ2 = ij; }
    }
    float districtEdge = (e2 - e1) / max(2.0 * length(sD2 - sD), 1e-3);
    uint dsalt = KFHash(dIJ.x, dIJ.y, 977u);
    float thD = PI * KFU01(KFHash(dIJ.x, dIJ.y, 975u));
    float2 aD = float2(cos(thD), sin(thD));       // long axis of the strips
    float2 nD = float2(-aD.y, aD.x);
    float2 r0 = lw - sD;
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
    float2 rel = lw - seed;           // layout frame (warped): strip index, seam and baulk distances
    float2 relR = local - seed;       // row frame (unwarped): rows, windrows, tramlines stay straight

    float fp = max(footprint, 1e-3);
    half n5 = KFNoise(local, origin, 5.0, 951u);
    half n17 = KFNoise(local, origin, 17.0, 953u);
    half nL = KFNoise(local, origin, KF_WOB_L_M, 983u);
#if defined(_KAMION_WORLD_DETAIL)
    half n1 = KFNoise(local, origin, 1.7, 985u);
#else
    half n1 = 0.5h;
#endif
    float wob = (nL - 0.5) * KF_WOB_AL + (n17 - 0.5) * KF_WOB_A17 + (n5 - 0.5) * KF_WOB_A5;
    // r3: the small noises fade to their mean once their cell is under ~2 px (they drive widths and thresholds; left
    // alone they shimmer on the far fields seen at a grazing angle)
    n1 = lerp(0.5h, n1, (half)saturate(1.7 / (2.0 * fp) - 0.5));
    n5 = lerp(0.5h, n5, (half)saturate(5.0 / (2.0 * fp) - 0.5));
    // r2: the strip edge is not a ruled line - the strip coordinate meanders by up to +-1.2 m (gentle 71 m bows, a little
    // 17 m and 5 m wiggle - seen end-on from the cab the furrows must stay near-straight, r2 render review), so the colour seam, the baulk and every row parallel to the edge follow one ploughed-by-eye line
    // r2 polygon border: the flag passes 0.90 (the grassland code) on its way from arable 1.00 to the verge - that used
    // to draw a ruler-straight band of vivid meadow green around every arable polygon. Now the ramp below the arable
    // threshold is a margin of rough grass, and the threshold wanders by ~+-0.5 m of ground (ragged crop edge).
    float thA = 0.95 + (ramp ? clamp(((n1 - 0.5) + (n5 - 0.5) * 0.8) * 1.6 * gl, -0.04, 0.04) : 0.0);
    bool arable = m.b > thA;
    float dA = max(0.3 * gl, 0.004);
    // r3: only on the high side - the grassland code 0.00 has no margin of its own (its ramp IS open ground)
    half margin = ramp ? (half)saturate((thA + dA - m.b) / (2.0 * dA)) * farmHi : 0.0h;
    float t = (dot(rel, dir) + wob) / w;          // across the strips, relative to the block seed (fp32-safe)
    float along = dot(relR, float2(-dir.y, dir.x)); // along the rows (m)
    float rowc = dot(relR, dir) + wob;            // r3: across the rows (m), continuous over the strips of a block
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
    // r4 far plan (critic s24 wave 11 pt 10: "pola w dali płaska plama, brak miedz / rzędów"): once a pixel covers
    // metres of ground the rows, windrows and baulks are filtered away and a field 300 m out was one flat colour.
    // farK ramps in with the pixel footprint (from ~6 m / px, full at ~26 m / px - at the cab eye ~150 / 250 m out);
    // with it the strips of one use part by tone, every strip shows its drill / sprayer passes as long bands along
    // the rows, and baulks and block borders stay as darker lines (below). WORKING_VALUE.
    half farK = (half)saturate((fp - 6.0) / 20.0);
    half3 col = alb.rgb * (1.0h + dev * (0.12h + 0.30h * farK)) * (1.0h + (driftN - 0.5h) * 0.16h);
    half fa = 0.0h;

    // ---- r2 headland (uwrocie): where the block border crosses the strips, the last KF_HEADLAND_M (x 0.65..1.35 per
    // block, wobbling) are worked ALONG the border - every row / windrow / furrow of the use turns by 90 deg there
    float Hd = KF_HEADLAND_M * (0.65 + 0.7 * KFU01(KFHash(b1.x, b1.y, 949u ^ dsalt))) + (n17 - 0.5) * 2.0;
    bool hrow = arable && crossK > 0.5h && blockEdge < Hd;
    float rc = hrow ? blockEdge : rowc;                   // coordinate across the rows (m)
    float rl = hrow ? t * w : along;                      // coordinate along the rows (m)
    float2 rdir = hrow ? gW : dir;
    float fpr = max(abs(dot(enDx, rdir)) + abs(dot(enDy, rdir)), 1e-4);   // footprint across the rows
    fpr = min(fpr, fp * 1.5);

    // streaks along the rows: every pass of a machine leaves its own tone (pass-wide) and fine drill / chaff lines
    // r3 (critic wave10-pre "pasy jak boisko golfowe", f2_obl_headland): value noise on ONE 2.6 m lattice across the
    // rows is a quasi-periodic light / dark alternation - from above every meadow was evenly striped. Now a broad
    // 7.3 m octave carries most of the tone and the pass-wide streaks come and go in patches (17 m / 71 m noise)
    // r4: both octaves fade to their mean once their cell across the rows is under ~2 px (no aliasing noise far out)
    half sfA = (KFNoiseSF(rc, rl, 7.3, 90.0, 1029u) - 0.5h) * (half)saturate(7.3 / (2.0 * fpr) - 0.5);
    half sfB = (KFNoiseSF(rc, rl, 2.6, 60.0, 987u) - 0.5h) * (half)saturate(2.6 / (2.0 * fpr) - 0.5);
    half sf2 = sfA * 0.8h + sfB * lerp(0.15h, 1.0h, smoothstep(0.42h, 0.70h, n17 * 0.5h + nL * 0.5h));
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
        // tramlines: two wheel tracks 1.8 m apart every 18 m - bare soil in a standing crop.
        // r4 (critic s24 wave 11: "koleiny w zagonie to namalowane paski"): a track is a RUT - its line wanders a
        // hand's width, its width breathes 0.2-0.6 m, the crop beside it is thinned and bent in over 0.2-0.5 m (soil
        // between sparse stalks, not a ruled colour step), weeds take it over where the sprayer has not been for
        // weeks, the damp bottom is darker than the crumbled rim, and the profile tilts the normal (gone under ~1 px).
        float qq = frac((rc - 0.5 * KF_TRAM_M) / KF_TRAM_M) * KF_TRAM_M;
        float dc = min(qq, KF_TRAM_M - qq);
        float tc = 0.9 + (n17 - 0.5) * 0.14 + (n1 - 0.5) * 0.05;
        float thw = 0.10 + 0.12 * n5 + (n1 - 0.5) * 0.06;
        float tsr = (dc - tc) / max(thw, 0.05);
        half tvis = (half)saturate(0.9 / fpr - 0.5);
        half track = (half)saturate((thw - abs(dc - tc)) / fpr + 0.5) * tvis;
        half tthin = (half)saturate(1.0 - (abs(dc - tc) - thw) / (0.20 + 0.30 * n17)) * tvis;
        half tweed = smoothstep(0.55h, 0.80h, n17 * 0.5h + KFNoise(local, origin, 9.0, 1025u) * 0.5h);
        half3 tsoil = half3(0.150h, 0.112h, 0.072h) * (0.85h + 0.30h * n5);
        tsoil = lerp(tsoil * 0.70h, tsoil * 1.08h, (half)saturate(abs(tsr)));      // damp packed bottom, dry rim
        tsoil = lerp(tsoil, half3(0.070h, 0.110h, 0.035h), tweed * 0.65h);         // weeds in the rut
        col = lerp(col, lerp(col, tsoil, 0.45h) * 0.90h, tthin * (0.35h + 0.40h * n1));  // sparse, bent-in stalks
        col = lerp(col, tsoil, track * (0.80h - 0.25h * tweed));
        float dsg = qq < 0.5 * KF_TRAM_M ? 1.0 : -1.0;                             // direction of growing dc
        slopeEN += (half2)(rdir * dsg) * (half)(clamp(tsr, -1.0, 1.0) * 0.40) * track * (half)saturate(0.35 / fpr - 0.5);
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
        // r4: in the shade of the canopy, with fallen dry leaves and weeds in patches - not an even soil stripe
        half gap = KFBand(rc + 0.375, 0.75, 0.30, fpr);
        half3 litter = lerp(half3(0.095h, 0.078h, 0.052h), half3(0.150h, 0.128h, 0.080h), smoothstep(0.4h, 0.8h, n1));
        col = lerp(col, litter, gap * (0.18h + 0.30h * n5));
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
        // windrows of cut grass (tedder / rake), lighter and yellower than the cut sward between them.
        // r3 (critic wave10-pre: "pasy jak boisko golfowe"): no two windrows alike - every row sits off its 6 m line
        // by up to +-1.1 m, has its own width and strength, thins out and breaks along its length (already raked up,
        // blown apart), and a third of the rows are missing altogether (WORKING_VALUE)
        float wi = floor(rc / 6.0);
        uint hw0 = KFHash((int)wi + KF_BLOCK_HASH_OFS * 4, (int)(fid & 0xFFFFu), 1021u);
        float wj = (KFU01(hw0) - 0.5) * 2.2;
        float wd = abs(rc - (wi + 0.5) * 6.0 - wj);
        half wwid = (half)(0.35 + 0.9 * KFU01(KFHash((int)hw0, 1, 1027u))) * (0.6h + 0.8h * n5);
        // box filter that keeps the energy: a 0.8 m windrow under a 3 m footprint is a faint tone, not a 3 m band
        // (the r2 bands kept full strength while they widened - the far meadow turned into even stripes)
        float fw = max(fpr, 0.25);
        half row = (half)(saturate((0.5 * wwid - wd) / fw + 0.5) * min(1.0, wwid / fw) * saturate(6.0 / (3.0 * fpr) - 0.5));
        row *= (KFU01(KFHash((int)hw0, 3, 1027u)) < 0.6 ? 1.0h : 0.0h) * smoothstep(0.38h, 0.60h, KFNoiseSF(rc, rl, 6.0, 23.0, 1023u));
        col = lerp(col, u == KF_MOWN ? half3(0.170h, 0.185h, 0.070h) : half3(0.250h, 0.225h, 0.105h), row * (0.45h + 0.4h * n17));
        stA1 = 0.12h; stA2 = 0.07h;
    }
    else
    {
        // ley / meadow regrowth. r3: the r2 mower passes (alternate 2.8 m light / dark bands) read as a football
        // pitch from above; a meadow three weeks after the cut shows no swath direction - only the pass-wide tone
        // streaks (sf2, irregular) and the lusher / drier patches below stay
        stA1 = 0.06h; stA2 = 0.05h;
    }
    if (u >= KF_LEY && u != KF_FALLOW)
    {
        // r3 sward variation (critic: "kafelek wzoru w trawie"): lusher clover / dung patches and drier knolls of
        // 1-17 m, a hue shift and not only a tone - breaks the 3 m grass tile that showed through the flat use colour
        half lush = smoothstep(0.52h, 0.80h, mott * 0.55h + n5 * 0.45h);
        half dryp = smoothstep(0.55h, 0.85h, (1.0h - mott) * 0.5h + n17 * 0.5h);
        col = lerp(col, col * half3(0.80h, 0.94h, 0.78h), lush * 0.55h);
        col = lerp(col, col * half3(1.22h, 1.10h, 0.90h), dryp * 0.45h);
    }
    col *= 1.0h + stA1 * sf1 + stA2 * sf2;
    if (farK > 0.0h && !hrow)
    {
        // r4 far plan: passes of the drill / sprayer / mower 6-12 m wide along the strip, each its own tone - from
        // afar the direction of the rows shows as long bands (filtered across the rows like the rows themselves)
        float pw = 6.0 + 6.0 * KFU01(KFHash((int)fid, 7, 1065u));
        float pIdx = floor((rowc + 0.37 * w) / pw);
        half pt = (half)(KFU01(KFHash((int)fid, (int)pIdx + KF_BLOCK_HASH_OFS * 4, 1067u)) - 0.5);
        col *= 1.0h + pt * 0.26h * farK * (half)saturate(pw / (2.0 * fpr) - 0.5);
    }
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
    float hw = max(0.5 * bw * (0.55 + 0.9 * n5) + (n1 - 0.5) * 0.60, 0.12);
    float fpe = max(fp, 0.30);     // a grass edge is never sharper than a few blades
    // r3 (critic: "pola bez miedz z kabiny"): the baulk is filtered by the footprint ACROSS it, like the rows - seen
    // along its length from the cab it stays a crisp line to the horizon instead of dissolving 40 m out, where the
    // isotropic footprint of a grazing view is already metres
    float fpb = clamp(abs(dot(enDx, dir)) + abs(dot(enDy, dir)), 1e-4, fp * 1.5);
    half baulk = hasBaulk ? (half)(saturate((hw - e) / max(fpb, 0.30) + 0.5) * saturate(2.0 * hw / fpb)) : 0.0h;
    // r4 far plan: tall unmown grass, tansy and a bush here and there - a baulk far away reads as a darker line; it
    // keeps up to ~half its strength down to a third of a pixel across (energy-true would drop it to nothing)
    if (hasBaulk) baulk = max(baulk, (half)(saturate((hw - e) / max(fpb, 0.30) + 0.5) * saturate(6.0 * hw / fpb) * 0.65) * farK);
    half thin = hasBaulk ? (half)saturate(1.0 - (e - hw) / (0.6 + 2.2 * n17)) : 0.0h;
    // block border: a wider grass strip, on some borders a field track (two sandy ruts 1.6 m apart in the grass)
    float hbw = (fieldTrack ? 1.9 : 1.2) + (n17 - 0.5) * 1.2 + (n5 - 0.5) * 0.5 + (n1 - 0.5) * 0.3;
    half bblock = (half)(saturate((hbw - blockEdge) / fpe + 0.5) * saturate(2.0 * hbw / fp));
    // r4: the block border filtered ACROSS it as the baulk (seen along it, it stays a line to the horizon) and kept as
    // a darker line far away
    float fpk = clamp(abs(dot(enDx, gW)) + abs(dot(enDy, gW)), 1e-4, fp * 1.5);
    bblock = max(bblock, (half)(saturate((hbw - blockEdge) / max(fpk, 0.30) + 0.5) * saturate(2.0 * hbw / fpk)));
    bblock = max(bblock, (half)(saturate((hbw - blockEdge) / max(fpk, 0.30) + 0.5) * saturate(6.0 * hbw / fpk) * 0.75) * farK);
    thin = max(thin, (half)saturate(1.0 - (blockEdge - hbw) / (0.6 + 2.2 * n17)));
    baulk = max(baulk, max(bblock, margin));
    if (ramp && arable) thin = max(thin, (half)saturate(1.0 - (m.b - thA) / max(2.5 * gl, 1e-3)));
    half3 bc = lerp(half3(0.078h, 0.122h, 0.038h), half3(0.150h, 0.140h, 0.072h), smoothstep(0.50h, 0.85h, n5));
    bc *= 0.85h + 0.30h * n1;
    bc *= 1.0h - 0.45h * farK;                  // r4: far away the sward's own shadow darkens the line
    col = lerp(col, lerp(col, bc, 0.55h), thin * thin * (0.25h + 0.70h * n5));
    half bstr = lerp(arable ? 0.92h : 0.35h, 0.92h, margin);     // between two meadows the baulk is only rougher grass
    col = lerp(col, bc, baulk * bstr);
    slopeEN *= (1.0h - baulk) * farm * alb.a;
    if (fieldTrack)
    {
        // r3 (critic wave10-pre: "dwa proste pasy o stałej szerokości, jak namalowane"): a field track is two ruts
        // that live - each wanders +-0.25 m, swells from a hand-wide thread to 0.6 m and back (1.7 m / 5 m noise),
        // grows over for metres where nobody drove this year (17 m / 5 m noise under a threshold), has a soft ragged
        // grass edge, a darker damp bottom with a pale dry rim, and it is DOWN: the rut profile tilts the normal.
        // Between the ruts the middle strip is taller, rougher grass. All WORKING_VALUE.
        float rcen = 0.8 + (n17 - 0.5) * 0.5 + (n1 - 0.5) * 0.12;
        float rhw = max(0.08 + 0.17 * n5 + (n1 - 0.5) * 0.10, 0.05);
        half live = smoothstep(0.34h, 0.52h, n17 * 0.55h + KFNoise(local, origin, 9.0, 1025u) * 0.45h);
        float sr = (blockEdge - rcen) / rhw;
        float fpt = max(fp, 0.10);
        half rut = (half)(saturate((rhw - abs(blockEdge - rcen)) / fpt + 0.5) * saturate(2.0 * rhw / fp)) * live;
        rut *= 0.55h + 0.45h * smoothstep(0.25h, 0.6h, n1);                       // grass creeping into the rut
        half3 soil = half3(0.215h, 0.180h, 0.120h) * (0.80h + 0.35h * n5);
        soil = lerp(soil * 0.62h, soil, (half)saturate(abs(sr)));               // damp, packed bottom; dry crumbled rim
        col = lerp(col, soil, rut * (0.50h + 0.40h * n17));
        half hump = (half)saturate(1.0 - blockEdge / max(rcen - rhw, 0.05)) * live;
        col = lerp(col, col * half3(0.82h, 0.90h, 0.78h), hump * 0.5h);
        half rk = (half)saturate(0.5 / fp - 0.5);                                // the dent is gone under ~1 px
        slopeEN += (half2)gW * (half)(clamp(sr, -1.0, 1.0) * 0.45) * rut * rk;
    }
    fb = lerp(fb, 0.32h, baulk * bstr);     // r2: 0.50 browned the baulk into a dirt track beside a green crop

    m.b = lerp(m.b, fb, farm);
    m.a = lerp(m.a, fa, farm);
    field = half4(col, alb.a * farm);
}

#endif
