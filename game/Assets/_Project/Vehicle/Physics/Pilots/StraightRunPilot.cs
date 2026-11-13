using System;

namespace Game.Vehicle.Physics
{
    /// <summary>Phase of the scripted straight run (<see cref="StraightRunPilot"/>).</summary>
    public enum StraightRunPhase : byte { Idle = 0, Settle = 1, Launch = 2, Hold = 3, Brake = 4, Stopped = 5 }

    /// <summary>
    /// Online results of one straight run, same definitions as the .NET runner metrics (tools/physics-runner/Sim/Metrics.cs):
    /// times from the first step with throttle, stop distance from the brake-onset position to |v| &lt; 0.05 m/s,
    /// MFDD per UN R13 Annex 4 (between 0.8 v0 and 0.1 v0). NaN = not reached.
    /// </summary>
    public struct StraightRunResult
    {
        public double TimeTo60, TimeTo80, DistanceTo80;
        public double BrakeSpeedKmh, StopDistance, StopTime, Mfdd, MaxDecel;
        public double MaxLateralDeviation, HoldSpeedMean, HoldSpeedStd;
        public bool Complete;
    }

    /// <summary>
    /// Deterministic scripted driver for the gate 1-2 straight run (ADR 0195): hold the brake to settle, full throttle
    /// 0 -&gt; target (80 km/h), hold the target with a PI controller, emergency brake (full pedal) to a stop, keep the brake.
    /// It produces only the driver's commands (pedals, selector, steering 0..1 of lock) - the vehicle model does the rest,
    /// exactly as with a human driver. Lateral control: pure pursuit on the start line (position + heading at
    /// <see cref="Begin"/>). Pure C#, stepped with the fixed physics step, no allocation per step.
    /// </summary>
    public sealed class StraightRunPilot
    {
        // ---- configuration (WORKING_VALUE: test-procedure choices, not vehicle data) ----
        public double TargetKmh = 80;
        /// <summary>Brake held at standstill before the throttle step [s] (air system / AMT settle, same as runner launch scenarios: 1 s).</summary>
        public double SettleSeconds = 1.0;
        /// <summary>Time at the target speed before the emergency stop [s].</summary>
        public double HoldSeconds = 4.0;
        /// <summary>Hold phase: the speed must be within this band of the target before the hold timer runs [km/h].</summary>
        public double HoldBandKmh = 1.5;
        public double BrakePedal = 1.0;
        /// <summary>Wheelbase [m] and road-wheel lock [rad] of the tractor (vehicle data) for the pure-pursuit steering.</summary>
        public double Wheelbase = 3.7;
        public double MaxRoadWheelAngle = 0.7;

        public StraightRunPhase Phase { get; private set; }
        public double Time { get; private set; }
        public StraightRunResult Result;

        double _ox, _oz, _dx, _dz;          // start line: origin and unit direction (x east, z north)
        double _tThrottle = double.NaN, _phaseT, _holdT, _integral;
        double _bx, _bz, _v0, _tBrake, _vPrev = double.NaN;
        double _sA = double.NaN, _sE = double.NaN, _vA, _vE, _s;
        double _holdSum, _holdSq; long _holdN;
        // max deceleration: mean over a 0.1 s sliding window (single-step dv/dt is noise from the contact solver)
        readonly double[] _vHist = new double[64];
        int _hHead, _hCount, _hWindow = 10;

        /// <summary>Starts the run at the vehicle's current pose: the line is the current position and heading.</summary>
        public void Begin(double x, double z, double fwdX, double fwdZ, double fixedDt)
        {
            double n = Math.Sqrt(fwdX * fwdX + fwdZ * fwdZ);
            if (n < 1e-6) { fwdX = 0; fwdZ = 1; n = 1; }
            _ox = x; _oz = z; _dx = fwdX / n; _dz = fwdZ / n;
            Phase = StraightRunPhase.Settle;
            Time = 0; _phaseT = 0; _holdT = 0; _integral = 0;
            _tThrottle = double.NaN; _vPrev = double.NaN; _sA = _sE = double.NaN; _s = 0;
            _holdSum = _holdSq = 0; _holdN = 0; _hHead = _hCount = 0;
            _hWindow = Math.Max(1, Math.Min(_vHist.Length - 1, (int)Math.Round(0.1 / Math.Max(fixedDt, 1e-4))));
            Result = new StraightRunResult
            {
                TimeTo60 = double.NaN, TimeTo80 = double.NaN, DistanceTo80 = double.NaN, BrakeSpeedKmh = double.NaN,
                StopDistance = double.NaN, StopTime = double.NaN, Mfdd = double.NaN, HoldSpeedMean = double.NaN, HoldSpeedStd = double.NaN,
            };
        }

        /// <summary>Distance along the start line [m] (signed).</summary>
        public double Along(double x, double z) => (x - _ox) * _dx + (z - _oz) * _dz;
        /// <summary>Lateral offset from the start line [m], + = right of the line.</summary>
        public double Lateral(double x, double z) => (x - _ox) * _dz - (z - _oz) * _dx;

