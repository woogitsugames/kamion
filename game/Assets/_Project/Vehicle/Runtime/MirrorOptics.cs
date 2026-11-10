using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Geometry of a rear-view / convex mirror seen from the design eye point (ADR 0042): the render camera sits at the mirror
    /// image of the eye, looks through the glass centre, and a convex glass of radius R widens each half field by s / R
    /// (s = glass half size). Used by TruckAssetBuilder (camera placement and the glass "adjustment") and by the EditMode
    /// test that checks the UN ECE R46 fields of vision (para 15.2.4) against the art manifest. Frame: any, as long as all
    /// inputs share it (vehicle frame: X right, Y up, Z forward).
    /// </summary>
    public static class MirrorOptics
    {
        public struct View
        {
            public Vector3 position, forward, up, right;
            public float tanHalfH, tanHalfV;
            /// <summary>Eye-image to glass distance (m).</summary>
            public float distance;
            public float HalfHDeg => Mathf.Atan(tanHalfH) * Mathf.Rad2Deg;
            public float HalfVDeg => Mathf.Atan(tanHalfV) * Mathf.Rad2Deg;
        }

        /// <summary>Unit direction from yaw (deg, 0 = straight back -Z, + towards +X) and pitch (deg, + up).</summary>
        public static Vector3 RearDirection(float yawDeg, float pitchDeg)
        {
            float y = yawDeg * Mathf.Deg2Rad, p = pitchDeg * Mathf.Deg2Rad;
            return new Vector3(Mathf.Sin(y) * Mathf.Cos(p), Mathf.Sin(p), -Mathf.Cos(y) * Mathf.Cos(p));
        }

        /// <summary>Glass normal (towards the eye) that reflects the eye ray through the glass centre into <paramref name="direction"/>.</summary>
        public static Vector3 AimNormal(Vector3 eye, Vector3 glassCentre, Vector3 direction)
        {
            Vector3 i = (glassCentre - eye).normalized;
            return (direction.normalized - i).normalized;
        }

        /// <summary>Camera of a mirror (normal towards the eye, glass up axis, glass size, radius of curvature; flat: +inf).</summary>
        public static View Build(Vector3 eye, Vector3 glassCentre, Vector3 normal, Vector3 glassUp, float width, float height, float radius)
        {
            Vector3 n = normal.normalized;
            Vector3 c = eye - 2f * Vector3.Dot(eye - glassCentre, n) * n;
            Vector3 f = glassCentre - c;
            float d = f.magnitude;
            f /= d;
            var rot = Quaternion.LookRotation(f, glassUp);
            float curv = float.IsInfinity(radius) || radius <= 0f ? 0f : 1f / radius;
            float hh = Mathf.Atan(width * 0.5f / d) + width * curv;
            float vh = Mathf.Atan(height * 0.5f / d) + height * curv;
            return new View
            {
                position = c, forward = f, up = rot * Vector3.up, right = rot * Vector3.right,
                tanHalfH = Mathf.Tan(hh), tanHalfV = Mathf.Tan(vh), distance = d,
            };
        }

        public static bool Sees(in View v, Vector3 p)
        {
            Vector3 d = p - v.position;
            float z = Vector3.Dot(d, v.forward);
            if (z <= 1e-4f) return false;
            return Mathf.Abs(Vector3.Dot(d, v.right) / z) <= v.tanHalfH && Mathf.Abs(Vector3.Dot(d, v.up) / z) <= v.tanHalfV;
        }

        /// <summary>Share (0..1) of an n x n grid of road points (y = groundY) in the rectangle [x0,x1] x [z0,z1] inside the view.</summary>
        public static float GroundCoverage(in View v, float x0, float x1, float z0, float z1, float groundY = 0f, int n = 11)
        {
            int ok = 0;
            for (int a = 0; a < n; a++)
            for (int b = 0; b < n; b++)
            {
                float x = Mathf.Lerp(x0, x1, a / (n - 1f)), z = Mathf.Lerp(z0, z1, b / (n - 1f));
                if (Sees(v, new Vector3(x, groundY, z))) ok++;
            }
            return ok / (float)(n * n);
        }
    }
}
