// Minimal UnityEngine stand-in so the ADR 0283 HUD sources compile in .NET unchanged (semantics of the Unity scripting
// reference: Color = sRGB floats, Rect x/y = min corner, Overlaps strict). PlayerPrefs is an in-memory dictionary.
using System;
using System.Collections.Generic;

namespace UnityEngine
{
    public static class Mathf
    {
        public const float Epsilon = 1.401298E-45f;
        public static float Abs(float f) => Math.Abs(f);
        public static float Min(float a, float b) => a < b ? a : b;
        public static float Max(float a, float b) => a > b ? a : b;
        public static int Min(int a, int b) => a < b ? a : b;
        public static int Max(int a, int b) => a > b ? a : b;
        public static float Pow(float f, float p) => (float)Math.Pow(f, p);
        public static float Sqrt(float f) => (float)Math.Sqrt(f);
        public static float Round(float f) => (float)Math.Round(f, MidpointRounding.ToEven);
        public static int RoundToInt(float f) => (int)Math.Round(f, MidpointRounding.ToEven);
        public static float Clamp(float v, float lo, float hi) => v < lo ? lo : v > hi ? hi : v;
        public static int Clamp(int v, int lo, int hi) => v < lo ? lo : v > hi ? hi : v;
        public static float Clamp01(float v) => v < 0f ? 0f : v > 1f ? 1f : v;
        public static bool Approximately(float a, float b) => Math.Abs(b - a) < Math.Max(1E-06f * Math.Max(Math.Abs(a), Math.Abs(b)), Epsilon * 8f);
    }

    public struct Color
    {
        public float r, g, b, a;
        public Color(float r, float g, float b, float a = 1f) { this.r = r; this.g = g; this.b = b; this.a = a; }
        public static Color white => new Color(1f, 1f, 1f, 1f);
        public static Color black => new Color(0f, 0f, 0f, 1f);
        public static Color grey => new Color(0.5f, 0.5f, 0.5f, 1f);
    }

    public struct Vector2
    {
        public float x, y;
        public Vector2(float x, float y) { this.x = x; this.y = y; }
        public static Vector2 zero => new Vector2(0f, 0f);
        public static Vector2 operator -(Vector2 a, Vector2 b) => new Vector2(a.x - b.x, a.y - b.y);
        public static Vector2 operator *(Vector2 a, float d) => new Vector2(a.x * d, a.y * d);
        public static bool operator ==(Vector2 a, Vector2 b) => Math.Abs(a.x - b.x) < 1e-5f && Math.Abs(a.y - b.y) < 1e-5f;
        public static bool operator !=(Vector2 a, Vector2 b) => !(a == b);
        public override bool Equals(object o) => o is Vector2 v && v == this;
        public override int GetHashCode() => HashCode.Combine(x, y);
        public override string ToString() => $"({x:F1}, {y:F1})";
    }

    public struct Rect
    {
        public float x, y, width, height;
        public Rect(float x, float y, float width, float height) { this.x = x; this.y = y; this.width = width; this.height = height; }
        public float xMin => x;
        public float yMin => y;
        public float xMax => x + width;
        public float yMax => y + height;
        public Vector2 center => new Vector2(x + width * 0.5f, y + height * 0.5f);
        public Vector2 size => new Vector2(width, height);
        public static Rect MinMaxRect(float xmin, float ymin, float xmax, float ymax) => new Rect(xmin, ymin, xmax - xmin, ymax - ymin);
        public bool Overlaps(Rect o) => o.xMax > xMin && o.xMin < xMax && o.yMax > yMin && o.yMin < yMax;
        public override string ToString() => $"(x:{x:F1}, y:{y:F1}, width:{width:F1}, height:{height:F1})";
    }

    public static class PlayerPrefs
    {
        static readonly Dictionary<string, object> s = new Dictionary<string, object>();
        public static int GetInt(string k, int d) => s.TryGetValue(k, out var v) && v is int i ? i : d;
        public static float GetFloat(string k, float d) => s.TryGetValue(k, out var v) && v is float f ? f : d;
        public static void SetInt(string k, int v) => s[k] = v;
        public static void SetFloat(string k, float v) => s[k] = v;
        public static bool HasKey(string k) => s.ContainsKey(k);
        public static void DeleteKey(string k) => s.Remove(k);
        public static void Save() { }
    }
}

namespace Game.Controls
{
    public static class ControlInputLogger
    {
        public static readonly List<string> Lines = new List<string>();
        public static void WriteNoStack(string line) => Lines.Add(line);
    }
}
