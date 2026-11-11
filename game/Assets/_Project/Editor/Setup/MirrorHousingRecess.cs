using System.Collections.Generic;
using UnityEngine;

namespace Game.Editor.Setup
{
    /// <summary>
    /// ADR 0104: the exported aero head is a solid rounded box; tilting the glass embeds its far edge in that box.
    /// Recess its inner backing, preserving the outer bezel, all topology, UVs, slots and optics. Editor build only.
    /// </summary>
    public static class MirrorHousingRecess
    {
        // WORKING_VALUE: 30 mm inside an 80 mm housing; 6 mm clearance round the adjustable glass.
        public const float Depth = 0.030f, Clearance = 0.006f;

        public struct Opening
        {
            public Vector3 centre, right, up, normal;
            public float halfWidth, bottom, top;
        }

        /// <summary>Returns a copy, or null when no backing vertices need moving. Never changes the input mesh.</summary>
        public static Mesh Apply(Mesh source, Matrix4x4 meshToVehicle, IReadOnlyList<Opening> openings, out int moved)
        {
            moved = 0;
            if (source == null || openings.Count == 0) return null;
            var positions = source.vertices;
            var changed = new bool[positions.Length];
            var inverse = meshToVehicle.inverse;
            for (int i = 0; i < positions.Length; i++)
            {
                Vector3 p = meshToVehicle.MultiplyPoint3x4(positions[i]);
                foreach (var opening in openings)
                {
                    Vector3 d = p - opening.centre;
                    float z = Vector3.Dot(d, opening.normal), y = Vector3.Dot(d, opening.up);
                    if (Mathf.Abs(Vector3.Dot(d, opening.right)) > opening.halfWidth + Clearance ||
                        y < opening.bottom - Clearance || y > opening.top + Clearance || z <= -Depth || z > 0.002f)
                        continue;
                    positions[i] = inverse.MultiplyPoint3x4(p - opening.normal * (z + Depth));
                    changed[i] = true;
                    moved++;
                    break;
                }
            }
            if (moved == 0) return null;
            var result = Object.Instantiate(source);
            result.name = source.name + "_MirrorRecess";
            result.vertices = positions;

            // Update shading only on the deformed housing faces and their immediate neighbours. Preserve the rest of
            // the cab's authored split normals, and keep the existing tangent direction orthogonal to the new normal.
            var normals = source.normals;
            if (normals.Length == positions.Length)
            {
                var affected = new bool[positions.Length];
                var sums = new Vector3[positions.Length];
                for (int sub = 0; sub < source.subMeshCount; sub++)
                {
                    var indices = source.GetTriangles(sub);
                    for (int t = 0; t < indices.Length; t += 3)
                    {
                        int a = indices[t], b = indices[t + 1], c = indices[t + 2];
                        Vector3 n = Vector3.Cross(positions[b] - positions[a], positions[c] - positions[a]);
                        sums[a] += n; sums[b] += n; sums[c] += n;
                        if (changed[a] || changed[b] || changed[c]) affected[a] = affected[b] = affected[c] = true;
                    }
                }
                var tangents = source.tangents;
                for (int i = 0; i < positions.Length; i++)
                {
                    if (!affected[i] || sums[i].sqrMagnitude < 1e-16f) continue;
                    normals[i] = sums[i].normalized;
                    if (tangents.Length != positions.Length) continue;
                    Vector3 t = new Vector3(tangents[i].x, tangents[i].y, tangents[i].z);
                    t = Vector3.ProjectOnPlane(t, normals[i]).normalized;
                    if (t.sqrMagnitude > 0f) tangents[i] = new Vector4(t.x, t.y, t.z, tangents[i].w);
                }
                result.normals = normals;
                if (tangents.Length == positions.Length) result.tangents = tangents;
            }
            result.bounds = source.bounds;
            return result;
        }
    }
}
