using System;
using System.Collections.Generic;

namespace Game.Vehicle.Physics
{
    /// <summary>Solver settings (not vehicle data).</summary>
    [Serializable]
    public class SolverSettings
    {
        /// <summary>Wheel / driveline substeps per fixed step.</summary>
        public int substeps = 4;
        /// <summary>Contact rays per wheel, spread over +/- contactArcDeg in the wheel plane.</summary>
        public int contactRays = 15;
        public double contactArcDeg = 63;
        /// <summary>Projected Gauss-Seidel iterations for clutch + brake constraints.</summary>
        public int constraintIterations = 4;
    }

    /// <summary>
    /// Tractor solver (Stage 2). Pure C#, no UnityEngine.
    ///
    /// Per fixed step: reads a <see cref="ChassisState"/>, queries the ground through <see cref="IGroundQuery"/>,
    /// and produces forces at world points (<see cref="Forces"/>) plus their resultant about the CoM.
    /// It does NOT integrate the chassis and does NOT add gravity: that is the job of the rigid-body host
    /// (PhysX Rigidbody in Unity, RigidBody6Dof in the .NET runner). With a semi-trailer use
    /// <see cref="CombinationModel"/>, which adds the trailer and the fifth-wheel constraint.
    /// Zero allocations after construction.
    /// </summary>
    public sealed class VehicleModel
    {
        public readonly VehicleDefinition Def;
        public readonly SolverSettings Settings;
        public readonly MassProperties MassProps;
        public readonly WheelGroup Group;
        public readonly WheelState[] Wheels;
        public readonly Engine Engine;
        public readonly AmtController Amt;
        public readonly Steering Steering;
        public readonly CabSuspension Cab;
        public readonly AirBrakeSystem Air;
        public readonly Retarder Retarder;

        public readonly AppliedForce[] Forces;
        public int ForceCount { get; private set; }
        public Vec3 TotalForce { get; private set; }
        public Vec3 TotalTorque { get; private set; }
        public Vec3 Gravity = new Vec3(0, -9.81, 0);

        // Coupling state (set by CombinationModel)
        /// <summary>Mass towed through the fifth wheel (trailer incl. cargo) [kg], used by the AMT, hill hold and resistance estimate.</summary>
        public double TowedMass;
        public bool TrailerConnected;
        public double ExtraDragArea;
        /// <summary>Runtime switch for the endurance brakes (engine brake + retarder), e.g. a driver setting or a fault.</summary>
        public bool EnduranceBrakesEnabled = true;

        // Telemetry-friendly state
        public double Time { get; private set; }
        public double SpeedForward { get; private set; }
        public Vec3 LocalAcceleration { get; private set; }
        public double YawRate { get; private set; }
        public double GradeSin { get; private set; }
        public double ThrottleDemand { get; private set; }
        public double EngineTorque { get; private set; }
        public double ClutchTorque { get; private set; }
        /// <summary>Service brake demand 0..1 after blending and hill hold.</summary>
        public double BrakeDemand { get; private set; }
        /// <summary>Endurance brake commands 0..1 (engine brake, retarder) after lever, blending and ABS cut-off.</summary>
        public double EngineBrakeCommand { get; private set; }
        public double RetarderCommand { get; private set; }
        public double ParkingBrakeState { get; private set; }
        public bool HillHoldActive { get; private set; }
        public double AligningTorqueTotal { get; private set; }
        public double ClutchSlipPower { get; private set; }

        readonly int[] _driven;
        readonly double _wheelRadiusRef;
        readonly double _zFront, _zRear;
        double _invDrivenInertiaSum;
        Vec3 _prevVelocityLocal;
        bool _hasPrevVelocity;
        bool _hsaArmed;
        double _hsaTimer;
        double _cruiseIntegral;

