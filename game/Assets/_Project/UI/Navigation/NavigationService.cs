using System.Globalization;
using Game.Core.Navigation;
using Game.UI.CabDisplays;
using UnityEngine;

namespace Game.UI.Navigation
{
    /// <summary>
    /// The truck's GPS (ADR 0150): routing graph of the region, destination pin, planned route, guidance and automatic
    /// re-planning after leaving the route. One per driving session; the full map, the HUD minimap and the cab navigation
    /// screen read it. Position from the truck transform in the region frame (x = east, z = north, ADR 0003).
    /// - Per frame: tracking (projection, next manoeuvre, off-route timer) - zero GC (EditMode + PlayMode tests).
    /// - Re-plan (A*, pre-allocated buffers, no GC) only when off the route for <see cref="RouteTracker.RerouteHoldS"/>.
    /// - The destination survives a restart / killed process (PlayerPrefs per region, written when it changes).
    /// </summary>
    [DefaultExecutionOrder(90)]
    public sealed class NavigationService : MonoBehaviour
    {
        const string PrefPrefix = "nav.dest.";
        /// <summary>ADR 0302: id of the active multi-tile trip (survives a restart; "-" = none chosen).</summary>
        public const string TripPref = "nav.trip";

        public Transform truck;
        public Rigidbody truckBody;
        [Tooltip("Region root of the navigation data; null = world frame")] public Transform regionFrame;
        public string regionId = "";
        /// <summary>Night palette (dipped beam on); set by the installer from the cab screens.</summary>
        public System.Func<bool> NightSource;

        RouteGraph m_Graph;
        RoutePlanner m_Planner;
        RoutePath m_Path;
        readonly RouteTracker m_Tracker = new RouteTracker();
        NavGuidance m_Guide;
        NavMapData m_Map;
        readonly System.Collections.Generic.List<NavMapData> m_Drawn = new System.Collections.Generic.List<NavMapData>();
        NavMapData[] m_Neighbours = System.Array.Empty<NavMapData>();
        Mesh m_StaticDay, m_StaticNight;
        float m_StreetT;
        ushort m_Street;
        float m_RestoreAt = -1f;
        bool m_TestPose;
        Vector2 m_RestoreGoal;
        NavTrip m_Trip;
        bool m_TripPlanning;

        /// <summary>ADR 0302: EPSG:2180 origin of the current region frame (streaming; 0 without). Set by
        /// <see cref="StartTrip"/>, moved by every <see cref="SwitchRegion"/> (old origin - oldToNew).</summary>
        public double AnchorX, AnchorY;
        /// <summary>ADR 0302: multi-tile trip (route over several streamed tiles) or null.</summary>
        public NavTrip Trip => m_Trip;
        public bool TripPlanning => m_TripPlanning;
        /// <summary>ADR 0302: trips offered in the map UI (ids / labels) and the request to start one (null id = none);
        /// set by the streaming follower (Gameplay), empty without streaming.</summary>
        public string[] TripIds = System.Array.Empty<string>(), TripLabels = System.Array.Empty<string>();
        public System.Action<string> RequestTrip;

        public RouteGraph Graph => m_Graph;
        public NavMapData Map => m_Map;
        /// <summary>The planned route: the multi-tile trip's combined path when a trip is active (ADR 0302).</summary>
        public RoutePath Path => m_Trip != null && m_Trip.Combined != null ? m_Trip.Combined : m_Path;
        public NavGuidance Guidance => m_Guide;
        public bool Ready => m_Graph != null && m_Map != null;
        public bool Night => NightSource != null && NightSource();
        /// <summary>ADR 0300: bumped whenever the static map changes (tile switch, neighbour set); map views re-fetch
        /// <see cref="StaticMap"/> when it differs from the version they baked.</summary>
        public int MapVersion { get; private set; }
        /// <summary>Neighbour maps drawn around the current region (already in its frame).</summary>
        public int NeighbourCount => m_Neighbours.Length;

