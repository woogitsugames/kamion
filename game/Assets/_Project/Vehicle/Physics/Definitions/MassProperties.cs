using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Mass, centre of mass and inertia tensor computed from lumped box elements (parallel-axis theorem),
    /// not from a collider. In Unity the adapter copies these into Rigidbody.mass / centerOfMass / inertiaTensor.
    /// </summary>
    public struct MassProperties
    {
        public double Mass;
        /// <summary>Centre of mass in vehicle frame [m].</summary>
        public Vec3 CenterOfMass;
        /// <summary>Inertia tensor about the CoM, vehicle axes [kg m^2].</summary>
        public Mat3 Inertia;

        public static MassProperties Compute(MassElement[] elements)
        {
            double m = 0;
            Vec3 c = Vec3.Zero;
            foreach (var e in elements)
            {
                if (e.massKg <= 0) throw new FormatException($"Mass element '{e.name}' must have positive mass");
                m += e.massKg;
                c += e.center * e.massKg;
            }
            c /= m;
            Mat3 inertia = default;
            foreach (var e in elements)
            {
                double mx = e.massKg;
                double sx = e.size.x, sy = e.size.y, sz = e.size.z;
                // Box about its own centre.
                Mat3 box = Mat3.Diagonal(mx * (sy * sy + sz * sz) / 12.0, mx * (sx * sx + sz * sz) / 12.0, mx * (sx * sx + sy * sy) / 12.0);
                // Parallel axis: m (|d|^2 I - d d^T)
                Vec3 d = e.center - c;
                double dd = d.SqrMagnitude;
                Mat3 pa;
                pa.m00 = mx * (dd - d.x * d.x); pa.m01 = -mx * d.x * d.y; pa.m02 = -mx * d.x * d.z;
                pa.m10 = -mx * d.y * d.x; pa.m11 = mx * (dd - d.y * d.y); pa.m12 = -mx * d.y * d.z;
                pa.m20 = -mx * d.z * d.x; pa.m21 = -mx * d.z * d.y; pa.m22 = mx * (dd - d.z * d.z);
                inertia = inertia + box + pa;
            }
            return new MassProperties { Mass = m, CenterOfMass = c, Inertia = inertia };
        }
    }
}
