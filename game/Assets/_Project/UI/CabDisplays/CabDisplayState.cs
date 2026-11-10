namespace Game.UI.CabDisplays
{
    /// <summary>
    /// One snapshot of everything the cab screens show (filled by <see cref="CabDisplaySource"/> from the solver, the lamp
    /// state and the trip computer; plain values so layouts and tests do not depend on Unity objects).
    /// </summary>
    public struct CabDisplayState
    {
        // ---- motion / powertrain
        /// <summary>Road speed [km/h], signed (negative when rolling backwards).</summary>
        public float SpeedKmh;
        public float EngineRpm;
        public bool EngineRunning;
        /// <summary>Engaged gear: &gt; 0 forward, &lt; 0 reverse, 0 = neutral.</summary>
        public int Gear;
        /// <summary>Gear being shifted to while the AMT is in a shift (0 = no shift in progress).</summary>
        public int ShiftTarget;
        public bool ManualMode;
        /// <summary>Selector: 'D', 'N' or 'R'.</summary>
        public char Selector;
        public float IdleRpm, MaxRpm;
        /// <summary>Economy band on the rev counter [rpm] (AMT light-load upshift .. full-load upshift points).</summary>
        public float EcoLowRpm, EcoHighRpm;

        // ---- brakes
        public float AirCircuit1Bar, AirCircuit2Bar;
        /// <summary>Low-pressure warning threshold of the air system [bar] (marked on the bars).</summary>
        public float AirWarnBar;
        public bool AirLowWarning;
        public bool ParkingBrake;
        /// <summary>Endurance brake stalk: 0 off, 1 engine brake, 2.. retarder stages.</summary>
        public int RetarderLever, RetarderStages;
        /// <summary>Retarder fill 0..1 (actual braking).</summary>
        public float RetarderFill;
        public float BrakeCruiseKmh;
        public bool AbsFault, AbsActive;
        public bool TrailerConnected, TrailerAbsFault;
        public bool HillHold;

        // ---- lamps
        public bool LowBeam, HighBeam;
        /// <summary>Turn signal lever: 0 off, -1 left, +1 right, 2 hazard (from the turn-signal stalk, <c>TurnSignal</c>).</summary>
        public int Indicators;
        /// <summary>Flasher phase (true = lamp lit), for the indicator telltales.</summary>
        public bool FlasherOn;

        // ---- trip computer
        public float FuelLitres, FuelCapacityLitres, AdBlueFraction;
        /// <summary>Coolant temperature [deg C] (first-order warm-up model, <c>CoolantModel</c>).</summary>
        public float CoolantC;
        public float RangeKm;
        /// <summary>Trip average [l/100 km]; NaN until enough distance for a meaningful value.</summary>
        public float AvgConsumption;
        public double OdometerKm, TripKm;
        /// <summary>Tachograph: driving time since the session start [min].</summary>
        public int DrivingMinutes;

        // ---- environment
        public int ClockMinutes;
        public float OutsideTempC;
        /// <summary>Night mode of the screens (same switch as the automatic dipped beam: light sensor).</summary>
        public bool Night;

        // ---- navigation
        public bool HasPosition;
        /// <summary>Truck position in the region-local frame (E, N metres) and heading (deg, 0 = north, clockwise).</summary>
        public float PosE, PosN, HeadingDeg;
    }
}
