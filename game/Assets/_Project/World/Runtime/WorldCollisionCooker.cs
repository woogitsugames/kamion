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
            Cook();
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
