// Analytic street-lamp pools at dusk / night (ADR 0062, ADR 0191), shared by Kamion/World Surface and Kamion/World PBR.
// StreetLamps sends the luminaires nearest a focus 30 m ahead of the camera:
//   _KamionLampPos[i]  = (luminaire xyz, fade weight)
//   _KamionLampAxis[i] = (arm direction x, z: unit, horizontal, towards the carriageway; sodium 0/1; road optic 0/1)
//   _KamionLampCount, _KamionLampColor = I0·k/π of an LED luminaire (exposed units; Unity's Lambert has no 1/π),
//   _KamionLampSodium = sodium / LED tint ratio at equal luminance, _KamionLampSpec = 1: GGX highlight (tier flag).
// ADR 0191 photometry (WORKING_VALUE, shape typical of EN 13201 road luminaires, no product copied): the intensity is
// defined through its ground footprint in units of the mounting height h. Over a level road the illuminance is
//   E = I0 / h² · F,  F = (1 - ρ²)²,  ρ² = (along / RA)² + (across / RC)²,
// RC = RS on the carriageway side of the arm, RH behind the column (house side); a luminaire without an arm (post-top)
// is symmetric (RSYM). Equivalent intensity table I(γ, C) = I0 · F · (d / h)³ - a bat-wing with ~2.2·I0 at ~54° along
// the road and nothing above ~67° (full cutoff), so on walls and vehicles the same I(γ, C)·cos / d² holds.
// Downward flux I0 · π·RA·(RS+RH)/2 / 3 = 2.76·I0 ≈ 6.9 klm for I0 2500 cd (an 8–12 klm luminaire, utilance ~0.6).
// Between two lamps at the data spacing (median 29 m, h 8–11 m -> S/h ≈ 3.3) the minimum is ~0.45 of the peak (0.2 at 8 m / 30 m).
// A uniform branch + loop, no variants, no lights, no shadows.
#ifndef KAMION_LAMP_POOLS_INCLUDED
#define KAMION_LAMP_POOLS_INCLUDED

float _KamionLampCount;
float4 _KamionLampColor;
// night-pc-s23: 16 slots (PC High / Ultra send up to 16 pools; phones keep 4-8, the loop stops at _KamionLampCount).
float4 _KamionLampPos[16];
float4 _KamionLampAxis[16];
float4 _KamionLampSodium;
float _KamionLampSpec;
// s20 night-int (review P1-2): night floor near lamps - light from the lamps not in the analytic set, their
// inter-reflections and the urban sky glow, as an irradiance (xyz, exposed LED units like _KamionLampColor) that fades to 0
// at w metres (horizontal) from the nearest chosen luminaire. 0 when lamps are off or the tier sets lampFloorOff.
// ADR 0199: beyond that the floor keeps _KamionLampColor.w × the near level (urban sky glow, 0.03 lx clear / 0.2 lx
// overcast instead of 0).
float4 _KamionLampFloor;
float _KamionHeadlampOn;
float4 _KamionHeadlampLeft, _KamionHeadlampRight, _KamionHeadlampAxisRight, _KamionHeadlampUp,
    _KamionHeadlampForward, _KamionHeadlampColor;

// Footprint radii in mounting heights (ADR 0191, WORKING_VALUE; mirrored in StreetLampOptics.cs).
#define KAMION_LAMP_RA 2.4      // along the road, each way
#define KAMION_LAMP_RS 1.5      // across, carriageway side of the arm
#define KAMION_LAMP_RH 0.7      // across, behind the column
#define KAMION_LAMP_RSYM 1.8    // post-top / no arm
// s20 night-int (review 0191 P1-3: pools read as stage spotlights with a drawn rim): a share TAIL_S of the flux goes to
// a wider footprint (radius TAIL_R x the main one), F = (1-S)(1-r2)^2 + S/R^2 (1-r2/R^2)^2 - same downward flux, nadir
// 0.86 I0, ~3 % of the peak at the old rim fading to 0 at 1.5x (full cutoff now ~74 deg along the road). WORKING_VALUE.
#define KAMION_LAMP_TAIL_S 0.25
#define KAMION_LAMP_TAIL_R 1.5

