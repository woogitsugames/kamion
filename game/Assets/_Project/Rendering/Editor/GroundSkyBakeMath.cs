using System;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;

namespace Game.Rendering.Editor
{
    /// <summary>
    /// BakeGrid math of the ADR 0064 ground lighting bake (Game.World.Import.WorldSkyBake rasterises the world into a
    /// <see cref="BakeGrid"/> and packs the result into the map of <see cref="WorldSkyVisibility"/>). Region-root XZ, metres.
    /// </summary>
    public static class GroundSkyBakeMath
    {
        /// <summary>Sky light through a tree crown seen from below (gap fraction of urban broadleaf crowns). WORKING_VALUE.</summary>
        public const float CrownSkyTransmittance = 0.3f;
        /// <summary>Sun extinction inside a crown (1/m): 3 m of crown = 0.35 transmitted (dappled). WORKING_VALUE.</summary>
        public const float CrownSunExtinction = 0.35f;
        public const float NoData = -1e6f;

        public sealed class BakeGrid
        {
            public int W, H;
            public float X0, Z0, Texel;
            public float[] Ground, Top, CrownBot, CrownTop;
            /// <summary>Texels covered by a carriageway (reference for <see cref="NormaliseToRoads"/>).</summary>
            public bool[] Road;

            public BakeGrid(float x0, float z0, int w, int h, float texel)
            {
                X0 = x0; Z0 = z0; W = w; H = h; Texel = texel;
                Ground = Fill(w * h, float.PositiveInfinity);
                Top = Fill(w * h, NoData);
                CrownBot = Fill(w * h, float.PositiveInfinity);
                CrownTop = Fill(w * h, NoData);
                Road = new bool[w * h];
            }

            static float[] Fill(int n, float v) { var a = new float[n]; for (int i = 0; i < n; i++) a[i] = v; return a; }

            public int Index(float x, float z)
            {
                int ix = (int)Math.Floor((x - X0) / Texel), iz = (int)Math.Floor((z - Z0) / Texel);
                if (ix < 0 || iz < 0 || ix >= W || iz >= H) return -1;
                return iz * W + ix;
            }
        }

        public enum Kind { Ground, Road, Solid, Crown, Skip }

        public static void Splat(BakeGrid g, Vector3 a, Vector3 b, Vector3 c, Kind k)
        {
            if (k == Kind.Ground || k == Kind.Road)
            {
                Vector3 nrm = Vector3.Cross(b - a, c - a);
                float len = nrm.magnitude;
                if (len < 1e-8f || Mathf.Abs(nrm.y) / len < 0.3f) return;   // skirts, kerb faces, walls of ditches
            }
            float e = Mathf.Max((b - a).magnitude, Mathf.Max((c - a).magnitude, (c - b).magnitude));
            int n = Mathf.Max(1, Mathf.CeilToInt(e / (g.Texel * 0.5f)));
            if (n > 4096) n = 4096;
            float inv = 1f / n;
            for (int i = 0; i <= n; i++)
                for (int j = 0; j <= n - i; j++)
                {
                    Vector3 p = a + (b - a) * (i * inv) + (c - a) * (j * inv);
                    int q = g.Index(p.x, p.z);
                    if (q < 0) continue;
                    switch (k)
                    {
                        case Kind.Ground: if (p.y < g.Ground[q]) g.Ground[q] = p.y; break;
                        case Kind.Road: if (p.y < g.Ground[q]) g.Ground[q] = p.y; g.Road[q] = true; break;
                        case Kind.Solid: if (p.y > g.Top[q]) g.Top[q] = p.y; break;
                        case Kind.Crown:
                            if (p.y > g.CrownTop[q]) g.CrownTop[q] = p.y;
                            if (p.y < g.CrownBot[q]) g.CrownBot[q] = p.y;
                            break;
                    }
                }
        }

