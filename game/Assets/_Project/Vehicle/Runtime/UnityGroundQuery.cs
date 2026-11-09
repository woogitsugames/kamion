using System.Collections.Generic;
using Game.Vehicle.Physics;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// <see cref="IGroundQuery"/> backed by <see cref="UnityEngine.Physics.Raycast(Vector3, Vector3, out RaycastHit, float, int, QueryTriggerInteraction)"/>.
    /// The vehicle's own colliders live on the "Vehicle" layer, which the mask excludes. Surface coefficients come
    /// from a <see cref="GroundSurface"/> on the hit collider (cached per collider). Allocation-free after the cache
    /// has seen each collider once.
    /// </summary>
    public sealed class UnityGroundQuery : IGroundQuery
    {
        public const string VehicleLayerName = "Vehicle";

        readonly int m_Mask;
        readonly Dictionary<Collider, SurfaceProps> m_Cache = new Dictionary<Collider, SurfaceProps>(64);

        /// <summary>Number of raycasts issued since construction (telemetry / profiling).</summary>
        public long RaycastCount { get; private set; }

        public UnityGroundQuery(int vehicleLayer)
        {
            int mask = UnityEngine.Physics.DefaultRaycastLayers;
            if (vehicleLayer >= 0) mask &= ~(1 << vehicleLayer);
            m_Mask = mask;
        }

        /// <summary>Layer used for vehicle colliders: "Vehicle" if defined, otherwise the built-in Ignore Raycast layer.</summary>
        public static int ResolveVehicleLayer()
        {
            int l = LayerMask.NameToLayer(VehicleLayerName);
            return l >= 0 ? l : 2; // 2 = Ignore Raycast (excluded from DefaultRaycastLayers anyway)
        }

        public bool Raycast(Vec3 origin, Vec3 direction, double maxDistance, out GroundHit hit)
        {
            RaycastCount++;
            if (!UnityEngine.Physics.Raycast(origin.ToUnity(), direction.ToUnity(), out RaycastHit rh, (float)maxDistance, m_Mask, QueryTriggerInteraction.Ignore))
            {
                hit = default;
                return false;
            }
            var s = Lookup(rh.collider);
            hit.Point = rh.point.ToCore();
            hit.Normal = rh.normal.ToCore();
            hit.Distance = rh.distance;
            hit.FrictionScale = s.Friction;
            hit.RollingResistanceScale = s.RollingResistance;
            hit.SurfaceId = s.Id;
            return true;
        }

        SurfaceProps Lookup(Collider c)
        {
            if (m_Cache.TryGetValue(c, out var s)) return s;
            s = c.TryGetComponent(out GroundSurface gs) ? SurfaceTable.Get(gs.kind) : SurfaceTable.Get(SurfaceKind.DryAsphalt);
            m_Cache[c] = s;
            return s;
        }

        public void ClearCache() => m_Cache.Clear();
    }
}
