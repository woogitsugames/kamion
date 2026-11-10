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
    half4 g = SAMPLE_TEXTURE2D(_KamionGIMap, sampler_KamionGIMap, uv);
    half inside = (uv.x > 0.0 && uv.y > 0.0 && uv.x < 1.0 && uv.y < 1.0) ? _KamionGIHeight.w : 0.0h;

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
    half sunApply = inside * (half)_KamionGISun.z * lerp(1.0h - saturate(hag), nearGround, up);   // walls: foot only
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