        public bool HasPin { get; private set; }
        public Vector2 Pin { get; private set; }
        public Vector2 PinOnRoad { get; private set; }
        public ushort PinName { get; private set; }
        public PlanStatus LastStatus { get; private set; } = PlanStatus.Ok;
        /// <summary>Time of the last automatic re-plan (unscaled), for the "new route" note on the banner.</summary>
        public float LastRerouteTime { get; private set; } = -100f;
        public int RerouteCount { get; private set; }
        /// <summary>Wall time of the last plan [ms].</summary>
        public double LastPlanMs { get; private set; }

        public Vector2 Position { get; private set; }
        public float HeadingDeg { get; private set; }
        public float SpeedMs { get; private set; }
        public bool HasPosition { get; private set; }
        /// <summary>Street under the truck (route name when on the route, else nearest road, refreshed twice a second).</summary>
        public ushort CurrentStreet => m_Guide.HasRoute && m_Guide.OnRoute ? m_Guide.CurrentName
            : m_Trip != null ? m_Trip.MapCurrentName(m_Street) : m_Street;

        public static NavigationService Install(GameObject host, Transform truck, Rigidbody body, Transform regionFrame, string regionId)
        {
            if (!host.TryGetComponent(out NavigationService s)) s = host.AddComponent<NavigationService>();
            s.truck = truck; s.truckBody = body; s.regionFrame = regionFrame; s.regionId = regionId ?? "";
            s.Init();
            return s;
        }

        public void Init()
        {
            m_Graph = RouteGraph.Load(regionId);
            m_Map = NavMapData.Load(regionId);
            if (m_Graph == null) { Debug.LogWarning("[NAV] no routing graph for region '" + regionId + "'"); return; }
            m_Planner = new RoutePlanner(m_Graph);
            m_Path = RoutePath.For(m_Graph);
            m_Tracker.Reset();
            Sample(0f);
            // Restore the saved destination once the truck stands at its spawn (the bootstrap places it in Start).
            if (TryLoadDestination(out Vector2 goal)) { m_RestoreGoal = goal; m_RestoreAt = 0.5f; }
            Debug.Log($"[NAV] ready region={regionId} nodes={m_Graph.NodeCount} edges={m_Graph.EdgeCount} restrictions={m_Graph.RestrFrom.Length} map={(m_Map != null)}");
        }

        void OnDestroy()
        {
            DestroyMesh(ref m_StaticDay); DestroyMesh(ref m_StaticNight);
        }

        static void DestroyMesh(ref Mesh m)
        {
            if (m == null) return;
            if (Application.isPlaying) Destroy(m); else DestroyImmediate(m);
            m = null;
        }

        /// <summary>Roads and buildings of the region (+ the resident neighbour tiles, ADR 0300) baked once per palette
        /// (region metres), shared by every map canvas.</summary>
        public Mesh StaticMap(bool night)
        {
            if (m_Map == null) return null;
            ref Mesh m = ref night ? ref m_StaticNight : ref m_StaticDay;
            if (m == null)
            {
                m_Drawn.Clear();
                m_Drawn.Add(m_Map);
                m_Drawn.AddRange(m_Neighbours);
                m = NavLayout.BuildStatic(m_Drawn, night ? DisplayPalette.NavNight : DisplayPalette.NavDay, 1.6f);
            }
            return m;
        }

