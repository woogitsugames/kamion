using System.Collections.Generic;
using UnityEngine;

namespace Game.Editor.Setup
{
    /// <summary>Small procedural mesh helpers for the DrivingLab generator (UVs in metres / tile size).</summary>
    public static class MeshGen
    {
        /// <summary>Axis-aligned box centred at the origin; top UVs = local XZ / tile.</summary>
        public static Mesh Slab(Vector3 size, float tile, string name)
        {
            var v = new List<Vector3>(); var n = new List<Vector3>(); var uv = new List<Vector2>(); var t = new List<int>();
            Vector3 h = size * 0.5f;
            void Face(Vector3 c, Vector3 u, Vector3 w, Vector3 normal, float su, float sw)
            {
                int i = v.Count;
                v.Add(c - u - w); v.Add(c - u + w); v.Add(c + u + w); v.Add(c + u - w);
                for (int k = 0; k < 4; k++) n.Add(normal);
                uv.Add(new Vector2(0, 0)); uv.Add(new Vector2(0, sw / tile)); uv.Add(new Vector2(su / tile, sw / tile)); uv.Add(new Vector2(su / tile, 0));
                t.Add(i); t.Add(i + 1); t.Add(i + 2); t.Add(i); t.Add(i + 2); t.Add(i + 3);
            }
            Face(new Vector3(0, h.y, 0), new Vector3(h.x, 0, 0), new Vector3(0, 0, h.z), Vector3.up, size.x, size.z);
            Face(new Vector3(0, -h.y, 0), new Vector3(0, 0, h.z), new Vector3(h.x, 0, 0), Vector3.down, size.z, size.x);
            Face(new Vector3(h.x, 0, 0), new Vector3(0, 0, h.z), new Vector3(0, h.y, 0), Vector3.right, size.z, size.y);
            Face(new Vector3(-h.x, 0, 0), new Vector3(0, h.y, 0), new Vector3(0, 0, h.z), Vector3.left, size.y, size.z);
            Face(new Vector3(0, 0, h.z), new Vector3(0, h.y, 0), new Vector3(h.x, 0, 0), Vector3.forward, size.y, size.x);
            Face(new Vector3(0, 0, -h.z), new Vector3(h.x, 0, 0), new Vector3(0, h.y, 0), Vector3.back, size.x, size.y);
            return Build(name, v, n, uv, t);
        }

        /// <summary>
        /// Extrudes a convex profile (z, y) along X from -width/2 to +width/2. Profile runs from z0 to z1 along the
        /// ground and is closed by a bottom face at y = 0. Top UVs = (x, arc length) / tile.
        /// </summary>
        public static Mesh Prism(Vector2[] profile, float width, float tile, string name)
        {
            var v = new List<Vector3>(); var n = new List<Vector3>(); var uv = new List<Vector2>(); var t = new List<int>();
            float hx = width * 0.5f, arc = 0f;
            for (int i = 0; i < profile.Length - 1; i++)
            {
                Vector2 a = profile[i], b = profile[i + 1];
                float len = (b - a).magnitude;
                Vector3 dir = new Vector3(0, b.y - a.y, b.x - a.x).normalized;
                Vector3 normal = Vector3.Cross(dir, Vector3.right).normalized;
                if (normal.y < 0) normal = -normal;
                int k = v.Count;
                v.Add(new Vector3(-hx, a.y, a.x)); v.Add(new Vector3(-hx, b.y, b.x)); v.Add(new Vector3(hx, b.y, b.x)); v.Add(new Vector3(hx, a.y, a.x));
                for (int q = 0; q < 4; q++) n.Add(normal);
                uv.Add(new Vector2(0, arc / tile)); uv.Add(new Vector2(0, (arc + len) / tile)); uv.Add(new Vector2(width / tile, (arc + len) / tile)); uv.Add(new Vector2(width / tile, arc / tile));
                t.Add(k); t.Add(k + 1); t.Add(k + 2); t.Add(k); t.Add(k + 2); t.Add(k + 3);
                arc += len;
            }
            // Side caps (fan from the first point; profile + bottom edge is convex).
            for (int s = -1; s <= 1; s += 2)
            {
                int k = v.Count;
                Vector3 normal = new Vector3(s, 0, 0);
                foreach (var p in profile) { v.Add(new Vector3(s * hx, p.y, p.x)); n.Add(normal); uv.Add(new Vector2(p.x / tile, p.y / tile)); }
                for (int i = 1; i < profile.Length - 1; i++)
                {
                    if (s > 0) { t.Add(k); t.Add(k + i); t.Add(k + i + 1); }
                    else { t.Add(k); t.Add(k + i + 1); t.Add(k + i); }
                }
            }
            // Bottom.
            {
                Vector2 a = profile[0], b = profile[profile.Length - 1];
                int k = v.Count;
                v.Add(new Vector3(-hx, 0, a.x)); v.Add(new Vector3(hx, 0, a.x)); v.Add(new Vector3(hx, 0, b.x)); v.Add(new Vector3(-hx, 0, b.x));
                for (int q = 0; q < 4; q++) { n.Add(Vector3.down); uv.Add(Vector2.zero); }
                t.Add(k); t.Add(k + 1); t.Add(k + 2); t.Add(k); t.Add(k + 2); t.Add(k + 3);
            }
            return Build(name, v, n, uv, t);
        }

        /// <summary>Flat ring in the XZ plane (y = 0) for painted circles.</summary>
        public static Mesh Ring(float radius, float lineWidth, int segments, string name)
        {
            var v = new List<Vector3>(); var n = new List<Vector3>(); var uv = new List<Vector2>(); var t = new List<int>();
            float r0 = radius - lineWidth * 0.5f, r1 = radius + lineWidth * 0.5f;
            for (int i = 0; i <= segments; i++)
            {
                float a = i * Mathf.PI * 2f / segments;
                var d = new Vector3(Mathf.Sin(a), 0, Mathf.Cos(a));
                v.Add(d * r0); v.Add(d * r1);
                n.Add(Vector3.up); n.Add(Vector3.up);
                uv.Add(new Vector2(0, i)); uv.Add(new Vector2(1, i));
                if (i < segments)
                {
                    int k = i * 2;
                    t.Add(k); t.Add(k + 1); t.Add(k + 2);
                    t.Add(k + 1); t.Add(k + 3); t.Add(k + 2);
                }
            }
            return Build(name, v, n, uv, t);
        }

        static Mesh Build(string name, List<Vector3> v, List<Vector3> n, List<Vector2> uv, List<int> t)
        {
            var m = new Mesh { name = name };
            m.SetVertices(v); m.SetNormals(n); m.SetUVs(0, uv); m.SetTriangles(t, 0);
            m.RecalculateBounds();
            m.RecalculateTangents();
            return m;
        }
    }
}
