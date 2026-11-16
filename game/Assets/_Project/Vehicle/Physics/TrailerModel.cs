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
            foreach (var w in Wheels) { w.Omega = speed / w.RollingRadius; w.OmegaPrevStep = w.Omega; }
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
            RelaxStickAtStandstill(dt, chassis);
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
        /// Only the trailer wheels relax (the tractor wheels and brakes keep holding the combination); the braked ones relax to
        /// the tractor's common-mode deflection (ADR 0280 section 10), so only the preload between the bodies goes and the
        /// grade force stays shared by stiffness: no load moves onto the tractor, no settling, no creep. Set to 0 to disable.
        /// </summary>
        public double StandstillRelaxTau = 2.0;
        public const double RelaxMaxSpeed = 0.05;
        /// <summary>Driveline torque on a towing wheel [N m] above which it counts as driven (ADR 0280 section 10 addendum D42).</summary>
        public const double DrivenTorqueEpsilon = 1.0;
        /// <summary>Set by <see cref="CombinationModel"/>: the kingpin is in the jaw, so the tractor can take the load the relaxed trailer wheels give up.</summary>
        public bool Coupled;
        /// <summary>
        /// Set by <see cref="CombinationModel"/> while coupled: the towing vehicle's wheels. Their contact-patch deflection is the
        /// reference the braked trailer wheels relax to (ADR 0280 section 10). Null = no towing vehicle (own-share fallback).
        /// </summary>
        public WheelState[] TowingWheels;

        void RelaxStickAtStandstill(double dt, in ChassisState chassis)
        {
            if (StandstillRelaxTau <= 0 || !Coupled || Math.Abs(SpeedForward) > RelaxMaxSpeed) return;
            double k = Math.Exp(-dt / StandstillRelaxTau);
            // What relaxes is the internal preload between the two bodies, not the grade load. With the kingpin in the jaw both
            // bodies stand still together, so a combination without internal preload has the same longitudinal contact-patch
            // deflection on every braked wheel (tractor and trailer alike: each holds k_x u of the grade force, the elastic
            // split of a load shared by parallel springs that move together). A slow pitch change (nose load moving from the legs
            // to the plate, air suspension re-levelling) shows up as a deflection *difference* between the trailer and the
            // tractor; carcass hysteresis and trailing-arm bushes bleed that difference off, so the braked trailer wheels relax to
            // the common-mode deflection of the tractor's braked wheels (capped by their brake). Unbraked trailer wheels relax to 0.
            // ADR 0280 section 10 (2026-11-16): the former target, each braked trailer wheel keeping only its "own share"
            // Fz tan(theta), also bled off the trailer's elastic share of the grade force above that, i.e. moved ~5 kN of the
            // empty trailer's grade force onto the kingpin over ~60 s on 12 % (trailer settling 5.0 mm through the tractor's
            // tire and bellows compliance after the combination had already come to rest). It stays the fallback when the
            // towing vehicle has no braked wheel in contact (then the tractor rolls and only the trailer brakes hold).
            // The reference is the stiffness-weighted mean (net braked-wheel force of the tractor / their stiffness): a preload
            // between the tractor's own axles (front pushing, rear pulling after a reverse-and-brake) cancels out of it.
            // ADR 0280 section 10 addendum (D42, 2026-11-16): a towing wheel that carries driveline torque is not a reaction to
            // a load shared with the trailer, it is the action (engine pushing against the brakes, e.g. full throttle with the
            // parking brake on and the interlock off). Its deflection points the other way from what the braked trailer wheels
            // hold, and relaxing towards it (or towards the own share, 0 on the flat) bled the trailer's reaction off at
            // (u_trailer - u_ref) / tau ~ 4 mm/s without end: park_brake_hold_no_interlock_comb crept 55 mm in 11 s and
            // 251 mm in 60 s. While the driveline pushes, the braked trailer wheels hold their deflection (only the elastic
            // wind-up remains, which stops); the driven wheels never enter the reference.
            bool towingDriven = false;
            double sumKu = 0, sumK = 0; int nRef = 0;
            if (TowingWheels != null)
                for (int i = 0; i < TowingWheels.Length; i++)
                {
                    var tw = TowingWheels[i];
                    if (tw.Contact && Math.Abs(tw.DriveTorque) > DrivenTorqueEpsilon) { towingDriven = true; continue; }
                    if (!tw.Contact || tw.BrakeTorque <= 0 || tw.Fz <= 0) continue;
                    double kt = tw.Tire.LongitudinalDeflectionStiffness(tw.Fz, tw.TireCount);
                    sumKu += kt * tw.Ux; sumK += kt; nRef++;
                }
            double uRef = nRef > 0 && sumK > 0 ? sumKu / sumK : 0;
            if (sumK <= 0) nRef = 0;
            double gs = MathUtil.Clamp((chassis.Rotation * Vec3.Forward).y, -0.5, 0.5);
            double tanTheta = gs / Math.Sqrt(1 - gs * gs);
            for (int i = 0; i < Wheels.Length; i++)
            {
                var w = Wheels[i];
                double target = 0;
                if (w.Contact && w.BrakeTorque > 0 && w.Fz > 0)
                {
                    if (towingDriven) continue;
                    double cap = w.BrakeTorque / w.RollingRadius;
                    double kx = w.Tire.LongitudinalDeflectionStiffness(w.Fz, w.TireCount);
                    if (kx > 0)
                    {
                        double f = nRef > 0 ? kx * uRef : w.Fz * tanTheta;
                        target = MathUtil.Clamp(f, -cap, cap) / kx;
                    }
                }
                w.Ux = target + (w.Ux - target) * k;
            }
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
