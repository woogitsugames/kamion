using System;
using UnityEngine;
using UnityEngine.Rendering;
using Game.Core;
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

        public struct Stats { public int Draws, Instances, Triangles, VisibleCells, HlodCells; }
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
            m_FixedCull = new bool[set.prototypes.Length];
            m_Ends = new float[set.prototypes.Length][];
            m_Lod0Min = new float[set.prototypes.Length];
            for (int p = 0; p < set.prototypes.Length; p++)
            {
                var pr = set.prototypes[p];
                m_Thin[p] = pr.name.StartsWith("tree_");
                m_FixedCull[p] = IsVehicle(pr.name);
                m_Lod0Min[p] = m_FixedCull[p] && pr.lods.Length > 1 ? VehicleLod0MinM : 0f;
                m_Ends[p] = (float[])pr.lodEndM.Clone();
                // Impostor forests: cap the cull distance (device measurement: DK8 forest 10 FPS on the A16 Medium,
                // 14 FPS on the S24+ High before thinning and this cap).
                if (m_Thin[p] && m_Ends[p].Length > 0) m_Ends[p][m_Ends[p].Length - 1] = Mathf.Min(m_Ends[p][m_Ends[p].Length - 1], m_TreeCull);
            }
            m_Origin = new Vector3(float.NaN, 0f, 0f);
            m_PoleCull = 0f;
            for (int p = 0; p < set.prototypes.Length; p++)
            {
                var pr = set.prototypes[p];
                if ((pr.name.StartsWith("power_pole") || pr.name.StartsWith("pylon")) && m_Ends[p].Length > 0)
                    m_PoleCull = Mathf.Max(m_PoleCull, m_Ends[p][m_Ends[p].Length - 1]);
            }
        }

        static readonly int k_WireFade = Shader.PropertyToID("_KamionWireFade");
        static readonly int k_ImpostorBlend = Shader.PropertyToID("_KamionImpostorBlend");
        float m_PoleCull;

        // Vegetation settings of the active tier (QualityProfile, ADR 0012 / device runs); the serialized fields below are
        // the fallback when no tier was applied (edit-mode tools without an applier).
        float m_TreeCull, m_TreeCard, m_ThinStart, m_HlodSwitch, m_HlodCull;
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
            m_TreeShadowMask = ok ? t.treeShadowLodMask : (TierLodBias < 1f ? 1 : 3);
            // forestHlodM: > 0 switch distance, < 0 off (rq_hlod=0), 0 = not set (profile before ADR 0015) → fallback field.
            m_HlodSwitch = ok && t.forestHlodM != 0f ? Mathf.Max(t.forestHlodM, 0f) : forestHlodM;
            m_HlodCull = ok && t.forestHlodM != 0f ? t.forestHlodCullM : forestHlodCullM;
            m_Trees = !RenderOverrides.Trees.HasValue || RenderOverrides.Trees.Value;
            // Impostor view cross-fade (Kamion/Vegetation _IMPOSTOR): 2 views on Medium and up, the nearest view on Low
            // (half the texture fetches; ADR 0023 cost table). Tier = LOD bias (Low 0.5).
            Shader.SetGlobalFloat(k_ImpostorBlend, TierLodBias >= 0.75f ? 1f : 0f);
            bool a2c = !ok || t.leafAlphaToCoverage;
            bool simple = ok && t.simpleFoliage;
            // Hero LOD0 can also be selected close to the site on Low. Gate thin-leaf lighting by the actual
            // active quality profile, never by LOD distance (including temporary mirror/extra-view bias).
            bool heroLeafHigh = QualityProfileApplier.HasCurrent && (t.name == "High" || t.name == "Ultra");   // review s10-0087-0090: Ultra too
            if (m_Mats == null || simple != m_SimpleFoliage || heroLeafHigh != m_HeroLeafHigh) BuildMaterials(simple);
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
        bool m_HeroLeafHigh;
        Shader m_FoliageShader;

        /// <summary>A leaf card or impostor material: alpha-clipped and double sided (InstanceImporter.ProtoMaterial).</summary>
        static bool IsFoliage(Material m) =>
            m != null && m.IsKeywordEnabled("_ALPHATEST_ON") && m.HasProperty("_Cull") && m.GetFloat("_Cull") == 0f &&
            (m.name.StartsWith("M_leaves_") || m.name.StartsWith("M_impostor_") || m.name.StartsWith("M_forest_edge_") || m.name.StartsWith("M_fab_"));

        void BuildMaterials(bool simple)
        {
            ReleaseMaterials();
            m_SimpleFoliage = simple;
            m_HeroLeafHigh = QualityProfileApplier.HasCurrent && QualityProfileApplier.Current.name == "High";
            var src = set != null ? set.materials : null;
            if (src == null) { m_Mats = Array.Empty<Material>(); return; }
            m_Mats = (Material[])src.Clone();
            // Street lamp glass: per-instance-set copies that StreetLamps lights at dusk (review r4 L3, rendering-perf).
            var lampCopies = new System.Collections.Generic.Dictionary<Material, Material>();
            for (int i = 0; i < m_Mats.Length; i++)
            {
                var m = m_Mats[i];
                if (!StreetLamps.IsLampGlass(m)) continue;
                if (!lampCopies.TryGetValue(m, out var c))
                {
                    c = new Material(m) { name = m.name, hideFlags = HideFlags.DontSave };
                    StreetLamps.RegisterGlass(c);
                    lampCopies[m] = c;
                }
                m_Mats[i] = c;
            }
            var qp = QualityProfile.Load();
            var template = qp != null ? qp.foliageMaterial : null;
            m_FoliageShader = template != null ? template.shader : null;
            if (!simple || m_FoliageShader == null || !m_FoliageShader.isSupported) return;
            var copies = new System.Collections.Generic.Dictionary<Material, Material>();
            for (int i = 0; i < m_Mats.Length; i++)
            {
                var m = m_Mats[i];
                // ADR0070 r7: a runtime copy for this one hero shell only. Source assets remain URP Lit so Low
                // keeps its original shader/cost even when a near camera selects the shared LOD0 mesh.
                bool heroLeaf = m_HeroLeafHigh && m != null && m.name == "M_fire_station_thuja_shell";
                if (!IsFoliage(m) && !(m != null && m.shader == m_FoliageShader) && !heroLeaf) continue;
                if (!copies.TryGetValue(m, out var c) && m.shader == m_FoliageShader)
                {
                    // Generated on Kamion/Vegetation already (impostors, HLOD edge walls; ADR 0023): copy as is.
                    c = new Material(m) { name = m.name + " (simple)", hideFlags = HideFlags.DontSave, enableInstancing = true };
                    c.SetFloat("_AlphaToMask", m_LeafA2C ? 1f : 0f);
                    copies[m] = c;
                }
                else if (!copies.TryGetValue(m, out c))
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
                VegetationCanopyPolicy.Apply(c);
                if (heroLeaf)
                {
                    c.SetFloat("_Transmission", 0.25f);
                    c.SetFloat("_CrownShade", 0f);
                }
                Game.Rendering.ForestFastPath.Register(c);   // ADR 0113: HLOD edge one-pass state, A/B
                m_Mats[i] = c;
            }
        }

        void ReleaseMaterials()
        {
            if (m_Mats == null || set == null || set.materials == null) { m_Mats = null; return; }
            foreach (var m in m_Mats)
                if (m != null && Array.IndexOf(set.materials, m) < 0)
                {
                    StreetLamps.UnregisterGlass(m);
                    Game.Rendering.ForestFastPath.Unregister(m);
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
            int n = set.Count;
            if (m_World == null || m_World.Length != n)
            {
                // rotation/scale decoded once (compact TRS, ADR 0025); only the translation follows the origin
                m_World = new Matrix4x4[n];
                for (int i = 0; i < n; i++) m_World[i] = set.LocalMatrix(i);
            }
            for (int i = 0; i < n; i++)
            {
                var p = set.LocalPosition(i);
                m_World[i].m03 = p.x + o.x; m_World[i].m13 = p.y + o.y; m_World[i].m23 = p.z + o.z;
            }
            if (m_CellBounds == null || m_CellBounds.Length != set.cells.Length) m_CellBounds = new Bounds[set.cells.Length];
            for (int i = 0; i < set.cells.Length; i++) { var b = set.cells[i].bounds; b.center += o; m_CellBounds[i] = b; }
            SendLampHeads();
        }

        Vector3[] m_LampHeads;
        /// <summary>Lamp head positions (top of the LOD0 bounds, over its centre) for StreetLamps' point lights.</summary>
        void SendLampHeads()
        {
            int n = 0;
            foreach (var r in set.runs) if (r.prototype >= 0 && set.prototypes[r.prototype].name.StartsWith("lamp_")) n += r.count;
            if (m_LampHeads == null || m_LampHeads.Length != n) m_LampHeads = new Vector3[n];
            int k = 0;
            foreach (var r in set.runs)
            {
                if (r.prototype < 0) continue;
                var pr = set.prototypes[r.prototype];
                if (!pr.name.StartsWith("lamp_") || pr.lods.Length == 0 || pr.lods[0] == null) continue;
                var b = pr.lods[0].bounds;
                var head = new Vector3(b.center.x, b.max.y - 0.25f, b.center.z);
                for (int i = 0; i < r.count && k < n; i++) m_LampHeads[k++] = m_World[r.start + i].MultiplyPoint3x4(head);
            }
            StreetLamps.SetHeads(m_LampHeads, k);
        }

        /// <summary>The tier LOD bias (not the temporary extra-view bias while a mirror renders; ADR 0068).</summary>
        static float TierLodBias => ExtraViewLod.Swapped ? ExtraViewLod.BaseLodBias : QualitySettings.lodBias;

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
            // ADR 0106 GPU breakdown (rq_props, rq_ab trees|props): diagnostics only, shipping state = both on.
            bool trees = m_Trees && !RenderOverrides.AbTreesOff;
            bool props = RenderOverrides.Props != false && !RenderOverrides.AbPropsOff;
            GeometryUtility.CalculateFrustumPlanes(cam, m_Planes);
            Vector3 cp = cam.transform.position;
            // ADR 0068: extra views (mirrors) use their own LOD scale on the tier bias (Game.Core.ExtraViewLod), whatever
            // the order of the beginCameraRendering handlers.
            float scale = Mathf.Max(0.05f, ExtraViewLod.EffectiveLodBias(cam) * distanceScale);
            float far = cam.farClipPlane, far2 = far;   // far2: the chunk-merge loop runs before cells (same limit)
            // Power-line conductors (Kamion/World Wire) fade out with the cull distance of the poles that carry them
            // (REVIEW r4 W-H2: wires hung in the air over the DK8 forest on Low after the poles were culled).
            if (m_PoleCull > 0f)
            {
                float pc = Mathf.Min(m_PoleCull * scale, far);
                Shader.SetGlobalVector(k_WireFade, new Vector4(pc * 0.8f, pc, 0f, 0f));
            }
            var protos = set.prototypes;
            var cells = set.cells;
            var runs = set.runs;
            var mats = m_World;
            Last = default;

            // Forest HLOD per chunk (ADR 0015): a chunk whose nearest point is beyond the switch distance is drawn as one
            // merged mesh; its cells then skip their own HLOD draw (and their forest trees, as below).
            var groups = set.hlodGroups;
            int ng = groups != null ? groups.Length : 0;
            if (m_GroupFar == null || m_GroupFar.Length != ng) m_GroupFar = new bool[ng];
            Vector3 o = m_Origin;
            for (int g = 0; g < ng; g++)
            {
                var mesh = groups[g].mesh;
                bool gFar = false;
                if (mesh != null && trees && m_HlodSwitch > 0f)
                {
                    var gb = mesh.bounds; gb.center += o;
                    float d = Mathf.Sqrt(gb.SqrDistance(cp));
                    gFar = d > m_HlodSwitch;
                    if (gFar && (m_HlodCull <= 0f || d < m_HlodCull) && d < far2 && GeometryUtility.TestPlanesAABB(m_Planes, gb))
                        DrawMesh(mesh, groups[g].materialStart, gb);
                }
                m_GroupFar[g] = gFar;
            }

            for (int ci = 0; ci < cells.Length; ci++)
            {
                var cell = cells[ci];
                var b = m_CellBounds[ci];
                if (!GeometryUtility.TestPlanesAABB(m_Planes, b)) continue;
                float dNear = Mathf.Sqrt(b.SqrDistance(cp));
                if (dNear > far) continue;
                float dFar = FarDistance(b, cp);
                Last.VisibleCells++;
                // Forest HLOD (ADR 0015): beyond the tier's switch distance the cell mesh replaces its forest trees.
                bool hlod = false;
                if (cell.hlod > 0 && trees && m_HlodSwitch > 0f && set.hlods != null && cell.hlod <= set.hlods.Length)
                {
                    var h = set.hlods[cell.hlod - 1];
                    bool groupDrawn = h.group >= 0 && h.group < ng && m_GroupFar[h.group];
                    hlod = groupDrawn || dNear > m_HlodSwitch;
                    if (hlod) Last.HlodCells++;
                    if (hlod && !groupDrawn && (m_HlodCull <= 0f || dNear < m_HlodCull)) DrawMesh(h.mesh, h.materialStart, b);
                }
                for (int ri = cell.runStart; ri < cell.runStart + cell.runCount; ri++)
                {
                    var run = runs[ri];
                    if (hlod && run.forest) continue;
                    var p = protos[run.prototype];
                    var ends = m_Ends[run.prototype];
                    if (!trees && m_Thin[run.prototype]) continue;
                    if (!props && !m_Thin[run.prototype]) continue;
                    float ls = thinnableProto(run.prototype) ? Mathf.Min(scale, m_TreeCard) * RenderOverrides.AbTreeCardScale : scale;
                    float cs = m_FixedCull[run.prototype] ? distanceScale : scale;   // vehicles: same cull on every tier
                    float l0 = m_Lod0Min[run.prototype] * distanceScale;   // vehicles: LOD0 floor on every tier
                    int ln = LodAt(ends, dNear, ls, cs, l0), lf = LodAt(ends, dFar, ls, cs, l0);
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
                        int l = LodAt(ends, d, ls, cs, l0);
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
            float s = m_ThinStart * scale * RenderOverrides.AbTreeThinScale;
            // v3.4 kept the strides: a later start (1.5x, +25 % instances in the DK8 view) did not fit the A16 Low budget
            // with certainty (editor timing noise > the gain; ADR 0023). The forest edge reads dense through the HLOD.
            return d < s ? 1 : d < 2.5f * s ? 2 : 4;
        }

        bool thinnableProto(int p) => m_Thin[p];

        [Tooltip("Upper limit of the LOD-bias factor for tree card LODs (LOD0/LOD1). Device measurement 2026-11-09, DK8 forest " +
                 "QA camera: A16 Low (bias 0.5) 30 FPS, Medium (0.8) 10-14 FPS, S24+ High (1.5) 14-15 FPS - overdraw of alpha-" +
                 "tested leaf cards. Cards beyond 10 m / 30 m become impostors on every tier.")]
        public float treeLodScaleMax = 0.5f;

        bool[] m_Thin;
        bool[] m_FixedCull;
        float[][] m_Ends;
        float[] m_Lod0Min;

        /// <summary>Cull distance (m) of parked vehicles on every tier (ADR 0041 v4, REVIEW r6 W-N6: Low culled the truck
        /// rigs at 60 m and the cars at 200 m, High at 180 / 600 m, so the same cab-dash frame showed different content).
        /// Only the LOD switches scale with lodBias. WORKING_VALUE; mirrored in build_world.py VEHICLE_CULL_M.</summary>
        public const float VehicleCullM = 300f;

        /// <summary>Floor (m) of the LOD0 distance of parked vehicles on every tier (ADR 0041 r8, REVIEW r7 N-14): LOD0 ends
        /// at max(policy x lodBias, this). Low (lodBias 0.5) switched cars to LOD1 at 12.5 m, so the cars next to the route
        /// (8-12 m from the cab) had disc wheels and no lamps while High showed rims and plates. With 16 m a car parked
        /// beside the lane is LOD0 on every tier. WORKING_VALUE; mirrored in build_world.py VEHICLE_LOD0_MIN_M.</summary>
        public const float VehicleLod0MinM = 16f;

        /// <summary>Vehicle prototypes and their contact-shadow patch prototypes ("contact_&lt;spec hash&gt;", ADR 0050): fixed cull.</summary>
        public static bool IsVehicle(string proto) =>
            proto.StartsWith("car_") || proto.StartsWith("van_") || proto.StartsWith("tractor_") || proto.StartsWith("trailer_") ||
            proto.StartsWith("contact_");
        [Tooltip("Cull distance of trees and shrubs (m at lodBias 1), caps the baked impostor distance")]
        public float treeCullM = 600f;

        static float FarDistance(Bounds b, Vector3 p)
        {
            Vector3 d = new Vector3(Mathf.Max(Mathf.Abs(p.x - b.min.x), Mathf.Abs(p.x - b.max.x)),
                Mathf.Max(Mathf.Abs(p.y - b.min.y), Mathf.Abs(p.y - b.max.y)),
                Mathf.Max(Mathf.Abs(p.z - b.min.z), Mathf.Abs(p.z - b.max.z)));
            return d.magnitude;
        }

        /// <summary>LOD index for distance d: switch distances × <paramref name="lodScale"/>, the cull distance (last end) × <paramref name="cullScale"/>;
        /// LOD0 (when it is not the only LOD) reaches at least <paramref name="lod0Min"/> metres.</summary>
        public static int LodAt(float[] ends, float d, float lodScale, float cullScale, float lod0Min = 0f)
        {
            int last = ends.Length - 1;
            for (int l = 0; l < ends.Length; l++)
            {
                float e = ends[l] * (l == last ? cullScale : lodScale);
                if (l == 0 && l != last && e < lod0Min) e = lod0Min;
                if (d < e) return l;
            }
            return -1;
        }

        [Tooltip("Forest HLOD switch distance (m to the cell bounds) when no tier was applied; QualityProfile.forestHlodM per tier")]
        public float forestHlodM = 120f;
        [Tooltip("Forest HLOD cull distance (0 = none) when no tier was applied")]
        public float forestHlodCullM = 0f;

        bool[] m_GroupFar;


        /// <summary>A forest HLOD mesh (cell or chunk merge), region-root space, no shadows (beyond every tier's shadow distance).</summary>
        void DrawMesh(Mesh mesh, int materialStart, Bounds b)
        {
            if (mesh == null || RenderOverrides.AbHlodOff) return;   // ADR 0106 A/B (diagnostics)
            var mats = m_Mats ?? set.materials;
            var trs = Matrix4x4.Translate(m_Origin);
            for (int s = 0; s < mesh.subMeshCount; s++)
            {
                var mat = Game.Rendering.ForestFastPath.Canopy(mats[materialStart + s]);   // ADR 0113: Kamion/Forest Canopy on forestFast tiers
                if (mat == null) continue;
                // ADR 0106 A/B (diagnostics): 1 = no canopy (opaque) submeshes, 2 = no edge-wall (Kamion/Vegetation) submeshes.
                if (RenderOverrides.AbHlodPart != 0 && (RenderOverrides.AbHlodPart == 2) == (mat.shader == m_FoliageShader)) continue;

                var rp = new RenderParams(mat)
                {
                    camera = m_Camera,
                    worldBounds = b,
                    shadowCastingMode = ShadowCastingMode.Off,
                    receiveShadows = true,
                    layer = gameObject.layer,
                    lightProbeUsage = LightProbeUsage.Off,
                    reflectionProbeUsage = ReflectionProbeUsage.Off,
                };
                Graphics.RenderMesh(rp, mesh, s, trs);
                Last.Draws++;
                Last.Triangles += (int)(mesh.GetIndexCount(s) / 3);
            }
        }

        void Append(int proto, int lod, Matrix4x4[] src, int start, int count, Bounds cellBounds)
        {
            if (RenderOverrides.AbImpostorOff && m_Thin[proto] && lod > 0 && lod == set.prototypes[proto].lods.Length - 1) return;   // ADR 0106 A/B
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
            int mask = m_Thin[proto] ? (RenderOverrides.AbTreeShadowOff ? 0 : p.shadowLodMask & m_TreeShadowMask) : p.shadowLodMask;
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
                    shadowCastingMode = set.noShadowMaterials.Length > 0 && Array.IndexOf(set.noShadowMaterials, m0 + s) >= 0 ? ShadowCastingMode.Off : shadows,
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
