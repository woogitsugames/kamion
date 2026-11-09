using System;
using Unity.Collections;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.UI.CabDisplays
{
    /// <summary>
    /// Immediate-mode 2D batch drawn into one render texture (a cab screen). Layouts call the primitives each refresh in
    /// design pixels (y down, origin top-left, e.g. 1560 x 600 for the 12.3" cluster); the canvas scales them to the
    /// render-texture size. Everything is one mesh and one draw (Hidden/Kamion/Display Canvas) issued through a command
    /// buffer outside the camera loop, then the mip chain is generated (the screens are seen small and at an angle).
    /// - Zero GC per refresh: persistent NativeArrays, Mesh.SetVertexBufferData/SetIndexBufferData, text from string
    ///   constants or char buffers (<see cref="TextBuffer"/>), glyph metrics from the dynamic font atlas.
    /// - Shapes have analytic 1-pixel edges (boxes, rotated boxes, rings / discs, ring sectors); glyphs come from the
    ///   Inter dynamic font atlas rasterised at the exact render-texture pixel size (no magnified bitmaps).
    /// </summary>
    public sealed class DisplayCanvas : IDisposable
    {
        public enum Align { Left = 0, Center = 1, Right = 2 }

        struct Vertex
        {
            public Vector3 pos;
            public Color32 col;
            public Vector4 uv;
        }

        static readonly VertexAttributeDescriptor[] s_Layout =
        {
            new VertexAttributeDescriptor(VertexAttribute.Position, VertexAttributeFormat.Float32, 3),
            new VertexAttributeDescriptor(VertexAttribute.Color, VertexAttributeFormat.UNorm8, 4),
            new VertexAttributeDescriptor(VertexAttribute.TexCoord0, VertexAttributeFormat.Float32, 4),
        };
        const MeshUpdateFlags k_Flags = MeshUpdateFlags.DontValidateIndices | MeshUpdateFlags.DontRecalculateBounds |
                                        MeshUpdateFlags.DontNotifyMeshUsers | MeshUpdateFlags.DontResetBoneBounds;
        static readonly int k_FontTex = Shader.PropertyToID("_FontTex");
        static readonly int k_Proj = Shader.PropertyToID("_DisplayProj");
        static readonly int k_Gamma = Shader.PropertyToID("_CoverageGamma");
        static readonly int k_PixelScale = Shader.PropertyToID("_PixelScale");
        public const string ShaderResource = "CabDisplay/DisplayCanvas";

        public readonly int DesignWidth, DesignHeight;
        public readonly float Scale;
        public RenderTexture Texture { get; private set; }
        public Font Font { get; }
        public int VertexCount => m_V;
        public int IndexCount => m_I;
        public int MaxVertices => m_Verts.Length;
        /// <summary>Primitives dropped this refresh because the buffers were full (layout bug: raise the capacity).</summary>
        public int Overflow { get; private set; }

        NativeArray<Vertex> m_Verts;
        NativeArray<int> m_Idx;
        int m_V, m_I;
        readonly Mesh m_Mesh;
        readonly Material m_Mat;
        readonly CommandBuffer m_Cb;
        float m_Pad;
        Matrix4x4 m_GpuProj;
        // Static underlay (e.g. the navigation map baked once in metres) drawn before the dynamic batch.
        Mesh m_Under;
        Material m_UnderMat;
        bool m_UnderOn;

        public DisplayCanvas(string name, int designWidth, int designHeight, float scale, int maxQuads, Font font, float coverageGamma)
        {
            DesignWidth = designWidth; DesignHeight = designHeight; Scale = scale;
            Font = font;
            int w = Mathf.Max(16, Mathf.RoundToInt(designWidth * scale)), h = Mathf.Max(16, Mathf.RoundToInt(designHeight * scale));
            var desc = new RenderTextureDescriptor(w, h, UnityEngine.Experimental.Rendering.GraphicsFormat.R8G8B8A8_SRGB, 0)
            {
                useMipMap = true, autoGenerateMips = false, msaaSamples = 1, sRGB = true,
            };
            Texture = new RenderTexture(desc)
            {
                name = "RT_CabDisplay_" + name, filterMode = FilterMode.Trilinear, anisoLevel = 4, wrapMode = TextureWrapMode.Clamp,
                hideFlags = HideFlags.DontSave,
            };
            Texture.Create();

            m_Verts = new NativeArray<Vertex>(maxQuads * 4, Allocator.Persistent, NativeArrayOptions.UninitializedMemory);
            m_Idx = new NativeArray<int>(maxQuads * 6, Allocator.Persistent, NativeArrayOptions.UninitializedMemory);
            m_Mesh = new Mesh { name = "CabDisplay_" + name, hideFlags = HideFlags.DontSave };
            m_Mesh.MarkDynamic();
            m_Mesh.SetVertexBufferParams(m_Verts.Length, s_Layout);
            m_Mesh.SetIndexBufferParams(m_Idx.Length, IndexFormat.UInt32);
            m_Mesh.subMeshCount = 1;
            m_Mesh.bounds = new Bounds(Vector3.zero, new Vector3(1e5f, 1e5f, 10f));

            var shader = Resources.Load<Shader>(ShaderResource);
            if (shader == null) throw new InvalidOperationException("Resources/" + ShaderResource + " missing");
            m_Mat = new Material(shader) { name = "M_CabDisplay_" + name, hideFlags = HideFlags.DontSave };
            m_Mat.SetFloat(k_Gamma, coverageGamma);
            m_Mat.SetFloat(k_PixelScale, scale);
            // Design pixels (y down) -> clip space of the render texture; GPU flip handled for render-to-texture.
            var ortho = Matrix4x4.Ortho(0f, designWidth, designHeight, 0f, -1f, 1f);
            m_GpuProj = GL.GetGPUProjectionMatrix(ortho, true);
            m_Mat.SetMatrix(k_Proj, m_GpuProj);
            m_Cb = new CommandBuffer { name = "CabDisplay " + name };
            m_Pad = 1f / scale + 0.5f;
        }

        /// <summary>
        /// Geometry builder without a render target (static meshes): primitives in arbitrary units (e.g. metres), edges
        /// padded by <paramref name="padUnits"/> (at least one render-texture pixel at the smallest drawn scale).
        /// </summary>
        public DisplayCanvas(string name, int maxQuads, float padUnits)
        {
            Scale = 1f;
            m_Verts = new NativeArray<Vertex>(maxQuads * 4, Allocator.Persistent, NativeArrayOptions.UninitializedMemory);
            m_Idx = new NativeArray<int>(maxQuads * 6, Allocator.Persistent, NativeArrayOptions.UninitializedMemory);
            m_Pad = padUnits;
        }

        /// <summary>Copies the current batch into a new static mesh (builder canvases).</summary>
        public Mesh BakeStatic(string name)
        {
            var mesh = new Mesh { name = name, hideFlags = HideFlags.DontSave };
            mesh.SetVertexBufferParams(m_V, s_Layout);
            mesh.SetIndexBufferParams(m_I, IndexFormat.UInt32);
            mesh.SetVertexBufferData(m_Verts, 0, 0, m_V, 0, k_Flags);
            mesh.SetIndexBufferData(m_Idx, 0, 0, m_I, k_Flags);
            Vector3 lo = new Vector3(float.MaxValue, float.MaxValue, 0f), hi = new Vector3(float.MinValue, float.MinValue, 0f);
            for (int i = 0; i < m_V; i++) { var p = m_Verts[i].pos; lo = Vector3.Min(lo, p); hi = Vector3.Max(hi, p); }
            var b = m_V > 0 ? new Bounds((lo + hi) * 0.5f, hi - lo + Vector3.forward) : new Bounds();
            mesh.subMeshCount = 1;
            mesh.SetSubMesh(0, new SubMeshDescriptor(0, m_I) { vertexCount = m_V, bounds = b }, k_Flags);
            mesh.bounds = b;
            mesh.UploadMeshData(true);
            return mesh;
        }

        /// <summary>Sets the static underlay mesh (null = none). The canvas does not own the mesh.</summary>
        public void SetUnderlay(Mesh mesh)
        {
            m_Under = mesh;
            if (mesh != null && m_UnderMat == null && m_Mat != null)
            {
                m_UnderMat = new Material(m_Mat) { name = m_Mat.name + "_Underlay", hideFlags = HideFlags.DontSave };
                m_UnderMat.SetFloat(k_Gamma, 1f);
            }
        }

        /// <summary>Draws the underlay this refresh with <paramref name="designFromMesh"/> (mesh units -> design px);
        /// <paramref name="rtPixelsPerUnit"/> drives the analytic edges. Call between Begin and End.</summary>
        public void DrawUnderlay(in Matrix4x4 designFromMesh, float rtPixelsPerUnit)
        {
            if (m_Under == null || m_UnderMat == null) return;
            m_UnderMat.SetMatrix(k_Proj, m_GpuProj * designFromMesh);
            m_UnderMat.SetFloat(k_PixelScale, rtPixelsPerUnit);
            m_UnderOn = true;
        }

        public void Dispose()
        {
            if (m_Verts.IsCreated) m_Verts.Dispose();
            if (m_Idx.IsCreated) m_Idx.Dispose();
            m_Cb?.Release();
            DestroyObj(m_Mesh);
            DestroyObj(m_Mat);
            DestroyObj(m_UnderMat);
            if (Texture != null) { Texture.Release(); DestroyObj(Texture); Texture = null; }
        }

        static void DestroyObj(UnityEngine.Object o)
        {
            if (o == null) return;
            if (Application.isPlaying) UnityEngine.Object.Destroy(o); else UnityEngine.Object.DestroyImmediate(o);
        }

        // ------------------------------------------------------------------ frame

        public void Begin() { m_V = 0; m_I = 0; Overflow = 0; m_UnderOn = false; }

        /// <summary>Uploads the batch and renders it into <see cref="Texture"/> (cleared to <paramref name="background"/>, sRGB).</summary>
        public void End(Color32 background)
        {
            m_Mesh.SetVertexBufferData(m_Verts, 0, 0, m_V, 0, k_Flags);
            m_Mesh.SetIndexBufferData(m_Idx, 0, 0, m_I, k_Flags);
            m_Mesh.SetSubMesh(0, new SubMeshDescriptor(0, m_I) { vertexCount = m_V, bounds = m_Mesh.bounds }, k_Flags);
            if (Font != null) m_Mat.SetTexture(k_FontTex, Font.material.mainTexture);
            m_Cb.Clear();
            m_Cb.SetRenderTarget(Texture, 0);
            // Clear colour is linear in a linear project; the sRGB target encodes it back.
            m_Cb.ClearRenderTarget(false, true, ((Color)background).linear);
            if (m_UnderOn) m_Cb.DrawMesh(m_Under, Matrix4x4.identity, m_UnderMat, 0, 0);
            if (m_I > 0) m_Cb.DrawMesh(m_Mesh, Matrix4x4.identity, m_Mat, 0, 0);
            m_Cb.GenerateMips(Texture);
            Graphics.ExecuteCommandBuffer(m_Cb);
        }

        bool Reserve(int verts, int idx)
        {
            if (m_V + verts > m_Verts.Length || m_I + idx > m_Idx.Length) { Overflow++; return false; }
            return true;
        }

        void Quad(Vector2 p0, Vector2 p1, Vector2 p2, Vector2 p3, Color32 c, Vector4 u0, Vector4 u1, Vector4 u2, Vector4 u3)
        {
            if (!Reserve(4, 6)) return;
            int v = m_V;
            m_Verts[v] = new Vertex { pos = p0, col = c, uv = u0 };
            m_Verts[v + 1] = new Vertex { pos = p1, col = c, uv = u1 };
            m_Verts[v + 2] = new Vertex { pos = p2, col = c, uv = u2 };
            m_Verts[v + 3] = new Vertex { pos = p3, col = c, uv = u3 };
            int i = m_I;
            m_Idx[i] = v; m_Idx[i + 1] = v + 1; m_Idx[i + 2] = v + 2;
            m_Idx[i + 3] = v; m_Idx[i + 4] = v + 2; m_Idx[i + 5] = v + 3;
            m_V += 4; m_I += 6;
        }

        // ------------------------------------------------------------------ shapes

        /// <summary>Axis-aligned filled rectangle (design px).</summary>
        public void Rect(float x, float y, float w, float h, Color32 c)
        {
            float hx = w * 0.5f, hy = h * 0.5f, cx = x + hx, cy = y + hy, p = m_Pad;
            float ex = hx + p, ey = hy + p;
            Quad(new Vector2(cx - ex, cy - ey), new Vector2(cx + ex, cy - ey), new Vector2(cx + ex, cy + ey), new Vector2(cx - ex, cy + ey), c,
                new Vector4(-ex, -ey, hx, hy), new Vector4(ex, -ey, hx, hy), new Vector4(ex, ey, hx, hy), new Vector4(-ex, ey, hx, hy));
        }

        /// <summary>Rectangle outline of the given stroke width (inside the rectangle).</summary>
        public void RectOutline(float x, float y, float w, float h, float stroke, Color32 c)
        {
            Rect(x, y, w, stroke, c);
            Rect(x, y + h - stroke, w, stroke, c);
            Rect(x, y + stroke, stroke, h - 2f * stroke, c);
            Rect(x + w - stroke, y + stroke, stroke, h - 2f * stroke, c);
        }

        /// <summary>Line segment of the given width with flat ends extended by half the width (a rotated box).</summary>
        public void Line(float x0, float y0, float x1, float y1, float width, Color32 c, bool extendEnds = true)
        {
            float dx = x1 - x0, dy = y1 - y0, len = Mathf.Sqrt(dx * dx + dy * dy);
            if (len < 1e-4f) return;
            float ux = dx / len, uy = dy / len;
            float hx = len * 0.5f + (extendEnds ? width * 0.5f : 0f), hy = width * 0.5f, p = m_Pad;
            float ex = hx + p, ey = hy + p, cx = (x0 + x1) * 0.5f, cy = (y0 + y1) * 0.5f;
            // Corners in the box frame (along u, along n = (-uy, ux)).
            Vector2 C(float a, float b) => new Vector2(cx + ux * a - uy * b, cy + uy * a + ux * b);
            Quad(C(-ex, -ey), C(ex, -ey), C(ex, ey), C(-ex, ey), c,
                new Vector4(-ex, -ey, hx, hy), new Vector4(ex, -ey, hx, hy), new Vector4(ex, ey, hx, hy), new Vector4(-ex, ey, hx, hy));
        }

        /// <summary>Filled disc.</summary>
        public void Disc(float cx, float cy, float r, Color32 c) => Ring(cx, cy, 0f, r, c);

        /// <summary>Full annulus (rIn = 0: disc).</summary>
        public void Ring(float cx, float cy, float rIn, float rOut, Color32 c)
        {
            float e = rOut + m_Pad;
            var u0 = new Vector4(-e, -e, rIn, -rOut); var u1 = new Vector4(e, -e, rIn, -rOut);
            var u2 = new Vector4(e, e, rIn, -rOut); var u3 = new Vector4(-e, e, rIn, -rOut);
            Quad(new Vector2(cx - e, cy - e), new Vector2(cx + e, cy - e), new Vector2(cx + e, cy + e), new Vector2(cx - e, cy + e), c, u0, u1, u2, u3);
        }

        /// <summary>
        /// Ring sector between angles a0 and a1 (degrees, mathematical: 0 = +x, counter-clockwise on screen, i.e. y up),
        /// as trapezoids with exact radial edges; the end caps are straight.
        /// </summary>
        public void Arc(float cx, float cy, float rIn, float rOut, float a0Deg, float a1Deg, Color32 c, int segments = 0)
        {
            float span = a1Deg - a0Deg;
            if (Mathf.Abs(span) < 1e-3f) return;
            if (segments <= 0) segments = Mathf.Clamp(Mathf.CeilToInt(Mathf.Abs(span) / 6f), 1, 64);
            float step = span / segments;
            float half = Mathf.Abs(step) * 0.5f * Mathf.Deg2Rad;
            float ro = (rOut + m_Pad) / Mathf.Cos(half), ri = Mathf.Max(0f, rIn - m_Pad);
            for (int s = 0; s < segments; s++)
            {
                float a = (a0Deg + step * s) * Mathf.Deg2Rad, b = (a0Deg + step * (s + 1)) * Mathf.Deg2Rad;
                float ca = Mathf.Cos(a), sa = -Mathf.Sin(a), cb = Mathf.Cos(b), sb = -Mathf.Sin(b);   // screen y down
                var p0 = new Vector2(ca * ri, sa * ri); var p1 = new Vector2(ca * ro, sa * ro);
                var p2 = new Vector2(cb * ro, sb * ro); var p3 = new Vector2(cb * ri, sb * ri);
                Quad(p0 + new Vector2(cx, cy), p1 + new Vector2(cx, cy), p2 + new Vector2(cx, cy), p3 + new Vector2(cx, cy), c,
                    new Vector4(p0.x, p0.y, rIn, -rOut), new Vector4(p1.x, p1.y, rIn, -rOut),
                    new Vector4(p2.x, p2.y, rIn, -rOut), new Vector4(p3.x, p3.y, rIn, -rOut));
            }
        }

        /// <summary>Solid triangle (no edge anti-aliasing beyond the mip chain; use for small glyph-like shapes and map areas).</summary>
        public void Triangle(Vector2 a, Vector2 b, Vector2 c, Color32 col)
        {
            var u = new Vector4(0f, 0f, 1e6f, 1e6f);
            Quad(a, b, c, c, col, u, u, u, u);
        }

        // ------------------------------------------------------------------ text

        /// <summary>Requests the glyphs of <paramref name="chars"/> at the render-texture size of <paramref name="designSize"/>.</summary>
        public void RequestGlyphs(string chars, float designSize)
        {
            if (Font != null) Font.RequestCharactersInTexture(chars, PixelSize(designSize), FontStyle.Normal);
        }

        int PixelSize(float designSize) => Mathf.Max(4, Mathf.RoundToInt(designSize * Scale));

        /// <summary>Advance width of a string in design px.</summary>
        public float Measure(string s, float size) => Measure(s, 0, s != null ? s.Length : 0, size, null);

        public float Measure(TextBuffer b, float size) => Measure(null, 0, b.Length, size, b.Chars);

        float Measure(string s, int start, int len, float size, char[] buf)
        {
            if (Font == null) return 0f;
            int px = PixelSize(size);
            float inv = 1f / Scale, w = 0f;
            for (int i = start; i < start + len; i++)
            {
                char ch = buf != null ? buf[i] : s[i];
                if (Font.GetCharacterInfo(ch, out var ci, px, FontStyle.Normal)) w += ci.advance * inv;
            }
            return w;
        }

        /// <summary>Text with its baseline at <paramref name="baseline"/> (design px).</summary>
        public float Text(string s, float x, float baseline, float size, Color32 c, Align align = Align.Left) =>
            s == null ? 0f : Glyphs(s, null, s.Length, x, baseline, size, c, align);

        public float Text(TextBuffer b, float x, float baseline, float size, Color32 c, Align align = Align.Left) =>
            Glyphs(null, b.Chars, b.Length, x, baseline, size, c, align);

        float Glyphs(string s, char[] buf, int len, float x, float baseline, float size, Color32 c, Align align)
        {
            if (Font == null || len == 0) return 0f;
            int px = PixelSize(size);
            float inv = 1f / Scale;
            if (align != Align.Left)
            {
                float w = Measure(s, 0, len, size, buf);
                x -= align == Align.Center ? w * 0.5f : w;
            }
            // Snap the pen to render-texture pixels so glyph bitmaps map 1:1.
            float pen = Mathf.Round(x * Scale), by = Mathf.Round(baseline * Scale);
            for (int i = 0; i < len; i++)
            {
                char ch = buf != null ? buf[i] : s[i];
                if (!Font.GetCharacterInfo(ch, out var ci, px, FontStyle.Normal)) continue;
                if (ch != ' ')
                {
                    float x0 = (pen + ci.minX) * inv, x1 = (pen + ci.maxX) * inv;
                    float y0 = (by - ci.maxY) * inv, y1 = (by - ci.minY) * inv;
                    Quad(new Vector2(x0, y0), new Vector2(x1, y0), new Vector2(x1, y1), new Vector2(x0, y1), c,
                        new Vector4(ci.uvTopLeft.x, ci.uvTopLeft.y, -1f, 0f), new Vector4(ci.uvTopRight.x, ci.uvTopRight.y, -1f, 0f),
                        new Vector4(ci.uvBottomRight.x, ci.uvBottomRight.y, -1f, 0f), new Vector4(ci.uvBottomLeft.x, ci.uvBottomLeft.y, -1f, 0f));
                }
                pen += ci.advance;
            }
            return pen * inv - x;
        }
    }
}
