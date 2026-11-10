using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Rendering
{
    /// <summary>
    /// Contact shadow / ambient occlusion on the ground under a vehicle (review r3 E3, r4 E-N1 P0: "the combination hangs
    /// over the asphalt"). One dynamic mesh per vehicle, one draw call, every tier:
    /// - body slabs (<see cref="slabs"/>): rectangles of the underside in the vehicle frame; a grid of vertices is
    ///   ray-cast onto the ground every frame, so the patch follows the road surface, and each vertex carries its
    ///   underside height h (suspension travel, pitch and roll included);
    /// - wheels (<see cref="wheels"/>): a small slab under each wheel centre (tyre width x contact length, low h), dark at
    ///   the contact patch.
    /// Kamion/Contact Shadow evaluates the 2D view factor of a slab of half-width a at height h for both axes
    ///   F(x) = ½ [(a − x)/√((a − x)² + h²) + (a + x)/√((a + x)² + h²)]
    /// (exact for an infinite strip: the cosine-weighted fraction of the sky hidden by the slab) and multiplies only the
    /// ambient share of the ground lighting (sky SH vs. sun x shadow map at that pixel): under the truck in sun the real
    /// shadow map already removes the sun, so the occlusion acts on the sky light only, as in reality.
    /// Raycasts: (rows + 1) x 2 per slab + 1 per wheel, ~40 for a tractor-trailer; no allocations after the first frame.
    /// </summary>
    [ExecuteAlways]
    [DefaultExecutionOrder(950)]
    public sealed class ContactShadowCaster : MonoBehaviour
    {
        [Serializable]
        public struct Slab
        {
            [Tooltip("Centre of the rectangle in this transform's frame (x, z), m")] public Vector2 centre;
            [Tooltip("Half width (x) and half length (z), m")] public Vector2 halfSize;
            [Tooltip("Underside height in this transform's frame (y of the lowest broad surface), m")] public float undersideY;
            [Tooltip("Occlusion strength (1 = opaque slab; chassis with gaps < 1)")] public float strength;
            [Tooltip("Rows along z (ground conformity)")] public int rows;
        }

        [Serializable]
        public struct Wheel
        {
            public Transform centre;
            public float radius;
            [Tooltip("Tyre (or dual pair) width, m")] public float width;
        }

        public Slab[] slabs = Array.Empty<Slab>();
        public Wheel[] wheels = Array.Empty<Wheel>();
        [Tooltip("Wheel blob strength")] public float wheelStrength = 0.9f;
        [Tooltip("Effective height of the tyre sidewall above the contact patch for the occlusion (m)")] public float wheelOcclusionHeight = 0.18f;
        [Tooltip("Ground layers (the vehicle layer is excluded)")] public LayerMask groundMask = ~((1 << 8) | (1 << 5) | (1 << 2));
        public float maxGroundDistance = 3f;
        [Tooltip("Effective occlusion height / real underside clearance: wheels, tanks and skirts close the sides of the gap, " +
                 "so the open strip formula with the full clearance under-darkens (photo Volvo FH: almost black under the frame). WORKING_VALUE")]
        public float heightScale = 0.6f;

        static Material s_Material;
        static readonly List<ContactShadowCaster> s_All = new List<ContactShadowCaster>();
        public static bool GlobalEnabled = true;

        Mesh m_Mesh;
        GameObject m_Go;
        MeshFilter m_Filter;
        MeshRenderer m_Renderer;
        readonly List<Vector3> m_Pos = new List<Vector3>();
        readonly List<Vector4> m_Uv0 = new List<Vector4>();   // x, z (m, slab frame), a, b
        readonly List<Vector2> m_Uv1 = new List<Vector2>();   // h, strength
        readonly List<int> m_Idx = new List<int>();
        int m_IndexedVerts = -1;
        /// <summary>Diagnostics: vertices and ground hits of the last refresh.</summary>
        public int LastVertices { get; private set; }
        public int LastHits { get; private set; }
        /// <summary>Diagnostics (visual QA log): per slab the occlusion height range h (m) and the ground offset below the vehicle origin.</summary>
        public string LastDiagnostics { get; private set; } = "";
        public static int Count => s_All.Count;
        public static ContactShadowCaster Get(int i) => s_All[i];

        void OnEnable()
        {
            s_All.Add(this);
            QualityProfileApplier.Applied += OnTier;
            if (QualityProfileApplier.HasCurrent) OnTier(QualityProfileApplier.Current);
        }

        void OnDisable()
        {
            s_All.Remove(this);
            QualityProfileApplier.Applied -= OnTier;
            if (m_Go != null) { if (Application.isPlaying) Destroy(m_Go); else DestroyImmediate(m_Go); }
            if (m_Mesh != null) { if (Application.isPlaying) Destroy(m_Mesh); else DestroyImmediate(m_Mesh); }
            m_Go = null; m_Mesh = null; m_IndexedVerts = -1;
        }

        static void OnTier(QualityProfile.Tier t) => GlobalEnabled = t.contactShadows;

        /// <summary>Visual QA (edit mode): rebuild every caster now.</summary>
        public static void RefreshAll()
        {
            Physics.SyncTransforms();
            foreach (var c in s_All) c.Refresh();
        }

        void LateUpdate() => Refresh();

        void EnsureObjects()
        {
            if (s_Material == null)
            {
                // A Resources material keeps the shader in player builds (Shader.Find alone would be stripped).
                s_Material = Resources.Load<Material>("M_ContactShadow");
                if (s_Material == null) return;
            }
            if (m_Go == null)
            {
                m_Go = new GameObject("ContactShadow (runtime)") { hideFlags = HideFlags.DontSave, layer = gameObject.layer };
                m_Go.transform.SetParent(transform, false);
                m_Filter = m_Go.AddComponent<MeshFilter>();
                m_Renderer = m_Go.AddComponent<MeshRenderer>();
                m_Renderer.shadowCastingMode = ShadowCastingMode.Off;
                m_Renderer.receiveShadows = false;
                m_Renderer.lightProbeUsage = LightProbeUsage.Off;
                m_Renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
                m_Renderer.sharedMaterial = s_Material;
                m_Mesh = new Mesh { name = "ContactShadow", hideFlags = HideFlags.DontSave };
                m_Mesh.MarkDynamic();
                m_Filter.sharedMesh = m_Mesh;
            }
        }

        bool Ground(Vector3 from, out Vector3 hit)
        {
            if (Physics.Raycast(from, Vector3.down, out var h, maxGroundDistance, groundMask, QueryTriggerInteraction.Ignore))
            { hit = h.point; LastHits++; return true; }
            // No collider (edit mode: WorldCollisionCooker cooks the world colliders on Awake in play mode only): the
            // plane through the wheel contact points (wheel centre - radius), or the vehicle frame origin without wheels.
            var t = transform;
            Vector3 onPlane = t.position;
            int nw = 0; Vector3 sum = Vector3.zero;
            foreach (var w in wheels) if (w.centre != null) { sum += w.centre.position - t.up * w.radius; nw++; }
            if (nw > 0) onPlane = sum / nw;
            var plane = new Plane(t.up, onPlane);
            var ray = new Ray(from, Vector3.down);
            if (plane.Raycast(ray, out float d) && d <= maxGroundDistance) { hit = ray.GetPoint(d); return true; }
            hit = from + Vector3.down * maxGroundDistance;
            return false;
        }

        /// <summary>Rebuilds the patch for the current pose.</summary>
        public void Refresh()
        {
            EnsureObjects();
            if (m_Go == null) return;
            m_Renderer.enabled = GlobalEnabled;
            if (!GlobalEnabled) return;
            m_Pos.Clear(); m_Uv0.Clear(); m_Uv1.Clear();
            LastHits = 0;
            var t = transform;
            var local = m_Go.transform;
            const float lift = 0.015f;
            var diag = Application.isPlaying ? null : new System.Text.StringBuilder();
            float hMin = 99f, hMax = 0f, gy = 0f;

            foreach (var s in slabs)
            {
                int rows = Mathf.Max(1, s.rows);
                // Margin beyond the footprint: the occlusion falls to ~15 % at one underside height outside the edge.
                float hRest = Mathf.Max(0.1f, s.undersideY);
                float mx = s.halfSize.x + hRest * 1.2f, mz = s.halfSize.y + hRest * 1.2f;
                for (int r = 0; r <= rows; r++)
                {
                    float z = Mathf.Lerp(-mz, mz, r / (float)rows);
                    for (int c = 0; c < 2; c++)
                    {
                        float x = c == 0 ? -mx : mx;
                        Vector3 under = t.TransformPoint(new Vector3(s.centre.x + x, s.undersideY, s.centre.y + z));
                        bool ok = Ground(under + Vector3.up * 0.05f, out var g);
                        float h = ok ? Mathf.Max(0.05f, under.y - g.y) * heightScale : 9f;
                        m_Pos.Add(local.InverseTransformPoint(g + Vector3.up * lift));
                        m_Uv0.Add(new Vector4(x, z, s.halfSize.x, s.halfSize.y));
                        m_Uv1.Add(new Vector2(h, ok ? s.strength : 0f));
                        if (diag != null) { hMin = Mathf.Min(hMin, h); hMax = Mathf.Max(hMax, h); gy = g.y; }
                    }
                }
                if (diag != null) diag.Append($"slab z {s.centre.y:F1} ±{s.halfSize.y:F1} h {hMin:F2}..{hMax:F2} groundWorldY {gy:F3} layer {gameObject.layer} r {m_Renderer.enabled}; ");
                hMin = 99f; hMax = 0f;
            }

            foreach (var w in wheels)
            {
                if (w.centre == null) continue;
                Vector3 c = w.centre.position;
                bool ok = Ground(c, out var g);
                float h = ok ? Mathf.Max(0.02f, (c.y - w.radius) - g.y) + wheelOcclusionHeight : 9f;
                float a = w.width * 0.5f, b = w.radius * 0.45f;
                float mx = a + 0.25f, mz = b + 0.3f;
                Vector3 right = Vector3.ProjectOnPlane(w.centre.right, Vector3.up).normalized;
                Vector3 fwd = Vector3.Cross(right, Vector3.up);
                for (int r = 0; r <= 1; r++)
                for (int k = 0; k < 2; k++)
                {
                    float x = k == 0 ? -mx : mx, z = r == 0 ? -mz : mz;
                    Vector3 p = g + right * x - fwd * z + Vector3.up * (lift + 0.003f);
                    m_Pos.Add(local.InverseTransformPoint(p));
                    m_Uv0.Add(new Vector4(x, z, a, b));
                    m_Uv1.Add(new Vector2(h, ok ? wheelStrength : 0f));
                }
            }

            if (diag != null) LastDiagnostics = diag.ToString();
            int verts = m_Pos.Count;
            LastVertices = verts;
            m_Mesh.Clear(true);
            m_Mesh.SetVertices(m_Pos);
            m_Mesh.SetUVs(0, m_Uv0);
            m_Mesh.SetUVs(1, m_Uv1);
            if (m_IndexedVerts != verts)
            {
                m_Idx.Clear();
                int v = 0;
                foreach (var s in slabs)
                {
                    int rows = Mathf.Max(1, s.rows);
                    for (int r = 0; r < rows; r++) Quad(v + r * 2, v + r * 2 + 1, v + r * 2 + 3, v + r * 2 + 2);
                    v += (rows + 1) * 2;
                }
                foreach (var w in wheels) { if (w.centre == null) continue; Quad(v, v + 1, v + 3, v + 2); v += 4; }
                m_IndexedVerts = verts;
            }
            m_Mesh.SetTriangles(m_Idx, 0, false);
            m_Mesh.bounds = new Bounds(Vector3.zero, Vector3.one * 60f);
        }

        void Quad(int a, int b, int c, int d)
        {
            // Kamion/Contact Shadow draws with Cull Off: the winding does not matter.
            m_Idx.Add(a); m_Idx.Add(c); m_Idx.Add(b);
            m_Idx.Add(a); m_Idx.Add(d); m_Idx.Add(c);
        }
    }
}