// night-pc-s23 (replaces the ADR 0108 r2 symmetric cone): dipped beam for right-hand traffic shaped to UN R112 class B
// (Annex 3 table, mlit.go.jp/jidosha/un/UN_R112.pdf p. 23: 75R/50R >= 10 100 cd, 50V >= 5 100, 25L/25R >= 1 700,
// zone IV >= 2 500, 50L <= 13 200, 75L <= 10 600, B50L <= 350, zone III <= 625). Mirrored in HeadlampBeam.cs (EditMode
// test checks those points). Angles as slopes (tan) in the cab frame; the horizontal cut-off sits KAMION_BEAM_AIM below
// the horizon (vehicle aim, WORKING_VALUE; UN R48 6.2.6.1.1 range UNVERIFIED), right of the elbow it rises at 15 deg up
// to KAMION_BEAM_RISE. I/Ipk = H(h) * V(below cut-off) or a stray floor above it. Ipk = the preset's peak cd. No occlusion.
#define KAMION_BEAM_AIM 0.015
#define KAMION_BEAM_RISE 0.0274       // cut-off right of the elbow at most ~1.57 deg above the elbow
#define KAMION_BEAM_HOT 0.02          // hot spot ~1.15 deg right of V (75R / 50R)
#define KAMION_BEAM_RANGE2 22500.0    // fade to 0 at 150 m
float KamionHeadlampRelI(float h, float v)
{
    float cut = -KAMION_BEAM_AIM + min(max(h, 0.0) * 0.267949, KAMION_BEAM_RISE);
    float below = cut - v;                                      // > 0 under the cut-off
    float hc = h - KAMION_BEAM_HOT;
    float hs = 0.75 * exp(-hc * hc * 138.89) + 0.25 * exp(-h * h * 6.3776);   // sigma 0.06 core, 0.28 spread
    float edge = smoothstep(-0.002, 0.003, below);
    float core = 0.05 + 0.95 * exp(-max(below - 0.008, 0.0) * 25.0);
    float stray = 0.012 * saturate(1.0 + below * 20.0) * (0.3 + 0.7 * hs);
    float lower = saturate((v + 0.35) * 10.0);                  // the truck's own front below ~-19 deg
    return max(hs * core * edge, stray) * lower * saturate(1.0 - abs(h) * 0.9);
}

// Relative intensity / d^2 towards positionWS and the unit vector to the source (for diffuse and GGX).
float KamionHeadlampCone(float3 positionWS, float3 source, out float3 l)
{
    float3 ray = positionWS-source;
    float forward = dot(ray, _KamionHeadlampForward.xyz);
    float d2 = max(dot(ray, ray), 1.0);
    l = -ray * rsqrt(d2);
    if (forward <= 0.5) return 0.0;
    float invForward = rcp(forward);
    float h = dot(ray, _KamionHeadlampAxisRight.xyz)*invForward;
    float v = dot(ray, _KamionHeadlampUp.xyz)*invForward;
    float rangeWindow = saturate(1.0-d2*d2/(KAMION_BEAM_RANGE2*KAMION_BEAM_RANGE2));
    return KamionHeadlampRelI(h, v)*rangeWindow/d2;
}

// s20 night-int: night floor irradiance at a point whose nearest chosen luminaire is sqrt(near2) m away (horizontal);
// sky-facing surfaces get all of it, walls half, undersides a quarter (light from above and around). Smooth fade at
// _KamionLampFloor.w metres down to the far level _KamionLampColor.w (ADR 0199), so streets away from lamps stay dark
// but not black.
float3 KamionLampFloor(float near2, half3 n)
{
    float fade = saturate(1.0 - near2 / max(_KamionLampFloor.w * _KamionLampFloor.w, 1.0));
    return _KamionLampFloor.rgb * (lerp(_KamionLampColor.w, 1.0, fade * fade) * (0.5 + 0.5 * n.y * (n.y > 0.0 ? 1.0 : 0.5)));
}

// Relative intensity towards positionWS (I / I0 times the fade weight) and the unit vector to the luminaire.
float KamionLampIntensity(float4 lp, float4 ax, float3 positionWS, out float3 l, out float d2)
{
    float3 dv = lp.xyz - positionWS;
    d2 = max(dot(dv, dv), 0.25);
    float invD = rsqrt(d2);
    l = dv * invD;
    float h = dv.y;                                   // height of the luminaire above the point
    if (h <= 0.05) return 0.0;                        // full cutoff: nothing at or above the horizontal
    float invH = rcp(h);
    float2 g = -dv.xz * invH;                         // ground offset in mounting heights
    float across = dot(g, ax.xy);
    float along = g.x * ax.y - g.y * ax.x;
    float rc = ax.w > 0.5 ? (across > 0.0 ? KAMION_LAMP_RS : KAMION_LAMP_RH) : KAMION_LAMP_RSYM;
    float ra = ax.w > 0.5 ? KAMION_LAMP_RA : KAMION_LAMP_RSYM;
    float2 q = float2(along / ra, across / rc);
    float r2 = dot(q, q);
    float f = saturate(1.0 - r2);
    float ft = saturate(1.0 - r2 * (1.0 / (KAMION_LAMP_TAIL_R * KAMION_LAMP_TAIL_R)));
    float dh = d2 * invD * invH;                      // d / h = 1 / cos γ
    return lp.w * ((1.0 - KAMION_LAMP_TAIL_S) * f * f
        + (KAMION_LAMP_TAIL_S / (KAMION_LAMP_TAIL_R * KAMION_LAMP_TAIL_R)) * ft * ft) * dh * dh * dh;
}

