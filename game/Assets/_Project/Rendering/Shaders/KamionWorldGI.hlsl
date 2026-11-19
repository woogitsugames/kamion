// Baked ground lighting of the static world (ADR 0064, Game.Rendering.WorldSkyVisibility).
// One bilinear fetch of an RGBA8 map in world XZ: R sky visibility at ground level, G/B ground sun visibility for the
// two baked sun directions, A ground height. No keywords: everything is gated by uniforms (strength 0 = no effect).
// Include after URP Lighting.hlsl.
#ifndef KAMION_WORLD_GI_INCLUDED
#define KAMION_WORLD_GI_INCLUDED

TEXTURE2D(_KamionGIMap); SAMPLER(sampler_KamionGIMap);
float4 _KamionGIRect;     // xy world XZ of the texel-(0,0) corner, zw 1 / extent (m)
float4 _KamionGIHeight;   // x world y of A = 0, y metres per A step, z texel size (m), w strength (0 = off)
float4 _KamionGISun;      // x, y weight of the G, B channel for the live sun, z far shadows on, w occluder bounce
#define KAMION_GI_EDGE_FADE_M 120.0   // ADR 0298: WORKING_VALUE

// ambientK: multiplies the SH ambient and the environment reflection (sky visibility; occluded directions return
//           `bounce` of the sky radiance they hide).
// bakedSun: ground sun visibility, to be blended in where the realtime shadows fade out (KamionFarShadow).
void KamionWorldGI(float3 pw, half3 nGeo, out half ambientK, out half bakedSun)
{
    ambientK = 1.0h;
    bakedSun = 1.0h;
    if (_KamionGIHeight.w <= 0.0) return;

    // Up-facing surfaces read their own texel; walls read the ground 1.5 texels in front of them (what faces the wall
    // occludes that ground as well).
    half up = saturate(nGeo.y * 2.5h - 1.25h);                 // 1 above n.y 0.9, 0 below n.y 0.5
    float2 nh = nGeo.xz;
    float lh = length(nh);
    float2 off = lh > 1e-3 ? nh * (1.5 * _KamionGIHeight.z / lh) * (1.0 - up) : float2(0.0, 0.0);
    float2 uv = (pw.xz + off - _KamionGIRect.xy) * _KamionGIRect.zw;
    // ADR 0298 (review 2026-11-18 N1): the map stopped with a step at the tile edge - the apron / neighbouring tile got
    // full sky visibility at once (one of the causes of the 15-22 level seam). Outside the rect the border texel holds and
    // is held (blurred over KAMION_GI_EDGE_FADE_M); baked sun shadows fade within 24 m.
    float2 halfTexel = 0.5 * _KamionGIHeight.z * _KamionGIRect.zw;
    float2 uvc = clamp(uv, halfTexel, 1.0 - halfTexel);
    float outM = length(max(abs(uv - 0.5) - 0.5, 0.0) / max(_KamionGIRect.zw, 1e-9));
    // Outside: a blurred border (up to mip 6 = 64 texels) so a house or tree on the edge does not smear a streak outwards,
    // held at full strength - fading to "open sky" made the apron 10-20 % brighter in ambient than the open fields of the
    // tile (their baked visibility is < 1: horizon, trees).
    half4 g = outM > 0.0 ? SAMPLE_TEXTURE2D_LOD(_KamionGIMap, sampler_KamionGIMap, uvc, 6.0 * saturate(outM / KAMION_GI_EDGE_FADE_M))
                         : SAMPLE_TEXTURE2D(_KamionGIMap, sampler_KamionGIMap, uv);
    half inside = (half)_KamionGIHeight.w;
    half insideSun = (half)(1.0 - smoothstep(0.0, 24.0, outM)) * (half)_KamionGIHeight.w;   // baked shadows: 24 m only

    float ground = _KamionGIHeight.x + g.a * 255.0 * _KamionGIHeight.y;
    half hag = (half)(pw.y - ground);                          // height above the baked ground
    // Up-facing: ground, kerbs, aprons, dock floors (< 1.5 m); roofs and decks (> 3 m) see the open sky.
    half nearGround = 1.0h - saturate((hag - 1.5h) / 1.5h);
    // Walls: the ground at the foot of a lone wall sees half the sky (vis 0.5) - normalise that away so only what
    // faces the wall (opposite hall, trees, parked trailers) darkens it; fade out up the wall (6 m).
    half visWall = lerp(saturate(g.r * 2.0h), 1.0h, saturate(hag / 6.0h));
    half visUp = lerp(1.0h, g.r, nearGround);
    half vis = lerp(1.0h, lerp(visWall, visUp, up), inside);
    ambientK = vis + (1.0h - vis) * (half)_KamionGISun.w;

    half sunRaw = g.g * (half)_KamionGISun.x + g.b * (half)_KamionGISun.y + (1.0h - (half)(_KamionGISun.x + _KamionGISun.y));
    half sunApply = insideSun * (half)_KamionGISun.z * lerp(1.0h - saturate(hag), nearGround, up);   // walls: foot only
    bakedSun = lerp(1.0h, sunRaw, sunApply);
}

// Realtime shadow attenuation extended by the baked ground shadow where the cascades fade out.
half KamionFarShadow(half realtimeShadow, half bakedSun, float3 pw)
{
#if defined(_MAIN_LIGHT_SHADOWS) || defined(_MAIN_LIGHT_SHADOWS_CASCADE) || defined(_MAIN_LIGHT_SHADOWS_SCREEN)
    half fade = GetMainLightShadowFade(pw);
#else
    half fade = 1.0h;
#endif
    return min(realtimeShadow, lerp(1.0h, bakedSun, fade));
}

#endif
