using System;
using Game.Vehicle.Physics;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Static-equilibrium poses for the semi-trailer, ported from the .NET runner (ScenarioRunner.Setup), so a spawn
    /// starts without a suspension or landing-gear transient. Call after the <see cref="CombinationModel"/> exists:
    /// the static axle offsets depend on its pre-levelling (coupled vs on the legs). The ground is assumed to be a
    /// plane through the given ground point with the given normal (spawn spots are flat).
    /// </summary>
    public static class CombinationPlacement
    {
        /// <summary>
        /// Tractor at static equilibrium for its current static loads (solo, or with the kingpin load after
        /// <see cref="VehicleBody.ConnectTrailer"/>): both axles' static contact points on the plane through
        /// <paramref name="groundPoint"/> (normal = rotation up), origin above the ground point (runner PlaceTwoPoint).
        /// </summary>
        public static void Tractor(VehicleModel tractor, Vector3 groundPoint, Quaternion rotation, out Vector3 position, out Quaternion rot)
        {
            var g = tractor.Group;
            var a = new Vector3(0f, (float)g.StaticGroundOffset(1), (float)tractor.Def.axles[1].positionZ);
            var b = new Vector3(0f, (float)g.StaticGroundOffset(0), (float)tractor.Def.axles[0].positionZ);
            PlaceTwoPoint(rotation, groundPoint, rotation * Vector3.up, a, 0, b, 0, out rot, out position);
        }

        /// <summary>Coupled: kingpin in the tractor's jaw, trailer pitched so its axle group sits on the ground plane.</summary>
        public static void Coupled(VehicleModel tractor, Vector3 tractorPos, Quaternion tractorRot, TrailerModel trailer,
            float articulationDeg, out Vector3 position, out Quaternion rotation)
        {
            Vector3 n = tractorRot * Vector3.up;
            Vector3 k = tractorPos + tractorRot * tractor.Def.fifthWheel.position.ToUnity();
            Vector3 kp = trailer.KingpinLocal.ToUnity();
            AxleGroupContact(trailer, out Vector3 axleContact);
            Quaternion q0 = Quaternion.AngleAxis(articulationDeg, n) * tractorRot;
            Vector3 right = q0 * Vector3.right;
            Func<double, double> f = phi =>
            {
                Quaternion q = Quaternion.AngleAxis((float)(phi * Mathf.Rad2Deg), right) * q0;
                Vector3 pos = k - q * kp;
                return Vector3.Dot(pos + q * axleContact - tractorPos, n);
            };
            double phiT = Bisect(f, -0.3, 0.3);
            rotation = Quaternion.AngleAxis((float)(phiT * Mathf.Rad2Deg), right) * q0;
            position = k - rotation * kp;
        }

        /// <summary>
        /// Parked on the lowered landing gear: the trailer frame origin (below the kingpin) is above
        /// <paramref name="kingpinGround"/>, heading = <paramref name="yaw"/>; axles on the ground, leg feet pressed in
        /// by their static share of the nose load.
        /// </summary>
        public static void Parked(TrailerModel trailer, Vector3 kingpinGround, Quaternion yaw, out Vector3 position, out Quaternion rotation)
        {
            var lg = trailer.Def.landingGear;
            AxleGroupContact(trailer, out Vector3 a);
            var b = new Vector3(0f, (float)lg.loweredFootY, (float)lg.positionZ);
            double pen = trailer.StaticNoseLoad(false) * 0.5 / lg.stiffness;
            PlaceTwoPoint(yaw, kingpinGround, Vector3.up, a, 0, b, -pen, out rotation, out position);
        }

        static void AxleGroupContact(TrailerModel trailer, out Vector3 contact)
        {
            double y = 0, z = 0;
            int n = trailer.Def.axles.Length;
            for (int i = 0; i < n; i++) { y += trailer.Group.StaticGroundOffset(i); z += trailer.Def.axles[i].positionZ; }
            contact = new Vector3(0f, (float)(y / n), (float)(z / n));
        }

        /// <summary>Rotation about the base right axis and offset along n so that two vehicle-frame points sit at the given heights above the plane.</summary>
        static void PlaceTwoPoint(Quaternion qBase, Vector3 basePoint, Vector3 n, Vector3 a, double ha, Vector3 b, double hb, out Quaternion q, out Vector3 pos)
        {
            Vector3 right = qBase * Vector3.right;
            Func<double, double> f = phi =>
            {
                Quaternion qq = Quaternion.AngleAxis((float)(phi * Mathf.Rad2Deg), right) * qBase;
                return Vector3.Dot(qq * b - qq * a, n) - (hb - ha);
            };
            double phiS = Bisect(f, -0.3, 0.3);
            q = Quaternion.AngleAxis((float)(phiS * Mathf.Rad2Deg), right) * qBase;
            // Heights are measured from the plane through basePoint.
            pos = basePoint + n * (float)(ha - Vector3.Dot(q * a, n));
        }

        static double Bisect(Func<double, double> f, double lo, double hi)
        {
            double flo = f(lo), fhi = f(hi);
            if (flo * fhi > 0) return 0;
            for (int i = 0; i < 60; i++)
            {
                double mid = 0.5 * (lo + hi), fm = f(mid);
                if ((fm < 0) == (flo < 0)) { lo = mid; flo = fm; } else hi = mid;
            }
            return 0.5 * (lo + hi);
        }
    }
}
