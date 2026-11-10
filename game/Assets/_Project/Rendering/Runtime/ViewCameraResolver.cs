using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// The camera the player (or the on-device control-camera capture) actually sees, for per-view CPU lighting state
    /// (CabInteriorLighting cab view, StreetLamps nearest lamps). ADR 0044 addendum r9: on the phone the control camera
    /// (qacam=cab-dash) is enabled and the tagged "MainCamera" disabled, so <see cref="Camera.main"/> was null and the cab
    /// interior was rendered with the exterior state (no cab-view gain, enclosure 0.88, no shadow lift): 25-44 % of the
    /// cab-dash frame below 3 % luma on the A16 against ~1.5 % in the editor, whose visual-QA runner passes the camera
    /// explicitly. Order: the explicit camera if it renders, the tagged main camera, else the enabled on-screen game camera
    /// with the highest depth (the one drawn last, i.e. on top). No allocation after the first call.
    /// </summary>
    public static class ViewCameraResolver
    {
        static Camera[] s_All = new Camera[8];

        public static Camera Resolve(Camera explicitCamera)
        {
            if (explicitCamera != null && explicitCamera.isActiveAndEnabled) return explicitCamera;
            var main = Camera.main;
            if (main != null) return main;
            int n = Camera.allCamerasCount;
            if (n == 0) return null;
            if (s_All.Length < n) s_All = new Camera[Mathf.NextPowerOfTwo(n)];
            n = Camera.GetAllCameras(s_All);
            Camera best = null;
            for (int i = 0; i < n; i++)
            {
                var c = s_All[i];
                s_All[i] = null;
                if (c == null || c.targetTexture != null || c.cameraType != CameraType.Game) continue;
                if (c.TryGetComponent<UniversalAdditionalCameraData>(out var d) && d.renderType == CameraRenderType.Overlay) continue;
                if (best == null || c.depth > best.depth) best = c;
            }
            return best;
        }
    }
}
