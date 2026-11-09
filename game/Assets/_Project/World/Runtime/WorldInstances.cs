using System;
using UnityEngine;
using UnityEngine.Rendering;
using Game.Rendering;

namespace Game.World
{
    /// <summary>
    /// GPU-instanced point content of a region (street props, signs, signals, trees + impostors) from
    /// instances_*.json, baked by the importer into <see cref="WorldInstanceSet"/> (ADR 0012).
    ///
    /// Why Graphics.RenderMeshInstanced and not the GPU Resident Drawer: GRD needs a GameObject + MeshRenderer per
    /// instance (≈ 112 000 trees in tile C alone), Forward+ and compute; on a 4 GB Mali-G57 phone the GameObject memory
    /// and the per-object CPU cost defeat the purpose. Here: instances live in flat arrays sorted by 64 m cell and
    /// prototype; per camera the cells are frustum-culled, a whole run takes one LOD when the cell lies inside one LOD
    /// band (else per-instance distance), matrices are copied into 1023-entry batches and drawn with
    /// RenderMeshInstanced (one draw per submesh per batch). No GC allocation per frame.
    ///
    /// Distances scale with QualitySettings.lodBias (the tier's LOD bias, QualityProfile). Draws are issued from
    /// RenderPipelineManager.beginCameraRendering for that camera only (mirrors and the reversing camera get their own,
    /// shorter cull), in edit mode too so visual QA captures them.
    /// </summary>
    [ExecuteAlways]
    public sealed class WorldInstances : MonoBehaviour
    {
        public WorldInstanceSet set;
        [Tooltip("Multiplier on all switch/cull distances on top of QualitySettings.lodBias")]
        public float distanceScale = 1f;
        [Tooltip("Camera types that receive instances")]
        public bool includeSceneViewCamera = true;

        const int BatchSize = 1023;

        // Per (prototype, lod) batch state.
        Matrix4x4[][] m_Batch;
        int[] m_BatchCount;
        Bounds[] m_BatchBounds;
        int[] m_BatchOffset;    // prototype → first batch slot
        readonly Plane[] m_Planes = new Plane[6];
        Vector3 m_Origin = new Vector3(float.NaN, 0f, 0f);   // region root position the world copies were made for
        Matrix4x4[] m_World;    // instance matrices in Unity world space (asset stores region-root space)
        Bounds[] m_CellBounds;  // cell bounds in world space
        Camera m_Camera;

        public struct Stats { public int Draws, Instances, Triangles, VisibleCells; }
        /// <summary>Counters of the last camera rendered (visual QA / diagnostics).</summary>
        public static Stats Last;

        void OnEnable()
        {
            RenderPipelineManager.beginCameraRendering += OnBeginCamera;
            QualityProfileApplier.Applied += OnTierApplied;
            m_TierRead = false;
            m_TreeCull = -1f;
        }

        void OnDisable()
        {
            RenderPipelineManager.beginCameraRendering -= OnBeginCamera;
            QualityProfileApplier.Applied -= OnTierApplied;
            ReleaseMaterials();
        }

        void Allocate()
        {
            if (set == null || set.prototypes == null) return;
            int slots = 0;
            m_BatchOffset = new int[set.prototypes.Length];
            for (int p = 0; p < set.prototypes.Length; p++) { m_BatchOffset[p] = slots; slots += set.prototypes[p].lods.Length; }
            m_Batch = new Matrix4x4[slots][];
            for (int i = 0; i < slots; i++) m_Batch[i] = new Matrix4x4[BatchSize];
            m_BatchCount = new int[slots];
            m_BatchBounds = new Bounds[slots];
            m_Thin = new bool[set.prototypes.Length];
            m_Ends = new float[set.prototypes.Length][];
            for (int p = 0; p < set.prototypes.Length; p++)
            {
                var pr = set.prototypes[p];
                m_Thin[p] = pr.name.StartsWith("tree_");
                m_Ends[p] = (float[])pr.lodEndM.Clone();
                // Impostor forests: cap the cull distance (device measurement: DK8 forest 10 FPS on the A16 Medium,
                // 14 FPS on the S24+ High before thinning and this cap).
                if (m_Thin[p] && m_Ends[p].Length > 0) m_Ends[p][m_Ends[p].Length - 1] = Mathf.Min(m_Ends[p][m_Ends[p].Length - 1], m_TreeCull);
            }
            m_Origin = new Vector3(float.NaN, 0f, 0f);
        }

        // Vegetation settings of the active tier (QualityProfile, ADR 0012 / device runs); the serialized fields below are
        // the fallback when no tier was applied (edit-mode tools without an applier).
        float m_TreeCull, m_TreeCard, m_ThinStart;
        int m_TreeShadowMask;
        bool m_Trees = true;
        bool m_LeafA2C = true;
        bool m_TierRead;

