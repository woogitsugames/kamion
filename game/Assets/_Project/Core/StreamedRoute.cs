using UnityEngine;

namespace Game.Core
{
    /// <summary>
    /// A world-space driving path that can be continued into a streamed tile (ADR 0235, int-stream-s23): the route autopilot
    /// (Game.Controls.PathFollowerDriverInput) implements it, the world streamer (Game.World) appends the start route of a
    /// neighbouring tile whose first point meets the path end. Lives in Game.Core because Game.World does not reference
    /// Game.Controls (asmdef unchanged).
    /// </summary>
    public interface IStreamedRoute
    {
        /// <summary>World-space last point of the path. false = no path, not driving it, or an explicit end was requested
        /// (route_end): such a path is never continued. Must not allocate (asked every streaming decision).</summary>
        bool TryGetPathEnd(out Vector3 worldEnd);

        /// <summary>Appends world-space points (a tile event; may allocate).</summary>
        void AppendPath(Vector3[] worldPoints, float[] speedLimitsKmh);
    }
}
