using System;

namespace Game.World.Streaming
{
    /// <summary>
    /// Where a tile's region root goes in Unity space for a given world anchor (ADR 0235, ADR 0003). Pure math in double;
    /// results cast to float once (tiles are at most a few km from the anchor, so float keeps ~1 mm).
    ///
    /// World anchor W = EPSG:2180 x / y and the EVRF2007 height that Unity (0, 0, 0) stands for:
    ///   unity = (X − Wx, h − Wz, Y − Wy).
    /// A region scene is imported with its own anchor A (root at (0, −Az, 0), chunk vertices in region-local metres with
    /// absolute heights). Placed for W, its root goes to (Ax − Wx, −Wz, Ay − Wy) and its WorldRegionRoot.originShift is
    /// (Wx − Ax, Wz − Az, Wy − Ay), which keeps ToUnity / ToGlobal / ShiftOrigin exact (position = (0, −Az, 0) − shift).
    /// The streamer rebases W horizontally to the anchor of the tile under the vehicle (the tile centre), so the vehicle
    /// stays within ~1.5 km of (0, 0, 0) (ADR 0003: re-centre beyond 2 km). Wz never changes (heights differ by < 100 m).
    /// </summary>
    public static class TilePlacement
    {
        public struct Placement
        {
            public float posX, posY, posZ;        // region root world position
            public float shiftX, shiftY, shiftZ;  // WorldRegionRoot.originShift
        }

        public static Placement For(double wx, double wy, double wz, double ax, double ay, double az)
        {
            double sx = wx - ax, sy = wz - az, sz = wy - ay;
            return new Placement
            {
                shiftX = (float)sx, shiftY = (float)sy, shiftZ = (float)sz,
                posX = (float)(ax - wx), posY = (float)(-wz), posZ = (float)(ay - wy),
            };
        }

        public static Placement For(double wx, double wy, double wz, TileData t) => For(wx, wy, wz, t.anchorX, t.anchorY, t.anchorZ);

        /// <summary>Unity offset every object moves by when the anchor goes from W to W' (horizontal only): −(W' − W).</summary>
        public static void RebaseOffset(double wx, double wy, double nwx, double nwy, out float ox, out float oz)
        {
            ox = (float)(wx - nwx);
            oz = (float)(wy - nwy);
        }

        /// <summary>Unity position → EPSG:2180 (x east, y north) for the anchor W.</summary>
        public static void ToGlobal(double wx, double wy, float ux, float uz, out double x, out double y)
        {
            x = wx + ux;
            y = wy + uz;
        }

        /// <summary>
        /// Should the anchor move to the current tile? Only when the vehicle is at least <paramref name="insideM"/> inside
        /// that tile (so a vehicle driving along a seam does not shift back and forth) and the anchor is not already there.
        /// </summary>
        public static bool ShouldRebase(TileGraph g, int current, double x, double y, double wx, double wy, double insideM)
        {
            if (current < 0) return false;
            var t = g.Tiles[current];
            if (Math.Abs(t.anchorX - wx) < 0.001 && Math.Abs(t.anchorY - wy) < 0.001) return false;
            return g.Contains(current, x, y, -insideM);
        }
    }
}
