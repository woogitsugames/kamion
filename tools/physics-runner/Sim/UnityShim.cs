// Minimal UnityEngine stand-in so the game's steering-input sources (Game.Controls: TouchSteeringWheel, SteeringColumn,
// SteeringMath, DriverIntent) compile in the .NET runner unchanged (ADR 0149). Only what those files use; semantics copied
// from the Unity scripting reference (Mathf.Sign(0) = 1, MoveTowards, DeltaAngle, Repeat). Not used by the physics core.
using System;
using System.Reflection;
using System.Text.Json;

namespace UnityEngine
{
    public static class Mathf
    {
        public const float Rad2Deg = 57.29578f;
        public const float Deg2Rad = 0.017453292f;
        public static float Abs(float f) => Math.Abs(f);
        public static float Sign(float f) => f >= 0f ? 1f : -1f;
        public static float Min(float a, float b) => a < b ? a : b;
        public static float Max(float a, float b) => a > b ? a : b;
        public static float Sqrt(float f) => (float)Math.Sqrt(f);
        public static float Exp(float f) => (float)Math.Exp(f);
        public static float Atan2(float y, float x) => (float)Math.Atan2(y, x);
        public static float Clamp(float v, float lo, float hi) => v < lo ? lo : v > hi ? hi : v;
        public static float Clamp01(float v) => v < 0f ? 0f : v > 1f ? 1f : v;
        public static float Lerp(float a, float b, float t) => a + (b - a) * Clamp01(t);
        public static float SmoothStep(float from, float to, float t) { t = Clamp01(t); t = -2f * t * t * t + 3f * t * t; return to * t + from * (1f - t); }
        public static float MoveTowards(float current, float target, float maxDelta)
            => Math.Abs(target - current) <= maxDelta ? target : current + Sign(target - current) * maxDelta;
        public static float Repeat(float t, float length) => Clamp(t - (float)Math.Floor(t / length) * length, 0f, length);
        public static float DeltaAngle(float current, float target)
        {
            float d = Repeat(target - current, 360f);
            if (d > 180f) d -= 360f;
            return d;
        }
    }

    public struct Vector2
    {
        public float x, y;
        public Vector2(float x, float y) { this.x = x; this.y = y; }
        public float magnitude => (float)Math.Sqrt(x * x + y * y);
        public static Vector2 zero => new Vector2(0f, 0f);
        public static Vector2 operator +(Vector2 a, Vector2 b) => new Vector2(a.x + b.x, a.y + b.y);
        public static Vector2 operator -(Vector2 a, Vector2 b) => new Vector2(a.x - b.x, a.y - b.y);
        public static Vector2 operator *(Vector2 a, float d) => new Vector2(a.x * d, a.y * d);
        public static Vector2 operator *(float d, Vector2 a) => new Vector2(a.x * d, a.y * d);
        public static float Dot(Vector2 a, Vector2 b) => a.x * b.x + a.y * b.y;
    }

    public struct Vector3
    {
        public float x, y, z;
        public Vector3(float x, float y, float z) { this.x = x; this.y = y; this.z = z; }
    }

    public class Object { }
    public class TextAsset : Object { public string text = ""; }

    public static class Resources
    {
        public static T Load<T>(string path) where T : Object => null;
    }

    public static class JsonUtility
    {
        /// <summary>Public float / float[] / bool / int / string fields by name (what SteeringFeel uses).</summary>
        public static void FromJsonOverwrite(string json, object target)
        {
            using var doc = JsonDocument.Parse(json);
            var type = target.GetType();
            foreach (var p in doc.RootElement.EnumerateObject())
            {
                var f = type.GetField(p.Name, BindingFlags.Public | BindingFlags.Instance);
                if (f == null) continue;
                var v = p.Value;
                if (f.FieldType == typeof(float)) f.SetValue(target, (float)v.GetDouble());
                else if (f.FieldType == typeof(int)) f.SetValue(target, v.GetInt32());
                else if (f.FieldType == typeof(bool)) f.SetValue(target, v.GetBoolean());
                else if (f.FieldType == typeof(string)) f.SetValue(target, v.GetString());
                else if (f.FieldType == typeof(float[]))
                {
                    var a = new float[v.GetArrayLength()];
                    int i = 0;
                    foreach (var e in v.EnumerateArray()) a[i++] = (float)e.GetDouble();
                    f.SetValue(target, a);
                }
            }
        }
    }
}

namespace Game.Controls
{
    // TurnSignal.cs (which defines this enum) carries Unity-only behaviour; the runner needs just the enum for DriverIntent.
    public enum TurnSignalRequest : byte { None = 0, Left = 1, Right = 2, Hazard = 3 }
}