// Diffuse irradiance (times the exposed LED colour) to multiply with the diffuse albedo (probes, simple surfaces).
half3 KamionLampPools(float3 positionWS, half3 n)
{
    float3 pool = 0.0;
    float3 floorLight = 0.0;
    if (_KamionLampCount > 0.5)
    {
        int lampCount = (int)_KamionLampCount;
        float near2 = 1e8;
        for (int li = 0; li < 16; li++)
        {
            if (li >= lampCount) break;
            float4 ax = _KamionLampAxis[li];
            float3 l; float d2;
            float i = KamionLampIntensity(_KamionLampPos[li], ax, positionWS, l, d2);
            float3 tint = lerp(float3(1.0, 1.0, 1.0), _KamionLampSodium.rgb, ax.z);
            pool += tint * (i * saturate(dot(n, l)) / d2);
            float2 hz = _KamionLampPos[li].xz - positionWS.xz;
            near2 = min(near2, dot(hz, hz));
        }
        floorLight = KamionLampFloor(near2, n);
    }
    float3 lighting = _KamionLampColor.rgb * pool + floorLight;
    if (_KamionHeadlampOn > 0.5)
    {
        float3 hl, hr;
        float il = KamionHeadlampCone(positionWS, _KamionHeadlampLeft.xyz, hl);
        float ir = KamionHeadlampCone(positionWS, _KamionHeadlampRight.xyz, hr);
        lighting += _KamionHeadlampColor.rgb * (il * saturate(dot(n, hl)) + ir * saturate(dot(n, hr)));
    }
    return (half3)lighting;
}

// ADR 0191: diffuse + GGX (same normalisation as the sun term of the world shaders) of the lamp pools. The highlight
// - the long bright streak of a lamp on asphalt towards the viewer - runs only where _KamionLampSpec is on (tier flag).
half3 KamionLampPoolsLit(float3 positionWS, half3 n, float3 V, half r, half r2, half3 diffColor, half3 specColor)
{
    float3 dif = 0.0, spc = 0.0;
    float3 floorLight = 0.0;
    if (_KamionLampCount > 0.5)
    {
        int lampCount = (int)_KamionLampCount;
        bool useSpec = _KamionLampSpec > 0.5;
        float near2 = 1e8;
        for (int li = 0; li < 16; li++)
        {
            if (li >= lampCount) break;
            float4 ax = _KamionLampAxis[li];
            float3 l; float d2;
            float i = KamionLampIntensity(_KamionLampPos[li], ax, positionWS, l, d2);
            float2 hz = _KamionLampPos[li].xz - positionWS.xz;
            near2 = min(near2, dot(hz, hz));
            float3 tint = lerp(float3(1.0, 1.0, 1.0), _KamionLampSodium.rgb, ax.z);
            float e = i * saturate(dot(n, l)) / d2;
            dif += tint * e;
            if (useSpec)
            {
                float3 H = SafeNormalize(l + V);
                float NoH = saturate(dot(n, H));
                float LoH = saturate(dot(l, H));
                float dd = NoH * NoH * (r2 - 1.0) + 1.00001;
                spc += tint * (e * r2 / ((dd * dd) * max(0.1, LoH * LoH) * (r * 4.0 + 2.0)));
            }
        }
        floorLight = KamionLampFloor(near2, n);
    }
    float3 lighting = _KamionLampColor.rgb * (dif * diffColor + spc * specColor) + floorLight * diffColor;
    if (_KamionHeadlampOn > 0.5)
    {
        // night-pc-s23: diffuse + (tier flag _KamionLampSpec) the GGX highlight of the two dipped beams, same
        // normalisation as the pools - the sheen of the own beam on dry asphalt, the glare streak when wet.
        float3 hl, hr;
        float il = KamionHeadlampCone(positionWS, _KamionHeadlampLeft.xyz, hl);
        float ir = KamionHeadlampCone(positionWS, _KamionHeadlampRight.xyz, hr);
        float el = il * saturate(dot(n, hl)), er = ir * saturate(dot(n, hr));
        float3 hlit = (el + er) * diffColor;
        if (_KamionLampSpec > 0.5 && el + er > 0.0)
        {
            float3 H = SafeNormalize(hl + V);
            float NoH = saturate(dot(n, H)), LoH = saturate(dot(hl, H));
            float dd = NoH * NoH * (r2 - 1.0) + 1.00001;
            float s = el * r2 / ((dd * dd) * max(0.1, LoH * LoH) * (r * 4.0 + 2.0));
            H = SafeNormalize(hr + V);
            NoH = saturate(dot(n, H)); LoH = saturate(dot(hr, H));
            dd = NoH * NoH * (r2 - 1.0) + 1.00001;
            s += er * r2 / ((dd * dd) * max(0.1, LoH * LoH) * (r * 4.0 + 2.0));
            hlit += s * specColor;
        }
        lighting += _KamionHeadlampColor.rgb * hlit;
    }
    return (half3)lighting;
}

#endif
