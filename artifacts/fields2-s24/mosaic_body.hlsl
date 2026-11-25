// local: region-local E/N (m); origin: EPSG:2180 of the region origin (whole metres); footprint: metres per pixel;
// enDx / enDy: screen-space derivatives of `local` (ddx, ddy - taken by the caller outside any branch): the row
// patterns are filtered by the footprint ACROSS the rows, so rows seen end-on stay visible far down the field.
// driftN: 0..1 low-frequency noise (macro map). m: terrain masks (in/out). field: linear albedo of the field (rgb)
// and its cover weight over the grass (a), applied after the ground-mask colouring. slopeEN: ground slope of the
// furrows / rows (dE, dN), added to the world normal by the caller.
void KamionFieldMosaic(float2 local, float2 origin, float footprint, float2 enDx, float2 enDy, half driftN,
                       inout half4 m, out half4 field, out half2 slopeEN)
{
    field = half4(0.0h, 0.0h, 0.0h, 0.0h);
    slopeEN = half2(0.0h, 0.0h);
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
    half n47 = KFNoise(local, origin, KF_WOB_L_M, 983u);
#if defined(_KAMION_WORLD_DETAIL)
    half n1 = KFNoise(local, origin, 1.7, 985u);
#else
    half n1 = 0.5h;
#endif
    // r2: the strip edge is not a ruled line - the strip coordinate meanders by up to +-1.9 m (gentle 47 m bows, a little
    // 17 m and 5 m wiggle - furrows stay near-straight), so the colour seam, the baulk and every row parallel to the edge follow one ploughed-by-eye line
    float wob = (n47 - 0.5) * KF_WOB_A47 + (n17 - 0.5) * KF_WOB_A17 + (n5 - 0.5) * KF_WOB_A5;
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
        rowD = 0.26h; rowS = 0.30h;
        stA1 = 0.26h; stA2 = 0.20h;
    }
    else if (u <= KF_ROOTS)
    {
        // crop rows 0.75 m (maize / potatoes), soil between the rows seen only close by
        half gap = KFBand(rc + 0.375, 0.75, 0.30, fpr);
        col = lerp(col, half3(0.120h, 0.095h, 0.062h), gap * 0.45h);
        col *= 1.0h + 0.10h * (n5 - 0.5h);
        rowP = 0.75; rowD = 0.0h; rowS = 0.45h;
        stA1 = 0.10h; stA2 = 0.12h;
    }
    else if (u == KF_DISKED)
    {
        if (ploughed)
        {
            // furrow slices 0.40 m (WORKING_VALUE: 14-16" plough bodies), lighter dried crests, plough passes 1.6 m
            col *= 1.0h + 0.10h * (KFBand(rc, 1.6, 0.8, fpr) - 0.5h);
            col = lerp(col, half3(0.175h, 0.140h, 0.098h), 0.22h * smoothstep(0.45h, 0.85h, n5));
            rowP = 0.40; rowD = 0.42h; rowS = 0.75h;
            stA1 = 0.30h; stA2 = 0.22h;
        }
        else
        {
            // disc harrow passes (3 m) and a little straw still on the surface
            col *= 1.0h + 0.16h * (KFBand(rc, 3.0, 1.5, fpr) - 0.5h);
            col = lerp(col, half3(0.260h, 0.220h, 0.140h), 0.18h * smoothstep(0.5h, 0.9h, n5));
            rowP = 0.22; rowD = 0.20h; rowS = 0.25h;
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
        float ph = frac(rc / rowP) * 6.2831853;
        half fr = (half)saturate(rowP / (3.0 * fpr) - 0.5);
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
    half baulk = hasBaulk ? (half)(saturate((hw - e) / fp + 0.5) * saturate(2.0 * hw / fp)) : 0.0h;
    half thin = hasBaulk ? (half)saturate(1.0 - (e - hw) / (0.6 + 2.2 * n17)) : 0.0h;
    // block border: a wider grass strip, on some borders a field track (two sandy ruts 1.6 m apart in the grass)
    float hbw = (fieldTrack ? 1.9 : 1.2) + (n17 - 0.5) * 1.2 + (n5 - 0.5) * 0.5 + (n1 - 0.5) * 0.3;
    half bblock = (half)(saturate((hbw - blockEdge) / fp + 0.5) * saturate(2.0 * hbw / fp));
    thin = max(thin, (half)saturate(1.0 - (blockEdge - hbw) / (0.6 + 2.2 * n17)));
    baulk = max(baulk, bblock);
    half3 bc = lerp(half3(0.072h, 0.112h, 0.036h), half3(0.150h, 0.140h, 0.072h), smoothstep(0.45h, 0.8h, n5));
    bc *= 0.85h + 0.30h * n1;
    col = lerp(col, lerp(col, bc, 0.55h), thin * thin * (0.25h + 0.70h * n5));
    col = lerp(col, bc, baulk * 0.92h);
    if (fieldTrack)
    {
        half rut = (half)(saturate((0.26 - abs(blockEdge - 0.8)) / fp + 0.5) * saturate(0.52 / fp));
        col = lerp(col, half3(0.215h, 0.180h, 0.120h) * (0.85h + 0.30h * n5), rut * (0.55h + 0.40h * n17));
    }
    slopeEN *= (1.0h - baulk) * farm * alb.a;
    fb = lerp(fb, 0.50h, baulk);

    m.b = lerp(m.b, fb, farm);
    m.a = lerp(m.a, fa, farm);
    field = half4(col, alb.a * farm);
}

#endif