        public VehicleModel(VehicleDefinition def, EngineDefinition engine, GearboxDefinition gearbox,
            IDictionary<string, TireDefinition> tires, SolverSettings settings = null)
        {
            def.Validate();
            Def = def;
            Settings = settings ?? new SolverSettings();
            if (Settings.substeps < 1) Settings.substeps = 1;
            if (Settings.contactRays < 1) Settings.contactRays = 1;
            MassProps = MassProperties.Compute(def.massElements);
            Engine = new Engine(engine);
            Amt = new AmtController(gearbox, def.driveline.finalDriveRatio);
            Steering = new Steering(def.steering);
            Cab = new CabSuspension(def.cab);
            Air = new AirBrakeSystem(def.air, def.brakes);
            Retarder = new Retarder(def.retarder);

            double refZ = 0; int nRef = 0;
            foreach (var a in def.axles) if (!a.steered) { refZ += a.positionZ; nRef++; }
            refZ = nRef > 0 ? refZ / nRef : def.axles[def.axles.Length - 1].positionZ;

            _zFront = def.axles[0].positionZ; _zRear = def.axles[1].positionZ;
            Group = new WheelGroup(def.axles, tires, Settings, AxleLoads(0), MassProps.CenterOfMass.x, refZ, "");
            Wheels = Group.Wheels;

            var driven = new List<int>();
            for (int i = 0; i < Wheels.Length; i++) if (Wheels[i].Driven) driven.Add(i);
            _driven = driven.ToArray();
            _invDrivenInertiaSum = 0;
            foreach (int i in _driven) _invDrivenInertiaSum += 1.0 / Wheels[i].Inertia;
            _wheelRadiusRef = Wheels[_driven[0]].Radius;

            Forces = new AppliedForce[Wheels.Length + 1];
            Air.InitSpringChambers(Group, false);
        }

        /// <summary>Static axle loads with an extra vertical load at the fifth wheel [N].</summary>
        public double[] AxleLoads(double kingpinLoad)
        {
            double w = MassProps.Mass * 9.81;
            double zK = Def.fifthWheel.position.z;
            double front = (w * (MassProps.CenterOfMass.z - _zRear) + kingpinLoad * (zK - _zRear)) / (_zFront - _zRear);
            return new[] { front, w + kingpinLoad - front };
        }

        /// <summary>Sets the static configuration (0 = solo). Air springs are pre-levelled to it.</summary>
        public void SetStaticKingpinLoad(double kingpinLoad)
        {
            Group.SetStaticLoads(AxleLoads(kingpinLoad), MassProps.CenterOfMass.x, true);
        }

        public double TotalStaticLoad => Group.TotalStaticLoad;
        public double TotalMass => MassProps.Mass + TowedMass;
        public double WheelRadiusRef => _wheelRadiusRef;

        /// <summary>Spring brakes start in the given state (no initial lag), e.g. a truck parked before the scenario.</summary>
        public void InitParking(bool applied) => Air.InitSpringChambers(Group, applied);

        /// <summary>Initialise wheel speeds and drivetrain for a vehicle already moving at `speed` m/s.</summary>
        public void InitializeMoving(double speed, int gear)
        {
            foreach (var w in Wheels) { w.Omega = speed / w.Radius; w.OmegaPrevStep = w.Omega; w.Ux = 0; w.Uy = 0; }
            if (gear == 0 && speed > 0.5)
            {
                gear = Amt.BestGearForSpeed(speed / _wheelRadiusRef, Amt.Def.downshiftRpmLight + 150);
                if (gear == 0) gear = 1;
            }
            Amt.ForceState(gear, gear != 0);
            if (gear != 0)
            {
                double eo = Math.Abs(Amt.TotalRatio * speed / _wheelRadiusRef);
                Engine.Omega = Math.Max(Engine.IdleOmega, eo);
            }
        }

