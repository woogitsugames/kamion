using System;
using Game.Vehicle.Physics;
using UnityEngine;
using static Game.Vehicle.Runtime.GrayboxTractorBuilder;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Body dimensions of the graybox 13.6 m curtainsider (trailer frame: origin on the ground below the kingpin,
    /// +Z forward). Axles, track, tire radius, kingpin height, landing-gear position and the cargo bay come from
    /// the physics definition (curtainsider_tridem_13_6.trailer.json); these are the remaining body numbers.
    /// </summary>
    [Serializable]
    public sealed class TrailerDimensions
    {
        /// <summary>External length 13.6 m and width 2.55 m: EU legal maximum for a semi-trailer box (docs/04 §5, Directive 96/53/EC) — SOURCED.</summary>
        public float length = 13.6f, width = 2.55f;
        /// <summary>Overall height 4.0 m: EU maximum vehicle height (96/53/EC) — SOURCED as the limit; the graybox uses it.</summary>
        public float height = 4.0f;
        /// <summary>Front wall thickness and gap ahead of the cargo bay front [m] — WORKING_VALUE.</summary>
        public float frontWall = 0.05f;
        /// <summary>Underside of the coupler plate = fifth-wheel plate top when coupled [m] — DERIVED (kingpin lock point 1.20 m minus 5 cm).</summary>
        public float plateBottom = 1.15f;
        /// <summary>Main beam depth below the floor behind the landing gear [m] — WORKING_VALUE.</summary>
        public float beamBottom = 0.92f;
        /// <summary>Rear underrun protection bar height range above ground [m] — WORKING_VALUE (UN R58 asks ≤ 0.55 m ground clearance).</summary>
        public float rupdBottom = 0.40f, rupdTop = 0.55f;
    }

    /// <summary>
    /// Builds the graybox curtainsider semi-trailer at true dimensions (13.6 × 2.55 × 4.0 m, tridem, landing gear)
    /// from primitives: <see cref="TrailerBody"/> + <see cref="TrailerVisuals"/>, PhysX colliders for world contact
    /// (dock bumpers, walls) and a reversing camera on the rear portal. Used by the DrivingLab editor builder (saved
    /// as a prefab) and by PlayMode tests (built at runtime).
    /// </summary>
    public static class GrayboxTrailerBuilder
    {
        public const string RootName = "Trailer_Curtainsider_Graybox";

        public static TrailerBody Build(VehicleDataAsset data, TrailerDimensions dims, GrayboxMaterials mats)
        {
            if (data == null) throw new ArgumentNullException(nameof(data));
            if (!data.HasTrailer) throw new InvalidOperationException($"{data.name}: no trailer definition");
            dims ??= new TrailerDimensions();
            mats ??= GrayboxMaterials.CreateRuntime();
            int layer = UnityGroundQuery.ResolveVehicleLayer();
            var def = data.Trailer;
            var probe = data.CreateTrailer();

            var root = new GameObject(RootName);
            root.AddComponent<Rigidbody>();
            var body = root.AddComponent<TrailerBody>();
            var visuals = root.AddComponent<TrailerVisuals>();
            visuals.body = body;

            float front = (float)def.cargoBay.frontZ + dims.frontWall;
            float rear = front - dims.length;
            float hw = dims.width * 0.5f;
            float floorTop = (float)def.cargoBay.floorHeight;
            float floorBottom = floorTop - 0.10f;
            float lgZ = (float)def.landingGear.positionZ;
            float firstAxle = (float)def.axles[0].positionZ, lastAxle = (float)def.axles[def.axles.Length - 1].positionZ;

            // ---- colliders (world contact only: dock bumpers, walls; wheels and legs are solver contacts) ----
            var col = Child(root.transform, "Colliders", Vector3.zero);
            BoxCol(col, "Body", new Vector3(0f, (dims.plateBottom + 0.07f + dims.height) * 0.5f, (front + rear) * 0.5f),
                new Vector3(dims.width, dims.height - dims.plateBottom - 0.07f, dims.length));
            BoxCol(col, "Beams", new Vector3(0f, (dims.beamBottom + floorBottom) * 0.5f, (lgZ - 0.4f + rear + 0.1f) * 0.5f),
                new Vector3(1.2f, floorBottom - dims.beamBottom, lgZ - 0.4f - rear - 0.1f));
            BoxCol(col, "RearUnderrun", new Vector3(0f, (dims.rupdBottom + dims.rupdTop) * 0.5f, rear + 0.25f),
                new Vector3(2.35f, dims.rupdTop - dims.rupdBottom, 0.12f));

            // ---- body ----
            var bodyT = Child(root.transform, "Body", Vector3.zero);
            void P(string n, float x0, float x1, float y0, float y1, float z0, float z1, Material mat) =>
                Box(bodyT, n, new Vector3((x0 + x1) * 0.5f, (y0 + y1) * 0.5f, (z0 + z1) * 0.5f), new Vector3(x1 - x0, y1 - y0, z1 - z0), mat);
            float top = dims.height;
            P("Floor", -hw, hw, floorBottom, floorTop, rear, front, mats.chassis);
            P("FrontWall", -hw, hw, floorTop, top, front - dims.frontWall, front, mats.trailerPanel);
            P("Roof", -hw, hw, top - 0.04f, top, rear, front, mats.trailerPanel);
            P("CouplerPlate", -1.15f, 1.15f, dims.plateBottom, floorBottom, lgZ - 0.6f, front - 0.05f, mats.chassis);
            P("Beam_L", -0.60f, -0.48f, dims.beamBottom, floorBottom, rear + 0.1f, lgZ + 0.3f, mats.chassis);
            P("Beam_R", 0.48f, 0.60f, dims.beamBottom, floorBottom, rear + 0.1f, lgZ + 0.3f, mats.chassis);
            Cyl(bodyT, "Kingpin", new Vector3(0f, dims.plateBottom - 0.04f, 0f), new Vector3(0.09f, 0.04f, 0.09f), Quaternion.identity, mats.rim);
            // Side: rave (bottom rail), curtain, top rail, posts.
            for (int s = -1; s <= 1; s += 2)
            {
                string n = s < 0 ? "_L" : "_R";
                float xo = s * hw, xi = s * (hw - 0.04f);
                float x0 = Mathf.Min(xo, xi), x1 = Mathf.Max(xo, xi);
                P("Rave" + n, x0, x1, floorBottom - 0.10f, floorTop + 0.08f, rear, front, mats.dark);
                P("Curtain" + n, x0, x1, floorTop + 0.08f, top - 0.12f, rear + 0.08f, front - dims.frontWall, mats.curtain);
                P("TopRail" + n, x0, x1, top - 0.12f, top - 0.02f, rear, front, mats.trailerPanel);
                // Sliding curtain posts every 3 m (light vertical bands on the curtain).
                for (float z = front - 0.6f; z > rear + 0.3f; z -= 3.0f)
                    P("Post" + n, xo - s * 0.005f - 0.01f, xo - s * 0.005f + 0.01f, floorTop + 0.08f, top - 0.12f, z - 0.04f, z + 0.04f, mats.trailerPanel);
            }
            // Rear portal and doors.
            P("RearHeader", -hw, hw, top - 0.25f, top, rear, rear + 0.08f, mats.trailerPanel);
            P("RearPost_L", -hw, -hw + 0.10f, floorBottom - 0.10f, top, rear, rear + 0.08f, mats.trailerPanel);
            P("RearPost_R", hw - 0.10f, hw, floorBottom - 0.10f, top, rear, rear + 0.08f, mats.trailerPanel);
            P("Door_L", -hw + 0.10f, -0.01f, floorTop, top - 0.25f, rear + 0.01f, rear + 0.06f, mats.trailerPanel);
            P("Door_R", 0.01f, hw - 0.10f, floorTop, top - 0.25f, rear + 0.01f, rear + 0.06f, mats.trailerPanel);
            for (int k = 0; k < 4; k++)
            {
                float x = -0.95f + k * 0.63f;
                P("DoorBar" + k, x - 0.02f, x + 0.02f, floorTop + 0.1f, top - 0.35f, rear - 0.03f, rear + 0.01f, mats.rim);
            }
            P("Underrun", -1.17f, 1.17f, dims.rupdBottom, dims.rupdTop, rear + 0.19f, rear + 0.31f, mats.dark);
            P("UnderrunStay_L", -0.62f, -0.52f, dims.rupdTop, dims.beamBottom, rear + 0.20f, rear + 0.30f, mats.chassis);
            P("UnderrunStay_R", 0.52f, 0.62f, dims.rupdTop, dims.beamBottom, rear + 0.20f, rear + 0.30f, mats.chassis);
            P("Lamp_L", -1.15f, -0.70f, floorBottom - 0.22f, floorBottom - 0.10f, rear - 0.02f, rear + 0.04f, mats.lamp);
            P("Lamp_R", 0.70f, 1.15f, floorBottom - 0.22f, floorBottom - 0.10f, rear - 0.02f, rear + 0.04f, mats.lamp);
            // Side underrun guards between the landing gear and the first axle.
            for (int s = -1; s <= 1; s += 2)
            {
                float x = s * (hw - 0.08f);
                P(s < 0 ? "SideGuard_L" : "SideGuard_R", x - 0.02f, x + 0.02f, 0.50f, 0.62f, firstAxle + 0.75f, lgZ - 0.5f, mats.dark);
                P(s < 0 ? "SideGuard2_L" : "SideGuard2_R", x - 0.02f, x + 0.02f, 0.80f, 0.90f, firstAxle + 0.75f, lgZ - 0.5f, mats.dark);
            }

            // ---- wheels (from the physics definition) ----
            var wheelsRoot = Child(root.transform, "Wheels", Vector3.zero);
            var wheels = probe.Wheels;
            var pivots = new Transform[wheels.Length];
            var spinners = new Transform[wheels.Length];
            var tireDims = new TractorDimensions();
            for (int i = 0; i < wheels.Length; i++)
            {
                var w = wheels[i];
                var pivot = Child(wheelsRoot, "W_" + w.Name, w.HardpointLocal.ToUnity() - new Vector3(0f, (float)w.S, 0f));
                var spin = Child(pivot, "Spin", Vector3.zero);
                Tire(spin, "Tire", 0f, (float)w.Radius, 0.385f, w.Side, mats, tireDims);
                pivots[i] = pivot;
                spinners[i] = spin;
            }
            float track = (float)def.axles[0].trackWidth * 0.5f;
            for (int s = -1; s <= 1; s += 2)
                P(s < 0 ? "Mudguard_L" : "Mudguard_R", s * track - 0.26f, s * track + 0.26f, 1.10f, 1.13f, lastAxle - 0.75f, firstAxle + 0.75f, mats.dark);
            visuals.wheelPivots = pivots;
            visuals.wheelSpinners = spinners;

            // ---- landing gear: fixed outer tubes, moving inner legs (origin at the foot) ----
            var lg = def.landingGear;
            var legs = new Transform[2];
            for (int k = 0; k < 2; k++)
            {
                float x = (k == 0 ? -1 : 1) * (float)lg.halfTrack;
                string n = k == 0 ? "_L" : "_R";
                Box(bodyT, "LegOuter" + n, new Vector3(x, (0.62f + dims.plateBottom) * 0.5f, lgZ), new Vector3(0.14f, dims.plateBottom - 0.62f, 0.14f), mats.dark);
                var leg = Child(root.transform, "LegInner" + n, new Vector3(x, (float)lg.raisedFootY, lgZ));
                Box(leg, "Tube", new Vector3(0f, 0.40f, 0f), new Vector3(0.10f, 0.80f, 0.10f), mats.rim);
                Box(leg, "Foot", new Vector3(0f, 0.02f, 0f), new Vector3(0.26f, 0.04f, 0.26f), mats.dark);
                legs[k] = leg;
            }
            Box(bodyT, "LegBrace", new Vector3(0f, 0.80f, lgZ), new Vector3(2f * (float)lg.halfTrack, 0.06f, 0.06f), mats.dark);
            Box(bodyT, "CrankBox", new Vector3(-(float)lg.halfTrack - 0.12f, 0.95f, lgZ), new Vector3(0.10f, 0.16f, 0.16f), mats.dark);
            visuals.legs = legs;

            // ---- reversing camera on the rear header, looking back and down ----
            var cam = Child(root.transform, "ReversingCamera", new Vector3(0f, top - 0.30f, rear - 0.10f));
            cam.localRotation = Quaternion.Euler(32f, 180f, 0f);
            RenderTextureMirror.ConfigureCheapCamera(cam.gameObject.AddComponent<Camera>(), 78f, 0.1f, 150f);
            cam.gameObject.AddComponent<ReversingCamera>();

            SetLayerRecursive(root, layer);
            body.SetDataForBuilder(data);
            if (Application.isPlaying) body.Initialize(data, CargoPreset.Empty, 0);
            return body;
        }
    }
}
