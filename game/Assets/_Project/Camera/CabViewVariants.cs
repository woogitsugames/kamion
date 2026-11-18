using UnityEngine;

namespace Game.Cameras
{
    /// <summary>
    /// D84 / P1-4 ("kadr FPP pusty"): candidate driver views for the owner's choice (agent cab-view-s24, 2026-11-18).
    /// QA data only - the game camera is unchanged: <see cref="CameraRig.cabFov"/> comes from ControlSettings.cabFov
    /// (default 55 deg, settings stepper "Pole widzenia" 45..75 deg in 5 deg steps) and the rest gaze from
    /// <see cref="DriverHead.RestPitchDownDeg"/> (6 deg). The eye point is the same for every variant (DriverEyePoint,
    /// art-source/truck/dims.json driver_eye_point_m, UNECE R46 R-point + 635 mm).
    /// Switching after the owner's decision: the FOV is one ControlSettings default (no new UI, the stepper exists);
    /// the pitch is DriverHead.RestPitchDownDeg. All values below are WORKING_VALUE (no seated reference photo, docs/07 section 4).
    /// </summary>
    public static class CabViewVariants
    {
        public readonly struct Variant
        {
            public readonly string Id;
            /// <summary>Vertical FOV [deg] (the convention of ControlSettings.cabFov and Camera.fieldOfView).</summary>
            public readonly float VerticalFovDeg;
            /// <summary>Rest gaze below the cab's horizontal [deg], positive = down.</summary>
            public readonly float PitchDownDeg;
            public readonly string Note;
            public Variant(string id, float fov, float pitch, string note) { Id = id; VerticalFovDeg = fov; PitchDownDeg = pitch; Note = note; }
            public float HorizontalFovDeg(float aspect) => HorizontalFov(VerticalFovDeg, aspect);
        }

        public static readonly Variant[] All =
        {
            new Variant("cab-view-0-fov55", 55f, DriverHead.RestPitchDownDeg, "game default today (ControlSettings.cabFov = 55)"),
            new Variant("cab-view-a-fov62", 62f, DriverHead.RestPitchDownDeg, "= QA camera cab-driver (A7, 62 deg)"),
            new Variant("cab-view-b-fov70", 70f, DriverHead.RestPitchDownDeg, "wider, same eye and gaze"),
            new Variant("cab-view-c-fov75", 75f, DriverHead.RestPitchDownDeg, "widest the settings allow (ControlSettings.FovMax)"),
            new Variant("cab-view-d-fov70-p10", 70f, 10f, "wider + rest gaze 10 deg down (as cab-driver-ab10)"),
        };

        /// <summary>Horizontal FOV [deg] of a vertical FOV at a screen aspect (width / height).</summary>
        public static float HorizontalFov(float verticalDeg, float aspect) =>
            2f * Mathf.Atan(Mathf.Tan(verticalDeg * 0.5f * Mathf.Deg2Rad) * aspect) * Mathf.Rad2Deg;
    }
}
