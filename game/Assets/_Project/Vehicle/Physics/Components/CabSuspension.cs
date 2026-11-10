using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Cab suspension: 3-DOF (heave, pitch, roll) cab on spring/damper mounts, excited by the motion of the
    /// chassis at the mount point (specific force: linear acceleration minus gravity, plus chassis angular
    /// acceleration). Output is the cab pose relative to the chassis, for the cabin camera.
    /// Soft progressive stops instead of a hard clamp (no velocity reset, no visible "hit").
    /// Symplectic Euler substepping (stable for these frequencies at 100 Hz). Visual/camera only: the cab
    /// mass is part of the chassis mass and there is no force feedback into the chassis.
    /// </summary>
    public sealed class CabSuspension
    {
        readonly CabSuspensionDefinition _def;
        readonly double _wp, _wr, _wh, _maxPitch, _maxRoll, _maxHeave;
        /// <summary>Pitch > 0 = nose down; roll > 0 = left side down; heave > 0 = cab moved down (compressed).</summary>
        public double Pitch, PitchRate, Roll, RollRate, Heave, HeaveRate;

        Vec3 _prevMountVel, _prevOmega;
        bool _hasPrev;

        public CabSuspension(CabSuspensionDefinition def)
        {
            _def = def;
            _wp = 2 * Math.PI * def.pitchFrequencyHz;
            _wr = 2 * Math.PI * def.rollFrequencyHz;
            _wh = 2 * Math.PI * Math.Max(0.1, def.heaveFrequencyHz);
            _maxPitch = def.maxPitchDeg * MathUtil.Deg2Rad;
            _maxRoll = def.maxRollDeg * MathUtil.Deg2Rad;
            _maxHeave = Math.Max(0.005, def.maxHeaveM);
        }

        /// <summary>Stage 1 entry point: excitation from the chassis CoM acceleration only (vehicle frame).</summary>
        public void Update(Vec3 accLocal, double dt) => Integrate(accLocal.z, accLocal.x, 0, 0, 0, dt);

        /// <summary>Full update from the chassis state: mount-point acceleration and chassis angular acceleration.</summary>
        public void Update(in ChassisState c, Vec3 gravity, double dt)
        {
            Vec3 mountWorld = c.LocalToWorld(_def.mountCenter);
            Vec3 v = c.PointVelocity(mountWorld);
            Vec3 vLocal = c.Rotation.InverseRotate(v);
            Vec3 wLocal = c.Rotation.InverseRotate(c.AngularVelocity);
            if (!_hasPrev)
            {
                _prevMountVel = vLocal; _prevOmega = wLocal; _hasPrev = true;
                return;
            }
            // Specific force in the chassis frame (what an accelerometer on the frame would read), minus static gravity.
            Vec3 aLocal = (vLocal - _prevMountVel) / dt + Vec3.Cross(wLocal, vLocal);
            Vec3 gLocal = c.Rotation.InverseRotate(gravity);
            Vec3 f = aLocal - gLocal;
            Vec3 alpha = (wLocal - _prevOmega) / dt;
            _prevMountVel = vLocal; _prevOmega = wLocal;
            Integrate(f.z, f.x, f.y - (-gravity.y), alpha.x, alpha.z, dt);
        }

        void Integrate(double fLong, double fLat, double fVertDev, double alphaPitchChassis, double alphaRollChassis, double dt)
        {
            double z = _def.dampingRatio;
            double g = _def.accelGain;
            int n = 2;
            double h = dt / n;
            for (int i = 0; i < n; i++)
            {
                // Pitch: braking (negative fLong) pitches the cab nose down (positive). Chassis pitch acceleration
                // about +X (nose down in this frame) is followed by the mounts, so the cab lags it.
                double kp = Stop(Pitch, _maxPitch);
                double pAcc = -fLong * g - 2 * z * _wp * PitchRate - _wp * _wp * kp * Pitch - alphaPitchChassis;
                PitchRate += pAcc * h; Pitch += PitchRate * h;
                // Roll: acceleration to the right rolls the cab left side down (outwards).
                double kr = Stop(Roll, _maxRoll);
                double rAcc = fLat * g - 2 * z * _wr * RollRate - _wr * _wr * kr * Roll - alphaRollChassis;
                RollRate += rAcc * h; Roll += RollRate * h;
                // Heave: an upward frame acceleration compresses the mounts (cab moves down relative to the frame).
                double kh = Stop(Heave, _maxHeave);
                double hAcc = fVertDev - 2 * z * _wh * HeaveRate - _wh * _wh * kh * Heave;
                HeaveRate += hAcc * h; Heave += HeaveRate * h;
            }
            // Hard end stops beyond the progressive rubber stops (ADR 0082): a crash, a roll-over or a free fall feeds
            // accelerations far outside the working range of the mounts; the cab (and the eye point on it) must stay
            // on the frame. Never reached in normal driving (the soft stops act from 0.8 x limit).
            Pitch = HardStop(Pitch, ref PitchRate, _maxPitch * HardStopFactor);
            Roll = HardStop(Roll, ref RollRate, _maxRoll * HardStopFactor);
            Heave = HardStop(Heave, ref HeaveRate, _maxHeave * HardStopFactor);
        }

        /// <summary>Hard stop as a multiple of the soft-stop limit (travel end of the cab mounts). WORKING_VALUE.</summary>
        public const double HardStopFactor = 1.5;

        static double HardStop(double x, ref double rate, double limit)
        {
            if (double.IsNaN(x) || double.IsInfinity(x) || double.IsNaN(rate) || double.IsInfinity(rate)) { rate = 0; return 0; }
            if (x > limit) { if (rate > 0) rate = 0; return limit; }
            if (x < -limit) { if (rate < 0) rate = 0; return -limit; }
            return x;
        }

        /// <summary>Stiffness multiplier: 1 inside the limit, rising steeply beyond it (rubber stop).</summary>
        static double Stop(double x, double limit)
        {
            double r = Math.Abs(x) / limit;
            if (r <= 0.8) return 1.0;
            double e = (r - 0.8) / 0.2;
            return 1.0 + 6.0 * e * e;
        }
    }
}
