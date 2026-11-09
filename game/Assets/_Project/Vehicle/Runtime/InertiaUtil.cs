using System;
using Game.Vehicle.Physics;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Diagonalises the symmetric inertia tensor from <see cref="MassProperties"/> into the form PhysX wants:
    /// principal moments (<see cref="Rigidbody.inertiaTensor"/>) and the rotation of the principal axes
    /// relative to the body (<see cref="Rigidbody.inertiaTensorRotation"/>), so that I = R diag(λ) Rᵀ.
    /// Cyclic Jacobi, double precision. Called once per vehicle at initialisation.
    /// </summary>
    public static class InertiaUtil
    {
        public static void Diagonalize(Mat3 m, out Vector3 principalMoments, out Quaternion rotation)
        {
            var a = new double[3, 3]
            {
                { m.m00, 0.5 * (m.m01 + m.m10), 0.5 * (m.m02 + m.m20) },
                { 0.5 * (m.m01 + m.m10), m.m11, 0.5 * (m.m12 + m.m21) },
                { 0.5 * (m.m02 + m.m20), 0.5 * (m.m12 + m.m21), m.m22 },
            };
            var v = new double[3, 3] { { 1, 0, 0 }, { 0, 1, 0 }, { 0, 0, 1 } };
            double scale = Math.Abs(a[0, 0]) + Math.Abs(a[1, 1]) + Math.Abs(a[2, 2]);
            for (int sweep = 0; sweep < 64; sweep++)
            {
                double off = Math.Abs(a[0, 1]) + Math.Abs(a[0, 2]) + Math.Abs(a[1, 2]);
                if (off <= 1e-15 * scale) break;
                for (int p = 0; p < 2; p++)
                for (int q = p + 1; q < 3; q++)
                {
                    double apq = a[p, q];
                    if (Math.Abs(apq) <= 1e-18 * scale) continue;
                    double theta = (a[q, q] - a[p, p]) / (2 * apq);
                    double t = Math.Sign(theta) / (Math.Abs(theta) + Math.Sqrt(theta * theta + 1));
                    if (theta == 0) t = 1;
                    double c = 1 / Math.Sqrt(t * t + 1), s = t * c;
                    for (int k = 0; k < 3; k++)
                    {
                        double akp = a[k, p], akq = a[k, q];
                        a[k, p] = c * akp - s * akq;
                        a[k, q] = s * akp + c * akq;
                    }
                    for (int k = 0; k < 3; k++)
                    {
                        double apk = a[p, k], aqk = a[q, k];
                        a[p, k] = c * apk - s * aqk;
                        a[q, k] = s * apk + c * aqk;
                    }
                    for (int k = 0; k < 3; k++)
                    {
                        double vkp = v[k, p], vkq = v[k, q];
                        v[k, p] = c * vkp - s * vkq;
                        v[k, q] = s * vkp + c * vkq;
                    }
                }
            }
            principalMoments = new Vector3((float)a[0, 0], (float)a[1, 1], (float)a[2, 2]);
            var e0 = new Vector3((float)v[0, 0], (float)v[1, 0], (float)v[2, 0]);
            var e1 = new Vector3((float)v[0, 1], (float)v[1, 1], (float)v[2, 1]);
            var e2 = new Vector3((float)v[0, 2], (float)v[1, 2], (float)v[2, 2]);
            // Proper rotation (det +1): LookRotation(e2, e1) maps X to Cross(e1, e2), which must equal e0.
            if (Vector3.Dot(e0, Vector3.Cross(e1, e2)) < 0) e0 = -e0;
            rotation = Quaternion.LookRotation(e2, e1);
        }
    }
}
