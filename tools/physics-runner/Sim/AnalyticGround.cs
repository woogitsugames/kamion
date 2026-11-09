using System;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    public struct SurfaceProps
    {
        public double Friction;
        public double RollingResistance;
        public int Id;

        public static SurfaceProps FromName(string name)
        {
            switch ((name ?? "dry_asphalt").ToLowerInvariant())
            {
                case "dry_asphalt": return new SurfaceProps { Friction = 1.0, RollingResistance = 1.0, Id = 0 };
                // WORKING_VALUE: wet asphalt friction ratio (see docs/VEHICLE_REFERENCE_DATA.md)
                case "wet_asphalt": return new SurfaceProps { Friction = 0.625, RollingResistance = 1.05, Id = 1 };
                case "concrete": return new SurfaceProps { Friction = 1.0, RollingResistance = 0.95, Id = 2 };
                default: throw new ArgumentException($"Unknown surface '{name}'");
            }
        }
    }

    /// <summary>Axis-aligned raised slab (curb, step) sitting on the ground.</summary>
    public struct GroundBox
    {
        public Vec3 Min, Max;
        public SurfaceProps Surface;
    }

    /// <summary>
    /// Analytic ground: an infinite plane (optionally inclined along world Z) plus axis-aligned boxes.
    /// Exact ray intersections, no allocations.
    /// </summary>
    public sealed class AnalyticGround : IGroundQuery
    {
        readonly Vec3 _planePoint;
        readonly Vec3 _planeNormal;
        readonly SurfaceProps _surface;
        readonly GroundBox[] _boxes;

        /// <param name="gradePercent">Ground rises towards +Z by this percentage (e.g. 12 = 12%).</param>
        public AnalyticGround(double gradePercent, SurfaceProps surface, GroundBox[] boxes = null)
        {
            double g = gradePercent / 100.0;
            _planePoint = Vec3.Zero;
            _planeNormal = new Vec3(0, 1, -g).Normalized;
            _surface = surface;
            _boxes = boxes ?? Array.Empty<GroundBox>();
        }

        public Vec3 PlaneNormal => _planeNormal;

        public double HeightAt(double x, double z)
        {
            // plane: n.(p - p0) = 0 -> y = -(nx x + nz z)/ny
            double y = -(_planeNormal.x * x + _planeNormal.z * z) / _planeNormal.y;
            foreach (var b in _boxes)
                if (x >= b.Min.x && x <= b.Max.x && z >= b.Min.z && z <= b.Max.z && b.Max.y > y) y = b.Max.y;
            return y;
        }

        public bool Raycast(Vec3 origin, Vec3 dir, double maxDistance, out GroundHit hit)
        {
            hit = default;
            bool found = false;
            double best = maxDistance;

            double denom = Vec3.Dot(dir, _planeNormal);
            if (denom < -1e-9)
            {
                double t = Vec3.Dot(_planePoint - origin, _planeNormal) / denom;
                if (t >= 0 && t <= best)
                {
                    best = t; found = true;
                    hit.Point = origin + dir * t; hit.Normal = _planeNormal; hit.Distance = t;
                    hit.FrictionScale = _surface.Friction; hit.RollingResistanceScale = _surface.RollingResistance; hit.SurfaceId = _surface.Id;
                }
            }

            for (int i = 0; i < _boxes.Length; i++)
            {
                if (RayBox(origin, dir, _boxes[i], out double t, out Vec3 n) && t <= best)
                {
                    best = t; found = true;
                    hit.Point = origin + dir * t; hit.Normal = n; hit.Distance = t;
                    hit.FrictionScale = _boxes[i].Surface.Friction; hit.RollingResistanceScale = _boxes[i].Surface.RollingResistance; hit.SurfaceId = _boxes[i].Surface.Id;
                }
            }
            return found;
        }

        static bool RayBox(Vec3 o, Vec3 d, GroundBox b, out double tHit, out Vec3 normal)
        {
            tHit = 0; normal = Vec3.Up;
            double tmin = double.NegativeInfinity, tmax = double.PositiveInfinity;
            int axisMin = -1; double signMin = 0;
            for (int a = 0; a < 3; a++)
            {
                double oa = a == 0 ? o.x : (a == 1 ? o.y : o.z);
                double da = a == 0 ? d.x : (a == 1 ? d.y : d.z);
                double mn = a == 0 ? b.Min.x : (a == 1 ? b.Min.y : b.Min.z);
                double mx = a == 0 ? b.Max.x : (a == 1 ? b.Max.y : b.Max.z);
                if (Math.Abs(da) < 1e-12)
                {
                    if (oa < mn || oa > mx) return false;
                    continue;
                }
                double t1 = (mn - oa) / da, t2 = (mx - oa) / da;
                double s = -1; // entering through min face -> normal points -axis
                if (t1 > t2) { double tmp = t1; t1 = t2; t2 = tmp; s = 1; }
                if (t1 > tmin) { tmin = t1; axisMin = a; signMin = s; }
                if (t2 < tmax) tmax = t2;
                if (tmin > tmax) return false;
            }
            if (tmax < 0 || tmin < 0 || axisMin < 0) return false; // origin inside box or behind
            tHit = tmin;
            normal = axisMin == 0 ? new Vec3(signMin, 0, 0) : (axisMin == 1 ? new Vec3(0, signMin, 0) : new Vec3(0, 0, signMin));
            return true;
        }
    }
}
