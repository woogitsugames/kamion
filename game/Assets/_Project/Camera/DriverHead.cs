using UnityEngine;

namespace Game.Cameras
{
    /// <summary>
    /// Head model of the seated driver for the cab camera (ADR 0052). Pure math, no scene access.
    ///
    /// Eye point (position): not here but in art-source/truck/dims.json (driver_h_point_m + driver_eye_above_h_point_m,
    /// mirrored in Game.Vehicle.Runtime.TractorDimensions): seat H/R-point + 0.635 m vertically (UNECE R46 ocular-point
    /// height above the R-point, SOURCED; seated 50th..95th percentile eye heights above the SgRP of SAE J1100/J941
    /// eyellipse data lie around it; the exact eyellipse tables were not opened, so the SAE comparison is UNVERIFIED).
    /// The camera is a child of the cab-suspension pivot (cab pitch / roll / heave move the head, not the chassis).
    ///
    /// Neck limits and pivot below are WORKING_VALUE (typical adult active range of motion, rounded; textbook values
    /// of the order rotation 70..90 deg, flexion 45..60 deg, extension 50..70 deg; not measured here).
    /// </summary>
    public static class DriverHead
    {
        /// <summary>Look yaw limit to either side [deg]: neck rotation (~80) plus a little torso twist in the belt.</summary>
        public const float YawLimitDeg = 90f;
        /// <summary>Look down (neck flexion) [deg], on top of <see cref="RestPitchDownDeg"/>.</summary>
        public const float PitchDownLimitDeg = 50f;
        /// <summary>Look up (neck extension) [deg], measured from the rest gaze.</summary>
        public const float PitchUpLimitDeg = 55f;
        /// <summary>Rest gaze below the cab's horizontal [deg]: dashboard top and the wheel rim stay in view
        /// (same value as the A7 control cameras cab-driver / TruckAssetBuilder).</summary>
        public const float RestPitchDownDeg = 6f;
        /// <summary>The eye relative to the neck pivot (atlanto-occipital joint), head frame (x right, y up, z forward) [m]. WORKING_VALUE.</summary>
        public static readonly Vector3 EyeFromNeckPivot = new Vector3(0f, 0.11f, 0.09f);

        public static float ClampYaw(float deg) => Mathf.Clamp(deg, -YawLimitDeg, YawLimitDeg);

        /// <summary>Look pitch relative to the rest gaze; positive = down.</summary>
        public static float ClampPitch(float deg) => Mathf.Clamp(deg, -PitchUpLimitDeg, PitchDownLimitDeg);

        /// <summary>Camera rotation relative to the eye anchor.</summary>
        public static Quaternion LookRotation(float yawDeg, float pitchDeg) =>
            Quaternion.Euler(RestPitchDownDeg + ClampPitch(pitchDeg), ClampYaw(yawDeg), 0f);

        /// <summary>
        /// Camera position in the anchor frame: the head turns about the neck pivot, so the eye moves a few cm when the
        /// driver looks sideways (parallax) and is exactly at the anchor in the rest pose. <paramref name="sway"/> is the
        /// limited acceleration-driven offset of the whole head.
        /// </summary>
        public static Vector3 LocalEyePosition(float yawDeg, float pitchDeg, Vector3 sway)
        {
            var look = Quaternion.Euler(ClampPitch(pitchDeg), ClampYaw(yawDeg), 0f);
            return sway + look * EyeFromNeckPivot - EyeFromNeckPivot;
        }
    }
}
