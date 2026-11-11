using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.Setup
{
    /// <summary>ADR 0112 K3: rounded opaque rim in the existing Trim submesh. Glass, UVs and optics stay untouched.</summary>
    public static class MirrorGlassBezel
    {
        public struct Opening
        {
            public Vector3 centre, right, up, normal;
            public float width, height;
        }

        // WORKING_VALUE, metres. The inner contour covers the rectangular glass corners without changing its UV basis.
        public const float Border = .006f, Overlap = .0015f, Radius = .012f, Front = .003f, Depth = .009f;

        static Vector2[] Contour(float halfWidth, float halfHeight, float radius)
        {
            var result = new Vector2[20];
            for (int corner = 0; corner < 4; corner++)
            {
                float x = corner == 0 || corner == 3 ? halfWidth - radius : -halfWidth + radius;
                float y = corner < 2 ? halfHeight - radius : -halfHeight + radius;
                for (int step = 0; step <= 4; step++)
                {
                    float angle = (corner + step / 4f) * Mathf.PI * .5f;
                    result[corner * 5 + step] = new Vector2(x + Mathf.Cos(angle) * radius, y + Mathf.Sin(angle) * radius);
                }
            }
            return result;
        }

        public static Mesh Apply(Mesh source, Matrix4x4 toVehicle, IReadOnlyList<Opening> openings,
            int trimSlot, Vector3 materialSamplePoint, out int addedTriangles)
        {
            if (trimSlot < 0 || trimSlot >= source.subMeshCount) throw new ArgumentOutOfRangeException(nameof(trimSlot));
            int count = source.vertexCount;
            var positions = source.vertices.ToList();
            var normals = source.normals.ToList();
            var tangents = source.tangents.ToList();
            if (normals.Count != count || tangents.Count != count) throw new InvalidOperationException("Mirror rim needs the cab's authored normals and tangents.");
            var uvs = new List<Vector2>[8];
            for (int channel = 0; channel < 8; channel++)
            {
                var attribute = (VertexAttribute)((int)VertexAttribute.TexCoord0 + channel);
                if (!source.HasVertexAttribute(attribute)) continue;
                if (source.GetVertexAttributeDimension(attribute) != 2) throw new InvalidOperationException("Unexpected cab UV layout.");
                uvs[channel] = new List<Vector2>(); source.GetUVs(channel, uvs[channel]);
            }
            bool hasColour = source.HasVertexAttribute(VertexAttribute.Color);
            bool packedColour = hasColour && source.GetVertexAttributeFormat(VertexAttribute.Color) == VertexAttributeFormat.UNorm8;
            if (hasColour && !packedColour && source.GetVertexAttributeFormat(VertexAttribute.Color) != VertexAttributeFormat.Float32)
                throw new InvalidOperationException("Unexpected cab colour format.");
            var colours = hasColour && !packedColour ? source.colors.ToList() : null;
            var packed = packedColour ? source.colors32.ToList() : null;
            var indices = source.GetTriangles(trimSlot).ToList();
            var original = source.vertices;
            int sample = -1;
            float nearest = float.MaxValue;
            for (int i = 0; i < indices.Count; i += 3)
            {
                Vector3 centre = (original[indices[i]] + original[indices[i + 1]] + original[indices[i + 2]]) / 3f;
                float distance = (toVehicle.MultiplyPoint3x4(centre) - materialSamplePoint).sqrMagnitude;
                if (distance < nearest) { nearest = distance; sample = i; }
            }
            if (sample < 0) throw new InvalidOperationException("No Trim face for the mirror rim material sample.");
            var sampleUv = new Vector2[8];
            for (int channel = 0; channel < 8; channel++)
                if (uvs[channel] != null) sampleUv[channel] = (uvs[channel][indices[sample]] + uvs[channel][indices[sample + 1]] + uvs[channel][indices[sample + 2]]) / 3f;
            Color sampleColour = Color.white;
            if (colours != null) sampleColour = (colours[indices[sample]] + colours[indices[sample + 1]] + colours[indices[sample + 2]]) / 3f;
            if (packed != null) sampleColour = ((Color)packed[indices[sample]] + (Color)packed[indices[sample + 1]] + (Color)packed[indices[sample + 2]]) / 3f;
            var inverse = toVehicle.inverse;
            void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 normal)
            {
                int first = positions.Count;
                Vector3 tangent = (b - a).normalized;
                Vector3 localNormal = toVehicle.transpose.MultiplyVector(normal).normalized;
                Vector3 localTangent = inverse.MultiplyVector(tangent).normalized;
                float hand = Vector3.Dot(Vector3.Cross(normal, tangent), d - a) >= 0 ? 1f : -1f;
                foreach (var point in new[] { a, b, c, d })
                {
                    positions.Add(inverse.MultiplyPoint3x4(point)); normals.Add(localNormal);
                    tangents.Add(new Vector4(localTangent.x, localTangent.y, localTangent.z, hand));
                    for (int channel = 0; channel < 8; channel++) if (uvs[channel] != null) uvs[channel].Add(sampleUv[channel]);
                    if (colours != null) colours.Add(sampleColour);
                    if (packed != null) packed.Add((Color32)sampleColour);
                }
                bool forward = Vector3.Dot(Vector3.Cross(b - a, c - a), normal) >= 0f;
                indices.AddRange(forward ? new[] { first, first + 1, first + 2, first, first + 2, first + 3 }
                    : new[] { first, first + 2, first + 1, first, first + 3, first + 2 });
            }
            int before = indices.Count;
            foreach (var opening in openings)
            {
                var outer = Contour(opening.width * .5f + Border, opening.height * .5f + Border, Radius + Border);
                var inner = Contour(opening.width * .5f - Overlap, opening.height * .5f - Overlap, Radius);
                Vector3 Point(Vector2 p, float depth) => opening.centre + opening.right * p.x + opening.up * p.y + opening.normal * depth;
                for (int i = 0; i < outer.Length; i++)
                {
                    int next = (i + 1) % outer.Length;
                    Vector3 oa = Point(outer[i], Front), ob = Point(outer[next], Front);
                    Vector3 ia = Point(inner[i], Front), ib = Point(inner[next], Front);
                    Quad(oa, ob, ib, ia, opening.normal);
                    Quad(oa - opening.normal * Depth, ob - opening.normal * Depth, ob, oa,
                        Vector3.Cross(ob - oa, opening.normal).normalized);
                    Quad(ib - opening.normal * Depth, ia - opening.normal * Depth, ia, ib,
                        -Vector3.Cross(ib - ia, opening.normal).normalized);
                }
            }
            if (positions.Count > 65535 && source.indexFormat == IndexFormat.UInt16) throw new InvalidOperationException("Mirror rim exceeds the cab's index format.");
            var result = UnityEngine.Object.Instantiate(source);
            result.name = source.name + "_MirrorBezel";
            result.SetVertices(positions); result.SetNormals(normals); result.SetTangents(tangents);
            for (int channel = 0; channel < 8; channel++) if (uvs[channel] != null) result.SetUVs(channel, uvs[channel]);
            if (colours != null) result.SetColors(colours);
            if (packed != null) result.SetColors(packed);
            result.SetTriangles(indices, trimSlot); result.RecalculateBounds();
            addedTriangles = (indices.Count - before) / 3;
            return result;
        }
    }
}
