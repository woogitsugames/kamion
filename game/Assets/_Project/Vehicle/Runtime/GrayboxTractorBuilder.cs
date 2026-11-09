using System;
using Game.Vehicle.Physics;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>Material set for the graybox (assets in the editor, runtime instances in tests).</summary>
    [Serializable]
    public sealed class GrayboxMaterials
    {
        public Material paint, chassis, tire, rim, interior, dark, marker;

        public static GrayboxMaterials CreateRuntime()
        {
            var shader = Shader.Find("Universal Render Pipeline/Lit");
            Material M(string n, Color c, float smooth)
            {
                var m = new Material(shader) { name = n };
                m.SetColor("_BaseColor", c);
                m.SetFloat("_Smoothness", smooth);
                return m;
            }
            var p = DefaultColors;
            return new GrayboxMaterials
            {
                paint = M("GB_Paint", p[0], 0.45f), chassis = M("GB_Chassis", p[1], 0.25f), tire = M("GB_Tire", p[2], 0.15f),
                rim = M("GB_Rim", p[3], 0.4f), interior = M("GB_Interior", p[4], 0.2f), dark = M("GB_Dark", p[5], 0.3f),
                marker = M("GB_Marker", p[6], 0.3f),
            };
        }

        /// <summary>sRGB base colours: paint, chassis, tire, rim, interior, dark trim, rotation marker.</summary>
        public static readonly Color[] DefaultColors =
        {
            new Color(0.78f, 0.78f, 0.76f), new Color(0.16f, 0.16f, 0.17f), new Color(0.07f, 0.07f, 0.07f),
            new Color(0.62f, 0.63f, 0.64f), new Color(0.30f, 0.30f, 0.29f), new Color(0.11f, 0.11f, 0.12f),
            new Color(0.85f, 0.55f, 0.10f),
        };
    }

    /// <summary>
    /// Builds the graybox 4x2 tractor from primitives at the true dimensions: body from
    /// <see cref="TractorDimensions"/> (art-source/truck/dims.json), wheel positions, tire radius and track widths
    /// from the physics definition. No art; legible shapes only. Used by the DrivingLab editor builder (saved as a
    /// prefab) and by PlayMode tests (built at runtime).
    /// </summary>
    public static class GrayboxTractorBuilder
    {
        public const string RootName = "Tractor4x2_Graybox";
        static Mesh s_Cube, s_Cylinder;

        public static VehicleBody Build(VehicleDataAsset data, TractorDimensions dims, GrayboxMaterials mats)
        {
            if (data == null) throw new ArgumentNullException(nameof(data));
            dims ??= new TractorDimensions();
            mats ??= GrayboxMaterials.CreateRuntime();
            int layer = UnityGroundQuery.ResolveVehicleLayer();
            var probe = data.CreateModel(); // geometry only (hardpoints, static travel, radii)

            var root = new GameObject(RootName);
            root.AddComponent<Rigidbody>();
            var body = root.AddComponent<VehicleBody>();
            var visuals = root.AddComponent<VehicleVisuals>();
            visuals.body = body;

            // ---- colliders (chassis-world contact only; wheels have no colliders) ----
            var col = Child(root.transform, "Colliders", Vector3.zero);
            float frameLen = dims.FrontFaceZ - dims.RearEndZ;
            BoxCol(col, "Frame", new Vector3(0f, dims.frameTopHeight - 0.11f, dims.RearEndZ + frameLen * 0.5f), new Vector3(dims.frameWidthOuter, 0.22f, frameLen));
            float cabLen = dims.FrontFaceZ - 0.05f - dims.CabRearZ;
            float cabH = dims.overallHeight - dims.cabBodyBottom;
            BoxCol(col, "Cab", new Vector3(0f, dims.cabBodyBottom + cabH * 0.5f, dims.CabRearZ + cabLen * 0.5f), new Vector3(dims.cabWidth, cabH, cabLen));
            BoxCol(col, "Bumper", new Vector3(0f, 0.60f, dims.FrontFaceZ - 0.10f), new Vector3(dims.cabWidth - 0.04f, 0.50f, 0.20f));

            // ---- chassis visuals ----
            var chassis = Child(root.transform, "Chassis", Vector3.zero);
            float railX = dims.frameWidthOuter * 0.5f - 0.045f;
            float railY = dims.frameTopHeight - 0.135f;
            float railLen = dims.FrontFaceZ - 0.25f - dims.RearEndZ;
            float railZ = dims.RearEndZ + railLen * 0.5f;
            Box(chassis, "Rail_L", new Vector3(-railX, railY, railZ), new Vector3(0.09f, 0.27f, railLen), mats.chassis);
            Box(chassis, "Rail_R", new Vector3(railX, railY, railZ), new Vector3(0.09f, 0.27f, railLen), mats.chassis);
            for (float z = dims.RearEndZ + 0.1f; z < dims.FrontFaceZ - 0.3f; z += 1.2f)
                Box(chassis, "Crossmember", new Vector3(0f, railY, z), new Vector3(dims.frameWidthOuter - 0.1f, 0.2f, 0.08f), mats.chassis);
            Cyl(chassis, "FifthWheel", new Vector3(0f, dims.frameTopHeight + (dims.fifthWheelHeight - dims.frameTopHeight) * 0.5f, dims.fifthWheelLead),
                new Vector3(0.9f, (dims.fifthWheelHeight - dims.frameTopHeight) * 0.5f, 0.9f), Quaternion.identity, mats.dark);
            Box(chassis, "FuelTank_L", new Vector3(-0.84f, 0.75f, 2.0f), new Vector3(0.72f, 0.60f, 1.20f), mats.rim);
            Box(chassis, "BatteryAirBox_R", new Vector3(0.82f, 0.78f, 2.1f), new Vector3(0.66f, 0.46f, 1.0f), mats.chassis);
            Box(chassis, "Bumper", new Vector3(0f, 0.60f, dims.FrontFaceZ - 0.10f), new Vector3(dims.cabWidth - 0.04f, 0.50f, 0.20f), mats.dark);
            Box(chassis, "Step_L", new Vector3(-dims.cabWidth * 0.5f + 0.15f, 0.75f, dims.wheelbase + 0.55f), new Vector3(0.30f, 0.06f, 0.45f), mats.dark);
            Box(chassis, "Step_R", new Vector3(dims.cabWidth * 0.5f - 0.15f, 0.75f, dims.wheelbase + 0.55f), new Vector3(0.30f, 0.06f, 0.45f), mats.dark);
            float rearTrack = (float)probe.Wheels[probe.Wheels.Length - 1].HardpointLocal.x;
            Box(chassis, "Mudguard_L", new Vector3(-Mathf.Abs(rearTrack), 1.12f, 0f), new Vector3(0.70f, 0.03f, 1.20f), mats.dark);
            Box(chassis, "Mudguard_R", new Vector3(Mathf.Abs(rearTrack), 1.12f, 0f), new Vector3(0.70f, 0.03f, 1.20f), mats.dark);
            Box(chassis, "RearLightBar", new Vector3(0f, 0.85f, dims.RearEndZ + 0.03f), new Vector3(2.3f, 0.12f, 0.06f), mats.dark);

            // ---- cab (pivot moves with the cab-suspension output) ----
            float cabMountZ = dims.CabRearZ + cabLen * 0.5f;
            var cabPivot = Child(root.transform, "CabPivot", new Vector3(0f, dims.cabBodyBottom, cabMountZ));
            Vector3 cabOrigin = cabPivot.localPosition;
            BuildCab(cabPivot, cabOrigin, dims, mats, out Transform steeringWheel);
            var eye = Child(cabPivot, "DriverEyePoint", dims.EyePointVehicle - cabOrigin);
            eye.localRotation = Quaternion.identity;

            // ---- wheels (positions from the physics definition) ----
            var wheelsRoot = Child(root.transform, "Wheels", Vector3.zero);
            var wheels = probe.Wheels;
            var pivots = new Transform[wheels.Length];
            var spinners = new Transform[wheels.Length];
            for (int i = 0; i < wheels.Length; i++)
            {
                var w = wheels[i];
                var hp = w.HardpointLocal.ToUnity();
                var pivot = Child(wheelsRoot, "W_" + w.Name, hp - new Vector3(0f, (float)w.S, 0f));
                var spin = Child(pivot, "Spin", Vector3.zero);
                float r = (float)w.Radius;
                float tw = dims.tyreSectionWidth;
                int side = w.Side;
                if (w.TireCount == 1)
                    Tire(spin, "Tire", 0f, r, tw, side, mats, dims);
                else
                {
                    Tire(spin, "Tire_Outer", side * dims.dualSpacing * 0.5f, r, tw, side, mats, dims);
                    Tire(spin, "Tire_Inner", -side * dims.dualSpacing * 0.5f, r, tw, 0, mats, dims);
                }
                pivots[i] = pivot;
                spinners[i] = spin;
            }
            visuals.wheelPivots = pivots;
            visuals.wheelSpinners = spinners;
            visuals.cabPivot = cabPivot;
            visuals.steeringWheel = steeringWheel;

            SetLayerRecursive(root, layer);
            body.SetDataForBuilder(data);
            if (Application.isPlaying) body.Initialize(data);
            return body;
        }

        static void BuildCab(Transform pivot, Vector3 o, TractorDimensions d, GrayboxMaterials m, out Transform steeringWheel)
        {
            float xl = -d.cabWidth * 0.5f, xr = d.cabWidth * 0.5f;
            float zb = d.CabRearZ, zf = d.FrontFaceZ - 0.05f;
            float yb = d.cabBodyBottom, yt = d.overallHeight, yFloor = d.cabInteriorFloor;
            const float th = 0.05f;
            Vector3 eye = d.EyePointVehicle;
            // Windscreen opening and side window band (WORKING_VALUE graybox proportions around the eye point).
            float wsBottom = eye.y - 0.45f, wsTop = eye.y + 0.65f;
            float winBottom = eye.y - 0.30f, winTop = eye.y + 0.50f;
            float doorRear = eye.z - 0.30f;

            void P(string n, float x0, float x1, float y0, float y1, float z0, float z1, Material mat) =>
                Box(pivot, n, new Vector3((x0 + x1) * 0.5f, (y0 + y1) * 0.5f, (z0 + z1) * 0.5f) - o, new Vector3(x1 - x0, y1 - y0, z1 - z0), mat);

            P("Floor", xl, xr, yb, yFloor, zb, zf, m.paint);
            P("BackWall", xl, xr, yFloor, yt - th, zb, zb + th, m.paint);
            P("Roof", xl, xr, yt - th, yt, zb, zf, m.paint);
            P("FrontLower", xl, xr, yFloor, wsBottom, zf - th, zf, m.paint);
            P("Grille", xl + 0.25f, xr - 0.25f, yb + 0.05f, wsBottom - 0.15f, zf, zf + 0.04f, m.dark);
            P("FrontUpper", xl, xr, wsTop, yt - th, zf - th, zf, m.paint);
            P("APillar_L", xl, xl + 0.12f, wsBottom, wsTop, zf - 0.12f, zf, m.paint);
            P("APillar_R", xr - 0.12f, xr, wsBottom, wsTop, zf - 0.12f, zf, m.paint);
            for (int s = -1; s <= 1; s += 2)
            {
                float x0 = s < 0 ? xl : xr - th, x1 = s < 0 ? xl + th : xr;
                string n = s < 0 ? "_L" : "_R";
                P("SideLower" + n, x0, x1, yFloor, winBottom, zb + th, zf - th, m.paint);
                P("SideRearBand" + n, x0, x1, winBottom, winTop, zb + th, doorRear, m.paint);
                P("SideFrontPost" + n, x0, x1, winBottom, winTop, zf - 0.15f, zf - th, m.paint);
                P("SideUpper" + n, x0, x1, winTop, yt - th, zb + th, zf - th, m.paint);
                // Mirror arm + head (head outer edge at mirrorHeadOuter from centre).
                float headX = s * (d.mirrorHeadOuter - 0.125f);
                Box(pivot, "MirrorArm" + n, new Vector3((headX + s * d.cabWidth * 0.5f) * 0.5f, eye.y + 0.25f, zf - 0.10f) - o,
                    new Vector3(Mathf.Abs(headX - s * d.cabWidth * 0.5f), 0.04f, 0.04f), m.dark);
                Box(pivot, "MirrorHead" + n, new Vector3(headX, eye.y + 0.05f, zf - 0.10f) - o, new Vector3(0.25f, 0.42f, 0.08f), m.dark);
            }
            // Interior.
            P("Dashboard", xl + 0.10f, xr - 0.10f, yFloor, wsBottom - 0.05f, zf - 0.45f, zf - th, m.interior);
            P("Binnacle", eye.x - 0.25f, eye.x + 0.25f, wsBottom - 0.05f, wsBottom + 0.07f, zf - 0.42f, zf - 0.28f, m.dark);
            P("DriverSeat", eye.x - 0.25f, eye.x + 0.25f, yFloor, yFloor + 0.50f, eye.z - 0.60f, eye.z - 0.10f, m.dark);
            P("DriverBackrest", eye.x - 0.25f, eye.x + 0.25f, yFloor + 0.50f, yFloor + 1.20f, eye.z - 0.70f, eye.z - 0.60f, m.dark);
            P("PassengerSeat", -eye.x - 0.25f, -eye.x + 0.25f, yFloor, yFloor + 0.50f, eye.z - 0.60f, eye.z - 0.10f, m.dark);
            P("PassengerBackrest", -eye.x - 0.25f, -eye.x + 0.25f, yFloor + 0.50f, yFloor + 1.20f, eye.z - 0.70f, eye.z - 0.60f, m.dark);
            P("Bunk", xl + th, xr - th, yFloor + 0.20f, yFloor + 0.45f, zb + th, zb + 0.75f, m.interior);

            // Steering wheel: Ø 0.5 m (WORKING_VALUE), centre 0.45 m below / 0.43 m ahead of the eye, wheel plane tilted 50°.
            var sw = Child(pivot, "SteeringWheel", new Vector3(eye.x, eye.y - 0.48f, eye.z + 0.43f) - o);
            sw.localRotation = Quaternion.Euler(50f, 0f, 0f);
            const float rr = 0.25f;
            const int seg = 16;
            for (int i = 0; i < seg; i++)
            {
                float a = i * Mathf.PI * 2f / seg;
                var seg_ = Child(sw, "Rim", new Vector3(Mathf.Sin(a) * rr, Mathf.Cos(a) * rr, 0f));
                seg_.localRotation = Quaternion.Euler(0f, 0f, -a * Mathf.Rad2Deg);
                Box(seg_, "S", Vector3.zero, new Vector3(2f * Mathf.PI * rr / seg + 0.01f, 0.035f, 0.035f), m.dark);
            }
            Box(sw, "Spoke_L", new Vector3(-rr * 0.5f, 0f, 0.01f), new Vector3(rr, 0.04f, 0.02f), m.dark);
            Box(sw, "Spoke_R", new Vector3(rr * 0.5f, 0f, 0.01f), new Vector3(rr, 0.04f, 0.02f), m.dark);
            Box(sw, "Spoke_B", new Vector3(0f, -rr * 0.5f, 0.01f), new Vector3(0.04f, rr, 0.02f), m.dark);
            Box(sw, "TopMarker", new Vector3(0f, rr, -0.005f), new Vector3(0.05f, 0.045f, 0.045f), m.marker);
            Cyl(sw, "Hub", new Vector3(0f, 0f, 0.02f), new Vector3(0.12f, 0.03f, 0.12f), Quaternion.Euler(90f, 0f, 0f), m.dark);
            Cyl(sw, "Column", new Vector3(0f, 0f, 0.25f), new Vector3(0.06f, 0.22f, 0.06f), Quaternion.Euler(90f, 0f, 0f), m.dark);
            steeringWheel = sw;
        }

        static void Tire(Transform spin, string name, float xOffset, float r, float width, int outerSide, GrayboxMaterials m, TractorDimensions d)
        {
            var t = Child(spin, name, new Vector3(xOffset, 0f, 0f));
            Cyl(t, "Tread", Vector3.zero, new Vector3(2f * r, width * 0.5f, 2f * r), Quaternion.Euler(0f, 0f, 90f), m.tire);
            Cyl(t, "Rim", Vector3.zero, new Vector3(d.rimFlangeDiameter, width * 0.5f + 0.004f, d.rimFlangeDiameter), Quaternion.Euler(0f, 0f, 90f), m.rim);
            if (outerSide != 0)
            {
                // Rotation markers on the outer face (a cross on the rim + one tread block).
                float x = outerSide * (width * 0.5f + 0.008f);
                Box(t, "MarkerA", new Vector3(x, 0f, 0f), new Vector3(0.01f, d.rimFlangeDiameter * 0.9f, 0.07f), m.marker);
                Box(t, "MarkerB", new Vector3(x, 0f, 0f), new Vector3(0.01f, 0.07f, d.rimFlangeDiameter * 0.9f), m.dark);
                Box(t, "TreadMark", new Vector3(0f, r - 0.01f, 0f), new Vector3(width * 0.9f, 0.04f, 0.10f), m.marker);
            }
        }

        // ------------------------------------------------------------------ helpers

        static Transform Child(Transform parent, string name, Vector3 localPos)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            return go.transform;
        }

        static void BoxCol(Transform parent, string name, Vector3 center, Vector3 size)
        {
            var t = Child(parent, name, center);
            t.gameObject.AddComponent<BoxCollider>().size = size;
        }

        static Transform Box(Transform parent, string name, Vector3 localPos, Vector3 size, Material mat) =>
            MeshObj(parent, name, localPos, size, Quaternion.identity, mat, CubeMesh);

        static Transform Cyl(Transform parent, string name, Vector3 localPos, Vector3 scale, Quaternion rot, Material mat) =>
            MeshObj(parent, name, localPos, scale, rot, mat, CylinderMesh);

        static Transform MeshObj(Transform parent, string name, Vector3 localPos, Vector3 scale, Quaternion rot, Material mat, Mesh mesh)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            go.transform.localRotation = rot;
            go.transform.localScale = scale;
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = mat;
            return go.transform;
        }

        static Mesh CubeMesh => s_Cube != null ? s_Cube : (s_Cube = PrimitiveMesh(PrimitiveType.Cube));
        static Mesh CylinderMesh => s_Cylinder != null ? s_Cylinder : (s_Cylinder = PrimitiveMesh(PrimitiveType.Cylinder));

        static Mesh PrimitiveMesh(PrimitiveType t)
        {
            var tmp = GameObject.CreatePrimitive(t);
            var mesh = tmp.GetComponent<MeshFilter>().sharedMesh;
            UnityEngine.Object.DestroyImmediate(tmp);
            return mesh;
        }

        static void SetLayerRecursive(GameObject go, int layer)
        {
            go.layer = layer;
            foreach (Transform c in go.transform) SetLayerRecursive(c.gameObject, layer);
        }
    }
}
