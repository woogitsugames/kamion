// Minimal UnityEngine stand-in so the game's navigation sources (Game.Core.Navigation: RouteGraph, RoutePlanner,
// RoutePath, RouteTracker, NavEta, NavVoice) compile in the .NET runner unchanged (ADR 0150). Only what those files
// use; semantics copied from the Unity scripting reference (SignedAngle: + = counter-clockwise from `from` to `to`,
// i.e. + = left for x-east/y-north). Resources.Load reads the real files under
// game/Assets/_Project/UI/Resources (repo root found by walking up from the assembly location), so the runner
// tests the committed <region>_route.bytes.
using System;
using System.IO;

namespace UnityEngine
{
    public static class Mathf
    {
        public const float Rad2Deg = 57.29578f;
        public const float Deg2Rad = 0.017453292f;
        public static float Abs(float f) => Math.Abs(f);
        public static int Abs(int v) => Math.Abs(v);
        public static float Sign(float f) => f >= 0f ? 1f : -1f;
        public static float Min(float a, float b) => a < b ? a : b;
        public static int Min(int a, int b) => a < b ? a : b;
        public static float Max(float a, float b) => a > b ? a : b;
        public static int Max(int a, int b) => a > b ? a : b;
        public static float Sqrt(float f) => (float)Math.Sqrt(f);
        public static float Sin(float f) => (float)Math.Sin(f);
        public static float Cos(float f) => (float)Math.Cos(f);
        public static float Atan2(float y, float x) => (float)Math.Atan2(y, x);
        public static float Clamp(float v, float lo, float hi) => v < lo ? lo : v > hi ? hi : v;
        public static int Clamp(int v, int lo, int hi) => v < lo ? lo : v > hi ? hi : v;
        public static float Clamp01(float v) => v < 0f ? 0f : v > 1f ? 1f : v;
        public static float Lerp(float a, float b, float t) => a + (b - a) * Clamp01(t);
    }

    public struct Vector2 : IEquatable<Vector2>
    {
        public float x, y;
        public Vector2(float x, float y) { this.x = x; this.y = y; }
        public float magnitude => (float)Math.Sqrt(x * x + y * y);
        public float sqrMagnitude => x * x + y * y;
        public Vector2 normalized { get { float m = magnitude; return m > 1e-5f ? new Vector2(x / m, y / m) : zero; } }
        public static Vector2 zero => new Vector2(0f, 0f);
        public static Vector2 up => new Vector2(0f, 1f);
        public static Vector2 operator +(Vector2 a, Vector2 b) => new Vector2(a.x + b.x, a.y + b.y);
        public static Vector2 operator -(Vector2 a, Vector2 b) => new Vector2(a.x - b.x, a.y - b.y);
        public static Vector2 operator -(Vector2 a) => new Vector2(-a.x, -a.y);
        public static Vector2 operator *(Vector2 a, float d) => new Vector2(a.x * d, a.y * d);
        public static Vector2 operator *(float d, Vector2 a) => new Vector2(a.x * d, a.y * d);
        public static Vector2 operator /(Vector2 a, float d) => new Vector2(a.x / d, a.y / d);
        public static bool operator ==(Vector2 a, Vector2 b) => a.x == b.x && a.y == b.y;
        public static bool operator !=(Vector2 a, Vector2 b) => !(a == b);
        public bool Equals(Vector2 o) => this == o;
        public override bool Equals(object o) => o is Vector2 v && Equals(v);
        public override int GetHashCode() => x.GetHashCode() ^ (y.GetHashCode() << 2);
        public static float Dot(Vector2 a, Vector2 b) => a.x * b.x + a.y * b.y;
        public static float Distance(Vector2 a, Vector2 b) => (a - b).magnitude;
        public static Vector2 Min(Vector2 a, Vector2 b) => new Vector2(Math.Min(a.x, b.x), Math.Min(a.y, b.y));
        public static Vector2 Max(Vector2 a, Vector2 b) => new Vector2(Math.Max(a.x, b.x), Math.Max(a.y, b.y));
        public static Vector2 Lerp(Vector2 a, Vector2 b, float t) => a + (b - a) * Mathf.Clamp01(t);
        // Unity: signed angle in degrees from `from` to `to`, + = COUNTER-clockwise (Unity: Angle * Sign(from.x*to.y - from.y*to.x));
        // for x-east/y-north + = left. RoutePlanner.SignedTurn swaps the arguments (+ = right).
        public static float SignedAngle(Vector2 from, Vector2 to)
        {
            float dot = Dot(from, to);
            float det = from.x * to.y - from.y * to.x;
            return (float)Math.Atan2(det, dot) * Mathf.Rad2Deg;
        }
        public override string ToString() => "(" + x + ", " + y + ")";
    }