        void ReadTier()
        {
            m_TierRead = true;
            var t = QualityProfileApplier.Current;
            bool ok = QualityProfileApplier.HasCurrent && t.treeCullM > 0f;
            float cull = ok ? t.treeCullM : treeCullM;
            m_TreeCard = ok ? t.treeCardLodScale : treeLodScaleMax;
            m_ThinStart = ok ? t.treeThinStartM : thinStartM;
            m_TreeShadowMask = ok ? t.treeShadowLodMask : (QualitySettings.lodBias < 1f ? 1 : 3);
            m_Trees = !RenderOverrides.Trees.HasValue || RenderOverrides.Trees.Value;
            bool a2c = !ok || t.leafAlphaToCoverage;
            bool simple = ok && t.simpleFoliage;
            if (m_Mats == null || simple != m_SimpleFoliage) BuildMaterials(simple);
            if (a2c != m_LeafA2C || !Mathf.Approximately(cull, m_TreeCull))
            {
                m_LeafA2C = a2c;
                SetLeafAlphaToCoverage(a2c);
            }
            if (!Mathf.Approximately(cull, m_TreeCull)) { m_TreeCull = cull; m_Batch = null; }   // re-cap impostor distances
        }

        /// <summary>Alpha-to-coverage on the alpha-clipped vegetation materials (URP Lit / Kamion/Vegetation _AlphaToMask render state).</summary>
        void SetLeafAlphaToCoverage(bool on)
        {
            if (set == null || set.materials == null || !Application.isPlaying) return;   // never edit the assets in the editor
            foreach (var m in set.materials)
                if (m != null && m.HasProperty("_AlphaToMask") && m.IsKeywordEnabled("_ALPHATEST_ON")) m.SetFloat("_AlphaToMask", on ? 1f : 0f);
            if (m_Mats != null)
                foreach (var m in m_Mats)
                    if (m != null && m.shader == m_FoliageShader) m.SetFloat("_AlphaToMask", on ? 1f : 0f);
        }

        // Materials actually drawn (set.materials, or runtime copies on Kamion/Vegetation for leaf cards / impostors on
        // tiers with simpleFoliage). The generated asset is never modified.
        Material[] m_Mats;
        bool m_SimpleFoliage;
        Shader m_FoliageShader;

        /// <summary>A leaf card or impostor material: alpha-clipped and double sided (InstanceImporter.ProtoMaterial).</summary>
        static bool IsFoliage(Material m) =>
            m != null && m.IsKeywordEnabled("_ALPHATEST_ON") && m.HasProperty("_Cull") && m.GetFloat("_Cull") == 0f &&
            (m.name.StartsWith("M_leaves_") || m.name.StartsWith("M_impostor_"));

        void BuildMaterials(bool simple)
        {
            ReleaseMaterials();
            m_SimpleFoliage = simple;
            var src = set != null ? set.materials : null;
            if (src == null) { m_Mats = Array.Empty<Material>(); return; }
            m_Mats = (Material[])src.Clone();
            var qp = QualityProfile.Load();
            var template = qp != null ? qp.foliageMaterial : null;
            m_FoliageShader = template != null ? template.shader : null;
            if (!simple || m_FoliageShader == null || !m_FoliageShader.isSupported) return;
            var copies = new System.Collections.Generic.Dictionary<Material, Material>();
            for (int i = 0; i < m_Mats.Length; i++)
            {
                var m = m_Mats[i];
                if (!IsFoliage(m)) continue;
                if (!copies.TryGetValue(m, out var c))
                {
                    c = new Material(template) { name = m.name + " (simple)", hideFlags = HideFlags.DontSave, enableInstancing = true, renderQueue = m.renderQueue };
                    c.SetTexture("_BaseMap", m.GetTexture("_BaseMap"));
                    c.SetTextureScale("_BaseMap", m.GetTextureScale("_BaseMap"));
                    c.SetTextureOffset("_BaseMap", m.GetTextureOffset("_BaseMap"));
                    c.SetColor("_BaseColor", m.GetColor("_BaseColor"));
                    c.SetFloat("_Cutoff", m.GetFloat("_Cutoff"));
                    c.SetFloat("_Cull", 0f);
                    c.SetFloat("_AlphaToMask", m_LeafA2C ? 1f : 0f);
                    copies[m] = c;
                }
                m_Mats[i] = c;
            }
        }

