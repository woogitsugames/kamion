using System;
using System.Collections.Generic;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Semi-trailer solver: own rigid body (mass properties include the cargo), axles with air suspension,
    /// tires, pneumatic brakes with emergency function, EBS load sensing and ABS, landing gear legs.
    /// Like <see cref="VehicleModel"/> it only produces forces; the host integrates the body and the
    /// <see cref="CombinationModel"/> adds the fifth-wheel constraint. No allocations after construction.
    /// </summary>
    public sealed class TrailerModel
    {
        public readonly TrailerDefinition Def;
        public readonly CargoDefinition Cargo;
        public readonly SolverSettings Settings;
        public readonly MassProperties MassProps;
        public readonly MassProperties EmptyMassProps;
        public readonly WheelGroup Group;
        public readonly WheelState[] Wheels;
        public readonly TrailerBrakeSystem Brakes;

        public readonly AppliedForce[] Forces;
        public int ForceCount { get; private set; }
        public Vec3 TotalForce { get; private set; }
        public Vec3 TotalTorque { get; private set; }

        public double Time { get; private set; }
        public double SpeedForward { get; private set; }
        public double YawRate { get; private set; }
        public Vec3 LocalAcceleration { get; private set; }

        /// <summary>Landing gear command (true = lowered) and current foot height in the trailer frame [m].</summary>
        public bool LandingGearDown;
        public double LandingGearFootY;
        public double LandingGearLoad { get; private set; }
        public bool AeroEnabled = true;

        readonly double _axleMeanZ;
        readonly Vec3[] _legAnchor = new Vec3[2];
        readonly bool[] _legStick = new bool[2];
        readonly double[] _legPenPrev = new double[2];
        Vec3 _prevVelocityLocal;
        bool _hasPrev;

        public TrailerModel(TrailerDefinition def, IDictionary<string, TireDefinition> tires, CargoDefinition cargo = null, SolverSettings settings = null)
        {
            def.Validate();
            Def = def;
            Cargo = cargo ?? new CargoDefinition();
            Settings = settings ?? new SolverSettings();
            EmptyMassProps = MassProperties.Compute(def.massElements);
            if (Cargo.massKg > 0)
            {
                var all = new MassElement[def.massElements.Length + 1];
                Array.Copy(def.massElements, all, def.massElements.Length);
                all[all.Length - 1] = Cargo.ToMassElement(def.cargoBay);
                MassProps = MassProperties.Compute(all);
            }
            else MassProps = EmptyMassProps;

            double z = 0;
            foreach (var a in def.axles) z += a.positionZ;
            _axleMeanZ = z / def.axles.Length;

            // Design ride height = empty trailer on its kingpin.
            Group = new WheelGroup(def.axles, tires, Settings, AxleLoads(EmptyMassProps, 0, true), EmptyMassProps.CenterOfMass.x, 0, "T_");
            Wheels = Group.Wheels;
            Brakes = new TrailerBrakeSystem(def.brakes);
            Forces = new AppliedForce[Wheels.Length + 3];
            LandingGearFootY = def.landingGear.raisedFootY;
            SetStatic(true);
        }

        public Vec3 KingpinLocal => new Vec3(0, Def.kingpinHeight, 0);
        public double Mass => MassProps.Mass;

        /// <summary>Static per-axle loads with the nose on the kingpin (supportZ = 0) or on the landing gear.</summary>
        double[] AxleLoads(in MassProperties mp, double unused, bool onKingpin)
        {
            double w = mp.Mass * 9.81;
            double zs = onKingpin ? 0 : Def.landingGear.positionZ;
            double nose = w * (mp.CenterOfMass.z - _axleMeanZ) / (zs - _axleMeanZ);
            double each = (w - nose) / Def.axles.Length; // interconnected bellows: equal axle loads
            var r = new double[Def.axles.Length];
            for (int i = 0; i < r.Length; i++) r[i] = each;
            return r;
        }

        /// <summary>Static nose load [N] on the kingpin (coupled) or on the landing gear.</summary>
        public double StaticNoseLoad(bool onKingpin)
        {
            double w = MassProps.Mass * 9.81;
            double zs = onKingpin ? 0 : Def.landingGear.positionZ;
            return w * (MassProps.CenterOfMass.z - _axleMeanZ) / (zs - _axleMeanZ);
        }

        /// <summary>Pre-levels the air suspension to the static loads of the current support (kingpin or legs).</summary>
        public void SetStatic(bool onKingpin)
        {
            Group.SetStaticLoads(AxleLoads(MassProps, 0, onKingpin), MassProps.CenterOfMass.x, true);
        }

        public void InitializeMoving(double speed)
        {
            foreach (var w in Wheels) { w.Omega = speed / w.Radius; w.OmegaPrevStep = w.Omega; }
        }

        /// <summary>Puts the landing gear in a state without the crank transient.</summary>
        public void SetLandingGear(bool down)
        {
            LandingGearDown = down;
            LandingGearFootY = down ? Def.landingGear.loweredFootY : Def.landingGear.raisedFootY;
        }

        public void Step(double dt, in ChassisState chassis, double redLine, double controlLine, IGroundQuery ground)
        {
            Time += dt;
            Vec3 up = chassis.Rotation * Vec3.Up;
            Vec3 vLocal = chassis.Rotation.InverseRotate(chassis.LinearVelocity);
            SpeedForward = vLocal.z;
            YawRate = Vec3.Dot(chassis.AngularVelocity, up);
            if (_hasPrev) LocalAcceleration = (vLocal - _prevVelocityLocal) / dt;
            _prevVelocityLocal = vLocal; _hasPrev = true;

            Group.UpdateContacts(dt, chassis, up, ground, null);
            Group.UpdateLevelling(dt);
            Brakes.Update(dt, redLine, controlLine, Group);

            int ns = Settings.substeps;
            double h = dt / ns;
            for (int i = 0; i < Wheels.Length; i++) Wheels[i].RetarderTorque = 0;
            Group.ClearAccumulators();
            Brakes.BeginSubsteps();
            for (int sub = 0; sub < ns; sub++)
            {
                Group.TireAndSpinSubstep(h);
                Brakes.UpdateChambers(h, Group);
                Group.SolveBrakes(h);
                Group.UpdateTreadAccel(h);
            }

            int count = 0;
            Vec3 totalF = Vec3.Zero, totalT = Vec3.Zero;
            Group.AssembleForces(ns, chassis, Forces, ref count, ref totalF, ref totalT);

            // Landing gear legs.
            var lg = Def.landingGear;
            double footTarget = LandingGearDown ? lg.loweredFootY : lg.raisedFootY;
            LandingGearFootY = MathUtil.MoveTowards(LandingGearFootY, footTarget, lg.crankSpeed * dt);
            LandingGearLoad = 0;
            for (int k = 0; k < 2; k++)
            {
                Vec3 footLocal = new Vec3((k == 0 ? -1 : 1) * lg.halfTrack, LandingGearFootY, lg.positionZ);
                LegContact(k, chassis, footLocal, up, ground, dt, ref count, ref totalF, ref totalT);
            }

            // Trailer aerodynamic share (body side, gap and base drag) at the trailer.
            Vec3 v = chassis.LinearVelocity;
            double speed = v.Magnitude;
            if (AeroEnabled && speed > 1e-3 && Def.dragArea > 0)
            {
                Vec3 fa = v * (-0.5 * 1.2 * Def.dragArea * speed);
                Vec3 pa = chassis.LocalToWorld(Def.aeroCenter);
                Forces[count].Force = fa; Forces[count].Point = pa; count++;
                totalF += fa;
                totalT += Vec3.Cross(pa - chassis.CenterOfMassWorld, fa);
            }
            ForceCount = count;
            TotalForce = totalF;
            TotalTorque = totalT;
        }

        void LegContact(int k, in ChassisState c, Vec3 footLocal, Vec3 up, IGroundQuery ground, double dt, ref int count, ref Vec3 totalF, ref Vec3 totalT)
        {
            var lg = Def.landingGear;
            Vec3 foot = c.LocalToWorld(footLocal);
            const double lift = 0.5;
            if (!ground.Raycast(foot + up * lift, -up, lift + 0.3, out GroundHit hit)) { _legStick[k] = false; _legPenPrev[k] = 0; return; }
            double pen = lift - hit.Distance;
            if (pen <= 0) { _legStick[k] = false; _legPenPrev[k] = 0; return; }
            Vec3 n = hit.Normal;
            Vec3 vp = c.PointVelocity(foot);
            double vn = Vec3.Dot(vp, n);
            double fn = Math.Max(0, lg.stiffness * pen - lg.damping * vn);
            _legPenPrev[k] = pen;
            Vec3 contact = foot + n * pen;
            if (!_legStick[k]) { _legAnchor[k] = contact; _legStick[k] = true; }
            Vec3 d = Vec3.ProjectOnPlane(contact - _legAnchor[k], n);
            Vec3 vt = Vec3.ProjectOnPlane(vp, n);
            double ct = 2 * 0.7 * Math.Sqrt(lg.tangentialStiffness * Math.Max(Mass * 0.3, 1000));
            Vec3 ft = d * (-lg.tangentialStiffness) - vt * ct;
            double cap = lg.friction * fn;
            double fm = ft.Magnitude;
            if (fm > cap)
            {
                // Sliding: move the anchor so the spring sits at the friction limit.
                ft = cap > 0 ? ft * (cap / fm) : Vec3.Zero;
                double dm = d.Magnitude;
                if (dm > 1e-9) _legAnchor[k] = contact - d * Math.Min(1.0, cap / (lg.tangentialStiffness * dm));
            }
            Vec3 f = n * fn + ft;
            Forces[count].Force = f; Forces[count].Point = contact; count++;
            totalF += f;
            totalT += Vec3.Cross(contact - c.CenterOfMassWorld, f);
            LandingGearLoad += fn;
        }
    }
}
