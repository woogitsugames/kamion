using System.Collections.Generic;
using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// ADR 0113: forest fast path of the tiers with <see cref="QualityProfile.Tier.forestFast"/> (Low). Three parts, each
    /// switchable on its own for the A/B on the phone (ExtraViewCostMonitor keys vegfast, hlod1pass, canopyfast, veganiso):
    /// <list type="number">
    /// <item><b>Keyword</b> <c>_KAMION_VEG_FAST</c> (Kamion/Vegetation colour pass): L2 SH per vertex on the HLOD edge walls,
    /// no shadow-map fetch past URP's shadow fade.</item>
    /// <item><b>Edge one-pass</b>: HLOD edge-wall materials draw their colour pass with ZWrite and alpha-to-coverage and
    /// without the depth pre-pass (a wall has ~1 layer of overdraw, the pre-pass doubled its raster and coverage work).</item>
    /// <item><b>Canopy</b>: the URP Lit HLOD canopy materials are drawn with a copy on Kamion/Forest Canopy (same BRDF,
    /// slowly varying terms per vertex, no shadow / additional-light work).</item>
    /// </list>
    /// World code (WorldInstances) registers its runtime material copies and asks for the canopy replacement per draw;
    /// generated assets are never modified.
    /// </summary>
    public static class ForestFastPath
    {
        public const string Keyword = "_KAMION_VEG_FAST";
        static readonly int k_ZWrite = Shader.PropertyToID("_VegZWrite");
        static readonly int k_Offset = Shader.PropertyToID("_VegOffset");
        static readonly int k_BaseMap = Shader.PropertyToID("_BaseMap");
        static readonly int k_NormalOcc = Shader.PropertyToID("_NormalOcc");
        static readonly int k_BaseColor = Shader.PropertyToID("_BaseColor");
        static readonly int k_Smoothness = Shader.PropertyToID("_Smoothness");

        /// <summary>Tier state (QualityProfileApplier).</summary>
        public static bool Shipping { get; private set; }
        /// <summary>A/B flips (true = the part is the opposite of <see cref="Shipping"/>).</summary>
        public static bool FlipKeyword, FlipEdgeOnePass, FlipCanopy, FlipAniso;

        public static bool KeywordOn => Shipping ^ FlipKeyword;
        public static bool EdgeOnePass => Shipping ^ FlipEdgeOnePass;
        public static bool CanopyOn => Shipping ^ FlipCanopy;

        static readonly List<Material> s_Edges = new List<Material>();
        static readonly List<Material> s_Foliage = new List<Material>();
        static readonly Dictionary<Material, Material> s_Canopy = new Dictionary<Material, Material>();
        static readonly Dictionary<Texture, int> s_Aniso = new Dictionary<Texture, int>();
        static Shader s_CanopyShader;
        static bool s_AnisoLow;

        public static void Apply(bool on)
        {
            Shipping = on;
            Refresh();
        }

        /// <summary>Re-applies the keyword, the edge-wall pass state and the A/B texture filtering after a change.</summary>
        public static void Refresh()
        {
            if (KeywordOn) Shader.EnableKeyword(Keyword); else Shader.DisableKeyword(Keyword);
            s_Edges.RemoveAll(m => m == null);
            foreach (var m in s_Edges) SetEdge(m, EdgeOnePass);
            SetAniso(FlipAniso);
        }

        /// <summary>A Kamion/Vegetation runtime material copy (cards, impostors, HLOD edge walls).</summary>
        public static void Register(Material m)
        {
            if (m == null) return;
            if (!s_Foliage.Contains(m)) s_Foliage.Add(m);
            if (!m.IsKeywordEnabled("_HLOD_EDGE")) return;
            if (!s_Edges.Contains(m)) s_Edges.Add(m);
            SetEdge(m, EdgeOnePass);
        }

        public static void Unregister(Material m)
        {
            s_Edges.Remove(m);
            s_Foliage.Remove(m);
        }

        static void SetEdge(Material m, bool onePass)
        {
            if (!m.HasProperty(k_ZWrite)) return;
            m.SetShaderPassEnabled("SRPDefaultUnlit", !onePass);
            m.SetFloat(k_ZWrite, onePass ? 1f : 0f);
            m.SetFloat(k_Offset, onePass ? 0f : -1f);
        }

        /// <summary>A/B only (key veganiso): aniso 1 instead of the import's 2 on the vegetation textures.</summary>
        static void SetAniso(bool low)
        {
            if (low == s_AnisoLow && !low) return;
            s_AnisoLow = low;
            foreach (var m in s_Foliage)
            {
                if (m == null) continue;
                SetAniso(m.HasProperty(k_BaseMap) ? m.GetTexture(k_BaseMap) : null, low);
                SetAniso(m.HasProperty(k_NormalOcc) ? m.GetTexture(k_NormalOcc) : null, low);
            }
        }

        static void SetAniso(Texture t, bool low)
        {
            if (t == null) return;
            if (!s_Aniso.TryGetValue(t, out int a)) { a = t.anisoLevel; s_Aniso[t] = a; }
            t.anisoLevel = low ? 1 : a;
        }

        /// <summary>The material to draw a forest HLOD submesh with: the Kamion/Forest Canopy copy of a URP Lit canopy material
        /// when the canopy part is on, else the material itself. No allocation after the first call per material.</summary>
        public static Material Canopy(Material m)
        {
            if (!CanopyOn || m == null) return m;
            if (s_Canopy.TryGetValue(m, out var c)) return c ?? m;
            c = null;
            if (m.name.StartsWith("M_forest_canopy_") && m.HasProperty(k_BaseMap))
            {
                if (s_CanopyShader == null)
                {
                    var qp = QualityProfile.Load();
                    s_CanopyShader = qp != null && qp.canopyMaterial != null ? qp.canopyMaterial.shader : null;
                }
                if (s_CanopyShader != null && s_CanopyShader.isSupported)
                {
                    c = new Material(s_CanopyShader) { name = m.name + " (canopy fast)", hideFlags = HideFlags.DontSave, enableInstancing = true };
                    c.SetTexture(k_BaseMap, m.GetTexture(k_BaseMap));
                    c.SetTextureScale(k_BaseMap, m.GetTextureScale(k_BaseMap));
                    c.SetTextureOffset(k_BaseMap, m.GetTextureOffset(k_BaseMap));
                    if (m.HasProperty(k_BaseColor)) c.SetColor(k_BaseColor, m.GetColor(k_BaseColor));
                    if (m.HasProperty(k_Smoothness)) c.SetFloat(k_Smoothness, m.GetFloat(k_Smoothness));
                }
            }
            s_Canopy[m] = c;
            return c ?? m;
        }
    }
}
