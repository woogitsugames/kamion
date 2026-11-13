using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Rendering
{
    /// <summary>
    /// ADR 0192 (review s19 0182 P2-8): glare halo around the street-lamp lenses (Kamion/Lamp Glare). One hidden object
    /// with one mesh: four vertices per lamp head (all at the head, corners in UV0), billboarded in the vertex shader at
    /// a constant angular size; rebuilt only when the head list changes (world load, floating-origin shift). Off by day
    /// (lamps off), on tiers with <see cref="QualityProfile.Tier.lampGlareOff"/>, and without heads.
    /// Photometry: Stiles-Holladay veil K E / phi², K = <see cref="CameraGlareK"/> (WORKING_VALUE), E from
    /// <see cref="StreetLamps.DownIntensityCd"/> and the luminaire profile in the shader; phi max 3°, core 0.12°.
    /// </summary>
    public static class LampGlare
    {
        public const float CameraGlareK = 0.4f, PhiMaxDeg = 3f, PhiCoreDeg = 0.12f;
        static readonly int k_Glare = Shader.PropertyToID("_KamionLampGlare"), k_Color = Shader.PropertyToID("_KamionLampGlareColor");
        static GameObject s_Go;
        static MeshRenderer s_Renderer;
        static Mesh s_Mesh;
        static Vector3[] s_BuiltFrom;
        static int s_BuiltCount = -1;

        /// <summary>Lamp heads in the glare mesh (diagnostics / tests).</summary>
        public static int Count => s_BuiltCount < 0 ? 0 : s_BuiltCount;
        public static Mesh MeshForTests => s_Mesh;

        /// <summary>StreetLamps.RefreshLights: keep the mesh in step with the heads, scale by exposure and switch.</summary>
        public static void Sync(Vector3[] heads, int count, float on, float exposure, Color ledColour)
        {
            bool tierOff = QualityProfileApplier.HasCurrent && QualityProfileApplier.Current.lampGlareOff;
            bool show = !tierOff && on > 0f && count > 0 && exposure > 0f;
            if (!show)
            {
                if (s_Renderer != null) s_Renderer.enabled = false;
                return;
            }
            if (!ReferenceEquals(heads, s_BuiltFrom) || count != s_BuiltCount || s_Go == null) Build(heads, count);
            if (s_Renderer == null) return;
            s_Renderer.enabled = true;
            float m = Mathf.Max(ledColour.r, Mathf.Max(ledColour.g, ledColour.b));
            Shader.SetGlobalVector(k_Color, m > 0f ? (Vector4)(ledColour / m) : Vector4.one);
            Shader.SetGlobalVector(k_Glare, new Vector4(CameraGlareK * StreetLamps.DownIntensityCd * exposure * on, PhiMaxDeg, PhiCoreDeg, 0f));
        }

        /// <summary>Head list replaced (floating-origin shift re-sends a new array): rebuild on the next sync.</summary>
        public static void Invalidate() { s_BuiltFrom = null; }

        static void Build(Vector3[] heads, int count)
        {
            if (s_Go == null)
            {
                var mat = Resources.Load<Material>("Night/M_LampGlare");
                if (mat == null) { Debug.LogWarning("[LampGlare] Resources/Night/M_LampGlare missing"); s_BuiltFrom = heads; s_BuiltCount = count; return; }
                s_Go = new GameObject("LampGlare (runtime)") { hideFlags = HideFlags.HideAndDontSave };
                s_Go.AddComponent<MeshFilter>();
                s_Renderer = s_Go.AddComponent<MeshRenderer>();
                s_Renderer.sharedMaterial = mat;
                s_Renderer.shadowCastingMode = ShadowCastingMode.Off;
                s_Renderer.receiveShadows = false;
                s_Renderer.lightProbeUsage = LightProbeUsage.Off;
                s_Renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
                s_Renderer.allowOcclusionWhenDynamic = false;
            }
            if (s_Mesh == null) s_Mesh = new Mesh { name = "LampGlare", hideFlags = HideFlags.HideAndDontSave, indexFormat = IndexFormat.UInt32 };
            s_Mesh.Clear();
            var v = new Vector3[count * 4];
            var uv = new Vector2[count * 4];
            var ix = new int[count * 6];
            Vector3 lo = Vector3.positiveInfinity, hi = Vector3.negativeInfinity;
            for (int i = 0; i < count; i++)
            {
                Vector3 h = heads[i];
                lo = Vector3.Min(lo, h); hi = Vector3.Max(hi, h);
                for (int k = 0; k < 4; k++) v[i * 4 + k] = h;
                uv[i * 4] = new Vector2(-1, -1); uv[i * 4 + 1] = new Vector2(1, -1); uv[i * 4 + 2] = new Vector2(1, 1); uv[i * 4 + 3] = new Vector2(-1, 1);
                ix[i * 6] = i * 4; ix[i * 6 + 1] = i * 4 + 1; ix[i * 6 + 2] = i * 4 + 2;
                ix[i * 6 + 3] = i * 4; ix[i * 6 + 4] = i * 4 + 2; ix[i * 6 + 5] = i * 4 + 3;
            }
            s_Mesh.vertices = v;
            s_Mesh.uv = uv;
            s_Mesh.triangles = ix;
            // the billboards grow with distance (constant angle): pad the bounds by the halo of a lamp 2 km away
            var b = new Bounds((lo + hi) * 0.5f, hi - lo);
            b.Expand(2f * 2000f * Mathf.Tan(PhiMaxDeg * Mathf.Deg2Rad));
            s_Mesh.bounds = b;
            s_Go.GetComponent<MeshFilter>().sharedMesh = s_Mesh;
            s_BuiltFrom = heads;
            s_BuiltCount = count;
        }

        /// <summary>Tests / domain teardown.</summary>
        public static void Dispose()
        {
            if (s_Go != null) { if (Application.isPlaying) Object.Destroy(s_Go); else Object.DestroyImmediate(s_Go); }
            if (s_Mesh != null) { if (Application.isPlaying) Object.Destroy(s_Mesh); else Object.DestroyImmediate(s_Mesh); }
            s_Go = null; s_Renderer = null; s_Mesh = null; s_BuiltFrom = null; s_BuiltCount = -1;
        }
    }
}