    public struct Vector4
    {
        public float x, y, z, w;
        public Vector4(float x, float y, float z, float w) { this.x = x; this.y = y; this.z = z; this.w = w; }
    }

    public class Object { }

    public class TextAsset : Object
    {
        public byte[] bytes = Array.Empty<byte>();
        public string text = "";
    }

    public static class Application
    {
        /// <summary>game/Assets of this repo (used by tests that dump artifacts next to the Unity project).</summary>
        public static string dataPath => RepoRoot.Find() + "/game/Assets";
    }

    internal static class RepoRoot
    {
        static string s_Root;
        public static string Find()
        {
            if (s_Root != null) return s_Root;
            // assembly location first (tests, runner), then the working directory (tools built outside the repo)
            foreach (string start in new[] { AppContext.BaseDirectory, Directory.GetCurrentDirectory() })
            {
                var dir = new DirectoryInfo(start);
                while (dir != null)
                {
                    if (Directory.Exists(Path.Combine(dir.FullName, "game", "Assets", "_Project", "UI", "Resources")))
                    {
                        s_Root = dir.FullName;
                        return s_Root;
                    }
                    dir = dir.Parent;
                }
            }
            throw new DirectoryNotFoundException("repo root (game/Assets/_Project/UI/Resources) not found above " + AppContext.BaseDirectory
                                                 + " or " + Directory.GetCurrentDirectory());
        }
    }

    public static class Resources
    {
        static string RepoRoot() => UnityEngine.RepoRoot.Find();

        /// <summary>Loads a file from game/Assets/_Project/UI/Resources (e.g. "CabDisplay/Nav/&lt;region&gt;_route" -> .bytes).</summary>
        public static T Load<T>(string path) where T : Object
        {
            string file = Path.Combine(RepoRoot(), "game", "Assets", "_Project", "UI", "Resources", path.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(file) && File.Exists(file + ".bytes")) file += ".bytes";
            if (!File.Exists(file)) return null;
            if (typeof(T) == typeof(TextAsset))
            {
                var ta = new TextAsset { bytes = File.ReadAllBytes(file) };
                ta.text = System.Text.Encoding.UTF8.GetString(ta.bytes);
                return (T)(Object)ta;
            }
            return null;
        }

        public static void UnloadAsset(Object asset) { }
    }

    public static class Debug
    {
        public static void Log(object message) => Console.WriteLine(message);
        public static void LogWarning(object message) => Console.WriteLine("[warn] " + message);
        public static void LogError(object message) => Console.WriteLine("[error] " + message);
    }
}

namespace UnityEngine.Profiling
{
    /// <summary>
    /// Stand-in for UnityEngine.Profiling.Recorder, only for the "GC.Alloc" marker (ADR 0157 / ADR 0168): the nav-runner
    /// zero-GC tests use the same <c>GcAllocCounter</c> API as the Unity tests. Unity counts GC.Alloc samples; CoreCLR has
    /// no per-allocation counter, so <see cref="sampleBlockCount"/> returns the allocated BYTES on the filtered thread
    /// between enable and disable (0 = no allocation, &gt; 0 = some - the only thing the tests compare).
    /// </summary>
    public sealed class Recorder
    {
        static readonly Recorder s_GcAlloc = new Recorder();
        long m_Start, m_Bytes;
        bool m_Enabled;

        public static Recorder Get(string samplerName)
        {
            if (samplerName != "GC.Alloc") throw new ArgumentException("nav-runner shim supports only the GC.Alloc recorder", nameof(samplerName));
            return s_GcAlloc;
        }

        public bool isValid => true;

        public bool enabled
        {
            get => m_Enabled;
            set
            {
                if (value == m_Enabled) return;
                long now = GC.GetAllocatedBytesForCurrentThread();
                if (value) { m_Start = now; m_Bytes = 0; }
                else m_Bytes = now - m_Start;
                m_Enabled = value;
            }
        }

        public int sampleBlockCount => (int)Math.Min(int.MaxValue, m_Bytes);
        public void FilterToCurrentThread() { }
        public void CollectFromAllThreads() { }
    }
}