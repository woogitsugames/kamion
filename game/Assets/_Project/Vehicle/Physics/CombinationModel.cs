using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Tractor + optional semi-trailer. Orchestrates one fixed step: tractor model (driveline, steering, air
    /// supply, endurance brakes), trailer air lines and charging, trailer model, then the fifth-wheel constraint.
    /// Outputs the total force and torque (about each CoM) for both rigid bodies; the host integrates them
    /// (gravity included in the host, exactly like for the solo tractor).
    ///
    /// Unity adapter: two Rigidbodies; FixedUpdate builds both ChassisStates, calls Step, then
    /// rb.AddForce(TractorForce) + rb.AddTorque(TractorTorque) and the same for the trailer.
    /// Do NOT add a PhysX joint between them: the coupling is in TractorForce/TrailerForce.
    /// </summary>
    public sealed class CombinationModel
    {
        public readonly VehicleModel Tractor;
        /// <summary>Current trailer (null = solo tractor). Swap it with <see cref="SetTrailer"/>.</summary>
        public TrailerModel Trailer { get; private set; }
        public readonly FifthWheel FifthWheel;
        public Vec3 Gravity = new Vec3(0, -9.81, 0);

        public Vec3 TractorForce { get; private set; }
        public Vec3 TractorTorque { get; private set; }
        public Vec3 TrailerForce { get; private set; }
        public Vec3 TrailerTorque { get; private set; }

        /// <summary>Coupling request: while armed, the jaw locks automatically when the kingpin enters the capture window.</summary>
        public bool CouplingArmed;
        public bool HasTrailer => Trailer != null;
        public bool Coupled => Trailer != null && FifthWheel.Coupled;

        public CombinationModel(VehicleModel tractor, TrailerModel trailer, bool coupled)
        {
            Tractor = tractor;
            Trailer = trailer;
            FifthWheel = new FifthWheel(tractor.Def.fifthWheel);
            if (trailer != null) SetCoupledStatic(coupled);
        }

        /// <summary>
        /// R7: replaces the trailer (or removes it with null) without rebuilding the tractor model or this combination.
        /// Resets the fifth wheel (open jaw, no force, not armed) and sets the static configuration for the new trailer,
        /// coupled or standing on its legs. The tractor keeps its drivetrain, air system and wheel states. The host must
        /// move / re-mass its trailer rigid body (<see cref="TrailerModel.MassProps"/>) and place the new trailer itself.
        /// Never call inside the fixed step's force application; call it between steps.
        /// </summary>
        public void SetTrailer(TrailerModel trailer, bool coupled)
        {
            if (Trailer != null) Trailer.Coupled = false;
            FifthWheel.ResetState();
            CouplingArmed = false;
            Trailer = trailer;
            TrailerForce = Vec3.Zero; TrailerTorque = Vec3.Zero;
            if (trailer != null) SetCoupledStatic(coupled && trailer != null);
            else
            {
                Tractor.SetStaticKingpinLoad(0);
                UpdateCouplingLinks();
            }
        }

        /// <summary>R7: changes the cargo of the current trailer in place (see <see cref="TrailerModel.SetCargo"/>) and re-levels both suspensions to the new kingpin load.</summary>
        public void SetCargo(CargoDefinition cargo)
        {
            if (Trailer == null) return;
            Trailer.SetCargo(cargo, FifthWheel.Coupled);
            SetCoupledStatic(FifthWheel.Coupled);
        }

        /// <summary>Sets the static configuration (suspension pre-levelling, air lines) and the coupling state.</summary>
        public void SetCoupledStatic(bool coupled)
        {
            FifthWheel.Coupled = coupled;
            if (Trailer == null) return;
            Trailer.SetStatic(coupled);
            Tractor.SetStaticKingpinLoad(coupled ? Trailer.StaticNoseLoad(true) : 0);
            Trailer.SetLandingGear(!coupled);
            if (!coupled) Trailer.Brakes.ParkValveApplied = true;
            UpdateCouplingLinks();
        }

        public double StaticKingpinLoad => Trailer != null && FifthWheel.Coupled ? Trailer.StaticNoseLoad(true) : 0;

        /// <summary>Opens the jaw. Refused (returns false) when the landing gear is not down: there is no chassis-ground collision to catch the nose.</summary>
        public bool Uncouple()
        {
            if (Trailer == null || !FifthWheel.Coupled) return false;
            if (!Trailer.LandingGearDown || Trailer.LandingGearFootY > Trailer.Def.landingGear.loweredFootY + 0.01) return false;
            FifthWheel.Release();
            Trailer.Brakes.ParkValveApplied = true;
            UpdateCouplingLinks();
            return true;
        }

        void UpdateCouplingLinks()
        {
            bool c = Coupled;
            Tractor.TrailerConnected = c;
            if (Trailer != null) Trailer.Coupled = c;
            Tractor.TowedMass = c ? Trailer.Mass : 0;
        }

        public void Step(double dt, in ChassisState tractorState, in ChassisState trailerState, in DriverInput input, IGroundQuery ground)
        {
            Tractor.Gravity = Gravity;
            UpdateCouplingLinks();
            Tractor.Step(dt, tractorState, input, ground);
            Vec3 fA = Tractor.TotalForce, tA = Tractor.TotalTorque;
            if (Trailer == null)
            {
                TractorForce = fA; TractorTorque = tA;
                return;
            }

            // Air lines (connected while coupled; red-line loss -> trailer emergency braking).
            double red = 0, yellow = 0;
            if (Coupled)
            {
                Tractor.Air.ChargeTrailer(ref Trailer.Brakes.Reservoir, Trailer.Brakes.VolumeL, dt);
                red = Tractor.Air.TrailerSupplyLine;
                yellow = Tractor.Air.TrailerControlLine;
                Trailer.Brakes.ParkValveApplied = false;
            }
            Trailer.Step(dt, trailerState, red, yellow, ground);
            Vec3 fB = Trailer.TotalForce, tB = Trailer.TotalTorque;

            Vec3 anchorA = Tractor.Def.fifthWheel.position, anchorB = Trailer.KingpinLocal;
            if (!FifthWheel.Coupled && CouplingArmed)
            {
                // R5: the throat ramps guide the kingpin to the jaw before the capture test.
                if (FifthWheel.ComputeThroatGuide(tractorState, anchorA, trailerState, anchorB, out Vec3 fg))
                {
                    Vec3 pk = trailerState.LocalToWorld(anchorB);
                    fB += fg; tB += Vec3.Cross(pk - trailerState.CenterOfMassWorld, fg);
                    fA -= fg; tA += Vec3.Cross(pk - tractorState.CenterOfMassWorld, -fg);
                }
                if (FifthWheel.TryCapture(tractorState, anchorA, trailerState, anchorB))
                {
                    CouplingArmed = false;
                    UpdateCouplingLinks();
                }
            }
            FifthWheel.Solve(dt, tractorState, Tractor.MassProps, anchorA, fA, tA, trailerState, Trailer.MassProps, anchorB, fB, tB, Gravity);
            if (FifthWheel.Coupled)
            {
                Vec3 fc = FifthWheel.ForceOnTrailer, tc = FifthWheel.TorqueOnTrailer;
                Vec3 p = FifthWheel.KingpinWorld;
                Vec3 pA = tractorState.LocalToWorld(anchorA);
                fB += fc; tB += Vec3.Cross(p - trailerState.CenterOfMassWorld, fc) + tc;
                fA -= fc; tA += Vec3.Cross(pA - tractorState.CenterOfMassWorld, -fc) - tc;
            }
            TractorForce = fA; TractorTorque = tA;
            TrailerForce = fB; TrailerTorque = tB;
        }
    }
}
