using System.Linq;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Game.Rendering
{
    /// <summary>ADR 0108 r2: optional diffuse low-beam projection in the existing surface-lighting pass.
    /// Uses the actual art anchors and the existing readable _TruckLightState contract, not the view camera.
    /// Like that texture, this supports one player truck per scene. No Unity lights or renderer objects are created.
    /// Beam shape and peak cd are WORKING_VALUE, separate from lens luminance; there is no occlusion/shadow pass.</summary>
    public static class KamionHeadlamps
    {
        static readonly int k_On = Shader.PropertyToID("_KamionHeadlampOn"),
            k_Left = Shader.PropertyToID("_KamionHeadlampLeft"), k_Right = Shader.PropertyToID("_KamionHeadlampRight"),
            k_AxisRight = Shader.PropertyToID("_KamionHeadlampAxisRight"), k_Up = Shader.PropertyToID("_KamionHeadlampUp"),
            k_Forward = Shader.PropertyToID("_KamionHeadlampForward"), k_Color = Shader.PropertyToID("_KamionHeadlampColor");
        static CabInteriorLighting s_Source;
        static Transform s_Left, s_Right;
        static int s_Scene = -1;
        static float s_NextSearch;
        static string s_Warned;
        public static bool Enabled { get; private set; }
        public static string Diagnostics { get; private set; } = "disabled";

        public static void Reset()
        {
            Enabled = false;
            Shader.SetGlobalFloat(k_On, 0f);
            s_Source = null; s_Left = s_Right = null; s_Scene = -1; s_NextSearch = 0f; s_Warned = null;
            Diagnostics = "reset";
        }

        static bool Resolve()
        {
            int scene = SceneManager.GetActiveScene().handle;
            if (scene == s_Scene && s_Source != null && s_Source.isActiveAndEnabled &&
                s_Source.cab != null && s_Left != null && s_Right != null) return true;
            if (scene == s_Scene && Time.realtimeSinceStartup < s_NextSearch) return false;
            s_Scene = scene; s_NextSearch = Time.realtimeSinceStartup+1f;
            s_Source = null; s_Left = s_Right = null;
            var sources = Resources.FindObjectsOfTypeAll<CabInteriorLighting>()
                .Where(c => c.isActiveAndEnabled && c.cab != null && c.gameObject.scene.IsValid() && c.gameObject.scene.isLoaded).ToArray();
            if (sources.Length != 1) return Reject("requires exactly one active player cab; found "+sources.Length);
            var source = sources[0];
            var anchors = source.cab.GetComponentsInChildren<Transform>(true);
            var left = anchors.Where(t => t.name == "LIGHT_LowBeam_L").ToArray();
            var right = anchors.Where(t => t.name == "LIGHT_LowBeam_R").ToArray();
            if (left.Length != 1 || right.Length != 1) return Reject("missing or ambiguous actual LIGHT_LowBeam_L/R anchors");
            s_Source = source; s_Left = left[0]; s_Right = right[0];
            return true;
        }

        static bool Reject(string reason)
        {
            Diagnostics = reason;
            if (s_Warned != reason) { Debug.LogWarning("[HEADLAMP] projection disabled: "+reason); s_Warned = reason; }
            return false;
        }

        public static void Push(SkyModel model, bool requested, float peakCd)
        {
            Enabled = false; Shader.SetGlobalFloat(k_On, 0f);
            if (!requested || model == null) { Diagnostics = "disabled by preset/override"; return; }
            if (float.IsNaN(peakCd) || float.IsInfinity(peakCd) || peakCd <= 0f) { Diagnostics = "zero/invalid peak cd"; return; }
            if (!Resolve()) return;
            var state = Shader.GetGlobalTexture("_TruckLightState") as Texture2D;
            if (state == null || !state.isReadable || state.width < 4 || state.height < 1)
            { Reject("readable player light-state texture unavailable"); return; }
            // Existing vehicle contract: texel2 is low-beam lens emission. Read only its on/off state,
            // never reinterpret lens nits as beam intensity. Forced lights therefore work too.
            Color low = state.GetPixel(2, 0);
            if (Mathf.Max(low.r, Mathf.Max(low.g, low.b)) <= 0f) { Diagnostics = "vehicle low beam off"; return; }
            var frame = s_Source.cab;
            Shader.SetGlobalVector(k_Left, s_Left.position); Shader.SetGlobalVector(k_Right, s_Right.position);
            Shader.SetGlobalVector(k_AxisRight, frame.right); Shader.SetGlobalVector(k_Up, frame.up);
            Shader.SetGlobalVector(k_Forward, frame.forward);
            Shader.SetGlobalVector(k_Color, new Vector4(1f, 0.97f, 0.92f, 0f)*(peakCd*model.Exposure/Mathf.PI));
            Shader.SetGlobalFloat(k_On, 1f); Enabled = true;
            Diagnostics = "actual anchors; low beam on; uncalibrated diffuse cone; no occlusion";
        }
    }
}