        /// <summary>
        /// One fixed step. Pose and speed are the tractor's state at the start of the step (vehicle-frame origin, world
        /// x/z, forward unit vector, signed forward speed m/s). Writes the commands for this step into <paramref name="input"/>.
        /// </summary>
        public void Step(double dt, double x, double z, double fwdX, double fwdZ, double vFwd, ref DriverInput input)
        {
            input.Selector = GearSelector.Drive;
            input.ParkingBrake = false;
            input.ManualMode = false;
            input.RetarderLever = 0;
            input.BrakeCruiseKmh = 0;
            input.ShiftUp = input.ShiftDown = false;
            if (Phase == StraightRunPhase.Idle) { input.Throttle = 0; input.Brake = 1; input.Steer = 0; return; }

            Time += dt; _phaseT += dt;
            double v = Math.Abs(vFwd), kmh = v * 3.6;
            double lat = Lateral(x, z);
            if (Phase >= StraightRunPhase.Launch && Phase <= StraightRunPhase.Brake && Math.Abs(lat) > Result.MaxLateralDeviation)
                Result.MaxLateralDeviation = Math.Abs(lat);
            if (!double.IsNaN(_vPrev)) _s += v * dt;
            PushSpeed(v);

            double throttle = 0, brake = 0;
            switch (Phase)
            {
                case StraightRunPhase.Settle:
                    brake = 1;
                    if (_phaseT >= SettleSeconds - 1e-9) Enter(StraightRunPhase.Launch);
                    break;
                case StraightRunPhase.Launch:
                    if (double.IsNaN(_tThrottle)) _tThrottle = Time - dt;
                    throttle = 1;
                    if (double.IsNaN(Result.TimeTo60) && kmh >= 60) Result.TimeTo60 = Time - _tThrottle;
                    if (kmh >= TargetKmh)
                    {
                        Result.TimeTo80 = Time - _tThrottle;
                        Result.DistanceTo80 = _s;
                        Enter(StraightRunPhase.Hold);
                        throttle = 0;
                    }
                    break;
                case StraightRunPhase.Hold:
                {
                    double e = TargetKmh / 3.6 - v;
                    _integral = Clamp(_integral + e * dt, -5, 10);
                    throttle = Clamp(0.25 * e + 0.06 * _integral + 0.35, 0, 1);
                    if (Math.Abs(kmh - TargetKmh) <= HoldBandKmh || _holdT > 0) _holdT += dt;
                    if (_holdT > 0) { _holdSum += kmh; _holdSq += kmh * kmh; _holdN++; }
                    if (_holdT >= HoldSeconds - 1e-9)
                    {
                        Enter(StraightRunPhase.Brake);
                        _bx = x; _bz = z; _v0 = v; _tBrake = Time - dt; _s = 0;
                        Result.BrakeSpeedKmh = kmh;
                        if (_holdN > 0)
                        {
                            Result.HoldSpeedMean = _holdSum / _holdN;
                            Result.HoldSpeedStd = Math.Sqrt(Math.Max(0, _holdSq / _holdN - Result.HoldSpeedMean * Result.HoldSpeedMean));
                        }
                        throttle = 0; brake = BrakePedal;
                    }
                    break;
                }
                case StraightRunPhase.Brake:
                    brake = BrakePedal;
                    if (double.IsNaN(_sA) && v <= 0.8 * _v0) { _sA = _s; _vA = v; }
                    if (double.IsNaN(_sE) && v <= 0.1 * _v0) { _sE = _s; _vE = v; }
                    if (_hCount > _hWindow)
                    {
                        double dec = (Back(_hWindow) - v) / (_hWindow * dt);
                        if (dec > Result.MaxDecel) Result.MaxDecel = dec;
                    }
                    if (v < 0.05)
                    {
                        double ddx = x - _bx, ddz = z - _bz;
                        Result.StopDistance = Math.Sqrt(ddx * ddx + ddz * ddz);
                        Result.StopTime = Time - _tBrake;
                        if (!double.IsNaN(_sA) && !double.IsNaN(_sE) && _sE > _sA)
                            Result.Mfdd = (_vA * _vA - _vE * _vE) / (2 * (_sE - _sA));
                        Result.Complete = true;
                        Enter(StraightRunPhase.Stopped);
                    }
                    break;
                case StraightRunPhase.Stopped:
                    brake = 1;
                    break;
            }
            _vPrev = v;

            input.Throttle = throttle;
            input.Brake = brake;
            input.Steer = Phase == StraightRunPhase.Settle || Phase == StraightRunPhase.Stopped ? 0 : SteerToLine(x, z, fwdX, fwdZ, v);
        }

        /// <summary>Pure pursuit to the point of the start line one look-ahead ahead; returns the steering command (+ = right).</summary>
        double SteerToLine(double x, double z, double fwdX, double fwdZ, double v)
        {
            double ld = Math.Max(10.0, 1.2 * v);
            double s = Along(x, z) + ld;
            double tx = _ox + _dx * s - x, tz = _oz + _dz * s - z;
            double n = Math.Sqrt(fwdX * fwdX + fwdZ * fwdZ);
            if (n < 1e-6) return 0;
            double fx = fwdX / n, fz = fwdZ / n;
            double localZ = tx * fx + tz * fz;
            double localX = tx * fz - tz * fx;           // right = (fz, -fx) in the x-east / z-north plane
            double alpha = Math.Atan2(localX, localZ);
            double dist = Math.Sqrt(tx * tx + tz * tz);
            double delta = Math.Atan(2 * Wheelbase * Math.Sin(alpha) / Math.Max(1, dist));
            return Clamp(delta / Math.Max(1e-3, MaxRoadWheelAngle), -1, 1);
        }

        void Enter(StraightRunPhase p) { Phase = p; _phaseT = 0; }

        void PushSpeed(double v)
        {
            _vHist[_hHead] = v;
            _hHead = (_hHead + 1) % _vHist.Length;
            if (_hCount < _vHist.Length) _hCount++;
        }

        /// <summary>Speed k samples before the newest one.</summary>
        double Back(int k) => _vHist[(_hHead - 1 - k + 2 * _vHist.Length) % _vHist.Length];

        static double Clamp(double v, double lo, double hi) => v < lo ? lo : (v > hi ? hi : v);
    }
}
