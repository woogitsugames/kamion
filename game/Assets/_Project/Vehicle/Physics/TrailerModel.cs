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
        /// <summary>Current load case; replaced in place by <see cref="SetCargo"/>.</summary>
        public CargoDefinition Cargo { get; private set; }
        public readonly SolverSettings Settings;
        /// <summary>Mass, CoM and inertia including the cargo. Changes with <see cref="SetCargo"/>: the host must copy it into its rigid body again.</summary>
        public MassProperties MassProps { get; private set; }
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

        readonly MassElement[] _massAll;
        readonly double[] _loadBuf;
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
            Settings = settings ?? new SolverSettings();
            EmptyMassProps = MassProperties.Compute(def.massElements);
            _massAll = new MassElement[def.massElements.Length + 1];
            Array.Copy(def.massElements, _massAll, def.massElements.Length);
            _loadBuf = new double[def.axles.Length];
            ApplyCargo(cargo ?? new CargoDefinition());

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
            var r = new double[Def.axles.Length];
            FillAxleLoads(mp, onKingpin, r);
            return r;
        }

        void FillAxleLoads(in MassProperties mp, bool onKingpin, double[] r)
        {
            double w = mp.Mass * 9.81;
            double zs = onKingpin ? 0 : Def.landingGear.positionZ;
            double nose = w * (mp.CenterOfMass.z - _axleMeanZ) / (zs - _axleMeanZ);
            double each = (w - nose) / Def.axles.Length; // interconnected bellows: equal axle loads
            for (int i = 0; i < r.Length; i++) r[i] = each;
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
            FillAxleLoads(MassProps, onKingpin, _loadBuf);
            Group.SetStaticLoads(_loadBuf, MassProps.CenterOfMass.x, true);
        }

        void ApplyCargo(CargoDefinition cargo)
        {
            Cargo = cargo;
            if (cargo.massKg > 0)
            {
                _massAll[_massAll.Length - 1] = cargo.ToMassElement(Def.cargoBay);
                MassProps = MassProperties.Compute(_massAll);
            }
            else MassProps = EmptyMassProps;
        }

        /// <summary>
        /// R7: swaps the load case in place (no new model, no new wheel group): recomputes mass / CoM / inertia, the static
        /// axle loads and the air suspension pre-levelling for the given support (kingpin or legs). Call between steps; it does not
        /// touch the per-step state and keeps the model's arrays (the cargo element itself may allocate). The host must copy
        /// <see cref="MassProps"/> into its rigid body and, when coupled, use <see cref="CombinationModel.SetCargo"/> so the
        /// tractor's kingpin load follows too.
        /// </summary>
        public void SetCargo(CargoDefinition cargo, bool onKingpin)
        {
            ApplyCargo(cargo ?? new CargoDefinition());
            SetStatic(onKingpin);
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
            RelaxStickAtStandstill(dt);
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

        /// <summary>
        /// R6: time constant [s] of the longitudinal stress relaxation of the trailer tire stick springs while the
        /// coupled combination stands still (|v| below <see cref="RelaxMaxSpeed"/>). WORKING_VALUE. Cause of the old
        /// 0.67-0.9x kingpin load: with locked trailer wheels every slow pitch change of the combination (nose load
        /// moving from the legs to the plate, the tractor's air suspension re-levelling) is a ~1 cm geometry mismatch
        /// that the stick springs store as ~50-110 kN of longitudinal preload; it acts at the plate height and shifts
        /// the kingpin load by Fx h / wheelbase. Real tire carcass hysteresis and trailing-arm bushes bleed that off.
        /// Only the trailer wheels relax (the tractor wheels and brakes keep holding the combination), so on a slope the
        /// trailer settles by about F / k_tractor and then stops: no creep. Set to 0 to disable.
        /// </summary>
        public double StandstillRelaxTau = 2.0;
        public const double RelaxMaxSpeed = 0.05;
        /// <summary>Set by <see cref="CombinationModel"/>: the kingpin is in the jaw, so the tractor can take the load the relaxed trailer wheels give up.</summary>
        public bool Coupled;

        void RelaxStickAtStandstill(double dt)
        {
            if (StandstillRelaxTau <= 0 || !Coupled || Math.Abs(SpeedForward) > RelaxMaxSpeed) return;
            double k = Math.Exp(-dt / StandstillRelaxTau);
            for (int i = 0; i < Wheels.Length; i++) Wheels[i].Ux *= k;
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
