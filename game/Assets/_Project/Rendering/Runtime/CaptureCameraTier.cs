using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// Camera-level tier settings for an off-screen capture camera (ADR 0246 photo-pair capture on the phone): far clip,
    /// MSAA/HDR flags, post-processing, antialiasing and dithering exactly as <see cref="QualityProfileApplier.Apply"/>
    /// sets them, without touching the volume or the world textures (those stay as the scene's applier set them).
    /// Lets assemblies without a URP reference (Game.Gameplay) configure such a camera.
    /// </summary>
    public static class CaptureCameraTier
    {
        public static void Apply(QualityProfile.Tier tier, Camera cam)
        {
            if (cam == null) return;
            Tonemapping tm = null;
            QualityProfileApplier.Apply(tier, cam, null, null, ref tm);
        }
    }
}
