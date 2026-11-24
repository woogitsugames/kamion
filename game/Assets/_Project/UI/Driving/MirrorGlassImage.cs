using Game.Cameras;
using Game.Controls;
using UnityEngine;
using UnityEngine.UI;

namespace Game.UI.Driving
{
    /// <summary>
    /// ADR 0340 (D70: the class II mirrors as fixed windows): the mirror picture drawn as a piece of slightly convex glass
    /// instead of a flat picture-in-picture rectangle. One draw call, no shader of its own (the default UI material):
    /// <list type="bullet">
    /// <item>the quad is a small grid whose UVs are barrel-mapped - the centre is magnified by 1 / (1 + k r_corner^2), the
    /// corners stay on the texture corners, so nothing outside the render texture is sampled and nothing is cropped;</item>
    /// <item>the vertex colour darkens towards the rim (vignette of a recessed glass under a housing lip).</item>
    /// </list>
    /// The grid is rebuilt only when the rect, the texture or a parameter changes (uGUI dirty flags), never per frame.
    /// </summary>
    public sealed class MirrorGlassImage : RawImage
    {
        /// <summary>Grid cells across / along (portrait glass). 8 x 14 = 135 vertices, 224 triangles per mirror.</summary>
        public const int CellsX = 8, CellsY = 14;
        /// <summary>Barrel strength k (uv scale = (1 + k r^2) / (1 + k r_corner^2), r in half-heights). WORKING_VALUE: a
        /// class II main mirror is only slightly convex (UN R46 allows r >= 1200 mm for class II; UNVERIFIED here), so the
        /// distortion is kept just visible on straight edges (kerb line, trailer side), not a fisheye.</summary>
        public const float DefaultCurvature = MirrorWindowLayout.GlassCurvature;
        /// <summary>Darkening at the glass corners (0 = none). WORKING_VALUE.</summary>
        public const float DefaultVignette = MirrorWindowLayout.GlassVignette;

        [SerializeField] float m_Curvature = DefaultCurvature;
        [SerializeField] float m_Vignette = DefaultVignette;

        public float Curvature
        {
            get => m_Curvature;
            set { if (m_Curvature != value) { m_Curvature = value; SetVerticesDirty(); } }
        }

        public float Vignette
        {
            get => m_Vignette;
            set { if (m_Vignette != value) { m_Vignette = value; SetVerticesDirty(); } }
        }

        protected override void OnPopulateMesh(VertexHelper vh)
        {
            vh.Clear();
            Rect r = GetPixelAdjustedRect();
            if (r.width <= 0f || r.height <= 0f) return;
            float aspect = r.width / r.height;
            Rect uv = uvRect;
            Color32 c = color;
            for (int j = 0; j <= CellsY; j++)
            {
                float t = j / (float)CellsY;
                for (int i = 0; i <= CellsX; i++)
                {
                    float s = i / (float)CellsX;
                    Vector2 b = MirrorWindowLayout.Barrel(s, t, aspect, m_Curvature);
                    float sh = MirrorWindowLayout.GlassShade(s, t, m_Vignette);
                    var col = new Color32((byte)(c.r * sh), (byte)(c.g * sh), (byte)(c.b * sh), c.a);
                    vh.AddVert(new Vector3(r.xMin + s * r.width, r.yMin + t * r.height),
                        col, new Vector2(uv.xMin + b.x * uv.width, uv.yMin + b.y * uv.height));
                }
            }
            int row = CellsX + 1;
            for (int j = 0; j < CellsY; j++)
            for (int i = 0; i < CellsX; i++)
            {
                int a = j * row + i;
                vh.AddTriangle(a, a + row, a + row + 1);
                vh.AddTriangle(a, a + row + 1, a + 1);
            }
        }
    }

