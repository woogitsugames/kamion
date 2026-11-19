// Minimal UnityEngine stand-in so the pure start search of ADR 0277 (Game.Gameplay.StartSearch,
// Game.World.StartClearance) compiles in the .NET runner unchanged. Only what those files use; semantics as the Unity
// scripting reference (Mathf.Lerp clamps t, Vector2.Lerp clamps t).
using System;

namespace UnityEngine
{
    public static class Mathf
    {
        public const float Deg2Rad = 0.017453292f;
        public static float Abs(float f) => Math.Abs(f);
        public static float Min(float a, float b) => a < b ? a : b;
        public static float Max(float a, float b) => a > b ? a : b;
        public static float Sqrt(float f) => (float)Math.Sqrt(f);
        public static float Sin(float f) => (float)Math.Sin(f);
        public static float Cos(float f) => (float)Math.Cos(f);
        public static float Clamp(float v, float lo, float hi) => v < lo ? lo : v > hi ? hi : v;
        public static float Clamp01(float v) => v < 0f ? 0f : v > 1f ? 1f : v;
        public static float Lerp(float a, float b, float t) => a + (b - a) * Clamp01(t);
    }

    public struct Vector2
    {
        public float x, y;
        public Vector2(float x, float y) { this.x = x; this.y = y; }
        public static Vector2 operator +(Vector2 a, Vector2 b) => new Vector2(a.x + b.x, a.y + b.y);
        public static Vector2 operator -(Vector2 a, Vector2 b) => new Vector2(a.x - b.x, a.y - b.y);
        public static Vector2 operator *(Vector2 a, float d) => new Vector2(a.x * d, a.y * d);
        public static float Dot(Vector2 a, Vector2 b) => a.x * b.x + a.y * b.y;
        public static Vector2 Lerp(Vector2 a, Vector2 b, float t) => a + (b - a) * Mathf.Clamp01(t);
    }

    public struct Vector3
    {
        public float x, y, z;
        public Vector3(float x, float y, float z) { this.x = x; this.y = y; this.z = z; }
    }
}

namespace Game.World
{
    /// <summary>Stand-in of the data part of the WorldBoundary MonoBehaviour (fields as in World/Runtime/WorldBoundary.cs).</summary>
    public sealed class WorldBoundary
    {
        public Closure[] closures = Array.Empty<Closure>();

        [Serializable]
        public struct Closure
        {
            public UnityEngine.Vector3 localPos;
            public float headingDeg;
            public Game.World.Streaming.TileSide exitSide;
            public float widthM;
            public string road;
            public float spanM;
        }
    }
}

namespace UnityEngine
{
    public sealed class TextAsset { public string text; }
    public static class Resources
    {
        public static T Load<T>(string path) => throw new NotSupportedException("Resources.Load requires Unity");
    }
    public static class JsonUtility
    {
        public static T FromJson<T>(string json) => System.Text.Json.JsonSerializer.Deserialize<T>(json,
            new System.Text.Json.JsonSerializerOptions { IncludeFields = true });
    }
}
