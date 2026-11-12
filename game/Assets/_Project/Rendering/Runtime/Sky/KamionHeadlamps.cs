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
        static Transform s_Frame, s_Left, s_Right;
        static Texture2D s_State;
        static int s_Scene = -1;
        static double s_NextSearch;
        const double BindingRefreshSeconds = 0.25;
        static string s_Warned;
        public static bool Enabled { get; private set; }
        public static string Diagnostics { get; private set; } = "disabled";

        public static void Reset()
        {
            Enabled = false;
            Shader.SetGlobalFloat(k_On, 0f);
            s_Source = null; s_Frame = s_Left = s_Right = null; s_State = null; s_Scene = -1; s_NextSearch = 0; s_Warned = null;
            Diagnostics = "reset";
        }

        static bool Resolve(Scene ownerScene)
        {
            if (!ownerScene.IsValid()) ownerScene = SceneManager.GetActiveScene();
#if UNITY_EDITOR
            if (UnityEditor.SceneManagement.EditorSceneManager.IsPreviewScene(ownerScene))
            { Diagnostics = "preview scene excluded"; return false; }
#endif
            int scene = ownerScene.handle;
            double now = System.Diagnostics.Stopwatch.GetTimestamp()/(double)System.Diagnostics.Stopwatch.Frequency;
            bool valid = s_Source != null && s_Source.isActiveAndEnabled && s_Source.gameObject.scene == ownerScene &&
                s_Frame != null && s_Source.cab == s_Frame && s_Left != null && s_Right != null &&
                s_Left.IsChildOf(s_Frame) && s_Right.IsChildOf(s_Frame);
            if (scene == s_Scene && now < s_NextSearch && valid) return true;
            if (scene == s_Scene && now < s_NextSearch && s_Source == null) return false;
            s_Scene = scene; s_NextSearch = now+BindingRefreshSeconds;
            var sources = Resources.FindObjectsOfTypeAll<CabInteriorLighting>()
                .Where(c => c.isActiveAndEnabled && c.cab != null && c.gameObject.scene == ownerScene && ownerScene.isLoaded).ToArray();
            if (sources.Length != 1)
            {
                s_Source = null; s_Frame = s_Left = s_Right = null;
                if (sources.Length == 0) { Diagnostics = "no player cab in environment scene"; return false; }
                return Reject("requires exactly one active player cab; found "+sources.Length);
            }
            var source = sources[0];
            if (valid && source == s_Source) return true;
            var anchors = source.cab.GetComponentsInChildren<Transform>(true);
            var left = anchors.Where(t => t.name == "LIGHT_LowBeam_L").ToArray();
            var right = anchors.Where(t => t.name == "LIGHT_LowBeam_R").ToArray();
            if (left.Length != 1 || right.Length != 1)
            {
                s_Source = null; s_Frame = s_Left = s_Right = null;
                return Reject("missing or ambiguous actual LIGHT_LowBeam_L/R anchors");
            }
            s_Source = source; s_Frame = source.cab; s_Left = left[0]; s_Right = right[0];
            return true;
        }

        static bool Reject(string reason)
        {
            Diagnostics = reason;
            if (s_Warned != reason) { Debug.LogWarning("[HEADLAMP] projection disabled: "+reason); s_Warned = reason; }
            return false;
        }

        public static void Push(SkyModel model, bool requested, float peakCd, Scene ownerScene = default)
        {
            Enabled = false; Shader.SetGlobalFloat(k_On, 0f);
            if (!requested || model == null) { Diagnostics = "disabled by preset/override"; return; }
            if (float.IsNaN(peakCd) || float.IsInfinity(peakCd) || peakCd <= 0f) { Diagnostics = "zero/invalid peak cd"; return; }
            var state = Shader.GetGlobalTexture("_TruckLightState") as Texture2D;
            if (state == null || !state.isReadable || state.width < 4 || state.height < 1)
            { Diagnostics = "readable player light-state texture unavailable"; return; }
            // Existing vehicle contract: texel2 is low-beam lens emission. Read only its on/off state,
            // never reinterpret lens nits as beam intensity. Forced lights therefore work too.
            Color low = state.GetPixel(2, 0);
            if (Mathf.Max(low.r, Mathf.Max(low.g, low.b)) <= 0f) { Diagnostics = "vehicle low beam off"; return; }
            // Scene loading may enable EnvironmentLighting before the truck. A new vehicle-state texture
            // invalidates the retry throttle; do not cache a missing cab while its low beam is still off.
            if (state != s_State) { s_State = state; s_NextSearch = 0; }
            if (!Resolve(ownerScene)) return;
            var frame = s_Source.cab;
            if (!Finite(s_Left.position) || !Finite(s_Right.position) || !Finite(frame.forward) ||
                !Finite(frame.right) || !Finite(frame.up) || float.IsNaN(model.Exposure) || float.IsInfinity(model.Exposure))
            { Reject("non-finite anchor/basis/exposure"); return; }
            Shader.SetGlobalVector(k_Left, s_Left.position); Shader.SetGlobalVector(k_Right, s_Right.position);
            Shader.SetGlobalVector(k_AxisRight, frame.right); Shader.SetGlobalVector(k_Up, frame.up);
            Shader.SetGlobalVector(k_Forward, frame.forward);
            Shader.SetGlobalVector(k_Color, new Vector4(1f, 0.97f, 0.92f, 0f)*(Mathf.Min(peakCd, 60000f)*model.Exposure/Mathf.PI));
            Shader.SetGlobalFloat(k_On, 1f); Enabled = true;
            Diagnostics = "actual anchors; low beam on; uncalibrated diffuse cone; no occlusion";
        }

        static bool Finite(Vector3 v) => !float.IsNaN(v.x) && !float.IsNaN(v.y) && !float.IsNaN(v.z) &&
            !float.IsInfinity(v.x) && !float.IsInfinity(v.y) && !float.IsInfinity(v.z);
    }
}
