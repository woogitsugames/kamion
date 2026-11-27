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

        // ------------------------------------------------------------------ mirror head (ADR 0340 addendum, critic build #10 p.8)

        /// <summary>How far the moulded head reaches outside the window rect on every side [canvas units]. The glass and
        /// the window rect do not move (layout tests); the head is drawn around them. WORKING_VALUE.</summary>
        public const float HeadOut = 14f;
        /// <summary>Outer corner radius of the head [canvas units]. WORKING_VALUE.</summary>
        public const float HeadRadius = 27f;
        /// <summary>Mounting arm stub: length (to the hinge barrel's far side) and sprite height [canvas units]. WORKING_VALUE.</summary>
        public const float ArmLength = 68f, ArmHeight = 54f;
        /// <summary>Margin of the head sprite outside the plastic outline (contact shadow on the view) [canvas units].</summary>
        public const float HeadShadow = 4f;

        const int HeadPx = 160;
        static Sprite s_Head, s_Arm;
        static Texture2D s_FilmHead;

        /// <summary>Light on the moulded parts: from above, slightly from the left and the viewer (texture y up).</summary>
        static readonly Vector3 k_Light = new Vector3(-0.28f, 0.74f, 0.61f).normalized;

        static Color32 Plastic(Vector3 n, float grain, float dust)
        {
            Color body = UiPalette.MirrorBezel;
            float diff = Mathf.Max(0f, Vector3.Dot(n, k_Light));
            Vector3 h = (k_Light + Vector3.forward).normalized;
            float spec = Mathf.Pow(Mathf.Max(0f, Vector3.Dot(n, h)), 18f) * 0.42f;
            float l = 0.34f + 1.30f * diff + (grain - 0.5f) * 0.12f;
            // dust settles on the faces that look up (warm grey, the project dirt colour family)
            float d = Mathf.Clamp01(dust * Mathf.Clamp01((n.y - 0.25f) * 1.6f)) * 0.55f;
            float r = Mathf.Lerp(body.r * l + spec, 0.44f, d), g = Mathf.Lerp(body.g * l + spec, 0.41f, d), b = Mathf.Lerp(body.b * l + spec, 0.37f, d);
            return new Color32((byte)(Mathf.Clamp01(r) * 255f), (byte)(Mathf.Clamp01(g) * 255f), (byte)(Mathf.Clamp01(b) * 255f), 255);
        }

        /// <summary>
        /// Nine-sliced mirror head (the moulded housing behind both glasses): rounded outline, a rolled edge lit from above
        /// (pseudo-normal from the outline's distance field), moulding grain, dust on the top face and a soft contact
        /// shadow just outside the outline. Drawn BEHIND the glasses; the lip ring (<see cref="Ring"/>) sits on top.
        /// </summary>
        public static Sprite Head()
        {
            if (s_Head != null) return s_Head;
            int n = HeadPx;
            float m = HeadShadow * PxPerUnit, ro = HeadRadius * PxPerUnit, roll = 10f * PxPerUnit;
            float seam = 0.58f * HeadOut * PxPerUnit;      // parting line of the two housing shells, inside the outline
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear, name = "MirrorHead" };
            tex.hideFlags = HideFlags.HideAndDontSave;
            var px = new Color32[n * n];
            for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float fx = x + 0.5f, fy = y + 0.5f;
                float d = RoundRect(fx, fy, n, m, ro);                              // < 0 inside the plastic
                float gx = RoundRect(fx + 1f, fy, n, m, ro) - RoundRect(fx - 1f, fy, n, m, ro);
                float gy = RoundRect(fx, fy + 1f, n, m, ro) - RoundRect(fx, fy - 1f, n, m, ro);
                float gl = Mathf.Sqrt(gx * gx + gy * gy);
                if (gl > 1e-4f) { gx /= gl; gy /= gl; }
                float t = Mathf.Clamp01(-d / roll);                                 // 0 at the outline .. 1 on the flat face
                float tilt = (1f - t) * (1f - t);                                   // rolled edge
                var nrm = new Vector3(gx * tilt, gy * tilt, 1f - 0.75f * tilt).normalized;
                float inside = Mathf.Clamp01(0.5f - d);
                float grain = 0.5f * Hash(x, y, 17) + 0.5f * ValueNoise(x * 0.35f, y * 0.35f, 19);
                float dust = 0.45f + 0.55f * ValueNoise(x * 0.11f, y * 0.21f, 23);
                Color32 c = Plastic(nrm, grain, dust);
                // parting line: a 1 px groove (dark) with the lower shell's edge catching light just inside it
                float sd = -d - seam;
                float groove = Mathf.Clamp01(1f - Mathf.Abs(sd) / 0.9f), catchL = Mathf.Clamp01(1f - Mathf.Abs(sd - 1.6f) / 0.9f) * Mathf.Max(0f, gy);
                float sk = 1f - 0.42f * groove + 0.30f * catchL;
                c = new Color32((byte)Mathf.Min(255f, c.r * sk), (byte)Mathf.Min(255f, c.g * sk), (byte)Mathf.Min(255f, c.b * sk), 255);
                // contact shadow outside the outline, a little lower than the head (light from above)
                float ds = RoundRect(fx, fy + 2.5f, n, m, ro);
                float sh = Mathf.Clamp01(1f - ds / (m * 0.9f)) * 0.34f;
                float a = inside + (1f - inside) * sh;
                float k = a > 1e-4f ? inside / a : 0f;                              // shadow = black, plastic = its colour
                px[y * n + x] = new Color32((byte)(c.r * k), (byte)(c.g * k), (byte)(c.b * k), (byte)(Mathf.Clamp01(a) * 255f));
            }
            tex.SetPixels32(px);
            tex.Apply(false, true);
            float b = Mathf.Ceil(m + Mathf.Max(ro, roll) + 2f);
            s_Head = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), 100f * PxPerUnit, 0, SpriteMeshType.FullRect, new Vector4(b, b, b, b));
            s_Head.hideFlags = HideFlags.HideAndDontSave;
            return s_Head;
        }

        /// <summary>
        /// Mounting arm stub (drawn for the LEFT window, pointing right towards the cab; the right window mirrors it): a
        /// round tube leaving the head and the vertical hinge barrel it ends in - the same parts as on the modelled TRAKT
        /// mirror (two arms, upper and lower). Own shape, no brand. <see cref="ArmLength"/> x <see cref="ArmHeight"/> units.
        /// </summary>
        public static Sprite Arm()
        {
            if (s_Arm != null) return s_Arm;
            int w = Mathf.RoundToInt(ArmLength * PxPerUnit), h = Mathf.RoundToInt(ArmHeight * PxPerUnit);
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear, name = "MirrorArm" };
            tex.hideFlags = HideFlags.HideAndDontSave;
            var px = new Color32[w * h];
            float cy = h * 0.5f, tube = h * 0.30f;                 // tube half thickness
            float bw = h * 0.21f, bx = w - bw - 2f;                // barrel half width, centre x
            float bh = h * 0.5f - 2f, cap = bw;                    // barrel half height, cap radius
            for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float fx = x + 0.5f, fy = y + 0.5f;
                float grain = 0.5f * Hash(x, y, 31) + 0.5f * ValueNoise(x * 0.4f, y * 0.4f, 37);
                float dust = 0.4f + 0.6f * ValueNoise(x * 0.15f, y * 0.3f, 41);
                // tube (round section across y), up to the barrel
                float ty = (fy - cy) / tube;
                float aTube = fx < bx ? Mathf.Clamp01((1f - Mathf.Abs(ty)) * tube + 0.5f) : 0f;
                // barrel: vertical capsule (round section across x)
                float qy = Mathf.Max(0f, Mathf.Abs(fy - cy) - (bh - cap));
                float dx = fx - bx;
                float dB = Mathf.Sqrt(dx * dx + qy * qy) - bw;
                float aBar = Mathf.Clamp01(0.5f - dB);
                Color32 c;
                float a;
                if (aBar > 0.01f)
                {
                    float sx = Mathf.Clamp(dx / bw, -1f, 1f), sy = Mathf.Clamp(qy / cap, 0f, 1f) * Mathf.Sign(fy - cy);
                    var nrm = new Vector3(sx, sy * 0.8f, Mathf.Sqrt(Mathf.Max(0.02f, 1f - sx * sx - 0.64f * sy * sy))).normalized;
                    c = Plastic(nrm, grain, dust); a = aBar;
                }
                else
                {
                    float sy = Mathf.Clamp(ty, -1f, 1f);
                    var nrm = new Vector3(0f, sy, Mathf.Sqrt(Mathf.Max(0.02f, 1f - sy * sy))).normalized;
                    c = Plastic(nrm, grain, dust); a = aTube;
                    // the barrel shades the tube where they meet; the head shades its root
                    float occl = 1f - 0.45f * Mathf.Clamp01(1f - (bx - bw - fx) / 5f) - 0.35f * Mathf.Clamp01(1f - fx / 7f);
                    c = new Color32((byte)(c.r * occl), (byte)(c.g * occl), (byte)(c.b * occl), 255);
                }
                px[y * w + x] = new Color32(c.r, c.g, c.b, (byte)(Mathf.Clamp01(a) * 255f));
            }
            tex.SetPixels32(px);
            tex.Apply(false, true);
            s_Arm = Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), 100f * PxPerUnit);
            s_Arm.hideFlags = HideFlags.HideAndDontSave;
            return s_Arm;
        }

        /// <summary>Uniform veil of the head's glass film (alpha): a silvered glass under a dusty outer surface does not
        /// return the scene's full contrast. With the veil colour (mid grey-blue) black lifts to ~0.035 and white drops
        /// to ~0.975 (contrast x 0.94). WORKING_VALUE.</summary>
        public const float FilmVeil = 0.060f;
        /// <summary>Largest film alpha in the middle third of the glass (the view must stay usable, D70) - tested.</summary>
        public const float FilmMidMax = 0.16f;

        /// <summary>
        /// Glass film of the monitor mirror head (RGBA, 128 x 232; ADR 0340 addendum - the build #10 critic still read the
        /// glass as "too clean"): (1) a uniform thin veil that lowers the picture's contrast, (2) road dirt held along the
        /// rim - a band a few percent of the glass wide, densest in the lower corners where the airflow leaves it,
        /// broken up by noise, (3) dried droplet marks (pale rim, darker core) and a few runs below them, mostly near the
        /// edges. The middle of the glass stays within <see cref="FilmMidMax"/>.
        /// </summary>
        public static Texture2D FilmHead()
        {
            if (s_FilmHead != null) return s_FilmHead;
            const int w = 128, h = 232;
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear, name = "MirrorHeadFilm" };
            tex.hideFlags = HideFlags.HideAndDontSave;
            var px = new Color32[w * h];
            const int drops = 52;
            var dx = new float[drops]; var dy = new float[drops]; var dr = new float[drops]; var run = new float[drops];
            for (int k = 0; k < drops; k++)
            {
                // towards the rim: push the uniform position away from the centre
                float ux = Hash(k, 11, 7) * 2f - 1f, uy = Hash(k, 23, 7) * 2f - 1f;
                ux = Mathf.Sign(ux) * Mathf.Pow(Mathf.Abs(ux), 0.45f); uy = Mathf.Sign(uy) * Mathf.Pow(Mathf.Abs(uy), 0.6f);
                if (k % 3 == 0) uy = -Mathf.Abs(uy);                                   // more of them low
                dx[k] = (0.5f + 0.47f * ux) * w; dy[k] = (0.5f + 0.47f * uy) * h;
                // two in three are small dried specks, the rest wider marks with a broken rim
                dr[k] = k % 3 != 0 ? 0.7f + 1.3f * Hash(k, 37, 7) : 2.2f + 3.0f * Hash(k, 37, 7) * Hash(k, 41, 7);
                run[k] = Hash(k, 53, 7) > 0.62f ? 8f + 26f * Hash(k, 59, 7) : 0f;      // some ran down before drying
            }
            for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float u = x / (float)(w - 1), v = y / (float)(h - 1);
                float ex = Mathf.Min(u, 1f - u) * w, ey = Mathf.Min(v, 1f - v) * h;    // px to the nearest rim
                float e = Mathf.Min(ex, ey);
                float cloud = 0.50f * ValueNoise(u * 6f, v * 11f, 1) + 0.30f * ValueNoise(u * 17f, v * 30f, 2) + 0.20f * ValueNoise(u * 53f, v * 95f, 3);
                float rim = Mathf.Exp(-e / 5.5f);                                       // wiped glass keeps dirt against the lip
                float low = Mathf.Pow(1f - v, 3.4f);
                float corner = Mathf.Exp(-(ex + ey * 0.6f) / 16f) * (0.4f + 0.6f * (1f - v));
                float dust = (0.50f * rim + 0.13f * low + 0.30f * corner) * (0.35f + 1.25f * cloud);
                dust += 0.018f * Mathf.Clamp01(cloud * 2f - 0.7f);                      // faint smears across the middle
                float markA = 0f, markDark = 0f;
                for (int k = 0; k < drops; k++)
                {
                    float px0 = x - dx[k], py0 = y - dy[k];
                    float d = Mathf.Sqrt(px0 * px0 + py0 * py0) / dr[k];
                    if (k % 3 != 0)
                    {
                        markA = Mathf.Max(markA, Mathf.Clamp01(1f - d) * (0.07f + 0.09f * Hash(k, 67, 7)));   // speck
                    }
                    else if (d < 1.6f)
                    {
                        // the rim of a dried drop is never a clean circle: thick where the water sat last, gone elsewhere
                        float ang = Mathf.Atan2(py0, px0);
                        float broken = Mathf.Clamp01(1.5f * ValueNoise(ang * 1.1f + k * 3.7f, k * 0.9f, 9) - 0.25f) * (0.6f + 0.4f * Mathf.Clamp01(-Mathf.Sin(ang)));
                        float ring = Mathf.Clamp01(1f - Mathf.Abs(d - 0.82f) * 3.2f);
                        markA = Mathf.Max(markA, ring * broken * 0.15f);
                        markDark = Mathf.Max(markDark, Mathf.Clamp01(1f - d * 1.25f) * 0.05f);
                    }
                    if (run[k] > 0f && py0 < 0f && -py0 < run[k])
                    {
                        float fade = 1f - (-py0) / run[k];
                        markA = Mathf.Max(markA, Mathf.Clamp01(1f - Mathf.Abs(px0 + 0.6f * Mathf.Sin(py0 * 0.35f + k)) / 0.9f) * 0.085f * fade);
                    }
                }
                // layers, bottom to top: veil (cool grey), dust (warm grey), droplet core (dark), droplet rim (pale)
                float r = 0.56f, g = 0.60f, b = 0.64f, a = FilmVeil;
                Over(ref r, ref g, ref b, ref a, 0.58f, 0.555f, 0.51f, Mathf.Clamp01(dust));
                Over(ref r, ref g, ref b, ref a, 0.16f, 0.17f, 0.18f, markDark);
                Over(ref r, ref g, ref b, ref a, 0.80f, 0.79f, 0.76f, markA);
                px[y * w + x] = new Color32((byte)(Mathf.Clamp01(r) * 255f), (byte)(Mathf.Clamp01(g) * 255f), (byte)(Mathf.Clamp01(b) * 255f), (byte)(Mathf.Clamp01(a) * 255f));
            }
            tex.SetPixels32(px);
            tex.Apply(false, false);   // stays readable: FilmHeadStats (tests)
            s_FilmHead = tex;
            return tex;
        }

        /// <summary>Straight-alpha "over": the layer (lr, lg, lb, la) on top of the accumulated colour.</summary>
        static void Over(ref float r, ref float g, ref float b, ref float a, float lr, float lg, float lb, float la)
        {
            float oa = la + a * (1f - la);
            if (oa < 1e-5f) return;
            r = (lr * la + r * a * (1f - la)) / oa; g = (lg * la + g * a * (1f - la)) / oa; b = (lb * la + b * a * (1f - la)) / oa;
            a = oa;
        }

        /// <summary>Film alpha statistics (tests): largest alpha in the middle third, mean alpha of the outer 6 % band.</summary>
        public static void FilmHeadStats(out float midMax, out float rimMean)
        {
            var t = FilmHead();
            var px = t.GetPixels32();
            int w = t.width, h = t.height;
            midMax = 0f; float sum = 0f; int cnt = 0;
            for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float u = x / (float)(w - 1), v = y / (float)(h - 1), a = px[y * w + x].a / 255f;
                if (u > 1f / 3f && u < 2f / 3f && v > 1f / 3f && v < 2f / 3f) midMax = Mathf.Max(midMax, a);
                if (Mathf.Min(Mathf.Min(u, 1f - u) * w, Mathf.Min(v, 1f - v) * h) < 0.06f * w) { sum += a; cnt++; }
            }
            rimMean = cnt > 0 ? sum / cnt : 0f;
        }
    }
}
