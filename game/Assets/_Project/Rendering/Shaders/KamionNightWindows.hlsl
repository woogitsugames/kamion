// ADR 0192: lit windows at dusk / night (Kamion/World PBR _NIGHTWIN, Kamion/World Surface _FAR_FACADE).
// - Which window a pixel belongs to: the window cell centre is known in UV (atlas id texture, or the bay grid of the
//   far facades); its position on the facade comes from the screen derivatives of the (affine, per triangle) UV ->
//   position map, so every pixel of one window computes the same anchor without any mesh data. The anchor is taken
//   in object space (independent of the camera and of floating-origin shifts) and hashed on a 1 m lattice: the
//   decision is fixed per window, frame after frame (no flicker); derivative noise is ~1e-4 m, so a window sits
//   within reach of a lattice edge with p ~ 1e-4.
// - Lit or dark: windows of one flat (6 m x one storey cell) switch together (P(window | flat lit) 0.75, stray rooms
//   0.06); offices by floor (20 m cells), halls by 30 m cells; stairwells alone. Shares per class come from
//   NightWindows.cs (sun elevation), the switch-on is progressive (h < p x on): no checkerboard, no global pulse.
// - Light: colour temperature per window (2700 / 3200 / 4000 K by class), luminance x 0.55-1.45 per window,
//   x pane transmission (clear glass shows the room, net curtains glow, blinds / drapes mostly block and tint).
// WORKING_VALUE shares and luminance (see NightWindows.cs).
#ifndef KAMION_NIGHT_WINDOWS_INCLUDED
#define KAMION_NIGHT_WINDOWS_INCLUDED

float4 _KamionWindows;      // share of lit windows: x flat, y office, z hall, w stairwell (already x switch-on)
float4 _KamionWindowsLum;   // x mean lit-window luminance x exposure (display units), y > 0 = on

uint KamionNwHash(int3 c, uint salt)
{
    uint h = (uint)c.x * 73856093u ^ (uint)c.y * 19349663u ^ (uint)c.z * 83492791u ^ salt * 2654435761u;
    h ^= h >> 16; h *= 2246822519u; h ^= h >> 13; h *= 3266489917u; h ^= h >> 16;
    return h;
}
float KamionNwU(uint h) { return (h & 0xFFFFFFu) * (1.0 / 16777216.0); }

// Position (space of `base`) of the UV point c, from a pixel at uv; dRel* = screen derivatives of a camera-relative
// position (precise), dUv* of the UV. Degenerate (edge-on) triangles keep the pixel's own position.
float3 KamionNwAnchor(float3 base, float3 dRelX, float3 dRelY, float2 uv, float2 dUvX, float2 dUvY, float2 c)
{
    float det = dUvX.x * dUvY.y - dUvY.x * dUvX.y;
    if (abs(det) < 1e-12) return base;
    float2 d = c - uv;
    float a = (dUvY.y * d.x - dUvY.x * d.y) / det;
    float b = (-dUvX.y * d.x + dUvX.x * d.y) / det;
    return base + dRelX * a + dRelY * b;
}

half3 KamionNwColour(float cls, float u)
{
    // linear Rec.709, luminance 1: 2700 K, 3200 K, 4000 K, 4500 K (CIE daylight / Planck locus, rounded)
    const half3 k2700 = half3(1.35, 0.93, 0.52), k3200 = half3(1.25, 0.96, 0.66), k4000 = half3(1.12, 0.99, 0.85),
                k4500 = half3(1.07, 1.0, 0.92);
    if (cls < 1.5) return u < 0.62 ? k2700 : (u < 0.88 ? k3200 : k4000);
    if (cls < 2.5) return u < 0.5 ? k4000 : k2700;
    if (cls < 3.5) return u < 0.8 ? k4000 : k3200;
    return k4500;
}

// Emitted display colour of one window pixel. anchor: window centre (object space); cls 1 flat, 2 stairwell,
// 3 office, 4 hall (float); trn: pane transmission (0 frame / wall); cov: fabric coverage (tints by the albedo there).
half3 KamionNightWindow(float3 anchor, float cls, half trn, half cov, half3 albedo)
{
    if (cls < 0.5 || trn <= 0.004h) return 0;   // cls is a float: an int next to half math hits D3D11 X8000 (min-precision int)
    int3 w = (int3)floor(anchor);
    uint hw = KamionNwHash(w, 11u);
    float p, inLit = 0.75, stray = 0.06;
    float3 group = float3(6.0, 2.8, 6.0);
    if (cls < 1.5) p = _KamionWindows.x;
    else if (cls < 2.5) { p = _KamionWindows.w; group = float3(1.0, 1.0, 1.0); inLit = 1.0; stray = 0.0; }
    else if (cls < 3.5) { p = _KamionWindows.y; group = float3(20.0, 3.3, 20.0); inLit = 0.85; stray = 0.04; }
    else { p = _KamionWindows.z; group = float3(30.0, 6.0, 30.0); inLit = 0.8; stray = 0.0; }
    // flat / floor lit with q so that the window share stays p: p = q inLit + (1 - q) stray
    float q = saturate((p - stray) / max(inLit - stray, 1e-3));
    uint hg = KamionNwHash((int3)floor(anchor / group), 23u + (uint)(cls + 0.5));
    bool lit = KamionNwU(hg) < q ? KamionNwU(hw) < inLit : KamionNwU(hw) < stray * saturate(p * 4.0);
    if (!lit) return 0;
    uint hc = KamionNwHash(w, 37u);
    half3 c = KamionNwColour(cls, KamionNwU(hc));
    half k = 0.55h + 0.9h * (half)KamionNwU(hc >> 7);
    // fabric in front of the lamp passes its own colour (red drapes glow red), normalised to luminance 1
    half la = max(dot(albedo, half3(0.2126h, 0.7152h, 0.0722h)), 0.02h);
    half3 tint = lerp(half3(1, 1, 1), clamp(albedo / la, 0.0h, 2.5h), cov * 0.8h);
    return c * tint * (trn * k * (half)_KamionWindowsLum.x);
}

#endif
