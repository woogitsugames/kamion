using UnityEngine;

namespace Game.Rendering
{
    /// <summary>Optional wet-road use of the existing truck cube. Creates no cameras or captures.
    /// The sampled origin is the existing reflection camera's last rendered position, never the view camera.
    /// Moving / mixed-origin cubes fail closed until a complete stable six-face window is observed.</summary>
    public static class KamionWetReflections
    {
        static readonly int k_Origin = Shader.PropertyToID("_KamionWetCaptureOrigin");
        static VehicleReflectionCapture s_Source;
        static RenderTexture s_Cube;
        static Camera s_Camera;
        static Vector3 s_Origin;
        static int s_StableFaces;
        static bool s_Valid;
        public static string Diagnostics { get; private set; } = "off";

        public static void Reset()
        {
            Shader.SetGlobalVector(k_Origin, Vector4.zero);
            s_Source = null; s_Cube = null; s_Camera = null; s_Valid = false;
            Diagnostics = "off";
        }

        public static void Push(bool enabled)
        {
            var source = VehicleReflectionCapture.Active;
            if (!enabled || source == null || !source.Enabled || source.Cube == null)
            { Reset(); return; }
            if (source != s_Source || source.Cube != s_Cube)
            {
                Reset(); s_Source = source; s_Cube = source.Cube;
                // CaptureCamera is a disabled DontSave camera, outside the truck hierarchy.
                // Resolve once per source/cube, require its exact runtime identity and scene.
                foreach (var candidate in Resources.FindObjectsOfTypeAll<Camera>())
                    if (candidate.name == "CaptureCamera" && candidate.cameraType == CameraType.Reflection &&
                        candidate.transform.parent != null && candidate.transform.parent.name == "VehicleReflectionCapture (runtime)" &&
                        candidate.gameObject.scene == source.gameObject.scene)
                    {
                        if (s_Camera != null) { Reset(); Diagnostics = "ambiguous capture camera"; return; }
                        s_Camera = candidate;
                    }
                if (s_Camera != null)
                {
                    s_Origin = s_Camera.transform.position;
                    s_StableFaces = source.FacesRendered;
                    // A newly allocated cube starts with RenderAllNow's six co-located faces.
                    s_Valid = source.FacesRendered == 6;
                }
            }
            if (s_Camera == null)
            { Shader.SetGlobalVector(k_Origin, Vector4.zero); Diagnostics = "no unique capture camera"; return; }
            Vector3 actual = s_Camera.transform.position;
            if ((actual - s_Origin).sqrMagnitude > 0.25f)
            { s_Origin = actual; s_StableFaces = source.FacesRendered; s_Valid = false; }
            if (source.FacesRendered - s_StableFaces >= 6) s_Valid = true;
            // A paused/stale camera does not follow a moving truck. Never re-label that old cube with a new origin.
            bool nearSource = (source.transform.TransformPoint(source.captureOffset) - s_Origin).sqrMagnitude <= 0.25f;
            bool valid = s_Valid && nearSource;
            Shader.SetGlobalVector(k_Origin, new Vector4(s_Origin.x, s_Origin.y, s_Origin.z, valid ? 1f : 0f));
            Diagnostics = valid ? "stable existing cube; local radius 12m; sphere parallax 20m WORKING_VALUE" : "moving/incomplete cube: analytic fallback";
        }
    }
}
