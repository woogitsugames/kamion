namespace Game.UI.Navigation
{
    /// <summary>
    /// String table of the GPS (map, minimap, guidance). Language: PL (start language); every visible word lives here so a
    /// later localisation table swap touches one file (same convention as <see cref="Game.UI.CabDisplays.CabDisplayText"/>).
    /// </summary>
    public static class NavText
    {
        public const string Attribution = "© OpenStreetMap contributors";
        public const string Back = "Wróć";
        public const string ZoomIn = "+";
        public const string ZoomOut = "−";
        public const string Recenter = "Pojazd";
        public const string North = "N";
        public const string PlanRoute = "Wyznacz trasę";
        public const string ClearRoute = "Wyczyść trasę";
        public const string ClearPin = "Wyczyść";
        public const string Drive = "Jedź";
        public const string TapHint = "Dotknij mapy, aby wybrać cel";
        public const string Destination = "Cel";
        public const string Unnamed = "Droga bez nazwy";
        public const string StraightLine = "w linii prostej";
        public const string About = "ok.";
        public const string Minutes = "min";
        public const string OffRoad = "Za daleko od drogi - wybierz miejsce bliżej ulicy";
        public const string NoPath = "Brak dojazdu do tego miejsca";
        public const string OffReach = "Cel poza zasięgiem mapy - pinezka na najbliższym węźle";
        public const string StartOffRoad = "Pojazd poza siecią dróg mapy";
        public const string AlreadyThere = "Jesteś już w tym miejscu";
        public const string Arrived = "Cel osiągnięty";
        public const string OffRoute = "Poza trasą";
        public const string Rerouting = "Nowa trasa";
        public const string Then = "potem";
        public const string Exit = "zjazd";
        public const string Paused = "Pauza - jazda wstrzymana na czas mapy";
        /// <summary>ADR 0302: destination of the multi-tile trip (button cycles the trips of the corridor).</summary>
        public const string TripButton = "Cel trasy";
        public const string TripNone = "brak";
        public const string TripPlanning = "Wyznaczanie trasy...";
        public const string Remaining = "pozostało";
        /// <summary>A leg of the trip only over a road with a truck limit (OSM, e.g. axle load 10 t) - no legal detour in the corridor.</summary>
        public const string TripRelaxed = "odcinek z ograniczeniem dla ciężarówek";

        // ADR 0307 (D91): limit of the road below the combination - warning only, the drive is never blocked
        public const string Restriction = "Ograniczenie";
        public const string RestrictionIn = "za";
        public const string RestrictionHere = "na tym odcinku";
        public const string LimitHeight = "wysokość do", LimitWeight = "masa do", LimitAxle = "nacisk osi do", LimitLength = "długość do";
        public const string Metres = "m", Tonnes = "t";

        /// <summary>"wysokość do 3,7 m, masa do 12 t": the limits of <paramref name="r"/> the combination exceeds.
        /// Allocates (full map panel, logs, tests) - the per-frame views draw signs (<see cref="NavDraw.RestrictionSigns"/>).</summary>
        public static string Describe(in Game.Core.Navigation.RouteRestriction r)
        {
            var b = new Game.UI.CabDisplays.TextBuffer(96);
            for (int i = 0; i < 4; i++)
            {
                var k = (Game.Core.Navigation.LimitKind)(1 << i);
                if ((r.Exceeded & k) == 0) continue;
                if (b.Length > 0) b.Append(", ");
                b.Append(k == Game.Core.Navigation.LimitKind.Height ? LimitHeight : k == Game.Core.Navigation.LimitKind.Weight ? LimitWeight
                    : k == Game.Core.Navigation.LimitKind.AxleLoad ? LimitAxle : LimitLength).Append(' ');
                NavDraw.AppendLimit(b, k, NavDraw.LimitValue(r, k), true);
            }
            return b.ToString();
        }

        /// <summary>Every character the map canvases draw (glyph requests).</summary>
        public const string Charset =
            " 0123456789,.:+-–−/°%()©ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĄĆĘŁŃÓŚŹŻąćęłńóśźż·";
    }
}
