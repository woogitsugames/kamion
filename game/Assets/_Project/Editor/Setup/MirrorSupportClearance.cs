using System;
using System.Collections.Generic;
using UnityEngine;

namespace Game.Editor.Setup
{
    /// <summary>ADR 0112: bend only the four disconnected support islands, preserving the cab's topology and UVs.</summary>
    public static class MirrorSupportClearance
    {
        [Serializable]
        public struct Support
        {
            public string name;
            public Vector3 start, end, right, up, shift;
            public float halfWidth, halfHeight;
        }

        public static Mesh Apply(Mesh source, Matrix4x4 toVehicle, IReadOnlyList<Support> supports, out int moved)
        {
            moved = 0;
            var vertices = source.vertices;
            var points = new Vector3[vertices.Length];
            var parent = new int[vertices.Length];
            int Find(int i) { while (parent[i] != i) { parent[i] = parent[parent[i]]; i = parent[i]; } return i; }
            void Join(int a, int b) { parent[Find(a)] = Find(b); }
            var welded = new Dictionary<Vector3Int, int>();
            for (int i = 0; i < vertices.Length; i++)
            {
                parent[i] = i;
                var p = points[i] = toVehicle.MultiplyPoint3x4(vertices[i]);
                // Atlas seams and split normals duplicate positions. Weld for island identification only.
                var key = new Vector3Int(Mathf.RoundToInt(p.x * 10000f), Mathf.RoundToInt(p.y * 10000f), Mathf.RoundToInt(p.z * 10000f));
                if (welded.TryGetValue(key, out int other)) Join(i, other); else welded.Add(key, i);
            }
            var triangles = source.triangles;
            for (int i = 0; i < triangles.Length; i += 3)
            {
                Join(triangles[i], triangles[i + 1]); Join(triangles[i], triangles[i + 2]);
            }
            var islands = new Dictionary<int, List<int>>();
            for (int i = 0; i < vertices.Length; i++)
            {
                int key = Find(i);
                if (!islands.TryGetValue(key, out var island)) islands.Add(key, island = new List<int>());
                island.Add(i);
            }
            var normals = source.normals;
            var tangents = source.tangents;
            var inverse = toVehicle.inverse;
            foreach (var support in supports)
            {
                Vector3 axis = support.end - support.start;
                float length = axis.magnitude;
                axis /= length;
                List<int> selected = null;
                int matches = 0;
                foreach (var island in islands.Values)
                {
                    if (island.Count < 4) continue;
                    bool inside = true;
                    float lo = float.MaxValue, hi = float.MinValue;
                    foreach (int i in island)
                    {
                        Vector3 d = points[i] - support.start;
                        float along = Vector3.Dot(d, axis);
                        if (along < -.002f || along > length + .002f ||
                            Mathf.Abs(Vector3.Dot(d, support.right)) > support.halfWidth + .002f ||
                            Mathf.Abs(Vector3.Dot(d, support.up)) > support.halfHeight + .002f)
                        { inside = false; break; }
                        lo = Mathf.Min(lo, along); hi = Mathf.Max(hi, along);
                    }
                    if (!inside || hi - lo < length * .5f) continue;
                    matches++; selected = island;
                }
                if (matches != 1) throw new InvalidOperationException($"Mirror support {support.name}: expected one island in {source.name}, found {matches}. Recheck authored support bounds after a truck export.");
                Vector3 target = support.end + support.shift - support.start;
                float scale = target.magnitude / length;
                var turn = Quaternion.FromToRotation(axis, target.normalized);
                foreach (int i in selected)
                {
                    Vector3 d = points[i] - support.start;
                    vertices[i] = inverse.MultiplyPoint3x4(support.start + turn * (d + axis * (Vector3.Dot(d, axis) * (scale - 1f))));
                    if (normals.Length == vertices.Length)
                    {
                        Vector3 n = toVehicle.inverse.transpose.MultiplyVector(normals[i]);
                        n = turn * (n + axis * (Vector3.Dot(n, axis) * (1f / scale - 1f)));
                        normals[i] = toVehicle.transpose.MultiplyVector(n).normalized;
                    }
                    if (tangents.Length == vertices.Length)
                    {
                        Vector3 t = toVehicle.MultiplyVector(new Vector3(tangents[i].x, tangents[i].y, tangents[i].z));
                        t = inverse.MultiplyVector(turn * (t + axis * (Vector3.Dot(t, axis) * (scale - 1f)))).normalized;
                        tangents[i] = new Vector4(t.x, t.y, t.z, tangents[i].w);
                    }
                    moved++;
                }
            }
            var result = UnityEngine.Object.Instantiate(source);
            result.name = source.name + "_MirrorSupports";
            result.vertices = vertices;
            if (normals.Length == vertices.Length) result.normals = normals;
            if (tangents.Length == vertices.Length) result.tangents = tangents;
            result.RecalculateBounds();
            return result;
        }
    }
}
