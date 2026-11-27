#ifndef KAMION_FAR_RING_INCLUDED
#define KAMION_FAR_RING_INCLUDED

// ADR 0354: far field (ADR 0085) as a ring BEYOND the loaded tiles. WorldStreamer publishes the Unity-world XZ rectangles
// (minX, minZ, maxX, maxZ) of the tiles whose geometry is shown (Activating / Ready); far-field sector renderers carry the
// renderer user value KAMION_FAR_RING_USER_VALUE. A marked far-field pixel is dropped when another loaded tile is strictly
// nearer to it than its own tile (inside a loaded tile the distance is 0, so that case is included): nearest-rectangle
// ownership, two loaded tiles never draw the same backdrop spot and the backdrop never covers real geometry.
// The owner tile is the loaded rectangle containing the renderer's object origin (far-field meshes are region-local:
// origin = tile anchor = tile centre), else origin +- 1024 m (far_field.py half). C# twin + tests: Game.World.Streaming.FarRing.
// Count 0 (no streamer, single-tile scenes, -farRing off): no clip, the old look.

#define KAMION_FAR_RING_USER_VALUE 0x46415252u
#define KAMION_FAR_RING_MAX 16

float4 _KamionFarRects[KAMION_FAR_RING_MAX];
float _KamionFarRectCount;

float KamionFarRectDist(float2 p, float4 r)
{
    float2 d = max(max(r.xy - p, p - r.zw), 0.0);
    return length(d);
}

// Vertex stage: owner centre (xy) of this draw, or a sentinel (z = 0) when the renderer is not a marked far field.
float3 KamionFarRingOwner()
{
    bool marked = unity_RendererUserValue == KAMION_FAR_RING_USER_VALUE && _KamionFarRectCount > 0.5;
    return float3(UNITY_MATRIX_M._m03, UNITY_MATRIX_M._m23, marked ? 1.0 : 0.0);
}

// Fragment stage: true = drop the far-field pixel at world XZ p (owner from KamionFarRingOwner, interpolated constant).
bool KamionFarRingHidden(float2 p, float3 owner)
{
    if (owner.z < 0.5) return false;
    float2 c = owner.xy;
    float dOwn = KamionFarRectDist(p, float4(c - 1024.0, c + 1024.0));
    float dOther = 1.0e30;
    int n = (int)_KamionFarRectCount;
    [loop] for (int i = 0; i < KAMION_FAR_RING_MAX; i++)
    {
        if (i >= n) break;
        float4 r = _KamionFarRects[i];
        float d = KamionFarRectDist(p, r);
        bool own = all(c >= r.xy) && all(c <= r.zw);
        dOwn = own ? d : dOwn;
        dOther = own ? dOther : min(dOther, d);
    }
    return dOther < dOwn - 0.001;
}

#endif
