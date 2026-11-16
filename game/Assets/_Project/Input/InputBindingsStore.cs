using System;
using System.Globalization;
using System.IO;
using System.Text;

namespace Game.Controls
{
    /// <summary>Player adjustments of the pad / keyboard feel (settings screen), stored with the binding overrides.</summary>
    public struct PadUserTuning
    {
        public const float DeadZoneMin = 0f, DeadZoneMax = 0.4f;
        public const float ExponentMin = 1f, ExponentMax = 3f;
        public const float SpeedLimitMin = 0.5f, SpeedLimitMax = 2f;
        public const float KeySpeedMin = 0.5f, KeySpeedMax = 2f;

        /// <summary>Steering-stick inner dead zone (fraction of travel).</summary>
        public float StickDeadZone;
        /// <summary>Steering-stick curve exponent (1 linear .. 3).</summary>
        public float StickExponent;
        /// <summary>Scale of the lateral-acceleration limit of the speed-dependent steering amplitude (1 = shipped; 2 = twice the lock at speed).</summary>
        public float SpeedLimitScale;
        /// <summary>Scale of the keyboard steering rate (1 = shipped).</summary>
        public float KeySteerScale;

        public static PadUserTuning From(PadKeyboardFeel feel)
        {
            feel = feel ?? PadKeyboardFeel.Defaults();
            return new PadUserTuning { StickDeadZone = feel.stickDeadZone, StickExponent = feel.stickExponent, SpeedLimitScale = 1f, KeySteerScale = 1f };
        }

        public void Clamp(PadUserTuning fallback)
        {
            StickDeadZone = Safe(StickDeadZone, DeadZoneMin, DeadZoneMax, fallback.StickDeadZone);
            StickExponent = Safe(StickExponent, ExponentMin, ExponentMax, fallback.StickExponent);
            SpeedLimitScale = Safe(SpeedLimitScale, SpeedLimitMin, SpeedLimitMax, fallback.SpeedLimitScale);
            KeySteerScale = Safe(KeySteerScale, KeySpeedMin, KeySpeedMax, fallback.KeySteerScale);
        }

        static float Safe(float v, float lo, float hi, float fb) => float.IsNaN(v) || float.IsInfinity(v) ? fb : (v < lo ? lo : v > hi ? hi : v);
    }

    /// <summary>
    /// Persistence of the input binding overrides (Input System <c>SaveBindingOverridesAsJson</c> text, kept opaque) and
    /// of <see cref="PadUserTuning"/> in one versioned JSON file (ADR 0264):
    /// <code>{"schema":1,"stickDeadZone":0.12,"stickExponent":1.8,"speedLimitScale":1,"keySteerScale":1,"overrides":"{\"bindings\":[...]}"}</code>
    /// Schema 0 = a bare overrides document (what <c>SaveBindingOverridesAsJson</c> writes) - migrated with default tuning.
    /// The file is written atomically (temp + replace): the process may be killed at any moment. Pure .NET (no Unity
    /// API) so the round trip is tested without the player; not used in the driving loop (allocates).
    /// </summary>
    public sealed class InputBindingsStore
    {
        public const int CurrentSchema = 1;
        public const string FileName = "input_bindings.json";

        /// <summary>
        /// Action-path renames applied when a save is loaded (old "Map/Action" → new). Empty in v1; the place where a
        /// merge with another naming (e.g. ADR 0261) keeps players' saved bindings (ADR 0264 section "Scalenie").
        /// </summary>
        public static readonly string[,] ActionRenames = new string[0, 2];

        public int Schema = CurrentSchema;
        public PadUserTuning Tuning;
        /// <summary>Opaque Input System overrides JSON; empty = defaults.</summary>
        public string OverridesJson = "";

        public static InputBindingsStore Defaults(PadKeyboardFeel feel) => new InputBindingsStore { Tuning = PadUserTuning.From(feel) };

        // ------------------------------------------------------------------ serialise

