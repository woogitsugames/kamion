using System.Globalization;

namespace Game.Controls
{
    /// <summary>Warnings of the monitor HUD telltale row, most severe first (ADR 0283). Values index <see cref="HudTexts.Warning"/>.</summary>
    public enum HudWarning : byte
    {
        None = 0,
        /// <summary>Drive-away attempt with the parking brake applied (VehicleModel.ParkingBrakeWarning).</summary>
        ParkDriveAway = 1,
        /// <summary>Air pressure below the warning threshold (STOP).</summary>
        AirLow = 2,
        /// <summary>Trailer emergency braking (supply line pressure lost).</summary>
        TrailerEmergency = 3,
        /// <summary>Parking brake applied (not a fault: the red P of the cluster).</summary>
        ParkingBrake = 4,
        AbsFault = 5,
        TrailerAbsFault = 6,
        /// <summary>ABS regulating right now (amber, short).</summary>
        AbsActive = 7,
    }

    /// <summary>Plain inputs of the warning row (filled from the vehicle model by the HUD; no Unity objects).</summary>
    public struct HudWarningInput
    {
        public bool ParkingBrake, ParkDriveAway, AirLow, TrailerEmergency, AbsFault, TrailerAbsFault, AbsActive;
    }

    /// <summary>Which parts of the screen HUD are on (ADR 0283). Pure.</summary>
    public struct HudVisibility
    {
        /// <summary>Speed / gear / air strip.</summary>
        public bool Strip;
        /// <summary>Second strip row (rev counter, endurance brake, brake cruise, trailer).</summary>
        public bool Extended;
        /// <summary>"Panel" button (developer / lab page): extended detail or developer diagnostics only.</summary>
        public bool DevToggle;
        /// <summary>Extended detail in the cab with live instruments: extended row only, off the wheel and the dash cluster
        /// (no second speedometer over the live one; int-ui-s23 §7 p.4, <see cref="DesktopHudInput.Compact"/>).</summary>
        public bool Compact;

        /// <summary>D90 / ADR 0294: whether the HUD sits over the driver's-eye view. The live rig decides; without one (visual-QA
        /// renders) the control camera's mode; neither known = not the cab (the strip shows).</summary>
        public static bool IsCabView(bool? rigInCab, bool? overrideInCab) => rigInCab ?? overrideInCab ?? false;

        /// <param name="cabCamera">Camera in the cab (driver's eye).</param>
        /// <param name="cabInstrumentsLive">The truck has live cab screens (the TRAKT cluster; the graybox lab truck has none).</param>
        public static HudVisibility Resolve(HudDetail detail, CabHudMode cab, bool cabCamera, bool cabInstrumentsLive, bool devDiagnostics)
        {
            bool extended = detail == HudDetail.Extended;
            bool cabOnly = cabCamera && (cab == CabHudMode.WarningsOnly || (cab == CabHudMode.Auto && cabInstrumentsLive));
            return new HudVisibility
            {
                Strip = extended || !cabOnly,   // asking for the extended detail always shows it
                Extended = extended,
                DevToggle = extended || devDiagnostics,
                Compact = extended && cabOnly,
            };
        }
    }

    /// <summary>
    /// Telltale-row logic (ADR 0283): the active warnings in a fixed order of severity (red ISO 2575 first, then amber),
    /// at most <see cref="MaxShown"/>. No allocation (caller-owned buffer).
    /// </summary>
    public static class HudWarnings
    {
        public const int MaxShown = 3;

        /// <summary>Fills <paramref name="buffer"/> (length &gt;= <see cref="MaxShown"/>) and returns the count.</summary>
        public static int Collect(in HudWarningInput s, HudWarning[] buffer)
        {
            int n = 0, max = buffer.Length < MaxShown ? buffer.Length : MaxShown;
            // The drive-away warning replaces the plain parking-brake telltale (same lamp, flashing in the cab).
            if (s.ParkDriveAway && n < max) buffer[n++] = HudWarning.ParkDriveAway;
            if (s.AirLow && n < max) buffer[n++] = HudWarning.AirLow;
            if (s.TrailerEmergency && n < max) buffer[n++] = HudWarning.TrailerEmergency;
            if (s.ParkingBrake && !s.ParkDriveAway && n < max) buffer[n++] = HudWarning.ParkingBrake;
            if (s.AbsFault && n < max) buffer[n++] = HudWarning.AbsFault;
            if (s.TrailerAbsFault && n < max) buffer[n++] = HudWarning.TrailerAbsFault;
            if (s.AbsActive && !s.AbsFault && n < max) buffer[n++] = HudWarning.AbsActive;
            for (int i = n; i < buffer.Length; i++) buffer[i] = HudWarning.None;
            return n;
        }