    /// <summary>
    /// ADR 0340: the procedural parts of a mirror window - the housing ring (dark moulded plastic with a rounded outline, a
    /// soft top-lit bevel and a gasket shadow where the glass sits) and the glass film (dust held along the lower edge and
    /// in the corners, a few specks, the lip's shadow at the top). Generated once, shared by both windows; no asset files,
    /// no brand marks.
    /// </summary>
    public static class MirrorWindowArt
    {
        /// <summary>Housing ring width [canvas units] on the monitor / touch layouts. The window rect does not change: the ring
        /// lies inside it. WORKING_VALUE (owner to judge on the build).</summary>
        public const float HousingDesktop = 7f, HousingTouch = 6f;
        /// <summary>Outer corner radius of the housing [canvas units]. WORKING_VALUE.</summary>
        public const float CornerRadius = 11f;

        const int RingPx = 96;         // texture size; 2 px per canvas unit
        const float PxPerUnit = 2f;
        static Sprite s_RingDesktop, s_RingTouch;
        static Texture2D s_Film;

        /// <summary>Nine-sliced housing ring for a ring width of <paramref name="housing"/> canvas units.</summary>
        public static Sprite Ring(bool desktop)
        {
            if (desktop) return s_RingDesktop != null ? s_RingDesktop : (s_RingDesktop = BuildRing(HousingDesktop));
            return s_RingTouch != null ? s_RingTouch : (s_RingTouch = BuildRing(HousingTouch));
        }

        /// <summary>Signed distance to a rounded rectangle centred in an n x n square (negative inside), in pixels.</summary>
        static float RoundRect(float x, float y, float n, float inset, float radius)
        {
            float h = n * 0.5f - inset;
            float qx = Mathf.Abs(x - n * 0.5f) - (h - radius), qy = Mathf.Abs(y - n * 0.5f) - (h - radius);
            float ox = Mathf.Max(qx, 0f), oy = Mathf.Max(qy, 0f);
            return Mathf.Sqrt(ox * ox + oy * oy) + Mathf.Min(Mathf.Max(qx, qy), 0f) - radius;
        }

