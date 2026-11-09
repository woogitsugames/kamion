using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Minimal cab suspension (pitch + roll), driven by chassis acceleration in the vehicle frame.
    /// Output angles are visual/camera only in Stage 1 (no force feedback into the chassis).
    /// </summary>
    public sealed class CabSuspension
    {
        readonly CabSuspensionDefinition _def;
        readonly double _wp, _wr, _maxPitch, _maxRoll;
        public double Pitch, PitchRate, Roll, RollRate; // rad, rad/s (pitch > 0 = nose down)

        public CabSuspension(CabSuspensionDefinition def)
        {
            _def = def;
            _wp = 2 * Math.PI * def.pitchFrequencyHz;
            _wr = 2 * Math.PI * def.rollFrequencyHz;
            _maxPitch = def.maxPitchDeg * MathUtil.Deg2Rad;
            _maxRoll = def.maxRollDeg * MathUtil.Deg2Rad;
        }

        /// <summary>accLocal: chassis acceleration in vehicle frame (m/s^2), x = right, z = forward.</summary>
        public void Update(Vec3 accLocal, double dt)
        {
            double z = _def.dampingRatio;
            // Deceleration (negative a_z) pitches the cab nose-down (positive pitch).
            double pitchAcc = -accLocal.z * _def.accelGain - 2 * z * _wp * PitchRate - _wp * _wp * Pitch;
            PitchRate += pitchAcc * dt;
            Pitch += PitchRate * dt;
            // Lateral acceleration to the right rolls the cab to the left (outward): roll > 0 = left side down.
            double rollAcc = accLocal.x * _def.accelGain - 2 * z * _wr * RollRate - _wr * _wr * Roll;
            RollRate += rollAcc * dt;
            Roll += RollRate * dt;
            if (Math.Abs(Pitch) > _maxPitch) { Pitch = Math.Sign(Pitch) * _maxPitch; PitchRate = 0; }
            if (Math.Abs(Roll) > _maxRoll) { Roll = Math.Sign(Roll) * _maxRoll; RollRate = 0; }
        }
    }
}