        /// <summary>
        /// ADR 0300 (streaming): the GPS follows the tile under the truck. Loads the routing graph and the map of
        /// <paramref name="newRegionId"/>, measures the truck in <paramref name="frame"/> (that tile's root: region-local
        /// metres, moved by every origin rebase together with the truck) and keeps the destination when it lies on a road
        /// of the new tile: <paramref name="oldToNew"/> = old region origin - new region origin (EPSG:2180 metres) moves
        /// the pin into the new frame. False (nothing changed) when the tile has no routing graph. Allocates (tile event).
        /// </summary>
        public bool SwitchRegion(string newRegionId, Transform frame, Vector2 oldToNew)
        {
            var g = RouteGraph.Load(newRegionId);
            if (g == null) return false;
            bool hadPin = HasPin && m_Trip == null;
            Vector2 pin = Pin + oldToNew;
            AnchorX -= oldToNew.x; AnchorY -= oldToNew.y;
            m_Graph = g;
            m_Map = NavMapData.Load(newRegionId);
            m_Planner = new RoutePlanner(g);
            m_Path = RoutePath.For(g);
            m_Tracker.Reset();
            m_Guide = default;
            m_Guide.Next = -1;
            HasPin = false;
            m_RestoreAt = -1f;
            regionId = newRegionId;
            regionFrame = frame;
            m_Neighbours = System.Array.Empty<NavMapData>();
            InvalidateStatic();
            Sample(0f);
            string pinNote;
            if (m_Trip != null)
            {
                // ADR 0302: the trip keeps its goal - re-expressed in the new frame, nothing re-planned
                m_Trip.SetCurrent(newRegionId);
                SetTripPin();
                // recomposed in the new frame (off the corridor too: the route stays drawn where it is)
                if (m_Trip.Combined != null) m_Trip.Compose(AnchorX, AnchorY);
                m_Tracker.Update(Path, Position, HeadingDeg, SpeedMs, 0f, ref m_Guide);
                pinNote = m_Trip.Current >= 0
                    ? string.Format(CultureInfo.InvariantCulture, "trip {0} kept (leg {1}/{2}, remaining {3:F0} m, ETA {4:F0} s)",
                        m_Trip.Id, m_Trip.Current + 1, m_Trip.Legs.Length, m_Guide.RemainingM, m_Guide.RemainingSeconds)
                    : "trip " + m_Trip.Id + " kept (tile off the corridor)";
            }
            else
            {
                if (hadPin && SetPin(pin)) PlanToPin();
                pinNote = HasPin ? "kept" : (hadPin ? "dropped (not in this tile)" : "none");
            }
            Debug.Log($"[NAV] region switched to {newRegionId} nodes={g.NodeCount} edges={g.EdgeCount} map={(m_Map != null)} pin={pinNote}");
            return true;
        }

        /// <summary>ADR 0300: neighbour tiles drawn around the current one (each already moved into the current frame,
        /// <see cref="NavMapData.Shifted"/>). Rebuilds the static map on the next <see cref="StaticMap"/> call.</summary>
        public void SetNeighbourMaps(System.Collections.Generic.IReadOnlyList<NavMapData> maps)
        {
            var a = new NavMapData[maps != null ? maps.Count : 0];
            for (int i = 0; i < a.Length; i++) a[i] = maps[i];
            m_Neighbours = a;
            InvalidateStatic();
        }

        void InvalidateStatic()
        {
            DestroyMesh(ref m_StaticDay); DestroyMesh(ref m_StaticNight);
            MapVersion++;
        }

        void Update()
        {
            if (m_Graph == null) return;
            float dt = Time.deltaTime;
            Sample(dt);
            if (m_RestoreAt >= 0f)
            {
                m_RestoreAt -= Time.unscaledDeltaTime;
                if (m_RestoreAt < 0f && HasPosition && m_Trip == null) { SetPin(m_RestoreGoal); PlanToPin(); }
            }
            if (m_TripPlanning) StepTrip();
            m_Tracker.Update(Path, Position, HeadingDeg, SpeedMs, dt, ref m_Guide);
            if (m_Guide.NeedsReroute && HasPin)
            {
                if (m_Trip != null) ReplanTripLeg(); else Replan(true);
                m_Tracker.ClearOffRoute();
            }
            m_StreetT -= Time.unscaledDeltaTime;
            if (m_StreetT <= 0f && HasPosition)
            {
                m_StreetT = 0.5f;
                int e = m_Graph.Snap(Position, 30f, out _, out _, out _);
                m_Street = e >= 0 ? m_Graph.EdgeName[e] : (ushort)0;
            }
        }