        void ReleaseMaterials()
        {
            if (m_Mats == null || set == null || set.materials == null) { m_Mats = null; return; }
            foreach (var m in m_Mats)
                if (m != null && Array.IndexOf(set.materials, m) < 0)
                {
                    if (Application.isPlaying) Destroy(m); else DestroyImmediate(m);
                }
            m_Mats = null;
        }

        void OnTierApplied(QualityProfile.Tier t) => m_TierRead = false;

        /// <summary>World-space copies of matrices and cell bounds; redone only when the region root moves (floating origin).</summary>
        void SyncOrigin()
        {
            Vector3 o = transform.position;
            if (m_World != null && o == m_Origin) return;
            m_Origin = o;
            var src = set.matrices;
            if (m_World == null || m_World.Length != src.Length) m_World = new Matrix4x4[src.Length];
            for (int i = 0; i < src.Length; i++)
            {
                var m = src[i];
                m.m03 += o.x; m.m13 += o.y; m.m23 += o.z;
                m_World[i] = m;
            }
            if (m_CellBounds == null || m_CellBounds.Length != set.cells.Length) m_CellBounds = new Bounds[set.cells.Length];
            for (int i = 0; i < set.cells.Length; i++) { var b = set.cells[i].bounds; b.center += o; m_CellBounds[i] = b; }
        }

        void OnBeginCamera(ScriptableRenderContext ctx, Camera cam)
        {
            if (set == null || set.cells == null || set.cells.Length == 0) return;
            if (cam.cameraType == CameraType.Preview || cam.cameraType == CameraType.Reflection) return;
            if (cam.cameraType == CameraType.SceneView && !includeSceneViewCamera) return;
            if (!m_TierRead) ReadTier();
            if (m_Batch == null || m_BatchOffset.Length != set.prototypes.Length) Allocate();
            Render(cam);
        }

        /// <summary>Culls and submits all instances for one camera.</summary>
        public void Render(Camera cam)
        {
            m_Camera = cam;
            SyncOrigin();
            GeometryUtility.CalculateFrustumPlanes(cam, m_Planes);
            Vector3 cp = cam.transform.position;
            float scale = Mathf.Max(0.05f, QualitySettings.lodBias * distanceScale);
            float far = cam.farClipPlane;
            var protos = set.prototypes;
            var cells = set.cells;
            var runs = set.runs;
            var mats = m_World;
            Last = default;

            for (int ci = 0; ci < cells.Length; ci++)
            {
                var cell = cells[ci];
                var b = m_CellBounds[ci];
                if (!GeometryUtility.TestPlanesAABB(m_Planes, b)) continue;
                float dNear = Mathf.Sqrt(b.SqrDistance(cp));
                if (dNear > far) continue;
                float dFar = FarDistance(b, cp);
                Last.VisibleCells++;
                for (int ri = cell.runStart; ri < cell.runStart + cell.runCount; ri++)
                {
                    var run = runs[ri];
                    var p = protos[run.prototype];
                    var ends = m_Ends[run.prototype];
                    if (!m_Trees && m_Thin[run.prototype]) continue;
                    float ls = thinnableProto(run.prototype) ? Mathf.Min(scale, m_TreeCard) : scale;
                    int ln = LodAt(ends, dNear, ls, scale), lf = LodAt(ends, dFar, ls, scale);
                    bool thinnable = m_Thin[run.prototype];
                    int stride = thinnable ? ThinStride(dNear, scale) : 1;
                    if (ln == lf && (stride == ThinStride(dFar, scale) || !thinnable))
                    {
                        if (ln < 0) continue;
                        if (stride == 1) Append(run.prototype, ln, mats, run.start, run.count, b);
                        else for (int i = run.start; i < run.start + run.count; i++) if ((i & (stride - 1)) == 0) Append(run.prototype, ln, mats, i, 1, b);
                        continue;
                    }
                    if (ln < 0) continue;   // nearest point already beyond the cull distance
                    for (int i = run.start; i < run.start + run.count; i++)
                    {
                        var m = mats[i];
                        float dx = m.m03 - cp.x, dy = m.m13 - cp.y, dz = m.m23 - cp.z;
                        float d = Mathf.Sqrt(dx * dx + dy * dy + dz * dz);
                        if (thinnable && (i & (ThinStride(d, scale) - 1)) != 0) continue;
                        int l = LodAt(ends, d, ls, scale);
                        if (l >= 0) Append(run.prototype, l, mats, i, 1, b);
                    }
                }
            }
            for (int p = 0; p < protos.Length; p++)
                for (int l = 0; l < protos[p].lods.Length; l++)
                    Flush(p, l);
        }