        public string ToJson()
        {
            var ci = CultureInfo.InvariantCulture;
            var sb = new StringBuilder(256 + (OverridesJson?.Length ?? 0));
            sb.Append("{\"schema\":").Append(CurrentSchema.ToString(ci));
            sb.Append(",\"stickDeadZone\":").Append(Tuning.StickDeadZone.ToString("R", ci));
            sb.Append(",\"stickExponent\":").Append(Tuning.StickExponent.ToString("R", ci));
            sb.Append(",\"speedLimitScale\":").Append(Tuning.SpeedLimitScale.ToString("R", ci));
            sb.Append(",\"keySteerScale\":").Append(Tuning.KeySteerScale.ToString("R", ci));
            sb.Append(",\"overrides\":");
            AppendString(sb, OverridesJson ?? "");
            sb.Append('}');
            return sb.ToString();
        }

        /// <summary>Parses a saved file; empty / corrupt text gives defaults (never throws). Older schemas are migrated.</summary>
        public static InputBindingsStore FromJson(string text, PadKeyboardFeel feel)
        {
            var defaults = Defaults(feel);
            var s = Defaults(feel);
            if (string.IsNullOrWhiteSpace(text)) return s;
            text = text.Trim();
            try
            {
                if (!TryParseFlat(text, s, out bool hasSchema, out bool hasBindings)) return defaults;
                if (!hasSchema)
                {
                    // Schema 0: the bare Input System document {"bindings":[...]} (no wrapper).
                    if (!hasBindings) return defaults;
                    s = Defaults(feel);
                    s.OverridesJson = text;
                    s.Schema = 0;
                }
            }
            catch (FormatException) { return defaults; }
            Migrate(s);
            s.Tuning.Clamp(defaults.Tuning);
            return s;
        }

        static void Migrate(InputBindingsStore s)
        {
            if (s.Schema < 1) s.Schema = 1;   // v0 -> v1: wrapper + tuning (defaults), overrides kept verbatim
            if (s.Schema > CurrentSchema) s.Schema = CurrentSchema;   // newer build: keep the known fields
            s.OverridesJson = RenameActions(s.OverridesJson, ActionRenames);
        }

        /// <summary>Replaces <c>"action":"Old"</c> paths in an overrides document by new names (exact, quoted match).</summary>
        public static string RenameActions(string overridesJson, string[,] renames)
        {
            if (string.IsNullOrEmpty(overridesJson) || renames == null) return overridesJson ?? "";
            for (int i = 0; i < renames.GetLength(0); i++)
            {
                string from = renames[i, 0], to = renames[i, 1];
                if (string.IsNullOrEmpty(from) || to == null) continue;
                overridesJson = overridesJson.Replace("\"action\":\"" + from + "\"", "\"action\":\"" + to + "\"")
                                             .Replace("\"action\": \"" + from + "\"", "\"action\": \"" + to + "\"");
            }
            return overridesJson;
        }

        // ------------------------------------------------------------------ files

        /// <summary>Atomic write: temp file in the same folder, then replace (or move when no file yet).</summary>
        public void SaveToFile(string path)
        {
            string dir = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
            string tmp = path + ".tmp";
            File.WriteAllText(tmp, ToJson(), new UTF8Encoding(false));
            if (!File.Exists(path)) { File.Move(tmp, path); return; }
            try { File.Replace(tmp, path, null); }
            catch (PlatformNotSupportedException) { File.Delete(path); File.Move(tmp, path); }   // UNVERIFIED on every IL2CPP target
        }

        /// <summary>Reads a saved file; missing or unreadable file gives defaults.</summary>
        public static InputBindingsStore LoadFromFile(string path, PadKeyboardFeel feel)
        {
            try { return File.Exists(path) ? FromJson(File.ReadAllText(path, Encoding.UTF8), feel) : Defaults(feel); }
            catch (IOException) { return Defaults(feel); }
            catch (UnauthorizedAccessException) { return Defaults(feel); }
        }

#if UNITY_5_3_OR_NEWER
        /// <summary>Default location: <c>Application.persistentDataPath/input_bindings.json</c>.</summary>
        public static string DefaultPath => Path.Combine(UnityEngine.Application.persistentDataPath, FileName);
#endif

        // ------------------------------------------------------------------ minimal flat JSON (strings, numbers, literals)

