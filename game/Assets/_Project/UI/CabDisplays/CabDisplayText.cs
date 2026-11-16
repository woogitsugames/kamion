namespace Game.UI.CabDisplays
{
    /// <summary>
    /// String table of the cab screens (language: PL, the start language). The project has no localisation package yet;
    /// every visible word of the cluster, navigation and DIN units lives here so a later table swap touches one file.
    /// Units follow Polish practice (km/h, 1/min, bar, l/100 km, decimal comma).
    /// </summary>
    public static class CabDisplayText
    {
        public const string KmH = "km/h";
        public const string Km = "km";
        public const string M = "m";
        public const string Bar = "bar";
        public const string RpmUnit = "1/min x100";
        public const string Fuel = "ON";               // olej napędowy
        public const string ScrFluid = "AUS 32";        // płyn do układu SCR wg ISO 22241 (nazwa ogólna, bez znaku towarowego; BRAND-SWEEP-S20 #1)
        public const string Coolant = "Chł";          // płyn chłodzący
        public const string AvgPrefix = "Ø ";
        public const string AvgUnit = " l/100 km";
        public const string AvgNone = "Ø –,– l/100 km";
        public const string Range = "Zasięg";
        public const string TripPrefix = "T ";
        public const string DegC = " °C";
        public const string Auto = "A";
        public const string Manual = "M";
        public const string Neutral = "N";
        public const string Reverse = "R";
        public const string BrakeCruise = "BC";
        public const string EngineBrake = "EB";
        public const string Retarder = "R";
        public const string HillHold = "HA";
        public const string AbsActive = "ABS";

        // Navigation
        public const string City = "Białystok";
        public const string OffRoute = "Poza trasą";
        public const string NoMap = "Brak mapy tego obszaru";
        public const string Arrive = "Cel";
        public const string Straight = "Prosto";
        public const string RoundaboutPrefix = "Rondo";
        public const string Exit = "zjazd";

        // DIN units
        public const string TachoHours = "h";
        public const string RadioBand = "FM";
        public const string RadioFreq = "98,4";       // UNVERIFIED: czy częstotliwość nie jest zajęta przez stację w regionie (wykaz UKE; BRAND-SWEEP-S20 #16)
        public const string CbChannel = "CH 19";
        public const string CbMode = "AM";

        /// <summary>Every character the screens can draw (requested in the font atlas before a refresh).</summary>
        public const string Charset =
            " 0123456789,.:+-–/°%Ø()ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĄĆĘŁŃÓŚŹŻąćęłńóśźż·";
        public const string Digits = "0123456789 ,:-";
    }
}