        /// <summary>
        /// Distance thinning of trees (Mali-G57 measurement 2026-11-09: the DK8 forest ran at 10 FPS on Medium - alpha-tested
        /// impostor and card overdraw, ~9 000 instances in view). Beyond ThinStartM·lodBias every 2nd tree, beyond
        /// 2.5×, every 4th; the instance order inside a cell is the generator's (spatially mixed), so the thinning is
        /// uniform. Tiers with lodBias ≥ 1.5 (High) start much farther away.
        /// </summary>
        public float thinStartM = 90f;

        int ThinStride(float d, float scale)
        {
            float s = m_ThinStart * scale;
            return d < s ? 1 : d < 2.5f * s ? 2 : 4;
        }

        bool thinnableProto(int p) => m_Thin[p];

        [Tooltip("Upper limit of the LOD-bias factor for tree card LODs (LOD0/LOD1). Device measurement 2026-11-09, DK8 forest " +
                 "QA camera: A16 Low (bias 0.5) 30 FPS, Medium (0.8) 10-14 FPS, S24+ High (1.5) 14-15 FPS - overdraw of alpha-" +
                 "tested leaf cards. Cards beyond 10 m / 30 m become impostors on every tier.")]
        public float treeLodScaleMax = 0.5f;

        bool[] m_Thin;
        float[][] m_Ends;
        [Tooltip("Cull distance of trees and shrubs (m at lodBias 1), caps the baked impostor distance")]
        public float treeCullM = 600f;

        static float FarDistance(Bounds b, Vector3 p)
        {
            Vector3 d = new Vector3(Mathf.Max(Mathf.Abs(p.x - b.min.x), Mathf.Abs(p.x - b.max.x)),
                Mathf.Max(Mathf.Abs(p.y - b.min.y), Mathf.Abs(p.y - b.max.y)),
                Mathf.Max(Mathf.Abs(p.z - b.min.z), Mathf.Abs(p.z - b.max.z)));
            return d.magnitude;
        }

        /// <summary>LOD index for distance d: switch distances × <paramref name="lodScale"/>, the cull distance (last end) × <paramref name="cullScale"/>.</summary>
        static int LodAt(float[] ends, float d, float lodScale, float cullScale)
        {
            int last = ends.Length - 1;
            for (int l = 0; l < ends.Length; l++)
                if (d < ends[l] * (l == last ? cullScale : lodScale)) return l;
            return -1;
        }

        void Append(int proto, int lod, Matrix4x4[] src, int start, int count, Bounds cellBounds)
        {
            int slot = m_BatchOffset[proto] + lod;
            while (count > 0)
            {
                int n = Mathf.Min(count, BatchSize - m_BatchCount[slot]);
                Array.Copy(src, start, m_Batch[slot], m_BatchCount[slot], n);
                if (m_BatchCount[slot] == 0) m_BatchBounds[slot] = cellBounds;
                else m_BatchBounds[slot].Encapsulate(cellBounds);
                m_BatchCount[slot] += n;
                start += n; count -= n;
                if (m_BatchCount[slot] == BatchSize) Flush(proto, lod);
            }
        }

        void Flush(int proto, int lod)
        {
            int slot = m_BatchOffset[proto] + lod;
            int n = m_BatchCount[slot];
            if (n == 0) return;
            var p = set.prototypes[proto];
            var mesh = p.lods[lod];
            var b = m_BatchBounds[slot];
            // Tree casters per tier (QualityProfile.treeShadowLodMask): LOD1 tree cards in the shadow pass doubled the
            // forest cost on the A16 (Low/Medium cast from LOD0 only).
            int mask = m_Thin[proto] ? p.shadowLodMask & m_TreeShadowMask : p.shadowLodMask;
            var shadows = (mask & (1 << lod)) != 0 ? ShadowCastingMode.On : ShadowCastingMode.Off;
            int m0 = p.materialStart[lod];
            for (int s = 0; s < mesh.subMeshCount; s++)
            {
                var mat = (m_Mats ?? set.materials)[m0 + s];
                if (mat == null) continue;
                var rp = new RenderParams(mat)
                {
                    camera = m_Camera,
                    worldBounds = b,
                    shadowCastingMode = shadows,
                    receiveShadows = true,
                    layer = gameObject.layer,
                    lightProbeUsage = LightProbeUsage.Off,
                    reflectionProbeUsage = ReflectionProbeUsage.Off,
                    motionVectorMode = MotionVectorGenerationMode.Camera,
                };
                Graphics.RenderMeshInstanced(rp, mesh, s, m_Batch[slot], n);
                Last.Draws++;
                Last.Triangles += (int)(mesh.GetIndexCount(s) / 3) * n;
            }
            Last.Instances += n;
            m_BatchCount[slot] = 0;
        }

    }
}