        /// <summary>Advance the vehicle model by one fixed step.</summary>
        public void Step(double dt, in ChassisState chassis, in DriverInput input, IGroundQuery ground)
        {
            Time += dt;
            Vec3 up = chassis.Rotation * Vec3.Up;
            Vec3 fwdChassis = chassis.Rotation * Vec3.Forward;
            Vec3 vLocal = chassis.Rotation.InverseRotate(chassis.LinearVelocity);
            SpeedForward = vLocal.z;
            YawRate = Vec3.Dot(chassis.AngularVelocity, up);
            GradeSin = fwdChassis.y;
            if (_hasPrevVelocity) LocalAcceleration = (vLocal - _prevVelocityLocal) / dt;
            _prevVelocityLocal = vLocal;
            _hasPrevVelocity = true;

            Steering.Update(input.Steer, dt);

            // ---------------- contacts & suspension ----------------
            Group.UpdateContacts(dt, chassis, up, ground, Steering);
            Group.UpdateLevelling(dt);

            // ---------------- brakes: blending, hill hold, air system, ABS ----------------
            UpdateBrakeDemands(dt, input);
            Air.Update(dt, Engine.Rpm, !Engine.Stalled, BrakeDemand, input.ParkingBrake, TrailerConnected, Group);
            ParkingBrakeState = 0;
            foreach (var w in Wheels) if (w.Axle.parkingBrakeTorque > 0)
                    ParkingBrakeState = Math.Max(ParkingBrakeState, MathUtil.Clamp01((Def.air.springReleaseFullBar - w.SpringChamberPressure) / (Def.air.springReleaseFullBar - Def.air.springReleaseStartBar)));

            // ---------------- AMT ----------------
            double drivelineOmega = 0;
            foreach (int i in _driven) drivelineOmega += Wheels[i].Omega;
            drivelineOmega /= _driven.Length;

            double vKmh = SpeedForward * 3.6;
            double limiter = MathUtil.Clamp01((Def.driveline.speedLimiterKmh - Math.Abs(vKmh)) / Def.driveline.speedLimiterBand);
            UpdateAsr(dt);
            double pedal = Math.Min(MathUtil.Clamp01(input.Throttle), limiter) * AsrFactor;
            DriverInput amtInput = input;
            amtInput.Throttle = pedal;
            Amt.AbsActive = Air.AbsAnyActive;
            Amt.EngineBrakeRequest = EngineBrakeCommand > 0.01;
            double mass = TotalMass;
            double resistance = mass * 9.81 * (GradeSin + 0.0055) + 0.5 * Def.aero.airDensity * DragArea * SpeedForward * Math.Abs(SpeedForward);
            Amt.Update(dt, amtInput, SpeedForward, drivelineOmega, Engine, mass, GradeSin, _wheelRadiusRef, resistance, Def.driveline.finalDriveEfficiency);
            if (Engine.Stalled && Amt.ClutchCommand <= 0.01) Engine.Restart();
            double demand = pedal * Amt.TorqueScale;
            ThrottleDemand = demand;
            Engine.UpdateEngineBrake(demand < 0.02 && Amt.Gear != 0 && Amt.State == AmtState.Drive ? EngineBrakeCommand : 0, dt);

            // Retarder on the gearbox output (works in any gear, also during shifts).
            double fd = Def.driveline.finalDriveRatio;
            Retarder.Update(dt, RetarderCommand, drivelineOmega * fd);
            double retWheel = Retarder.Torque * fd / _driven.Length;
            for (int i = 0; i < Wheels.Length; i++) Wheels[i].RetarderTorque = 0;
            foreach (int i in _driven) Wheels[i].RetarderTorque = retWheel;

            // ---------------- substeps: tires, wheels, engine, clutch, brakes ----------------
            int ns = Settings.substeps;
            double h = dt / ns;
            double ratio = Amt.TotalRatio;
            double eta = Amt.Efficiency * Def.driveline.finalDriveEfficiency;
            double clutchCap = Amt.ClutchCommand * Amt.Def.clutchMaxTorque;
            double invIe = 1.0 / Engine.Inertia;
            double engTorqueAcc = 0, clutchAcc = 0, slipPowerAcc = 0;
            Group.ClearAccumulators();
            Air.BeginSubsteps();
            for (int sub = 0; sub < ns; sub++)
            {
                Group.TireAndSpinSubstep(h);
                Air.UpdateChambers(h, Group);
                double te = Engine.ComputeTorque(demand, Amt.EngineTargetOmega, h);
                Engine.Omega += h * te * invIe;
                engTorqueAcc += te;

                double lamClutch = 0;
                double capC = clutchCap * h;
                bool coupled = ratio != 0 && capC > 0;
                double effC = coupled ? invIe + ratio * ratio * eta / (_driven.Length * (double)_driven.Length) * _invDrivenInertiaSum : 1;
                Group.BeginConstraintSubstep();
                for (int it = 0; it < Settings.constraintIterations; it++)
                {
                    if (coupled)
                    {
                        double avg = 0;
                        foreach (int d in _driven) avg += Wheels[d].Omega;
                        avg /= _driven.Length;
                        double slip = Engine.Omega - ratio * avg;
                        double dl = slip / effC;
                        double newLam = MathUtil.Clamp(lamClutch + dl, -capC, capC);
                        dl = newLam - lamClutch;
                        lamClutch = newLam;
                        Engine.Omega -= dl * invIe;
                        double perWheel = dl * ratio * eta / _driven.Length;
                        foreach (int d in _driven) Wheels[d].Omega += perWheel / Wheels[d].Inertia;
                    }
                    Group.BrakeIteration(h);
                }
                clutchAcc += lamClutch / h;
                if (coupled)
                {
                    double perWheelTorque = lamClutch / h * ratio * eta / _driven.Length;
                    foreach (int d in _driven) Wheels[d].DriveTorque += perWheelTorque;
                    double avg = 0;
                    foreach (int d in _driven) avg += Wheels[d].Omega;
                    avg /= _driven.Length;
                    slipPowerAcc += Math.Abs(lamClutch / h) * Math.Abs(Engine.Omega - ratio * avg);
                }
                Engine.CheckStall();
                Group.UpdateTreadAccel(h);
            }

            EngineTorque = engTorqueAcc / ns;
            ClutchTorque = clutchAcc / ns;
            ClutchSlipPower = slipPowerAcc / ns;
            Amt.UpdateClutchThermal(ClutchSlipPower, dt);

            // ---------------- assemble forces ----------------
            int count = 0;
            Vec3 totalF = Vec3.Zero, totalT = Vec3.Zero;
            Group.AssembleForces(ns, chassis, Forces, ref count, ref totalF, ref totalT);
            double mz = 0;
            foreach (var w in Wheels) if (w.Steered && w.Contact) mz += w.AligningTorque;
            AligningTorqueTotal = mz;

            // Aerodynamic drag (still air).
            Vec3 v = chassis.LinearVelocity;
            double speed = v.Magnitude;
            if (speed > 1e-3)
            {
                Vec3 fa = v * (-0.5 * Def.aero.airDensity * DragArea * speed);
                Vec3 pa = chassis.LocalToWorld(Def.aero.center);
                Forces[count].Force = fa;
                Forces[count].Point = pa;
                count++;
                totalF += fa;
                totalT += Vec3.Cross(pa - chassis.CenterOfMassWorld, fa);
            }
            ForceCount = count;
            TotalForce = totalF;
            TotalTorque = totalT;

            Cab.Update(chassis, Gravity, dt);
        }