        /// <summary>Red (stop / danger) or amber (fault / caution) tile.</summary>
        public static bool IsRed(HudWarning w) => w == HudWarning.ParkDriveAway || w == HudWarning.AirLow || w == HudWarning.TrailerEmergency || w == HudWarning.ParkingBrake;
    }

    /// <summary>
    /// Polish text table of the driving HUD (ADR 0283; one place for every visible HUD string, the localisation table
    /// replaces this class without touching the layout). No brand names. Numbers are prebuilt once (Polish decimal comma),
    /// so the per-frame refresh only looks strings up - no formatting, no allocation.
    /// </summary>
    public static class HudTexts
    {
        public const string KmH = "km/h";
        public const string Bar = "bar";
        public const string Circuit1 = "Obwód 1", Circuit2 = "Obwód 2";
        public const string Rpm = "obr/min";
        public const string Retarder = "Zwalniacz";
        public const string BrakeCruise = "Tempomat zjazdu";
        public const string Off = "wył.";
        public const string Trailer = "Naczepa";
        public const string TrailerCoupled = "sprzężona", TrailerParked = "odpięta", TrailerNone = "brak";
        public const string DevToggle = "Panel", DevToggleOpen = "Zamknij";
        public const string ReverseCamera = "KAMERA COFANIA";

        /// <summary>Endurance-brake stalk positions: 0 off, engine brake, retarder stages.</summary>
        public static readonly string[] RetarderStages = { "0", "HS", "R1", "R2", "R3", "R4" };

        static readonly string[] k_Warnings =
        {
            "",
            "ZWOLNIJ POSTOJOWY",
            "NISKIE CIŚNIENIE",
            "HAMOWANIE NACZEPY",
            "POSTOJOWY",
            "USTERKA ABS",
            "ABS NACZEPY",
            "ABS",
        };

        public static string Warning(HudWarning w) => k_Warnings[(int)w];

        /// <summary>All warning labels (tests: Polish, no brands, fit the tile).</summary>
        public static int WarningCount => k_Warnings.Length;

        // ---- prebuilt numbers
        static readonly string[] k_Speed = Numbers(200);
        static readonly string[] k_Air = Decimals(150);        // 0,0 .. 15,0 bar
        static readonly string[] k_Rpm = Hundreds(26);         // 0 .. 2500 rpm in 100 steps
        static readonly string[] k_Cruise = CruiseLabels(121);

        /// <summary>Speed 0..199 km/h (clamped).</summary>
        public static string Speed(int kmh) => k_Speed[kmh < 0 ? 0 : kmh >= k_Speed.Length ? k_Speed.Length - 1 : kmh];

        /// <summary>Air pressure in 0.1 bar steps (0..150 = 0,0..15,0), clamped.</summary>
        public static string Air(int tenths) => k_Air[tenths < 0 ? 0 : tenths >= k_Air.Length ? k_Air.Length - 1 : tenths];

        /// <summary>Engine speed rounded to 100 rpm (0..25), clamped.</summary>
        public static string RpmHundreds(int hundreds) => k_Rpm[hundreds < 0 ? 0 : hundreds >= k_Rpm.Length ? k_Rpm.Length - 1 : hundreds];

        /// <summary>Brake-cruise set speed label ("wył." at 0).</summary>
        public static string Cruise(int kmh) => kmh <= 0 ? Off : k_Cruise[kmh >= k_Cruise.Length ? k_Cruise.Length - 1 : kmh];

        static string[] Numbers(int n)
        {
            var a = new string[n];
            for (int i = 0; i < n; i++) a[i] = i.ToString(CultureInfo.InvariantCulture);
            return a;
        }

        static string[] Decimals(int maxTenths)
        {
            var a = new string[maxTenths + 1];
            for (int i = 0; i <= maxTenths; i++)
                a[i] = (i / 10).ToString(CultureInfo.InvariantCulture) + "," + (i % 10).ToString(CultureInfo.InvariantCulture);
            return a;
        }

        static string[] Hundreds(int n)
        {
            var a = new string[n];
            for (int i = 0; i < n; i++) a[i] = (i * 100).ToString(CultureInfo.InvariantCulture);
            return a;
        }

        static string[] CruiseLabels(int n)
        {
            var a = new string[n];
            for (int i = 0; i < n; i++) a[i] = i.ToString(CultureInfo.InvariantCulture) + " " + KmH;
            return a;
        }
    }
}
