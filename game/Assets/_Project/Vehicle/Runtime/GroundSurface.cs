using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Tags a ground collider with its surface kind. Colliders without this component count as dry asphalt.
    /// Looked up once per collider by <see cref="UnityGroundQuery"/> and cached.
    /// </summary>
    public sealed class GroundSurface : MonoBehaviour
    {
        public SurfaceKind kind = SurfaceKind.DryAsphalt;
    }
}