        void Sample(float dt)
        {
            if (truck == null) { if (!m_TestPose) HasPosition = false; return; }
            HasPosition = true;
            Vector3 p = regionFrame != null ? regionFrame.InverseTransformPoint(truck.position) : truck.position;
            Vector3 f = regionFrame != null ? regionFrame.InverseTransformDirection(truck.forward) : truck.forward;
            Position = new Vector2(p.x, p.z);
            HeadingDeg = Mathf.Atan2(f.x, f.z) * Mathf.Rad2Deg;
            float v = truckBody != null ? Vector3.Dot(truckBody.linearVelocity, truck.forward) : 0f;
            SpeedMs = dt > 0f ? Mathf.Lerp(SpeedMs, v, 1f - Mathf.Exp(-dt / 0.3f)) : v;
        }

        /// <summary>For tests (ADR 0300): one position sample from the truck transform now.</summary>
        public void SampleForTest() => Sample(0f);

        /// <summary>For tests: replace the routing graph (e.g. a synthetic one with reachability flags, M27).</summary>
        public void SetGraphForTest(RouteGraph g)
        {
            m_Graph = g;
            m_Planner = new RoutePlanner(g);
            m_Path = RoutePath.For(g);
            m_Tracker.Reset();
        }

        /// <summary>For tests and captures: place the truck without a transform.</summary>
        public void SetPoseForTest(Vector2 pos, float headingDeg, float speedMs)
        {
            truck = null; m_TestPose = true; HasPosition = true; Position = pos; HeadingDeg = headingDeg; SpeedMs = speedMs;
            m_Tracker.Update(Path, Position, HeadingDeg, SpeedMs, 0.02f, ref m_Guide);
            int e = m_Graph.Snap(Position, 30f, out _, out _, out _);
            m_Street = e >= 0 ? m_Graph.EdgeName[e] : (ushort)0;
        }

        /// <summary>Tracking step with an explicit pose (tests: zero-GC loop without a scene).</summary>
        public void StepForTest(Vector2 pos, float headingDeg, float speedMs, float dt)
        {
            HasPosition = true; Position = pos; HeadingDeg = headingDeg; SpeedMs = speedMs;
            m_Tracker.Update(Path, Position, HeadingDeg, SpeedMs, dt, ref m_Guide);
        }

        // ------------------------------------------------------------------ destination and route

        /// <summary>Sets the destination pin (region metres); returns false when no road is within reach.
        /// M27: a tap in an off-reach part of the map (outside the main strongly connected component, ADR 0150) snaps
        /// the pin to the nearest node of the main component and reports <see cref="PlanStatus.GoalOffReach"/> -
        /// a clear message instead of a later "Brak dojazdu".</summary>
        public bool SetPin(Vector2 p)
        {
            if (m_Graph == null) return false;
            if (m_Trip != null) EndTrip(false);   // a pin from the map replaces the trip (ADR 0302)
            int any = m_Graph.Snap(p, RoutePlanner.SnapGoalM, out _, out _, out _);
            if (any >= 0 && m_Graph.EdgeNotDestination(any))   // M27 off-reach or ADR 0168 no-return zone
            {
                // Integration r5: a reachable road within the snap radius beats the nearest reachable node.
                int me = m_Graph.Snap(p, RoutePlanner.SnapGoalM, out _, out Vector2 mOn, out _, mainComponentOnly: true);
                if (me >= 0)
                {
                    HasPin = true; Pin = p; PinOnRoad = mOn; PinName = m_Graph.EdgeName[me];
                    LastStatus = PlanStatus.GoalOffReach;
                    return true;
                }
                int n = m_Graph.NearestMainNode(p);
                if (n < 0) { LastStatus = PlanStatus.GoalOffRoad; return false; }
                HasPin = true; Pin = p; PinOnRoad = m_Graph.NodePos[n]; PinName = m_Graph.MainNameAt(n);
                LastStatus = PlanStatus.GoalOffReach;
                return true;
            }
            int e = m_Graph.Snap(p, RoutePlanner.SnapGoalM, out _, out Vector2 on, out _, mainComponentOnly: true);
            if (e < 0) { LastStatus = PlanStatus.GoalOffRoad; return false; }
            HasPin = true; Pin = p; PinOnRoad = on; PinName = m_Graph.EdgeName[e];
            LastStatus = PlanStatus.Ok;
            return true;
        }

