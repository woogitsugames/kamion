using System;

namespace Game.Vehicle.Physics
{
    /// <summary>Row-major 3x3 matrix (used for inertia tensors).</summary>
    [Serializable]
    public struct Mat3
    {
        public double m00, m01, m02, m10, m11, m12, m20, m21, m22;

        public static Mat3 Diagonal(double a, double b, double c)
        {
            Mat3 m = default;
            m.m00 = a; m.m11 = b; m.m22 = c;
            return m;
        }

        public static Vec3 operator *(Mat3 m, Vec3 v) => new Vec3(
            m.m00 * v.x + m.m01 * v.y + m.m02 * v.z,
            m.m10 * v.x + m.m11 * v.y + m.m12 * v.z,
            m.m20 * v.x + m.m21 * v.y + m.m22 * v.z);

        public static Mat3 operator +(Mat3 a, Mat3 b)
        {
            Mat3 r;
            r.m00 = a.m00 + b.m00; r.m01 = a.m01 + b.m01; r.m02 = a.m02 + b.m02;
            r.m10 = a.m10 + b.m10; r.m11 = a.m11 + b.m11; r.m12 = a.m12 + b.m12;
            r.m20 = a.m20 + b.m20; r.m21 = a.m21 + b.m21; r.m22 = a.m22 + b.m22;
            return r;
        }

        public double Determinant =>
            m00 * (m11 * m22 - m12 * m21) - m01 * (m10 * m22 - m12 * m20) + m02 * (m10 * m21 - m11 * m20);

        public Mat3 Inverse()
        {
            double det = Determinant;
            if (Math.Abs(det) < 1e-18) throw new InvalidOperationException("Singular matrix");
            double inv = 1.0 / det;
            Mat3 r;
            r.m00 = (m11 * m22 - m12 * m21) * inv;
            r.m01 = (m02 * m21 - m01 * m22) * inv;
            r.m02 = (m01 * m12 - m02 * m11) * inv;
            r.m10 = (m12 * m20 - m10 * m22) * inv;
            r.m11 = (m00 * m22 - m02 * m20) * inv;
            r.m12 = (m02 * m10 - m00 * m12) * inv;
            r.m20 = (m10 * m21 - m11 * m20) * inv;
            r.m21 = (m01 * m20 - m00 * m21) * inv;
            r.m22 = (m00 * m11 - m01 * m10) * inv;
            return r;
        }

        /// <summary>Returns R * M * R^T for rotation q (local tensor to world tensor).</summary>
        public static Mat3 Rotate(Mat3 m, Quat q)
        {
            Vec3 c0 = q * new Vec3(1, 0, 0);
            Vec3 c1 = q * new Vec3(0, 1, 0);
            Vec3 c2 = q * new Vec3(0, 0, 1);
            // R columns are c0,c1,c2. Compute A = R*M then A*R^T.
            Mat3 r;
            r.m00 = c0.x; r.m01 = c1.x; r.m02 = c2.x;
            r.m10 = c0.y; r.m11 = c1.y; r.m12 = c2.y;
            r.m20 = c0.z; r.m21 = c1.z; r.m22 = c2.z;
            Mat3 a = Mul(r, m);
            return Mul(a, Transpose(r));
        }

        public static Mat3 Transpose(Mat3 m)
        {
            Mat3 r;
            r.m00 = m.m00; r.m01 = m.m10; r.m02 = m.m20;
            r.m10 = m.m01; r.m11 = m.m11; r.m12 = m.m21;
            r.m20 = m.m02; r.m21 = m.m12; r.m22 = m.m22;
            return r;
        }

        public static Mat3 Mul(Mat3 a, Mat3 b)
        {
            Mat3 r;
            r.m00 = a.m00 * b.m00 + a.m01 * b.m10 + a.m02 * b.m20;
            r.m01 = a.m00 * b.m01 + a.m01 * b.m11 + a.m02 * b.m21;
            r.m02 = a.m00 * b.m02 + a.m01 * b.m12 + a.m02 * b.m22;
            r.m10 = a.m10 * b.m00 + a.m11 * b.m10 + a.m12 * b.m20;
            r.m11 = a.m10 * b.m01 + a.m11 * b.m11 + a.m12 * b.m21;
            r.m12 = a.m10 * b.m02 + a.m11 * b.m12 + a.m12 * b.m22;
            r.m20 = a.m20 * b.m00 + a.m21 * b.m10 + a.m22 * b.m20;
            r.m21 = a.m20 * b.m01 + a.m21 * b.m11 + a.m22 * b.m21;
            r.m22 = a.m20 * b.m02 + a.m21 * b.m12 + a.m22 * b.m22;
            return r;
        }
    }
}
