using System;
using UnityEngine;

namespace Game.World
{
    /// <summary>
    /// Root of an imported region (ADR 0003). Unity world (0, 0, 0) is the region anchor: chunk geometry is stored in
    /// local metres (X = east, Z = north) with absolute EVRF2007 heights, so the root is placed at y = −anchorZ.
    /// Global positions are kept in double (EPSG:2180 + height); <see cref="ToUnity"/> / <see cref="ToGlobal"/> convert.
    /// A floating-origin shift moves this root (and the vehicle) by −Δ and adds Δ to <see cref="originShift"/>; nothing
    /// in the region stores raw world positions, so the shift is exact.
    /// </summary>
    public sealed class WorldRegionRoot : MonoBehaviour
    {
        public string regionId;
        [Tooltip("EPSG:2180 x of the region anchor (east)")] public double anchorX;
        [Tooltip("EPSG:2180 y of the region anchor (north)")] public double anchorY;
        [Tooltip("EVRF2007 height of the anchor (m)")] public double anchorZ;
        public float chunkSizeM = 256f;
        [Tooltip("Accumulated floating-origin shift in local metres (x east, y up, z north)")]
        public Vector3 originShift;
        public ChunkInfo[] chunks = Array.Empty<ChunkInfo>();

        [Serializable]
        public struct ChunkInfo
        {
            public string id;
            public Vector2 minEN, maxEN;
            public bool corridor;
            public string sha256;
        }

        /// <summary>EPSG:2180 (x east, y north) + EVRF2007 height → Unity world position.</summary>
        public Vector3 ToUnity(double x, double y, double h) =>
            new Vector3((float)(x - anchorX) - originShift.x, (float)(h - anchorZ) - originShift.y, (float)(y - anchorY) - originShift.z);

        /// <summary>Region-local metres (E, N, absolute height) → Unity world position.</summary>
        public Vector3 LocalToUnity(double e, double n, double h) =>
            new Vector3((float)e - originShift.x, (float)(h - anchorZ) - originShift.y, (float)n - originShift.z);

        public void ToGlobal(Vector3 p, out double x, out double y, out double h)
        {
            x = anchorX + p.x + originShift.x;
            y = anchorY + p.z + originShift.z;
            h = anchorZ + p.y + originShift.y;
        }

        /// <summary>Shifts the region (not yet the dynamic objects) so that <paramref name="newOrigin"/> becomes (0,0,0).</summary>
        public void ShiftOrigin(Vector3 newOrigin)
        {
            originShift += newOrigin;
            transform.position -= newOrigin;
        }
    }
}
