using System;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Body dimensions of the graybox tractor. Defaults = art-source/truck/dims.json (Track A1 working
    /// dimensions; statuses SOURCED/DERIVED/WORKING_VALUE are in that file). The DrivingLab editor builder
    /// re-reads dims.json and fails if it disagrees with these defaults (EditMode test too), so the runtime
    /// copy cannot silently drift.
    ///
    /// dims.json frame: Z up, +Y forward, origin on the ground under the FRONT axle, driver (LHD) at -X.
    /// Unity vehicle frame (physics core): Y up, +Z forward, origin on the ground under the REAR axle.
    /// Mapping: unity = (x, z_dims, y_dims + wheelbase).
    /// Wheel positions, track widths and tire radius come from the physics definition, not from here.
    /// </summary>
    [Serializable]
    public sealed class TractorDimensions
    {
        public float wheelbase = 3.70f;
        public float frontOverhang = 1.45f;
        public float rearOverhang = 0.80f;
        public float cabWidth = 2.49f;
        public float overallHeight = 3.95f;
        public float cabBackBehindFrontAxle = 0.95f;
        public float cabBodyBottom = 1.15f;
        public float cabInteriorFloor = 1.40f;
        public float frameWidthOuter = 0.85f;
        public float frameTopHeight = 0.97f;
        public float fifthWheelHeight = 1.15f;
        public float fifthWheelLead = 0.55f;
        public float dualSpacing = 0.34f;
        public float tyreSectionWidth = 0.315f;
        public float rimFlangeDiameter = 0.60f;
        public float mirrorHeadOuter = 1.545f;
        /// <summary>Driver eye point in dims.json frame (x, y forward of front axle, z height).</summary>
        public Vector3 driverEyePointDims = new Vector3(-0.55f, 0.45f, 2.50f);

        /// <summary>Driver eye point in the Unity vehicle frame.</summary>
        public Vector3 EyePointVehicle => new Vector3(driverEyePointDims.x, driverEyePointDims.z, driverEyePointDims.y + wheelbase);
        public float CabRearZ => wheelbase - cabBackBehindFrontAxle;
        public float FrontFaceZ => wheelbase + frontOverhang;
        public float RearEndZ => -rearOverhang;
    }
}
