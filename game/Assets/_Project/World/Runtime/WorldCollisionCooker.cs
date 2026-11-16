using System.Diagnostics;
using Unity.Collections;
using Unity.Jobs;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace Game.World
{
    /// <summary>
    /// Cooks the region's MeshColliders at load instead of shipping prebaked PhysX data (ADR 0012 §6; the prebaked data
    /// was ~17 MB of the Low/Medium APK). The scene builder saves the world MeshColliders disabled; here every mesh is
    /// cooked with <see cref="Physics.BakeMesh(int, bool, MeshColliderCookingOptions)"/> in a parallel job (worker threads),
    /// then the colliders are enabled - PhysX reuses the baked data when the cooking options match, so enabling is cheap.
    /// Runs before the vehicle bootstrap (execution order −900) so the truck never spawns over missing ground.
    /// Collision meshes must be readable (WorldMeshBake.PositionsOnly).
    /// </summary>
    [DefaultExecutionOrder(-900)]
    public sealed class WorldCollisionCooker : MonoBehaviour
    {
        [Tooltip("World MeshColliders saved disabled by the scene builder")]
        public MeshCollider[] colliders = System.Array.Empty<MeshCollider>();
        [Tooltip("Streamed tile scene (ADR 0235): no cooking in Awake; Game.World.Streaming.WorldStreamer calls BeginCook / PollCook " +
                 "so the bake runs on worker threads over several frames and the colliders are enabled in batches")]
        public bool deferCook;

        // Deferred cook state (streamed tiles).
        JobHandle m_Handle;
        NativeArray<EntityId> m_Ids;
        NativeArray<MeshColliderCookingOptions> m_Opts;
        bool m_Scheduled, m_Baked;
        int m_EnableNext;
        readonly Stopwatch m_Deferred = new Stopwatch();

        /// <summary>Wall-clock time of the last cook (ms) and the number of meshes (diagnostics / device report).</summary>
        public static float LastCookMs { get; private set; }
        public static int LastCookCount { get; private set; }

        struct BakeJob : IJobParallelFor
        {
            [ReadOnly] public NativeArray<EntityId> meshIds;
            [ReadOnly] public NativeArray<MeshColliderCookingOptions> options;
            public void Execute(int i) => Physics.BakeMesh(meshIds[i], false, options[i]);
        }

        /// <summary>Layer of kerb collision: hit by the wheel rays, ignored by vehicle body colliders (ProjectSetup layer 9).</summary>
        public const string KerbLayerName = "WorldKerb";
        public const string VehicleLayerName = "Vehicle";

        void Awake()
        {
            int kerb = LayerMask.NameToLayer(KerbLayerName), vehicle = LayerMask.NameToLayer(VehicleLayerName);
            if (kerb >= 0 && vehicle >= 0) Physics.IgnoreLayerCollision(vehicle, kerb, true);
            if (!deferCook) Cook();
        }

        /// <summary>
        /// Streamed tiles (ADR 0235): schedules the parallel bake without waiting for it. Returns false when there is
        /// nothing to cook (then <see cref="PollCook"/> only enables). Call once.
        /// </summary>
        public bool BeginCook()
        {
            if (m_Scheduled) return true;
            m_Scheduled = true;
            m_Deferred.Restart();
            int n = 0;
            foreach (var c in colliders) if (c != null && c.sharedMesh != null && !c.enabled) n++;
            if (n == 0) { m_Baked = true; return false; }
            m_Ids = new NativeArray<EntityId>(n, Allocator.Persistent);
            m_Opts = new NativeArray<MeshColliderCookingOptions>(n, Allocator.Persistent);
            int k = 0;
            foreach (var c in colliders)
            {
                if (c == null || c.sharedMesh == null || c.enabled) continue;
                m_Ids[k] = c.sharedMesh.GetEntityId();
                m_Opts[k] = c.cookingOptions;
                k++;
            }
            m_Handle = new BakeJob { meshIds = m_Ids, options = m_Opts }.Schedule(n, 1);
            JobHandle.ScheduleBatchedJobs();
            return true;
        }

        /// <summary>
        /// Streamed tiles: once the bake job has finished, enables at most <paramref name="maxEnablePerCall"/> colliders per
        /// call. Returns true when every collider is enabled (the tile may then open its edges). Never blocks on the job.
        /// </summary>
        public bool PollCook(int maxEnablePerCall)
        {
            if (!m_Scheduled) BeginCook();
            if (!m_Baked)
            {
                if (!m_Handle.IsCompleted) return false;
                m_Handle.Complete();
                if (m_Ids.IsCreated) m_Ids.Dispose();
                if (m_Opts.IsCreated) m_Opts.Dispose();
                m_Baked = true;
            }
            int end = Mathf.Min(colliders.Length, m_EnableNext + Mathf.Max(1, maxEnablePerCall));
            for (; m_EnableNext < end; m_EnableNext++)
            {
                var c = colliders[m_EnableNext];
                if (c != null && c.sharedMesh != null) c.enabled = true;
            }
            if (m_EnableNext < colliders.Length) return false;
            if (m_Deferred.IsRunning)
            {
                m_Deferred.Stop();
                LastCookMs = (float)m_Deferred.Elapsed.TotalMilliseconds;
                LastCookCount = colliders.Length;
                Debug.Log($"[WORLD] collision cooked deferred (streamed tile {name}): {colliders.Length} colliders, {LastCookMs:F0} ms wall clock over frames");
            }
            return true;
        }

        void OnDestroy()
        {
            // A tile unloaded while its bake is still running: finish the job before freeing its input.
            if (m_Scheduled && !m_Baked) m_Handle.Complete();
            if (m_Ids.IsCreated) m_Ids.Dispose();
            if (m_Opts.IsCreated) m_Opts.Dispose();
        }

        public void Cook()
        {
            var sw = Stopwatch.StartNew();
            int n = 0;
            foreach (var c in colliders) if (c != null && c.sharedMesh != null && !c.enabled) n++;
            if (n == 0) return;
            var ids = new NativeArray<EntityId>(n, Allocator.TempJob);
            var opts = new NativeArray<MeshColliderCookingOptions>(n, Allocator.TempJob);
            int k = 0;
            foreach (var c in colliders)
            {
                if (c == null || c.sharedMesh == null || c.enabled) continue;
                ids[k] = c.sharedMesh.GetEntityId();
                opts[k] = c.cookingOptions;
                k++;
            }
            new BakeJob { meshIds = ids, options = opts }.Schedule(n, 1).Complete();
            ids.Dispose();
            opts.Dispose();
            float bakeMs = (float)sw.Elapsed.TotalMilliseconds;
            foreach (var c in colliders) if (c != null && c.sharedMesh != null) c.enabled = true;
            LastCookMs = (float)sw.Elapsed.TotalMilliseconds;
            LastCookCount = n;
            Debug.Log($"[WORLD] collision cooked at load: {n} meshes, bake {bakeMs:F0} ms (parallel), enable {LastCookMs - bakeMs:F0} ms, total {LastCookMs:F0} ms");
        }
    }
}
