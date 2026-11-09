using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Double-precision unit quaternion with UnityEngine.Quaternion component layout (x, y, z, w)
    /// and the same multiplication / vector rotation formulas.
    /// </summary>
    [Serializable]
    public struct Quat
    {
        public double x, y, z, w;

        public Quat(double x, double y, double z, double w) { this.x = x; this.y = y; this.z = z; this.w = w; }

        public static readonly Quat Identity = new Quat(0, 0, 0, 1);

        public static Quat AngleAxis(double radians, Vec3 axis)
        {
            Vec3 n = axis.Normalized;
            double h = 0.5 * radians;
            double s = Math.Sin(h);
            return new Quat(n.x * s, n.y * s, n.z * s, Math.Cos(h));
        }

        public static Quat operator *(Quat a, Quat b) => new Quat(
            a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
            a.w * b.y + a.y * b.w + a.z * b.x - a.x * b.z,
            a.w * b.z + a.z * b.w + a.x * b.y - a.y * b.x,
            a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z);

        public static Vec3 operator *(Quat q, Vec3 v)
        {
            // v' = v + 2w(u x v) + 2 u x (u x v)
            Vec3 u = new Vec3(q.x, q.y, q.z);
            Vec3 t = Vec3.Cross(u, v) * 2.0;
            return v + t * q.w + Vec3.Cross(u, t);
        }

        public Quat Conjugate => new Quat(-x, -y, -z, w);

        public Quat Normalized
        {
            get
            {
                double m = Math.Sqrt(x * x + y * y + z * z + w * w);
                return m > 1e-15 ? new Quat(x / m, y / m, z / m, w / m) : Identity;
            }
        }

        /// <summary>Rotates a world-space vector into the local frame.</summary>
        public Vec3 InverseRotate(Vec3 v) => Conjugate * v;

        /// <summary>First-order integration of a world-space angular velocity over dt.</summary>
        public Quat Integrate(Vec3 omegaWorld, double dt)
        {
            Quat o = new Quat(omegaWorld.x, omegaWorld.y, omegaWorld.z, 0);
            Quat d = o * this;
            double h = 0.5 * dt;
            return new Quat(x + d.x * h, y + d.y * h, z + d.z * h, w + d.w * h).Normalized;
        }
    }
}