        public static void Disc(BakeGrid g, float cx, float cz, float r, float bot, float top)
        {
            int x0 = Mathf.FloorToInt((cx - r - g.X0) / g.Texel), x1 = Mathf.FloorToInt((cx + r - g.X0) / g.Texel);
            int z0 = Mathf.FloorToInt((cz - r - g.Z0) / g.Texel), z1 = Mathf.FloorToInt((cz + r - g.Z0) / g.Texel);
            for (int iz = Math.Max(0, z0); iz <= Math.Min(g.H - 1, z1); iz++)
                for (int ix = Math.Max(0, x0); ix <= Math.Min(g.W - 1, x1); ix++)
                {
                    float x = g.X0 + (ix + 0.5f) * g.Texel - cx, z = g.Z0 + (iz + 0.5f) * g.Texel - cz;
                    float d2 = (x * x + z * z) / (r * r);
                    if (d2 > 1f) continue;
                    // ellipsoid-ish crown: thinner towards the rim
                    float k = Mathf.Sqrt(1f - d2);
                    float mid = (bot + top) * 0.5f, half = (top - bot) * 0.5f * Mathf.Max(0.35f, k);
                    int q = iz * g.W + ix;
                    g.CrownTop[q] = Mathf.Max(g.CrownTop[q], mid + half);
                    g.CrownBot[q] = Mathf.Min(g.CrownBot[q], mid - half);
                }
        }

        public static void FillHoles(BakeGrid g)
        {
            var src = g.Ground;
            for (int pass = 0; pass < 64; pass++)
            {
                int holes = 0;
                var dst = (float[])src.Clone();
                for (int z = 0; z < g.H; z++)
                    for (int x = 0; x < g.W; x++)
                    {
                        int q = z * g.W + x;
                        if (!float.IsPositiveInfinity(src[q])) continue;
                        float s = 0f; int n = 0;
                        for (int dz = -1; dz <= 1; dz++)
                            for (int dx = -1; dx <= 1; dx++)
                            {
                                int xx = x + dx, zz = z + dz;
                                if (xx < 0 || zz < 0 || xx >= g.W || zz >= g.H) continue;
                                float v = src[zz * g.W + xx];
                                if (!float.IsPositiveInfinity(v)) { s += v; n++; }
                            }
                        if (n > 0) dst[q] = s / n; else holes++;
                    }
                src = dst;
                if (holes == 0) break;
            }
            for (int i = 0; i < src.Length; i++) if (float.IsPositiveInfinity(src[i])) src[i] = 0f;
            g.Ground = src;
        }

        // Horizon march: every metre to 32 m (thin noise barriers / fence walls are not skipped), then 2 m to 64 m, 4 m to 120 m.
        static readonly float[] k_Steps = BuildSteps();
        static float[] BuildSteps()
        {
            var l = new System.Collections.Generic.List<float>();
            for (float d = 1f; d <= 32f; d += 1f) l.Add(d);
            for (float d = 34f; d <= 64f; d += 2f) l.Add(d);
            for (float d = 68f; d <= 120f; d += 4f) l.Add(d);
            return l.ToArray();
        }

        public static float[] SkyVisibility(BakeGrid g)
        {
            const int az = 16;
            var dirs = new Vector2[az];
            for (int a = 0; a < az; a++) { float t = (a + 0.5f) * Mathf.PI * 2f / az; dirs[a] = new Vector2(Mathf.Cos(t), Mathf.Sin(t)); }
            var vis = new float[g.W * g.H];
            Parallel.For(0, g.H, z =>
            {
                for (int x = 0; x < g.W; x++)
                {
                    int q = z * g.W + x;
                    float y0 = g.Ground[q] + 0.15f;
                    float sum = 0f;
                    for (int a = 0; a < az; a++)
                    {
                        float ts = 0f, tc = 0f;
                        foreach (float d in k_Steps)
                        {
                            int xx = x + (int)Math.Round(dirs[a].x * d / g.Texel), zz = z + (int)Math.Round(dirs[a].y * d / g.Texel);
                            if (xx < 0 || zz < 0 || xx >= g.W || zz >= g.H) break;
                            int p = zz * g.W + xx;
                            float t = (g.Top[p] - y0) / d;
                            if (t > ts) ts = t;
                            if (g.CrownTop[p] > y0)
                            {
                                float tcp = (g.CrownTop[p] - y0) / d;
                                if (tcp > tc) tc = tcp;
                            }
                        }
                        float cs = 1f / (1f + ts * ts);
                        float cc = 1f / (1f + Mathf.Max(ts, tc) * Mathf.Max(ts, tc));
                        sum += cc + CrownSkyTransmittance * (cs - cc);
                    }
                    float v = sum / az;
                    if (g.CrownBot[q] < float.PositiveInfinity && g.CrownTop[q] > y0 && g.CrownBot[q] > y0 - 0.5f)
                        v *= CrownSkyTransmittance + (1f - CrownSkyTransmittance) * 0.25f;   // under the crown (its zenith part)
                    vis[q] = Mathf.Clamp01(v);
                }
            });
            return vis;
        }

