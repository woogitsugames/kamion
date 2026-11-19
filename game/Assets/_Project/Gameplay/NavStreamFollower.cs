using System.Collections.Generic;
using Game.UI.CabDisplays;
using Game.UI.Navigation;
using Game.World.Streaming;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// ADR 0300: keeps the GPS (<see cref="NavigationService"/>: HUD minimap, full map) and the cab navigation screen on
    /// the streamed tile under the truck. Before it the GPS stayed on the start region: after the first origin rebase
    /// the truck was measured in the start region's frame, and once that region was unloaded (its root destroyed) in the
    /// world frame - the minimap showed the start region's streets around a wrong point and nothing under the truck
    /// (owner's run Bialystok -> Tykocin, s24).
    /// - Switch: when the truck is <see cref="switchInsideM"/> inside another tile (hysteresis at the seam), or at once
    ///   when the region the GPS measures in lost its frame. Frame = the tile's region root
    ///   (<see cref="WorldStreamer.FrameOf"/>), which every origin rebase moves together with the truck - no offset.
    /// - Neighbours: every other Ready tile with a map is drawn around the current one, moved by its origin difference.
    /// Checks every <see cref="intervalS"/>; allocation only on a switch / a change of the resident set (tile events).
    /// No streaming (single region, DrivingLab) = does nothing.
    /// ADR 0302: also starts the multi-tile GPS trip (<see cref="NavTrip"/>, Resources/Nav/nav_trips.json) once the GPS
    /// stands in a tile: destination = <c>-route_to</c> when given, else the one chosen last in the map (PlayerPrefs
    /// <see cref="NavigationService.TripPref"/>), else <see cref="WorldStreamer.routeDestination"/> (default tykocin).
    /// The map UI's destination button goes through <see cref="NavigationService.RequestTrip"/> to <see cref="StartTrip"/>.
    /// </summary>
    public sealed class NavStreamFollower : MonoBehaviour
    {
        public NavigationService nav;
        public CabScreens screens;
        public Transform vehicle;
        [Tooltip("Seconds between checks")] public float intervalS = 0.25f;
        [Tooltip("Metres the truck must be inside the next tile before the GPS switches to it (seam hysteresis, WORKING_VALUE)")]
        public float switchInsideM = 15f;

        float m_T;
        bool[] m_Drawn;            // Ready neighbour set drawn now (index = tile)
        readonly Dictionary<string, NavMapData> m_Maps = new Dictionary<string, NavMapData>();
        readonly List<NavMapData> m_Shifted = new List<NavMapData>();

        public int SwitchCount { get; private set; }
        /// <summary>ADR 0302: start the multi-tile trip automatically (tests switch it off).</summary>
        public bool autoTrip = true;
        bool m_TripTried;
        float m_LogT = -1f;
        /// <summary>ADR 0302 evidence: launch argument <c>-nav_log &lt;s&gt;</c> logs the GPS state every s seconds
        /// ([NAV] status: tile, leg, remaining, ETA, on route) - allocates a log line, so only when asked.</summary>
        public float logEveryS = -1f;
        NavTripsData m_Trips;
        public string CurrentTile => nav != null ? nav.regionId : "";

        public static NavStreamFollower Install(GameObject host, NavigationService nav, CabScreens screens, Transform vehicle)
        {
            if (host == null || nav == null) return null;
            if (!host.TryGetComponent(out NavStreamFollower f)) f = host.AddComponent<NavStreamFollower>();
            f.nav = nav; f.screens = screens; f.vehicle = vehicle;
            var args = System.Environment.GetCommandLineArgs();
            for (int i = 0; i + 1 < args.Length; i++)
                if (args[i] == "-nav_log" && float.TryParse(args[i + 1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float s) && s > 0f)
                    f.logEveryS = s;
            return f;
        }

        void Update()
        {
            m_T -= Time.unscaledDeltaTime;
            if (m_T > 0f) return;
            m_T = intervalS;
            var ws = WorldStreamer.Active;
            if (ws != null && ws.Graph != null && nav != null && vehicle != null) Step(ws);
            if (logEveryS > 0f && nav != null && Time.unscaledTime >= m_LogT)
            {
                m_LogT = Time.unscaledTime + logEveryS;
                var gd = nav.Guidance;
                var t = nav.Trip;
                Debug.Log(string.Format(System.Globalization.CultureInfo.InvariantCulture,
                    "[NAV] status t={0:F0}s tile={1} trip={2} leg={3}/{4} route={5} onRoute={6} remaining={7:F0} m eta={8:F0} s next={9:F0} m street='{10}' pos=({11:F1},{12:F1}) pathV={13}",
                    Time.unscaledTime, nav.regionId, t != null ? t.Id : "-", t != null ? t.Current + 1 : 0, t != null ? t.Legs.Length : 0,
                    gd.HasRoute, gd.OnRoute, gd.RemainingM, gd.RemainingSeconds, gd.Next >= 0 ? gd.NextM : -1f, nav.NameOf(nav.CurrentStreet),
                    nav.Position.x, nav.Position.y, nav.Path != null ? nav.Path.Version : -1));
            }
        }

        /// <summary>One check (public for tests).</summary>
        public void Step(WorldStreamer ws)
        {
            var g = ws.Graph;
            Vector3 p = vehicle.position;
            double x = ws.AnchorX + p.x, y = ws.AnchorY + p.z;
            int cur = g.TileAt(x, y);
            int navTile = g.IndexOf(nav.regionId);
            bool lost = nav.regionFrame == null;
            if (cur >= 0 && cur != navTile && ws.FrameOf(cur) != null &&
                (lost || navTile < 0 || InsideM(g.Tiles[cur], x, y) >= switchInsideM))
            {
                if (Switch(ws, navTile, cur)) navTile = cur;
            }
            else if (lost && navTile >= 0)
            {
                var fr = ws.FrameOf(navTile);
                if (fr != null) { nav.regionFrame = fr; if (screens != null) screens.regionFrame = fr; }
            }
            if (navTile >= 0) UpdateNeighbours(ws, navTile);
            if (!m_TripTried && autoTrip && navTile >= 0 && nav.HasPosition) { m_TripTried = true; AutoStartTrip(ws); }
        }

        // ------------------------------------------------------------------ multi-tile trip (ADR 0302)

        NavTripsData Trips() => m_Trips ??= NavTripsData.LoadDefault();

        void AutoStartTrip(WorldStreamer ws)
        {
            var trips = Trips();
            int n = trips.trips != null ? trips.trips.Length : 0;
            nav.TripIds = new string[n]; nav.TripLabels = new string[n];
            for (int i = 0; i < n; i++) { nav.TripIds[i] = trips.trips[i].id; nav.TripLabels[i] = trips.trips[i].label; }
            nav.RequestTrip = id =>
            {
                if (string.IsNullOrEmpty(id)) { nav.EndTrip(true); return; }
                var w = WorldStreamer.Active;
                if (w != null && StartTrip(w, id)) w.routeDestination = id;   // the route autopilot follows the choice too
            };
            string id = ChooseTrip(System.Environment.GetCommandLineArgs(), PlayerPrefs.GetString(NavigationService.TripPref, ""), ws.routeDestination);
            if (id == null) { Debug.Log("[NAV] trip: none chosen"); return; }
            if (StartTrip(ws, id)) ws.routeDestination = id;
        }

        /// <summary>Trip id to start: <c>-route_to</c> / <c>route_to=</c> given, else the remembered choice ("-" = none →
        /// null), else <paramref name="streamerDestination"/>. Public for tests.</summary>
        public static string ChooseTrip(string[] args, string remembered, string streamerDestination)
        {
            if (args != null)
                foreach (var a in args)
                    if (a == "-route_to" || a == "--route_to" || a.StartsWith("route_to=", System.StringComparison.Ordinal))
                        return RouteLinks.DestinationFromArgs(args);
            if (remembered == "-") return null;
            if (!string.IsNullOrEmpty(remembered)) return remembered;
            return string.IsNullOrEmpty(streamerDestination) ? RouteLinks.DefaultDestination : streamerDestination;
        }

        /// <summary>Starts trip <paramref name="id"/> from the GPS's current tile (allocates: a planning event).</summary>
        public bool StartTrip(WorldStreamer ws, string id)
        {
            var data = Trips().Find(id);
            var g = ws.Graph;
            int cur = g.IndexOf(nav.regionId);
            if (data == null || cur < 0) { Debug.LogWarning($"[NAV] trip '{id}' not started ({(data == null ? "unknown trip" : "GPS tile not in the tile graph")})"); return false; }
            var trip = new NavTrip(data, tid =>
            {
                int i = g.IndexOf(tid);
                return i >= 0 ? (true, g.Tiles[i].anchorX, g.Tiles[i].anchorY) : (false, 0.0, 0.0);
            });
            nav.StartTrip(trip, g.Tiles[cur].anchorX, g.Tiles[cur].anchorY);
            return true;
        }

        /// <summary>Distance [m] of (x, y) inside the tile rectangle (negative = outside).</summary>
        public static double InsideM(TileData t, double x, double y) =>
            System.Math.Min(System.Math.Min(x - t.xmin, t.xmax - x), System.Math.Min(y - t.ymin, t.ymax - y));

        bool Switch(WorldStreamer ws, int from, int to)
        {
            var g = ws.Graph;
            var tt = g.Tiles[to];
            var frame = ws.FrameOf(to);
            Vector2 oldToNew = from >= 0
                ? new Vector2((float)(g.Tiles[from].anchorX - tt.anchorX), (float)(g.Tiles[from].anchorY - tt.anchorY))
                : Vector2.zero;
            if (!nav.SwitchRegion(tt.id, frame, oldToNew)) return false;
            SwitchCount++;
            if (screens != null)
            {
                screens.regionFrame = frame;
                screens.regionId = tt.id;
                screens.NavLayout.Map = MapOf(tt.id);
            }
            m_Drawn = null;   // rebuild the neighbour set in the new frame
            return true;
        }

        NavMapData MapOf(string id)
        {
            if (!m_Maps.TryGetValue(id, out var m)) { m = NavMapData.Load(id); m_Maps[id] = m; }
            return m;
        }

        void UpdateNeighbours(WorldStreamer ws, int cur)
        {
            var g = ws.Graph;
            if (m_Drawn == null || m_Drawn.Length != g.Count) { m_Drawn = new bool[g.Count]; Rebuild(ws, cur); return; }
            for (int i = 0; i < g.Count; i++)
            {
                bool want = i != cur && ws.FrameOf(i) != null;
                if (want != m_Drawn[i]) { Rebuild(ws, cur); return; }
            }
        }

        void Rebuild(WorldStreamer ws, int cur)
        {
            var g = ws.Graph;
            var c = g.Tiles[cur];
            m_Shifted.Clear();
            for (int i = 0; i < g.Count; i++)
            {
                m_Drawn[i] = i != cur && ws.FrameOf(i) != null;
                if (!m_Drawn[i]) continue;
                var m = MapOf(g.Tiles[i].id);
                if (m == null) continue;
                m_Shifted.Add(m.Shifted(new Vector2((float)(g.Tiles[i].anchorX - c.anchorX), (float)(g.Tiles[i].anchorY - c.anchorY))));
            }
            nav.SetNeighbourMaps(m_Shifted);
        }
    }
}