        static void AppendString(StringBuilder sb, string s)
        {
            sb.Append('"');
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    case '\b': sb.Append("\\b"); break;
                    case '\f': sb.Append("\\f"); break;
                    default:
                        if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4", CultureInfo.InvariantCulture));
                        else sb.Append(c);
                        break;
                }
            }
            sb.Append('"');
        }

        /// <summary>
        /// Parses the top-level object, reading the known fields; nested values (the bare v0 document's "bindings" array,
        /// fields of a newer schema) are skipped. Returns false when the text is not an object. Throws FormatException
        /// on broken syntax.
        /// </summary>
        static bool TryParseFlat(string t, InputBindingsStore s, out bool hasSchema, out bool hasBindings)
        {
            hasSchema = false; hasBindings = false;
            int i = 0;
            SkipWs(t, ref i);
            if (i >= t.Length || t[i] != '{') return false;
            i++;
            bool sawSchema = false;
            while (true)
            {
                SkipWs(t, ref i);
                if (i >= t.Length) throw new FormatException("eof");
                if (t[i] == '}') { i++; break; }
                if (t[i] == ',') { i++; continue; }
                string key = ReadString(t, ref i);
                SkipWs(t, ref i);
                if (i >= t.Length || t[i] != ':') throw new FormatException("colon");
                i++;
                SkipWs(t, ref i);
                if (i >= t.Length) throw new FormatException("eof");
                char c = t[i];
                if (key == "bindings") hasBindings = true;
                if (c == '{' || c == '[') { SkipNested(t, ref i); continue; }
                if (c == '"')
                {
                    string v = ReadString(t, ref i);
                    if (key == "overrides") s.OverridesJson = v;
                }
                else
                {
                    int start = i;
                    while (i < t.Length && t[i] != ',' && t[i] != '}' && !char.IsWhiteSpace(t[i])) i++;
                    string lit = t.Substring(start, i - start);
                    if (lit == "true" || lit == "false" || lit == "null") continue;
                    if (!float.TryParse(lit, NumberStyles.Float, CultureInfo.InvariantCulture, out float f)) throw new FormatException("number");
                    switch (key)
                    {
                        case "schema": s.Schema = (int)f; sawSchema = true; break;
                        case "stickDeadZone": s.Tuning.StickDeadZone = f; break;
                        case "stickExponent": s.Tuning.StickExponent = f; break;
                        case "speedLimitScale": s.Tuning.SpeedLimitScale = f; break;
                        case "keySteerScale": s.Tuning.KeySteerScale = f; break;
                    }
                }
            }
            hasSchema = sawSchema;
            return true;
        }

        /// <summary>Skips one nested object / array (strings with brackets and escapes inside are respected).</summary>
        static void SkipNested(string t, ref int i)
        {
            int depth = 0;
            while (i < t.Length)
            {
                char c = t[i];
                if (c == '"') { ReadString(t, ref i); continue; }
                i++;
                if (c == '{' || c == '[') depth++;
                else if (c == '}' || c == ']') { if (--depth == 0) return; }
            }
            throw new FormatException("unterminated nested value");
        }

        static void SkipWs(string t, ref int i) { while (i < t.Length && char.IsWhiteSpace(t[i])) i++; }

        static string ReadString(string t, ref int i)
        {
            if (i >= t.Length || t[i] != '"') throw new FormatException("string");
            i++;
            var sb = new StringBuilder();
            while (i < t.Length)
            {
                char c = t[i++];
                if (c == '"') return sb.ToString();
                if (c != '\\') { sb.Append(c); continue; }
                if (i >= t.Length) break;
                char e = t[i++];
                switch (e)
                {
                    case '"': sb.Append('"'); break;
                    case '\\': sb.Append('\\'); break;
                    case '/': sb.Append('/'); break;
                    case 'n': sb.Append('\n'); break;
                    case 'r': sb.Append('\r'); break;
                    case 't': sb.Append('\t'); break;
                    case 'b': sb.Append('\b'); break;
                    case 'f': sb.Append('\f'); break;
                    case 'u':
                        if (i + 4 > t.Length) throw new FormatException("\\u");
                        sb.Append((char)int.Parse(t.Substring(i, 4), NumberStyles.HexNumber, CultureInfo.InvariantCulture));
                        i += 4;
                        break;
                    default: throw new FormatException("escape");
                }
            }
            throw new FormatException("unterminated string");
        }
    }
}