        static Sprite BuildRing(float housing)
        {
            int n = RingPx;
            float w = housing * PxPerUnit, ro = CornerRadius * PxPerUnit, ri = Mathf.Max(2f, ro - w * 0.75f);
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear, name = "MirrorHousingRing" };
            tex.hideFlags = HideFlags.HideAndDontSave;
            var px = new Color32[n * n];
            Color body = UiPalette.MirrorBezel;
            for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float fx = x + 0.5f, fy = y + 0.5f;
                float dOut = RoundRect(fx, fy, n, 0f, ro);          // < 0 inside the housing outline
                float dIn = RoundRect(fx, fy, n, w, ri);            // < 0 inside the glass opening
                float aOut = Mathf.Clamp01(0.5f - dOut), aIn = Mathf.Clamp01(0.5f + dIn);
                float ring = aOut * aIn;
                // Moulded edge: lit from above (texture y up), the outer 2 px roll away, the inner lip is in shadow.
                float across = Mathf.Clamp01(-dOut / w);            // 0 at the outer edge .. 1 at the glass
                float up = (fy / n - 0.5f) * 2f;                    // -1 bottom .. +1 top
                float roll = Mathf.Clamp01(-dOut / 2.5f);           // outer chamfer
                float l = 0.86f + 0.20f * up * (1f - across) + 0.10f * (1f - Mathf.Abs(across - 0.35f) * 2.2f);
                l *= 0.72f + 0.28f * roll;
                l *= 1f - 0.55f * Mathf.Clamp01(1f - dIn / 2.2f);   // gasket shadow against the glass
                // Shadow the lip casts onto the glass just inside the opening (soft, strongest under the top edge).
                float cast = Mathf.Clamp01(1f + dIn / 5f) * (1f - aIn) * (0.20f + 0.16f * Mathf.Max(0f, up));
                float a = Mathf.Max(ring * body.a, cast * aOut);
                Color col = ring > 0.001f ? new Color(body.r * l, body.g * l, body.b * l) : new Color(0f, 0f, 0f);
                px[y * n + x] = new Color32((byte)(Mathf.Clamp01(col.r) * 255f), (byte)(Mathf.Clamp01(col.g) * 255f), (byte)(Mathf.Clamp01(col.b) * 255f), (byte)(Mathf.Clamp01(a) * 255f));
            }
            tex.SetPixels32(px);
            tex.Apply(false, true);
            float b = Mathf.Ceil(Mathf.Max(ro, w + 6f));            // slice border [px]: corner + lip shadow
            var sp = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), 100f * PxPerUnit, 0, SpriteMeshType.FullRect, new Vector4(b, b, b, b));
            sp.hideFlags = HideFlags.HideAndDontSave;
            return sp;
        }

        static float Hash(int x, int y, int seed)
        {
            unchecked
            {
                uint h = (uint)(x * 374761393 + y * 668265263 + seed * 1274126177);
                h = (h ^ (h >> 13)) * 1274126177u;
                return ((h ^ (h >> 16)) & 0xFFFFFF) / 16777215f;
            }
        }

        static float ValueNoise(float x, float y, int seed)
        {
            int xi = Mathf.FloorToInt(x), yi = Mathf.FloorToInt(y);
            float fx = x - xi, fy = y - yi;
            fx = fx * fx * (3f - 2f * fx); fy = fy * fy * (3f - 2f * fy);
            float a = Hash(xi, yi, seed), b = Hash(xi + 1, yi, seed), c = Hash(xi, yi + 1, seed), d = Hash(xi + 1, yi + 1, seed);
            return Mathf.Lerp(Mathf.Lerp(a, b, fx), Mathf.Lerp(c, d, fx), fy);
        }

        /// <summary>
        /// Glass film (RGBA, 96 x 176): road dust that the airflow leaves on a mirror - denser along the lower edge and the
        /// outer corners, thin in the middle - plus a few dried droplet marks. Peak alpha ~0.16 at the very bottom rim,
        /// &lt; 0.03 over the middle third: the view stays usable (D70), the glass stops being a clean video rectangle.
        /// The same film is used on both windows, the right one flipped. WORKING_VALUE.
        /// </summary>
        public static Texture2D Film()
        {
            if (s_Film != null) return s_Film;
            const int w = 96, h = 176;
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear, name = "MirrorGlassFilm" };
            tex.hideFlags = HideFlags.HideAndDontSave;
            var px = new Color32[w * h];
            // dried droplet marks: position, radius [px]
            const int drops = 9;
            var dx = new float[drops]; var dy = new float[drops]; var dr = new float[drops];
            for (int k = 0; k < drops; k++)
            {
                dx[k] = Hash(k, 11, 5) * w; dy[k] = Mathf.Pow(Hash(k, 23, 5), 1.6f) * h * 0.8f; dr[k] = 1.6f + 2.6f * Hash(k, 37, 5);
            }
            for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float u = x / (float)(w - 1), v = y / (float)(h - 1);
                float low = Mathf.Pow(1f - v, 3.2f);                                   // lower edge
                float side = Mathf.Pow(Mathf.Abs(u - 0.5f) * 2f, 4f) * (0.35f + 0.65f * (1f - v));
                float cloud = 0.55f * ValueNoise(u * 5f, v * 9f, 1) + 0.30f * ValueNoise(u * 13f, v * 22f, 2) + 0.15f * ValueNoise(u * 41f, v * 70f, 3);
                float dust = (0.020f + 0.14f * low + 0.07f * side) * (0.45f + 1.1f * cloud);
                float mark = 0f;
                for (int k = 0; k < drops; k++)
                {
                    float d = Mathf.Sqrt((x - dx[k]) * (x - dx[k]) + (y - dy[k]) * (y - dy[k])) / dr[k];
                    // a ring (the rim of a dried drop), faint inside
                    mark = Mathf.Max(mark, Mathf.Clamp01(1f - Mathf.Abs(d - 0.85f) * 3.5f) * 0.07f + Mathf.Clamp01(1f - d) * 0.02f);
                }
                float a = Mathf.Clamp01(dust + mark);
                // warm grey dust (the project dirt colour family), not white haze
                px[y * w + x] = new Color32(168, 158, 142, (byte)(a * 255f));
            }
            tex.SetPixels32(px);
            tex.Apply(false, true);
            s_Film = tex;
            return tex;
        }
    }
}