        /// <summary>Tractor drag area for the current configuration [m^2] (the trailer's own share is applied on the trailer body).</summary>
        public double DragArea => TrailerConnected && Def.aero.dragAreaWithTrailer > 0 ? Def.aero.dragAreaWithTrailer : Def.aero.dragArea;

        /// <summary>ASR engine intervention factor 0..1 (1 = no intervention).</summary>
        public double AsrFactor { get; private set; } = 1;

        void UpdateAsr(double dt)
        {
            var bd = Def.brakes;
            if (!bd.asrEnabled) { AsrFactor = 1; return; }
            double maxSlip = 0;
            foreach (int i in _driven)
            {
                var w = Wheels[i];
                if (!w.Contact) continue;
                double slip = w.KinematicSlip * Math.Sign(w.Omega);
                if (slip > maxSlip) maxSlip = slip;
            }
            if (maxSlip > bd.asrSlipThreshold) AsrFactor -= bd.asrReduceRate * dt;
            else AsrFactor += bd.asrRecoverRate * dt;
            AsrFactor = MathUtil.Clamp(AsrFactor, 0.2, 1.0);
        }

        void UpdateBrakeDemands(double dt, in DriverInput input)
        {
            var bd = Def.brakes;
            double pedal = MathUtil.Clamp01(input.Brake);

            // Blending: the first part of the pedal travel uses the endurance brakes only.
            double service = pedal, endurancePedal = 0;
            if (bd.brakeBlending && EnduranceBrakesEnabled && (Retarder.Def.present || Engine.HasEngineBrake))
            {
                double bt = MathUtil.Clamp(bd.blendingPedalTravel, 0.01, 0.9);
                service = MathUtil.Clamp01((pedal - bt) / (1 - bt));
                endurancePedal = MathUtil.Clamp01(pedal / bt);
            }

            // Hill start aid: hold pressure after brake release at standstill until drive torque builds up.
            bool stopped = Math.Abs(SpeedForward) < 0.3;
            if (bd.hillStartAid && input.Selector != GearSelector.Neutral)
            {
                if (stopped && pedal > 0.1 && Math.Abs(GradeSin) > 0.02) { _hsaArmed = true; _hsaTimer = 0; }
                if (_hsaArmed && pedal < 0.05)
                {
                    _hsaTimer += dt;
                    double need = TotalMass * 9.81 * Math.Abs(GradeSin) * _wheelRadiusRef;
                    double have = Math.Abs(ClutchTorque * Amt.TotalRatio * Amt.Efficiency * Def.driveline.finalDriveEfficiency);
                    bool release = (have >= need * 1.05 && input.Throttle > 0.02) || _hsaTimer > bd.hillStartMaxHold;
                    if (release) _hsaArmed = false;
                    else service = Math.Max(service, 0.5);
                }
                if (!stopped && _hsaArmed && pedal < 0.05 && _hsaTimer > 0.1 && Math.Abs(SpeedForward) > 1.0) _hsaArmed = false;
            }
            else _hsaArmed = false;
            HillHoldActive = _hsaArmed && pedal < 0.05;
            BrakeDemand = service;

            // Endurance brakes: lever stage 1 = engine brake, 2.. = engine brake + retarder fraction.
            int lever = Math.Max(0, input.RetarderLever);
            int stages = Math.Max(1, Retarder.Def.stages);
            double eb = lever >= 1 ? 1 : 0;
            double ret = lever >= 2 ? Math.Min(1.0, (lever - 1) / (double)stages) : 0;
            if (endurancePedal > 0.02) { eb = 1; ret = Math.Max(ret, endurancePedal); }
            // Brake cruise: continuous PI modulation of the endurance brakes on the speed error (km/h).
            if (input.BrakeCruiseKmh > 0 && input.Throttle < 0.02)
            {
                double e = SpeedForward * 3.6 - input.BrakeCruiseKmh;
                _cruiseIntegral = MathUtil.Clamp(_cruiseIntegral + 0.08 * e * dt, 0, 1.2);
                double u = 0.35 * e + _cruiseIntegral;
                if (u > 0.05) { eb = 1; ret = Math.Max(ret, MathUtil.Clamp01((u - 0.05) / 0.95)); }
            }
            else _cruiseIntegral = 0;
            // Throttle or ABS on the drive axle cancels endurance braking (it would lock the driven wheels).
            if (input.Throttle > 0.02 || Air.AbsDriveAxleActive || Math.Abs(SpeedForward) < 1.0) { eb = 0; ret = 0; }
            if (input.Selector == GearSelector.Reverse) ret = 0;
            if (!EnduranceBrakesEnabled) { eb = 0; ret = 0; }
            EngineBrakeCommand = eb;
            RetarderCommand = ret;
        }
    }
}
