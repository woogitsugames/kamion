using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// Tier settings for an off-screen capture camera (ADR 0246 photo-pair capture): far clip, MSAA/HDR flags,
    /// post-processing, antialiasing and dithering exactly as <see cref="QualityProfileApplier.Apply"/> sets them.
    /// NOT camera-only: this is the full <see cref="QualityProfileApplier.Apply"/> with volume = null and
    /// worldTextures = null, so it also re-sets Current/HasCurrent, the global shader keywords, the pipeline overrides
    /// and raises <see cref="QualityProfileApplier.Applied"/> (listeners such as vegetation re-evaluate the tier). Only the
    /// volume and the world textures are left as the scene's applier set them. Call it with the tier that is already
    /// current (G3PoseRunner does), where all of that is idempotent; never with a different tier.
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
