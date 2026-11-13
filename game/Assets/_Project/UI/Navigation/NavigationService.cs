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
        Mesh m_StaticDay, m_StaticNight;
        float m_StreetT;
        ushort m_Street;
        float m_RestoreAt = -1f;
        bool m_TestPose;
        Vector2 m_RestoreGoal;

        public RouteGraph Graph => m_Graph;
        public NavMapData Map => m_Map;
        public RoutePath Path => m_Path;
        public NavGuidance Guidance => m_Guide;
        public bool Ready => m_Graph != null && m_Map != null;
        public bool Night => NightSource != null && NightSource();

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
        public ushort CurrentStreet => m_Guide.HasRoute && m_Guide.OnRoute ? m_Guide.CurrentName : m_Street;

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

        /// <summary>Roads and buildings of the region baked once per palette (region metres), shared by every map canvas.</summary>
        public Mesh StaticMap(bool night)
        {
            if (m_Map == null) return null;
            ref Mesh m = ref night ? ref m_StaticNight : ref m_StaticDay;
            if (m == null) m = NavLayout.BuildStatic(m_Map, night ? DisplayPalette.NavNight : DisplayPalette.NavDay, 1.6f);
            return m;
        }

        void Update()
        {
            if (m_Graph == null) return;
            float dt = Time.deltaTime;
            Sample(dt);
            if (m_RestoreAt >= 0f)
            {
                m_RestoreAt -= Time.unscaledDeltaTime;
                if (m_RestoreAt < 0f && HasPosition) { SetPin(m_RestoreGoal); PlanToPin(); }
            }
            m_Tracker.Update(m_Path, Position, HeadingDeg, SpeedMs, dt, ref m_Guide);
            if (m_Guide.NeedsReroute && HasPin)
            {
                Replan(true);
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
            m_Tracker.Update(m_Path, Position, HeadingDeg, SpeedMs, 0.02f, ref m_Guide);
            int e = m_Graph.Snap(Position, 30f, out _, out _, out _);
            m_Street = e >= 0 ? m_Graph.EdgeName[e] : (ushort)0;
        }

        /// <summary>Tracking step with an explicit pose (tests: zero-GC loop without a scene).</summary>
        public void StepForTest(Vector2 pos, float headingDeg, float speedMs, float dt)
        {
            HasPosition = true; Position = pos; HeadingDeg = headingDeg; SpeedMs = speedMs;
            m_Tracker.Update(m_Path, Position, HeadingDeg, SpeedMs, dt, ref m_Guide);
        }

        // ------------------------------------------------------------------ destination and route

        /// <summary>Sets the destination pin (region metres); returns false when no road is within reach.
        /// M27: a tap in an off-reach part of the map (outside the main strongly connected component, ADR 0150) snaps
        /// the pin to the nearest node of the main component and reports <see cref="PlanStatus.GoalOffReach"/> -
        /// a clear message instead of a later "Brak dojazdu".</summary>
        public bool SetPin(Vector2 p)
        {
            if (m_Graph == null) return false;
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

        public string NameOf(ushort i) => m_Graph != null && i < m_Graph.Names.Length ? m_Graph.Names[i] : "";
    }
}
