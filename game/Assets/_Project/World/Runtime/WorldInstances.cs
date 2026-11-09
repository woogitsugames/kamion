using System;
using UnityEngine;
using UnityEngine.Rendering;

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
            Allocate();
        }

        void OnDisable() => RenderPipelineManager.beginCameraRendering -= OnBeginCamera;

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
            m_Origin = new Vector3(float.NaN, 0f, 0f);
        }

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
                    int ln = LodAt(p, dNear, scale), lf = LodAt(p, dFar, scale);
                    if (ln == lf)
                    {
                        if (ln >= 0) Append(run.prototype, ln, mats, run.start, run.count, b);
                        continue;
                    }
                    if (ln < 0) continue;   // nearest point already beyond the cull distance
                    for (int i = run.start; i < run.start + run.count; i++)
                    {
                        var m = mats[i];
                        float dx = m.m03 - cp.x, dy = m.m13 - cp.y, dz = m.m23 - cp.z;
                        int l = LodAt(p, Mathf.Sqrt(dx * dx + dy * dy + dz * dz), scale);
                        if (l >= 0) Append(run.prototype, l, mats, i, 1, b);
                    }
                }
            }
            for (int p = 0; p < protos.Length; p++)
                for (int l = 0; l < protos[p].lods.Length; l++)
                    Flush(p, l);
        }

        static float FarDistance(Bounds b, Vector3 p)
        {
            Vector3 d = new Vector3(Mathf.Max(Mathf.Abs(p.x - b.min.x), Mathf.Abs(p.x - b.max.x)),
                Mathf.Max(Mathf.Abs(p.y - b.min.y), Mathf.Abs(p.y - b.max.y)),
                Mathf.Max(Mathf.Abs(p.z - b.min.z), Mathf.Abs(p.z - b.max.z)));
            return d.magnitude;
        }

        static int LodAt(WorldInstanceSet.Prototype p, float d, float scale)
        {
            var ends = p.lodEndM;
            for (int l = 0; l < ends.Length; l++)
                if (d < ends[l] * scale) return l;
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
            var shadows = (p.shadowLodMask & (1 << lod)) != 0 ? ShadowCastingMode.On : ShadowCastingMode.Off;
            int m0 = p.materialStart[lod];
            for (int s = 0; s < mesh.subMeshCount; s++)
            {
                var mat = set.materials[m0 + s];
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
