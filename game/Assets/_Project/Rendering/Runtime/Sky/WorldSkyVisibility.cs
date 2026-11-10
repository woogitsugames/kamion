using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Rendering
{
    /// <summary>
    /// Baked ground lighting of a static world region (ADR 0064): one RGBA8 map in region-root XZ, made by the import
    /// pipeline (<c>Game.World.Import.WorldSkyBake</c>), read by <c>Kamion/World PBR</c> and <c>Kamion/World Surface</c>
    /// through <c>KamionWorldGI.hlsl</c>.
    /// R = cosine-weighted sky visibility at ground level (buildings, bridges, walls, parked vehicles solid; tree crowns
    /// porous), G/B = sun visibility at ground level for the baked sun directions (<see cref="sunDirs"/>; far shadows beyond
    /// the realtime shadow distance), A = ground height ((A·255)·heightStep + heightBase, region-root space).
    /// Time-of-day independent for R; G/B are used only while the live sun matches a baked direction within 3°.
    /// Per tier: <see cref="QualityProfile.Tier.worldSkyVisOff"/> and <see cref="QualityProfile.Tier.worldBakedSunOff"/>;
    /// launch args <c>rq_worldgi 0|1</c>, <c>rq_worldsun 0|1</c> (<see cref="RenderOverrides"/>).
    /// Cost: one bilinear fetch + ~25 ALU per world pixel, no keywords, no variants.
    /// </summary>
    [ExecuteAlways]
    [DisallowMultipleComponent]
    public sealed class WorldSkyVisibility : MonoBehaviour
    {
        public Texture2D map;
        [Tooltip("Region-root XZ (E, N) of the map's texel-(0,0) corner")] public Vector2 originLocal;
        [Tooltip("Metres per texel")] public float texelM = 1f;
        [Tooltip("Ground height of A = 0, region-root space (m)")] public float heightBase;
        [Tooltip("Metres per A step (1/255)")] public float heightStep = 0.3f;
        [Tooltip("Directions towards the sun of the G and B channels, region-root space (zero = unused)")]
        public Vector3[] sunDirs = new Vector3[2];
        [Tooltip("Preset names baked into G and B (documentation)")] public string[] sunPresets = new string[2];
        [Tooltip("Radiance of the occluders relative to the sky they hide (ambient = vis + (1 - vis) · bounce). WORKING_VALUE")]
        [Range(0f, 1f)] public float bounce = 0.3f;

        public static WorldSkyVisibility Active { get; private set; }

        static readonly int k_Map = Shader.PropertyToID("_KamionGIMap");
        static readonly int k_Rect = Shader.PropertyToID("_KamionGIRect");
        static readonly int k_Height = Shader.PropertyToID("_KamionGIHeight");
        static readonly int k_Sun = Shader.PropertyToID("_KamionGISun");

        /// <summary>Active sun channel weights (G, B) for the current sun direction; zero when it matches no baked one.</summary>
        public Vector2 SunWeights(Vector3 towardsSunWorld)
        {
            var w = Vector2.zero;
            if (sunDirs == null) return w;
            Vector3 local = transform.InverseTransformDirection(towardsSunWorld).normalized;
            for (int i = 0; i < sunDirs.Length && i < 2; i++)
            {
                if (sunDirs[i].sqrMagnitude < 0.5f) continue;
                if (Vector3.Dot(local, sunDirs[i].normalized) > 0.99863f) { w[i] = 1f; break; }   // cos 3°
            }
            return w;
        }

        void OnEnable()
        {
            Active = this;
            RenderPipelineManager.beginContextRendering += OnBeginRendering;
            Push();
        }

        void OnDisable()
        {
            RenderPipelineManager.beginContextRendering -= OnBeginRendering;
            if (Active == this) Active = null;
            Shader.SetGlobalVector(k_Height, Vector4.zero);   // strength 0 = off
            Shader.SetGlobalVector(k_Sun, Vector4.zero);
        }

        // Before every frame (also editor / batch control-camera renders): floating-origin shifts, preset and tier switches.
        void OnBeginRendering(ScriptableRenderContext ctx, List<Camera> cams) => Push();

        /// <summary>Writes the globals (a few SetGlobal calls per frame, no allocation).</summary>
        public void Push()
        {
            if (map == null) { Shader.SetGlobalVector(k_Height, Vector4.zero); return; }
            float strength = 1f;
            bool far = true;
            if (QualityProfileApplier.HasCurrent)
            {
                strength = QualityProfileApplier.Current.worldSkyVisOff ? 0f : 1f;
                far = !QualityProfileApplier.Current.worldBakedSunOff;
            }

            Vector3 o = transform.TransformPoint(new Vector3(originLocal.x, heightBase, originLocal.y));
            float ex = map.width * texelM, ez = map.height * texelM;
            Shader.SetGlobalTexture(k_Map, map);
            Shader.SetGlobalVector(k_Rect, new Vector4(o.x, o.z, 1f / ex, 1f / ez));
            Shader.SetGlobalVector(k_Height, new Vector4(o.y, heightStep, texelM, Mathf.Clamp01(strength)));

            Vector2 w = Vector2.zero;
            var sun = RenderSettings.sun;
            if (sun != null && sun.isActiveAndEnabled && sun.intensity > 0f) w = SunWeights(-sun.transform.forward);
            Shader.SetGlobalVector(k_Sun, new Vector4(w.x, w.y, far && strength > 0f ? 1f : 0f, bounce));
        }
    }
}
