// Minimal UnityEngine stand-in so the ADR 0243 control sources compile in .NET unchanged. Only what those files use;
// semantics follow the Unity scripting reference (Rect: x/y = min corner, Overlaps strict; JsonUtility: public fields,
// FromJsonOverwrite keeps fields missing in the JSON). PlayerPrefs is an in-memory dictionary.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;

namespace UnityEngine
{
    public static class Mathf
    {
        public const float Rad2Deg = 57.29578f, Deg2Rad = 0.017453292f, PI = 3.14159274f, Epsilon = 1.401298E-45f;
        public static float Abs(float f) => Math.Abs(f);
        public static int Abs(int v) => Math.Abs(v);
        public static float Sign(float f) => f >= 0f ? 1f : -1f;
        public static float Min(float a, float b) => a < b ? a : b;
        public static int Min(int a, int b) => a < b ? a : b;
        public static float Max(float a, float b) => a > b ? a : b;
        public static int Max(int a, int b) => a > b ? a : b;
        public static float Sqrt(float f) => (float)Math.Sqrt(f);
        public static float Pow(float f, float p) => (float)Math.Pow(f, p);
        public static float Exp(float f) => (float)Math.Exp(f);
        public static float Sin(float f) => (float)Math.Sin(f);
        public static float Cos(float f) => (float)Math.Cos(f);
        public static float Atan2(float y, float x) => (float)Math.Atan2(y, x);
        public static float Floor(float f) => (float)Math.Floor(f);
        public static int FloorToInt(float f) => (int)Math.Floor(f);
        public static float Round(float f) => (float)Math.Round(f, MidpointRounding.ToEven);
        public static int RoundToInt(float f) => (int)Math.Round(f, MidpointRounding.ToEven);
        public static float Repeat(float t, float length) => Clamp(t - (float)Math.Floor(t / length) * length, 0f, length);
        public static float DeltaAngle(float current, float target) { float d = Repeat(target - current, 360f); if (d > 180f) d -= 360f; return d; }
        public static float MoveTowards(float c, float t, float maxDelta) => Math.Abs(t - c) <= maxDelta ? t : c + Math.Sign(t - c) * maxDelta;
        public static float Clamp(float v, float lo, float hi) => v < lo ? lo : v > hi ? hi : v;
        public static int Clamp(int v, int lo, int hi) => v < lo ? lo : v > hi ? hi : v;
        public static float Clamp01(float v) => v < 0f ? 0f : v > 1f ? 1f : v;
        public static float Lerp(float a, float b, float t) => a + (b - a) * Clamp01(t);
        public static float InverseLerp(float a, float b, float v) => a != b ? Clamp01((v - a) / (b - a)) : 0f;
        public static float SmoothStep(float from, float to, float t) { t = Clamp01(t); t = -2f * t * t * t + 3f * t * t; return to * t + from * (1f - t); }
        public static bool Approximately(float a, float b) => Math.Abs(b - a) < Math.Max(1E-06f * Math.Max(Math.Abs(a), Math.Abs(b)), Epsilon * 8f);
    }

    public struct Vector2
    {
        public float x, y;
        public Vector2(float x, float y) { this.x = x; this.y = y; }
        public float magnitude => (float)Math.Sqrt(x * x + y * y);
        public float sqrMagnitude => x * x + y * y;
        public static Vector2 zero => new Vector2(0f, 0f);
        public static Vector2 one => new Vector2(1f, 1f);
        public static Vector2 up => new Vector2(0f, 1f);
        public static Vector2 operator +(Vector2 a, Vector2 b) => new Vector2(a.x + b.x, a.y + b.y);
        public static Vector2 operator -(Vector2 a, Vector2 b) => new Vector2(a.x - b.x, a.y - b.y);
        public static Vector2 operator *(Vector2 a, float d) => new Vector2(a.x * d, a.y * d);
        public static Vector2 operator *(float d, Vector2 a) => new Vector2(a.x * d, a.y * d);
        public static Vector2 operator /(Vector2 a, float d) => new Vector2(a.x / d, a.y / d);
        public static bool operator ==(Vector2 a, Vector2 b) => a.x == b.x && a.y == b.y;
        public static bool operator !=(Vector2 a, Vector2 b) => !(a == b);
        public override bool Equals(object o) => o is Vector2 v && v == this;
        public override int GetHashCode() => HashCode.Combine(x, y);
        public override string ToString() => $"({x:F1}, {y:F1})";
    }

