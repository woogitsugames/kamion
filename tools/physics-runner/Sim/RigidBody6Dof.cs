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
            Vec3 wB = Rotation.InverseRotate(AngularVelocity);
            Vec3 tB = Rotation.InverseRotate(torqueAboutCom);
            Vec3 lB = InertiaLocal * wB;
            Vec3 dwB = InvInertiaLocal * (tB - Vec3.Cross(wB, lB));
            wB += dwB * dt;
            AngularVelocity = Rotation * wB;

            // Position: integrate CoM then recover origin (rotation about CoM).
            Vec3 com = CenterOfMassWorld + Velocity * dt;
            Rotation = Rotation.Integrate(AngularVelocity, dt);
            Position = com - Rotation * CenterOfMassLocal;
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
