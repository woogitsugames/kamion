using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Double-precision 3D vector. Same component convention as UnityEngine.Vector3
    /// (X = right/east, Y = up, Z = forward/north). Formulas are handedness-agnostic,
    /// so numbers map 1:1 to Unity's left-handed frame.
    /// </summary>
    [Serializable]
    public struct Vec3
    {
        public double x, y, z;

        public Vec3(double x, double y, double z) { this.x = x; this.y = y; this.z = z; }

        public static readonly Vec3 Zero = new Vec3(0, 0, 0);
        public static readonly Vec3 Up = new Vec3(0, 1, 0);
        public static readonly Vec3 Right = new Vec3(1, 0, 0);
        public static readonly Vec3 Forward = new Vec3(0, 0, 1);

        public static Vec3 operator +(Vec3 a, Vec3 b) => new Vec3(a.x + b.x, a.y + b.y, a.z + b.z);
        public static Vec3 operator -(Vec3 a, Vec3 b) => new Vec3(a.x - b.x, a.y - b.y, a.z - b.z);
        public static Vec3 operator -(Vec3 a) => new Vec3(-a.x, -a.y, -a.z);
        public static Vec3 operator *(Vec3 a, double s) => new Vec3(a.x * s, a.y * s, a.z * s);
        public static Vec3 operator *(double s, Vec3 a) => new Vec3(a.x * s, a.y * s, a.z * s);
        public static Vec3 operator /(Vec3 a, double s) => new Vec3(a.x / s, a.y / s, a.z / s);

        public static double Dot(Vec3 a, Vec3 b) => a.x * b.x + a.y * b.y + a.z * b.z;

        public static Vec3 Cross(Vec3 a, Vec3 b) =>
            new Vec3(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x);

        public double SqrMagnitude => x * x + y * y + z * z;
        public double Magnitude => Math.Sqrt(x * x + y * y + z * z);

        public Vec3 Normalized
        {
            get
            {
                double m = Magnitude;
                return m > 1e-12 ? this / m : Zero;
            }
        }

        /// <summary>Removes the component along unit vector n.</summary>
        public static Vec3 ProjectOnPlane(Vec3 v, Vec3 n) => v - n * Dot(v, n);

        public override string ToString() => $"({x:F4}, {y:F4}, {z:F4})";
    }
}
