using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace Game.Editor.Setup
{
    /// <summary>Maps the authored 5 cm rim tile to the physical CC0 crop, without scaling the 12 cm hub tile.</summary>
    public static class CabLeatherMapping
    {
        public static Mesh Apply(Mesh source, Matrix4x4 toWheel, IReadOnlyList<int> leatherSlots,
            float minRadius, float maxRadius, float ratio, out int scaledVertices)
        {
            if (!(minRadius > 0 && maxRadius > minRadius && ratio > 0)) throw new ArgumentOutOfRangeException(nameof(ratio));
            var vertices = source.vertices;
            var uv = source.uv;
            if (uv.Length != vertices.Length) throw new InvalidOperationException("Missing wheel detail UV");
            var selected = new HashSet<int>();
            var slots = new HashSet<int>(leatherSlots);
            bool InRim(int i)
            {
                var p = toWheel.MultiplyPoint3x4(vertices[i]);
                float radius = new Vector2(p.x, p.y).magnitude;
                return radius >= minRadius && radius <= maxRadius;
            }
            foreach (int slot in slots)
            {
                var indices = source.GetTriangles(slot);
                for (int j = 0; j < indices.Length; j += 3)
                {
                    bool a = InRim(indices[j]), b = InRim(indices[j + 1]), c = InRim(indices[j + 2]);
                    if (a != b || b != c) throw new InvalidOperationException("Rim mapping boundary crosses a leather triangle; review authored regions.");
                    if (a) { selected.Add(indices[j]); selected.Add(indices[j + 1]); selected.Add(indices[j + 2]); }
                }
            }
            for (int slot = 0; slot < source.subMeshCount; ++slot)
                if (!slots.Contains(slot) && source.GetTriangles(slot).Any(selected.Contains))
                    throw new InvalidOperationException("Wheel rim UV vertices shared with another material");
            if (selected.Count == 0) throw new InvalidOperationException("No leather rim vertices found");
            foreach (int i in selected) uv[i] *= ratio;
            Mesh result = UnityEngine.Object.Instantiate(source);
            result.name = source.name + "_CC0LeatherUv";
            result.uv = uv;
            scaledVertices = selected.Count;
            return result;
        }
    }
}
