using System.Globalization;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace Game.Rendering.Editor
{
    /// <summary>
    /// ADR 0199 diagnostic: dumps the clear-dome colour of LP_Dusk / LP_Night (SkyModel radiance, the same LUT × Perez the
    /// Kamion/Sky shader draws) on a grid of elevation × azimuth offset from the sun, as linear and display (exposed,
    /// clipped sRGB) values with saturation. Batch:
    /// -executeMethod Game.Rendering.Editor.TwilightSkyProbe.Dump -probeOut &lt;file.tsv&gt;
    /// </summary>
    public static class TwilightSkyProbe
    {
        static readonly float[] k_Elev = { 0.5f, 1f, 2f, 3f, 4f, 6f, 8f, 10f, 12f, 15f, 20f, 30f, 45f, 70f };
        static readonly float[] k_Az = { 0f, 10f, 20f, 30f, 45f, 60f, 90f, 135f, 180f };

        public static void Dump()
        {
            string outPath = Path.GetFullPath(Path.Combine(Application.dataPath, "../../artifacts/twilight-sky-probe.tsv"));
            var args = System.Environment.GetCommandLineArgs();
            for (int i = 0; i + 1 < args.Length; i++) if (args[i] == "-probeOut") outPath = args[i + 1];
            var sb = new StringBuilder();
            sb.AppendLine(Table(LightingPreset.CreateDusk()));
            sb.AppendLine(Table(LightingPreset.CreateNight()));
            sb.AppendLine("el\ttwilightFactor\tE_lux");
            for (float el = 1f; el >= -8f; el -= 0.5f)
                sb.AppendLine(string.Format(CultureInfo.InvariantCulture, "{0:F1}\t{1:G5}\t{2:G5}", el, SkyModel.TwilightFactorAt(el),
                    new SkyModel(el, 300f, 4f, 0f, 5f).HorizontalIlluminanceLux));
            Directory.CreateDirectory(Path.GetDirectoryName(outPath));
            File.WriteAllText(outPath, sb.ToString());
            Debug.Log("[TwilightSkyProbe] wrote " + outPath);
            if (Application.isBatchMode) EditorApplication.Exit(0);
        }

        public static string Table(LightingPreset p)
        {
            var m = p.CreateModel();
            var sb = new StringBuilder();
            sb.AppendLine($"# {p.name} sun {m.TrueSunElevationDeg:F1} deg, overcast {p.overcast:F2}, exposure {m.Exposure:G4}");
            sb.AppendLine("el\taz_from_sun\tlin_r\tlin_g\tlin_b\tY_cd\tsrgb_r\tsrgb_g\tsrgb_b\tsat");
            float sunAz = Mathf.Atan2(m.SunDirection.x, m.SunDirection.z) * Mathf.Rad2Deg;
            foreach (float el in k_Elev)
                foreach (float az in k_Az)
                {
                    float a = (sunAz + az) * Mathf.Deg2Rad, e = el * Mathf.Deg2Rad;
                    var d = new Vector3(Mathf.Cos(e) * Mathf.Sin(a), Mathf.Sin(e), Mathf.Cos(e) * Mathf.Cos(a));
                    Color L = m.Radiance(d);
                    float Y = 0.2126f * L.r + 0.7152f * L.g + 0.0722f * L.b;
                    Color x = m.ExposedRadiance(d);
                    float r = Srgb(x.r), g = Srgb(x.g), b = Srgb(x.b);
                    float mx = Mathf.Max(r, Mathf.Max(g, b)), mn = Mathf.Min(r, Mathf.Min(g, b));
                    float sat = mx > 1e-4f ? (mx - mn) / mx : 0f;
                    float n = Y > 1e-9f ? 1f / Y : 0f;
                    sb.AppendLine(string.Format(CultureInfo.InvariantCulture, "{0}\t{1}\t{2:F3}\t{3:F3}\t{4:F3}\t{5:G4}\t{6:F0}\t{7:F0}\t{8:F0}\t{9:F2}",
                        el, az, L.r * n, L.g * n, L.b * n, Y, r * 255f, g * 255f, b * 255f, sat));
                }
            Object.DestroyImmediate(p);
            return sb.ToString();
        }

        static float Srgb(float v)
        {
            v = Mathf.Clamp01(v);
            return v <= 0.0031308f ? 12.92f * v : 1.055f * Mathf.Pow(v, 1f / 2.4f) - 0.055f;
        }
    }
}