        public static float[] SunVisibility(BakeGrid g, Vector3 sunLocal)
        {
            var hd = new Vector2(sunLocal.x, sunLocal.z);
            float hl = hd.magnitude;
            var res = new float[g.W * g.H];
            if (hl < 1e-4f) { for (int i = 0; i < res.Length; i++) res[i] = 1f; return res; }
            hd /= hl;
            float tanEl = sunLocal.y / hl;
            float maxTop = Mathf.Max(g.Top.Max(), g.CrownTop.Max());
            float step = g.Texel * 0.5f;
            Parallel.For(0, g.H, z =>
            {
                for (int x = 0; x < g.W; x++)
                {
                    int q = z * g.W + x;
                    float y0 = g.Ground[q] + 0.2f;
                    float maxD = Mathf.Min(300f, (maxTop - y0) / Mathf.Max(tanEl, 1e-3f));
                    float tr = 1f;
                    float px = g.X0 + (x + 0.5f) * g.Texel, pz = g.Z0 + (z + 0.5f) * g.Texel;
                    for (float d = g.Texel; d <= maxD; d += step)
                    {
                        int p = g.Index(px + hd.x * d, pz + hd.y * d);
                        if (p < 0) break;
                        float yr = y0 + d * tanEl;
                        if (g.Top[p] > yr) { tr = 0f; break; }
                        if (g.CrownTop[p] > yr && g.CrownBot[p] < yr) { tr *= Mathf.Exp(-CrownSunExtinction * step); if (tr < 0.02f) { tr = 0f; break; } }
                    }
                    res[q] = tr;
                }
            });
            return res;
        }

        /// <summary>
        /// Divides the sky visibility by its median over the carriageway texels (clamped to 1) and returns that median.
        /// The asphalt albedo and the exposure (ADR 0010, D23) were calibrated against photos of real streets, which
        /// already include the typical street horizon (buildings, barriers, trees); without this the open carriageway
        /// would darken by that horizon a second time. Contact zones keep their contrast to the open road.
        /// </summary>
        public static float NormaliseToRoads(BakeGrid g, float[] vis)
        {
            var road = Enumerable.Range(0, vis.Length).Where(i => g.Road[i]).Select(i => vis[i]).OrderBy(v => v).ToArray();
            float med = road.Length > 0 ? road[road.Length / 2] : 1f;
            med = Mathf.Clamp(med, 0.5f, 1f);
            for (int i = 0; i < vis.Length; i++) vis[i] = Mathf.Min(1f, vis[i] / med);
            return med;
        }

        public static float[] Box3(BakeGrid g, float[] a)
        {
            var o = new float[a.Length];
            Parallel.For(0, g.H, z =>
            {
                for (int x = 0; x < g.W; x++)
                {
                    float s = 0f; int n = 0;
                    for (int dz = -1; dz <= 1; dz++)
                        for (int dx = -1; dx <= 1; dx++)
                        {
                            int xx = x + dx, zz = z + dz;
                            if (xx < 0 || zz < 0 || xx >= g.W || zz >= g.H) continue;
                            s += a[zz * g.W + xx]; n++;
                        }
                    o[z * g.W + x] = s / n;
                }
            });
            return o;
        }
    }
}