        public PlanStatus PlanToPin()
        {
            if (!HasPin || m_Graph == null) return LastStatus = PlanStatus.GoalOffRoad;
            Replan(false);
            if (LastStatus == PlanStatus.Ok) SaveDestination(Pin);
            return LastStatus;
        }

        void Replan(bool automatic)
        {
            long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
            // Plan to the snapped point (M27: a pin redirected to the main component plans to that node, not to the off-reach tap).
            LastStatus = m_Planner.Plan(Position, HasPosition ? HeadingDeg : float.NaN, PinOnRoad, m_Path);
            LastPlanMs = (System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
            if (automatic) { LastRerouteTime = Time.unscaledTime; RerouteCount++; }
            m_Tracker.Update(m_Path, Position, HeadingDeg, SpeedMs, 0f, ref m_Guide);
            if (!automatic || RerouteCount < 20)   // log, but not unbounded while circling off-route
                Debug.Log(string.Format(CultureInfo.InvariantCulture, "[NAV] plan{0} status={1} length={2:F0} m edges={3} manoeuvres={4} expanded={5} {6:F2} ms",
                    automatic ? " (reroute)" : "", LastStatus, m_Path.Length, m_Path.DirectedCount, m_Path.ManCount, m_Planner.LastExpanded, LastPlanMs));
        }

        /// <summary>Removes the route and the pin (and the saved destination).</summary>
        public void ClearRoute()
        {
            if (m_Trip != null) EndTrip(true);
            HasPin = false;
            m_Path?.Clear();
            m_Tracker.Reset();
            m_Guide = default;
            m_Guide.Next = -1;
            LastStatus = PlanStatus.Ok;
            PlayerPrefs.DeleteKey(PrefPrefix + regionId);
        }

        void SaveDestination(Vector2 p)
        {
            PlayerPrefs.SetString(PrefPrefix + regionId, p.x.ToString("R", CultureInfo.InvariantCulture) + ";" + p.y.ToString("R", CultureInfo.InvariantCulture));
            PlayerPrefs.Save();
        }

        bool TryLoadDestination(out Vector2 p)
        {
            p = default;
            string s = PlayerPrefs.GetString(PrefPrefix + regionId, "");
            int k = s.IndexOf(';');
            if (k <= 0) return false;
            if (!float.TryParse(s.Substring(0, k), NumberStyles.Float, CultureInfo.InvariantCulture, out float x)) return false;
            if (!float.TryParse(s.Substring(k + 1), NumberStyles.Float, CultureInfo.InvariantCulture, out float y)) return false;
            p = new Vector2(x, y);
            return true;
        }

        public string NameOf(ushort i) => m_Trip != null ? m_Trip.NameOf(i)
            : m_Graph != null && i < m_Graph.Names.Length ? m_Graph.Names[i] : "";

        // ------------------------------------------------------------------ multi-tile trip (ADR 0302)

        /// <summary>
        /// Starts a trip over several streamed tiles. <paramref name="frameX"/> / <paramref name="frameY"/> = EPSG:2180
        /// origin of the current region frame. The legs are planned incrementally, one per frame (<see cref="Update"/>,
        /// or <see cref="StepTripForTest"/>); the truck's leg first, so the guidance starts at once.
        /// </summary>
        public void StartTrip(NavTrip trip, double frameX, double frameY, bool remember = true)
        {
            if (trip == null) return;
            AnchorX = frameX; AnchorY = frameY;
            m_Trip = trip;
            m_RestoreAt = -1f;
            m_Path?.Clear();
            trip.SetCurrent(regionId);
            SetTripPin();
            m_TripPlanning = !trip.Failed;
            m_Tracker.Reset();
            m_Guide = default; m_Guide.Next = -1;
            if (remember) { PlayerPrefs.SetString(TripPref, trip.Id); PlayerPrefs.Save(); }
            Debug.Log($"[NAV] trip {trip.Id} ({trip.Label}): {trip.Legs.Length} tiles, current {regionId} = leg {trip.Current + 1}{(trip.Failed ? " FAILED " + trip.FailReason : "")}");
        }

        void SetTripPin()
        {
            HasPin = true;
            Pin = PinOnRoad = m_Trip.GoalIn(AnchorX, AnchorY);
            PinName = m_Trip.LabelName;
            LastStatus = PlanStatus.Ok;
        }

        /// <summary>Ends the trip (route and pin gone). <paramref name="forget"/>: also the remembered choice.</summary>
        public void EndTrip(bool forget)
        {
            if (m_Trip == null) return;
            Debug.Log($"[NAV] trip {m_Trip.Id} ended");
            m_Trip = null; m_TripPlanning = false;
            HasPin = false;
            m_Tracker.Reset();
            m_Guide = default; m_Guide.Next = -1;
            if (forget) { PlayerPrefs.SetString(TripPref, "-"); PlayerPrefs.Save(); }
        }

        /// <summary>One incremental planning step (one leg); composes after the truck's leg and at the end.</summary>
        void StepTrip()
        {
            var t = m_Trip;
            int before = t.PlannedCount;
            bool done = t.StepPlan(Position, HasPosition ? HeadingDeg : float.NaN);
            int after = t.PlannedCount;
            if (t.Failed)
            {
                m_TripPlanning = false;
                LastStatus = PlanStatus.NoPath;
                Debug.LogWarning($"[NAV] trip {t.Id} planning failed: {t.FailReason}");
                if (after > 0) t.Compose(AnchorX, AnchorY);
                return;
            }
            if ((before == 0 && after > 0) || done)
            {
                t.Compose(AnchorX, AnchorY);
                m_Tracker.Update(Path, Position, HeadingDeg, SpeedMs, 0f, ref m_Guide);
            }
            if (done)
            {
                m_TripPlanning = false;
                LastPlanMs = t.TotalPlanMs;
                var c = t.Combined;
                Debug.Log(string.Format(CultureInfo.InvariantCulture,
                    "[NAV] trip {0} planned: legs {1}..{2}, length {3:F0} m, ETA {4:F0} s, points {5}, manoeuvres {6}, planning {7:F1} ms over {8} frames (max leg {9:F2} ms), legs over a truck limit {10}",
                    t.Id, t.Current + 1, t.Legs.Length, c != null ? c.Length : 0f, m_Guide.RemainingSeconds,
                    c != null ? c.Count : 0, c != null ? c.ManCount : 0, t.TotalPlanMs, t.StepCount, t.MaxLegMs, t.RelaxedCount));
            }
        }

        /// <summary>Off the route during a trip: re-plan the truck's leg only (one A* in this tile, no allocation) and
        /// recompose. Off the corridor (tile not on the trip) there is nothing to plan in: the route stays drawn.</summary>
        void ReplanTripLeg()
        {
            var t = m_Trip;
            if (t.Current < 0 || m_TripPlanning) return;
            t.PlanLeg(t.Current, Position, HeadingDeg);
            LastPlanMs = t.Legs[t.Current].PlanMs;
            LastRerouteTime = Time.unscaledTime; RerouteCount++;
            if (t.Legs[t.Current].Planned) t.Compose(AnchorX, AnchorY);
            LastStatus = t.Legs[t.Current].Status;
            m_Tracker.Update(Path, Position, HeadingDeg, SpeedMs, 0f, ref m_Guide);
            if (RerouteCount < 20)
                Debug.Log(string.Format(CultureInfo.InvariantCulture, "[NAV] trip reroute in {0}: status={1} remaining={2:F0} m {3:F2} ms",
                    regionId, LastStatus, m_Guide.RemainingM, LastPlanMs));
        }

        /// <summary>For tests: run the incremental trip planning to the end (one leg per call, as Update does).</summary>
        public int StepTripForTest(int maxSteps = 1000)
        {
            int n = 0;
            while (m_TripPlanning && n < maxSteps) { StepTrip(); n++; }
            m_Tracker.Update(Path, Position, HeadingDeg, SpeedMs, 0f, ref m_Guide);
            return n;
        }

        /// <summary>For tests: the re-route path of a trip (as Update does after leaving the route).</summary>
        public void ReplanTripLegForTest() => ReplanTripLeg();
    }
}
