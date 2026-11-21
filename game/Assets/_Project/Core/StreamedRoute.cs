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

    /// <summary>
    /// route-start-s24: a streamed route whose whole path can be swapped for another one that starts at the same point
    /// (the world streamer replaces the start tile's control route by a route link of the chosen trip destination when the
    /// game starts in that tile, Data/Streaming/route_links.yaml `replaces_route`). Separate from <see cref="IStreamedRoute"/>
    /// so existing implementations keep compiling.
    /// </summary>
    public interface IReplaceableStreamedRoute : IStreamedRoute
    {
        /// <summary>
        /// Replaces the path by <paramref name="worldPoints"/> and keeps driving from the point of the new path nearest to
        /// the current progress point (searched only up to the current route distance + a margin: the new path shares the
        /// start of the old one). false = nothing changed: no path / not driving it / explicit end (route_end), or the
        /// current progress point is more than <paramref name="maxOffsetM"/> from the new path (already past the fork).
        /// A tile event; may allocate.
        /// </summary>
        bool TryReplacePath(Vector3[] worldPoints, float[] speedLimitsKmh, float maxOffsetM);
    }
}
