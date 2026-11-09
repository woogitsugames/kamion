using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace Game.Rendering.Editor
{
    /// <summary>
    /// Deterministic, tileable single-channel detail textures for <c>Kamion/World Surface</c> (mean ≈ 0.5, linear),
    /// plus a two-octave macro-noise texture. Procedural placeholders for the surface character only (grain, aggregate,
    /// joints, wear); the mean albedo comes from the material (world manifest). To be replaced or layered with CC0
    /// photo scans (docs/06 §3) once the owner approves downloading them.
    /// Output: Assets/_Project/Rendering/Textures/World/*.png (committed, ~1.3 MB total).
    /// </summary>
    public static class WorldTextureGenerator
    {
        public const string Dir = "Assets/_Project/Rendering/Textures/World";
        public const string Grass = Dir + "/T_World_Grass.png";
        public const string Asphalt = Dir + "/T_World_Asphalt.png";
        public const string Concrete = Dir + "/T_World_Concrete.png";
        public const string Paving = Dir + "/T_World_Paving.png";
        public const string Sett = Dir + "/T_World_Sett.png";
        public const string Gravel = Dir + "/T_World_Gravel.png";
        public const string Paint = Dir + "/T_World_Paint.png";
        public const string Macro = Dir + "/T_World_Macro.png";

        public static readonly string[] All = { Grass, Asphalt, Concrete, Paving, Sett, Gravel, Paint, Macro };

        [MenuItem("Kamion/Rendering/Generate world surface textures")]
        public static void GenerateAll()
        {
            Directory.CreateDirectory(Path.Combine(ProjectRoot, Dir));
            Write(Grass, 512, GrassFn, false);
            Write(Asphalt, 512, AsphaltFn, false);
            Write(Concrete, 512, ConcreteFn, false);
            Write(Paving, 512, PavingFn, false);
            Write(Sett, 512, SettFn, false);
            Write(Gravel, 512, GravelFn, false);
            Write(Paint, 512, PaintFn, false);
            Write(Macro, 256, null, true);
            AssetDatabase.Refresh();
            Debug.Log("[RENDER] world surface textures generated in " + Dir);
        }

        public static bool Exist()
        {
            foreach (var p in All) if (!File.Exists(Path.Combine(ProjectRoot, p))) return false;
            return true;
        }

        static string ProjectRoot => Path.GetDirectoryName(Application.dataPath);

        delegate float Fn(float u, float v, int n);

        static void Write(string path, int size, Fn fn, bool macro)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGB24, false, true);
            var px = new Color32[size * size];
            var raw = new float[size * size];
            var raw2 = new float[size * size];
            for (int y = 0; y < size; y++)
            for (int x = 0; x < size; x++)
            {
                float u = (float)x / size, v = (float)y / size;
                if (macro)
                {
                    raw[y * size + x] = Fbm(u, v, 4, 5, 101);
                    raw2[y * size + x] = Fbm(u, v, 3, 5, 202);
                }
                else raw[y * size + x] = fn(u, v, size);
            }
            Normalise(raw, 0.5f, macro ? 0.16f : -1f);
            if (macro) Normalise(raw2, 0.5f, 0.16f);
            for (int i = 0; i < px.Length; i++)
            {
                byte r = ToByte(raw[i]);
                byte g = macro ? ToByte(raw2[i]) : r;
                px[i] = new Color32(r, g, r, 255);
            }
            tex.SetPixels32(px);
            File.WriteAllBytes(Path.Combine(ProjectRoot, path), tex.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(tex);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            var imp = (TextureImporter)AssetImporter.GetAtPath(path);
            imp.sRGBTexture = false;           // linear data: mean 0.5 multiplies a calibrated albedo
            imp.mipmapEnabled = true;
            imp.mipmapFilter = TextureImporterMipFilter.KaiserFilter;
            imp.wrapMode = TextureWrapMode.Repeat;
            imp.filterMode = FilterMode.Trilinear;
            imp.anisoLevel = 4;                // overridden per tier at run time (QualityProfileApplier)
            imp.maxTextureSize = size;
            imp.textureCompression = TextureImporterCompression.Compressed;
            imp.SetPlatformTextureSettings(new TextureImporterPlatformSettings
            {
                name = "Android", overridden = true, maxTextureSize = size, format = TextureImporterFormat.ASTC_6x6,
                textureCompression = TextureImporterCompression.Compressed,
            });
            imp.SaveAndReimport();
        }

        static byte ToByte(float v) => (byte)Mathf.Clamp(Mathf.RoundToInt(v * 255f), 0, 255);

        /// <summary>Shift to the target mean; optionally rescale to a target standard deviation.</summary>
        static void Normalise(float[] a, float mean, float std)
        {
            double s = 0, s2 = 0;
            foreach (var x in a) { s += x; s2 += x * x; }
            float m = (float)(s / a.Length);
            float sd = Mathf.Sqrt(Mathf.Max(1e-8f, (float)(s2 / a.Length) - m * m));
            float k = std > 0f ? std / sd : 1f;
            for (int i = 0; i < a.Length; i++) a[i] = mean + (a[i] - m) * k;
        }

        // ---------------------------------------------------------------- noise (tileable)
        static float Hash(int x, int y, int seed)
        {
            unchecked
            {
                uint h = (uint)(x * 374761393 + y * 668265263 + seed * 1442695041);
                h = (h ^ (h >> 13)) * 1274126177u;
                return ((h ^ (h >> 16)) & 0xFFFFFF) / 16777215f;
            }
        }

        static int Wrap(int i, int p) => ((i % p) + p) % p;

        /// <summary>Value noise with period p cells over the unit square.</summary>
        static float Value(float u, float v, int p, int seed)
        {
            float x = u * p, y = v * p;
            int x0 = Mathf.FloorToInt(x), y0 = Mathf.FloorToInt(y);
            float fx = x - x0, fy = y - y0;
            fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy);
            float a = Hash(Wrap(x0, p), Wrap(y0, p), seed), b = Hash(Wrap(x0 + 1, p), Wrap(y0, p), seed);
            float c = Hash(Wrap(x0, p), Wrap(y0 + 1, p), seed), d = Hash(Wrap(x0 + 1, p), Wrap(y0 + 1, p), seed);
            return Mathf.Lerp(Mathf.Lerp(a, b, fx), Mathf.Lerp(c, d, fx), fy);
        }

        static float Fbm(float u, float v, int basePeriod, int octaves, int seed)
        {
            float sum = 0, amp = 1, norm = 0;
            int p = basePeriod;
            for (int o = 0; o < octaves; o++)
            {
                sum += Value(u, v, p, seed + o * 17) * amp;
                norm += amp; amp *= 0.5f; p *= 2;
            }
            return sum / norm;
        }

        /// <summary>Cellular (Worley F1) distance with period p, returns (distance, cell id hash).</summary>
        static float Worley(float u, float v, int p, int seed, out float id)
        {
            float x = u * p, y = v * p;
            int cx = Mathf.FloorToInt(x), cy = Mathf.FloorToInt(y);
            float best = 9f; id = 0;
            for (int j = -1; j <= 1; j++)
            for (int i = -1; i <= 1; i++)
            {
                int gx = cx + i, gy = cy + j;
                float px = gx + Hash(Wrap(gx, p), Wrap(gy, p), seed), py = gy + Hash(Wrap(gx, p), Wrap(gy, p), seed + 7);
                float d = (px - x) * (px - x) + (py - y) * (py - y);
                if (d < best) { best = d; id = Hash(Wrap(gx, p), Wrap(gy, p), seed + 13); }
            }
            return Mathf.Sqrt(best);
        }

        // ---------------------------------------------------------------- surfaces (u, v over one tile)
        // Grass, tile 3.1 m: blade-scale grain, clumps (~0.3 m), a few dry/bare spots.
        static float GrassFn(float u, float v, int n)
        {
            float grain = Value(u, v, 256, 1) * 0.5f + Value(u, v, 128, 2) * 0.5f;
            float clump = Fbm(u, v, 10, 3, 3);
            float dry = Mathf.SmoothStep(0.62f, 0.78f, Fbm(u, v, 4, 3, 4));
            return 0.35f * grain + 0.25f * clump + 0.2f * dry;   // low-frequency weight kept small: no blotchy 'noise layer' on Low (single sample)
        }

        // Asphalt AC 0/11, tile 2.3 m: binder with aggregate (bright chips), fine pores, faint tyre polish.
        static float AsphaltFn(float u, float v, int n)
        {
            float chips = Worley(u, v, 180, 11, out float id);
            float stone = chips < 0.38f ? 0.55f + 0.45f * id : 0.25f;
            float pores = Value(u, v, 256, 12) < 0.12f ? -0.3f : 0f;
            float blotch = Fbm(u, v, 6, 3, 13);
            return 0.55f * stone + 0.12f * blotch + pores;
        }

        // Concrete (kerbs, bridges), tile 2 m: smooth blotches and pores.
        static float ConcreteFn(float u, float v, int n)
        {
            float b = Fbm(u, v, 5, 4, 21);
            float pores = Value(u, v, 256, 22) < 0.08f ? -0.25f : 0f;
            return b + pores + 0.15f * Value(u, v, 128, 23);
        }

        // Concrete paving (kostka 20×10 cm, running bond), tile 1.6 m = 8 × 16 stones.
        static float PavingFn(float u, float v, int n)
        {
            const int cols = 8, rows = 16;
            float y = v * rows; int row = Mathf.FloorToInt(y);
            float x = u * cols + (row % 2) * 0.5f; int col = Mathf.FloorToInt(x);
            float fx = x - col, fy = y - row;
            float joint = Mathf.Min(Mathf.Min(fx, 1 - fx) * 0.2f, Mathf.Min(fy, 1 - fy) * 0.1f);  // metres to joint
            float j = Mathf.SmoothStep(0.002f, 0.006f, joint);
            float stone = 0.45f + 0.25f * Hash(Wrap(col, cols), Wrap(row, rows), 31) + 0.15f * Fbm(u, v, 16, 3, 32);
            return Mathf.Lerp(0.12f, stone, j);
        }

        // Granite setts (kostka kamienna ~10×10 cm, segmental arcs approximated as a jittered grid), tile 1.6 m.
        static float SettFn(float u, float v, int n)
        {
            float d = Worley(u, v, 16, 41, out float id);
            float edge = Mathf.SmoothStep(0.45f, 0.62f, d);
            float stone = 0.4f + 0.35f * id + 0.15f * Value(u, v, 128, 42);
            return Mathf.Lerp(stone, 0.12f, edge);
        }

        // Gravel shoulder, tile 2 m: pebbles of mixed brightness.
        static float GravelFn(float u, float v, int n)
        {
            float d = Worley(u, v, 90, 51, out float id);
            float peb = d < 0.45f ? 0.35f + 0.5f * id : 0.2f;
            return peb + 0.2f * Fbm(u, v, 8, 3, 52);
        }

        // Thermoplastic paint, tile 1.7 m: mostly intact, worn spots where asphalt shows through, fine grain.
        static float PaintFn(float u, float v, int n)
        {
            float wear = Mathf.SmoothStep(0.58f, 0.70f, Fbm(u, v, 6, 4, 61));
            float grain = 0.08f * Value(u, v, 256, 62);
            return Mathf.Lerp(0.56f, 0.18f, wear) + grain;
        }
    }
}