    public struct Vector3
    {
        public float x, y, z;
        public Vector3(float x, float y, float z) { this.x = x; this.y = y; this.z = z; }
        public static Vector3 zero => new Vector3(0f, 0f, 0f);
        public static Vector3 forward => new Vector3(0f, 0f, 1f);
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
        public static Rect MinMaxRect(float xmin, float ymin, float xmax, float ymax) => new Rect(xmin, ymin, xmax - xmin, ymax - ymin);
        public bool Overlaps(Rect o) => o.xMax > xMin && o.xMin < xMax && o.yMax > yMin && o.yMin < yMax;
        public override string ToString() => $"(x:{x:F1}, y:{y:F1}, width:{width:F1}, height:{height:F1})";
    }

    public static class Debug
    {
        public static void Log(object m) { }
        public static void LogWarning(object m) { }
    }

    public class TextAsset
    {
        public string text;
    }

    /// <summary>Resources.Load of a TextAsset reads the real file under game/Assets/_Project/Input/Resources.</summary>
    public static class Resources
    {
        public static T Load<T>(string path) where T : TextAsset, new()
        {
            var dir = new System.IO.DirectoryInfo(AppContext.BaseDirectory);
            while (dir != null && !System.IO.Directory.Exists(System.IO.Path.Combine(dir.FullName, "game", "Assets"))) dir = dir.Parent;
            if (dir == null) return null;
            string f = System.IO.Path.Combine(dir.FullName, "game", "Assets", "_Project", "Input", "Resources", path + ".json");
            return System.IO.File.Exists(f) ? new T { text = System.IO.File.ReadAllText(f) } : null;
        }
    }

    public static class PlayerPrefs
    {
        static readonly Dictionary<string, object> s = new Dictionary<string, object>();
        public static bool HasKey(string k) => s.ContainsKey(k);
        public static void DeleteKey(string k) => s.Remove(k);
        public static string GetString(string k, string d = "") => s.TryGetValue(k, out var v) && v is string t ? t : d;
        public static void SetString(string k, string v) => s[k] = v;
        public static int GetInt(string k, int d = 0) => s.TryGetValue(k, out var v) && v is int t ? t : d;
        public static void SetInt(string k, int v) => s[k] = v;
        public static void Save() { }
    }

    /// <summary>JsonUtility over public instance fields (bool, int, float), as ControlSettings uses it.</summary>
    public static class JsonUtility
    {
        public static string ToJson(object o)
        {
            var sb = new StringBuilder("{");
            bool first = true;
            foreach (var f in o.GetType().GetFields(BindingFlags.Public | BindingFlags.Instance))
            {
                if (!first) sb.Append(',');
                first = false;
                sb.Append('"').Append(f.Name).Append("\":");
                object v = f.GetValue(o);
                sb.Append(v is bool b ? (b ? "true" : "false") : Convert.ToString(v, CultureInfo.InvariantCulture));
            }
            return sb.Append('}').ToString();
        }

        public static void FromJsonOverwrite(string json, object o)
        {
            using var doc = JsonDocument.Parse(json);   // throws on corrupt input, like Unity's ArgumentException
            foreach (var p in doc.RootElement.EnumerateObject())
            {
                var f = o.GetType().GetField(p.Name, BindingFlags.Public | BindingFlags.Instance);
                if (f == null) continue;
                if (f.FieldType == typeof(bool)) f.SetValue(o, p.Value.ValueKind == JsonValueKind.True);
                else if (f.FieldType == typeof(int)) f.SetValue(o, (int)p.Value.GetDouble());
                else if (f.FieldType == typeof(float)) f.SetValue(o, (float)p.Value.GetDouble());
                else if (f.FieldType == typeof(float[]) && p.Value.ValueKind == JsonValueKind.Array)
                {
                    var a = new float[p.Value.GetArrayLength()];
                    int i = 0;
                    foreach (var e in p.Value.EnumerateArray()) a[i++] = (float)e.GetDouble();
                    f.SetValue(o, a);
                }
            }
        }
    }
}

namespace Game.Controls
{
    /// <summary>Stand-ins for the Input System / logging types ControlSettings touches (not under test here).</summary>
    public sealed class GyroSteering
    {
        public bool Enabled, Invert, SpeedSensitive;
        public float MaxTiltDeg;
    }

    public static class ControlInputLogger
    {
        public static void WriteNoStack(string line) { }
    }
}
