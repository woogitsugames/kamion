using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    /// <summary>
    /// Minimal 6-DOF rigid body (semi-implicit Euler, world-frame angular velocity, gyroscopic term).
    /// Stands in for PhysX Rigidbody in the .NET runner. Gravity is applied here, like Unity does.
    /// </summary>
    public sealed class RigidBody6Dof
    {
        public double Mass;
        public Mat3 InertiaLocal;      // about CoM, body axes
        public Mat3 InvInertiaLocal;
        public Vec3 CenterOfMassLocal; // in vehicle frame
        public Vec3 Position;          // vehicle-frame origin, world
        public Quat Rotation = Quat.Identity;
        public Vec3 Velocity;          // CoM velocity
        public Vec3 AngularVelocity;   // world
        public Vec3 Gravity = new Vec3(0, -9.81, 0);

        public RigidBody6Dof(MassProperties mp)
        {
            Mass = mp.Mass;
            InertiaLocal = mp.Inertia;
            InvInertiaLocal = mp.Inertia.Inverse();
            CenterOfMassLocal = mp.CenterOfMass;
        }

        public Vec3 CenterOfMassWorld => Position + Rotation * CenterOfMassLocal;

        public ChassisState State => new ChassisState
        {
            Position = Position,
            Rotation = Rotation,
            CenterOfMassWorld = CenterOfMassWorld,
            LinearVelocity = Velocity,
            AngularVelocity = AngularVelocity,
        };

        public void Integrate(double dt, Vec3 force, Vec3 torqueAboutCom)
        {
            // Linear
            Velocity += (force / Mass + Gravity) * dt;
            // Angular (body frame for inertia)
            AngularVelocity = PredictAngularVelocity(torqueAboutCom, dt);

            // Position: integrate CoM then recover origin (rotation about CoM).
            Vec3 com = CenterOfMassWorld + Velocity * dt;
            Rotation = Rotation.Integrate(AngularVelocity, dt);
            Position = com - Rotation * CenterOfMassLocal;
        }

        /// <summary>
        /// World angular velocity at the end of a step under <paramref name="torqueAboutCom"/> (what <see cref="Integrate"/>
        /// sets). The torque enters linearly after the gyroscopic update, so an extra contact torque T adds exactly
        /// I_world^-1 T dt (used by <see cref="BodyGroundContact"/>).
        /// </summary>
        public Vec3 PredictAngularVelocity(Vec3 torqueAboutCom, double dt)
        {
            Vec3 wB = Rotation.InverseRotate(AngularVelocity);
            Vec3 tB = Rotation.InverseRotate(torqueAboutCom);
            if (ImplicitGyroscopic) wB = GyroscopicImplicit(wB, dt);
            else wB -= (InvInertiaLocal * Vec3.Cross(wB, InertiaLocal * wB)) * dt;
            wB += (InvInertiaLocal * tB) * dt;
            return Rotation * wB;
        }

        /// <summary>
        /// ADR 0158: the gyroscopic term w x (I w) integrated explicitly gains energy on a tumbling body (a lone trailer
        /// body spinning torque-free at |w| 2.5 rad/s: +136 % KE in 30 s at dt 10 ms). true = one Newton step of the
        /// implicit (backward Euler) gyroscopic update, body frame: solve I (w - w0) + dt w x (I w) = 0 with
        /// J = I + dt (skew(w0) I - skew(I w0)) (E. Catto, "Numerical Methods", GDC 2015; Bullet
        /// computeGyroscopicImpulseImplicit_Body). It never adds energy. false = the old explicit update (tests only).
        /// </summary>
        public bool ImplicitGyroscopic = true;

        Vec3 GyroscopicImplicit(Vec3 w0, double dt)
        {
            Mat3 I = InertiaLocal;
            Vec3 Iw = I * w0;
            Vec3 f = Vec3.Cross(w0, Iw) * dt;
            Mat3 J = I + Scale(Mat3.Mul(Skew(w0), I) + Scale(Skew(Iw), -1), dt);
            return w0 - J.Inverse() * f;
        }

        static Mat3 Skew(Vec3 v)
        {
            Mat3 m = default;
            m.m01 = -v.z; m.m02 = v.y;
            m.m10 = v.z; m.m12 = -v.x;
            m.m20 = -v.y; m.m21 = v.x;
            return m;
        }

        static Mat3 Scale(Mat3 m, double s)
        {
            m.m00 *= s; m.m01 *= s; m.m02 *= s;
            m.m10 *= s; m.m11 *= s; m.m12 *= s;
            m.m20 *= s; m.m21 *= s; m.m22 *= s;
            return m;
        }

        public double KineticEnergy
        {
            get
            {
                Vec3 wB = Rotation.InverseRotate(AngularVelocity);
                return 0.5 * Mass * Velocity.SqrMagnitude + 0.5 * Vec3.Dot(wB, InertiaLocal * wB);
            }
        }
    }
}
