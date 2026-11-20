using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using Game.Core;
using UnityEngine;
using UnityEngine.SceneManagement;
using Debug = UnityEngine.Debug;

namespace Game.World.Streaming
{
    /// <summary>
    /// Additive streaming of neighbouring region tiles while driving (ADR 0235). The start scene (World_&lt;id&gt; with the
    /// truck, camera and lighting) is the base; neighbours come as tile scenes (World_&lt;id&gt;_Tile: region root + start
    /// route only, chunks saved inactive, collision cooking deferred, see WorldSceneBuilder.BuildTileScene).
    ///
    /// Per frame (no GC allocations in the steady loop; a tile event - load, activation, unload, origin rebase - allocates
    /// a little once, like Unity's own async load):
    ///  1. every <see cref="decideIntervalS"/> the pure <see cref="StreamingPolicy"/> decides from the vehicle position and
    ///     velocity which tile to load / unload;
    ///  2. a load is <c>SceneManager.LoadSceneAsync(tile, Additive)</c> with <c>allowSceneActivation = false</c> under
    ///     <c>Application.backgroundLoadingPriority = Low</c>; activation is allowed when the load reached 90 %;
    ///  3. on <c>sceneLoaded</c> (after Awake/OnEnable, before the first render) the region root is placed for the current
    ///     world anchor (<see cref="TilePlacement"/>) and the collision bake job is scheduled (worker threads);
    ///  4. chunks are enabled within <see cref="activationBudgetMs"/> per frame, colliders <see cref="collidersPerFrame"/>
    ///     per frame; then the tile is Ready and the seam with each Ready neighbour opens (closures, apron piece and
    ///     far-field sector on that side are disabled). A seam never opens before both tiles are Ready, so a late load
    ///     means a closed road, never a hole;
    ///  5. when the vehicle is <see cref="rebaseInsideM"/> inside a new tile, the world anchor moves to that tile's anchor
    ///     in FixedUpdate: every scene root moves, region roots are re-placed exactly from double, physics transforms are
    ///     synced and <see cref="FloatingOrigin.Moved"/> is raised (camera smoothing, autopilot path, safe poses).
    /// </summary>
    [DefaultExecutionOrder(-950)]
    public sealed class WorldStreamer : MonoBehaviour
    {
        /// <summary>The streamer of the running world scene (null when streaming is off).</summary>
        public static WorldStreamer Active { get; private set; }

        public Transform vehicle;
        public Rigidbody vehicleBody;
        public StreamingSettings settings = new StreamingSettings();
        [Tooltip("Content tier of the tile scenes: \"Low\" (Low + Medium) or \"High\" (RegionScenes)")]
        public string contentTier = RegionScenes.LowTier;
        [Tooltip("Seconds between streaming decisions")] public float decideIntervalS = 0.25f;
        [Tooltip("Main-thread time for enabling chunks of an activating tile per frame [ms] (WORKING_VALUE)")]
        public float activationBudgetMs = 2f;
        [Tooltip("Colliders enabled per frame after the bake (WORKING_VALUE)")] public int collidersPerFrame = 16;
        [Tooltip("The world anchor moves to a tile once the vehicle is this far inside it [m] (WORKING_VALUE)")]
        public float rebaseInsideM = 100f;
        [Tooltip("Resources.UnloadUnusedAssets after an unload at most this often [s] (WORKING_VALUE; hitch measured on device)")]
        public float unloadAssetsMinIntervalS = 20f;
        [Tooltip("Async loading priority while streaming (Low = smallest main-thread slice per frame)")]
        public ThreadPriority loadingPriority = ThreadPriority.Low;

        /// <summary>
        /// Launch-time switch for tests and tools (ADR 0273 §7): non-null overrides the launch argument <c>stream</c>
        /// (streaming is opt-in, <c>stream=1</c>, until measured on Windows and the A16). Reset it after use.
        /// </summary>
        public static bool? EnabledOverride;

        /// <summary>World-space point the safety net would restore the vehicle to (ADR 0273 §8). false = no safe pose yet,
        /// the scene spawn of the start tile would be used.</summary>
        public delegate bool RecoveryPointProvider(out Vector3 worldPosition);

        /// <summary>Set by <see cref="TryInstallFromLaunch"/> (newest safe pose of the safety net's <see cref="SafePoseBuffer"/>
        /// older than its safeMinAge) or by a test. The tile containing the point - or the start tile while there is none - is
        /// pinned: never unloaded, so a reset never lands over a void. Called every decision (0.25 s); must not allocate.</summary>
        public RecoveryPointProvider recoveryPoint;

        /// <summary>Source of tile scenes: player build or region pack (ADR 0273 §3). Set before <see cref="Init"/>.</summary>
        public ITileSceneSource source;

        /// <summary>
        /// Route autopilot path continued across seams (int-stream-s23): when a Ready tile's start route begins within
        /// <see cref="routeJoinM"/> of the path end, that route is appended (the D67 corridor routes chain end to start,
        /// Data/Regions/*/route_start.json). Set by <see cref="TryInstallFromLaunch"/> from the hook's origin listener
        /// (the route driver's Offset); null = no continuation.
        /// </summary>
        public IStreamedRoute routePath;
        [Tooltip("Max horizontal gap between the autopilot path end and a tile route start to chain them [m]")]
        public float routeJoinM = 3f;

        /// <summary>
        /// Destination of the route autopilot across forks of the corridor (stream-gaps-s23): route links
        /// (Resources/WorldStreaming/route_links.json) of another destination are never appended. Launch argument
        /// <c>-route_to tykocin|monki</c> (<see cref="TryInstallFromLaunch"/>); default <see cref="RouteLinks.DefaultDestination"/>.
        /// </summary>
        public string routeDestination = RouteLinks.DefaultDestination;

        /// <summary>Route links bound to <see cref="Graph"/> (set in <see cref="Init"/>; empty when the json is missing).</summary>
        public RouteLinks Links { get; private set; }
        bool[] m_LinkChained;

        public TileGraph Graph { get; private set; }
        public StreamingPolicy Policy { get; private set; }
        /// <summary>World anchor: EPSG:2180 x / y and EVRF2007 height of Unity (0, 0, 0).</summary>
        public double AnchorX => m_Wx;
        public double AnchorY => m_Wy;
        public double AnchorZ => m_Wz;
        /// <summary>Diagnostics: last load / activation times [ms] and counters (log, PlayMode test).</summary>
        public float LastLoadMs { get; private set; }
        public float LastActivationMs { get; private set; }
        public float LastRebaseMs { get; private set; }
        public int LoadCount { get; private set; }
        public int UnloadCount { get; private set; }
        public int RebaseCount { get; private set; }
        /// <summary>Index of the tile of the start scene (the scene spawn lives there).</summary>
        public int StartTile { get; private set; } = -1;

        sealed class Tile
        {
            public int index;
            public string sceneName;
            public bool fromStartScene;
            public Scene scene;
            public AsyncOperation op;
            public WorldRegionRoot root;
            public WorldBoundary boundary;
            public WorldCollisionCooker cooker;
            public WorldInstances instances;
            public Transform route;
            public WorldRoute routeComp;
            public bool routeChained;   // its route was appended to the autopilot path (sticky: never appended twice)
            public GameObject[] chunks;
            public int nextChunk;
            public float loadStart, activateStart;
            public Vector2 min, max;
            public TileSide openSides;
            public TileSide coveredSides;   // sides with a Ready neighbour, whatever this tile's own state (ADR 0308)
            public int readyCorners;        // ready diagonal neighbours (EdgeSides.CornerBit mask, ADR 0308)
            public bool apronCorners;       // the scene has Apron_NE / SE / SW / NW pieces
            // edge objects (ADR 0169 closures, ADR 0085 far field, apron)
            public GameObject edgeRoot; public GameObject[] closures; public TileSide[] closureSide; public float[] closureE, closureN; public bool[] closureOpen;
            public GameObject[] groups; public Vector4[] groupBounds;   // (minE, minN, maxE, maxN)
            public GameObject[] farSectors; public TileSide[] farSide;
            public GameObject apronWhole; public GameObject[] apronPieces; public TileSide[] apronSide;
            public bool warnedApron;
            public bool acquiring, leased;   // pack lease taken through ITileSceneSource (ADR 0273)
        }

        Tile[] m_Tiles;
        // Outer-edge buffers of the safety-net query (ADR 0273 §10 pkt 5): filled per call, allocated once in Init.
        TileState[] m_EdgeState; EdgeRect[] m_EdgeDrivable, m_EdgeTile; bool m_Decided;
        double m_Wx, m_Wy, m_Wz;
        readonly StreamCommand[] m_Cmd = new StreamCommand[8];
        readonly List<GameObject> m_Roots = new List<GameObject>(64);
        readonly List<Rigidbody> m_Bodies = new List<Rigidbody>(32);
        readonly List<Vector3> m_BodyPos = new List<Vector3>(32);
        readonly Stopwatch m_Clock = new Stopwatch();
        float m_NextDecide, m_LastUnloadAssets = -1000f;
        bool m_UnloadAssetsPending, m_RebasePending;
        AsyncOperation m_UnloadAssetsOp;
        double m_UnloadAssetsStart, m_LastUpdateReal = -1;
        int m_LastGc0, m_LastGc1, m_LastGc2;
        int m_RebaseTile = -1;
        ThreadPriority m_PrevPriority;

        // ------------------------------------------------------------------ install

        /// <summary>
        /// Adds the streamer to <paramref name="host"/> when the start region is in the tile graph and at least one
        /// neighbour tile scene is in the build (else streaming stays off and the region behaves as before: closed edges).
        /// </summary>
        public static WorldStreamer TryInstall(GameObject host, WorldRegionRoot start, Transform vehicle, Rigidbody body, string contentTier) =>
            TryInstall(host, start, vehicle, body, contentTier, StreamingSettings.BudgetForTier(Game.Rendering.QualityTiers.Current, !Application.isMobilePlatform), null);

        /// <summary>As above with the world memory budget [MB] and the tile source (null = player build,
        /// <see cref="BuildTileSource"/>; a region-pack source is a future implementation of <see cref="ITileSceneSource"/>).</summary>
        public static WorldStreamer TryInstall(GameObject host, WorldRegionRoot start, Transform vehicle, Rigidbody body, string contentTier,
                                               float memoryBudgetMB, ITileSceneSource tileSource)
        {
            if (host == null || start == null) return null;
            var graph = TileGraph.LoadDefault();
            if (graph == null) { Debug.LogWarning("[STREAM] off: Resources/" + TileGraph.ResourcePath + " missing"); return null; }
            int idx = graph.IndexOf(start.regionId);
            if (idx < 0) { Debug.Log($"[STREAM] off: region {start.regionId} not in the tile graph"); return null; }
            var src = tileSource ?? new BuildTileSource();
            int available = 0, fromPacks = 0;
            foreach (int j in graph.Neighbors[idx])
            {
                string id = graph.Tiles[j].id;
                if (!src.IsAvailable(id, contentTier)) continue;
                available++;
                if (src.FromPack(id, contentTier)) fromPacks++;
            }
            if (available == 0)
            {
                Debug.Log($"[STREAM] off: no neighbour tile scene of {start.regionId} in the build or in installed packs (tier {contentTier}; build with -Regions ... and scripts/import-region.ps1)");
                return null;
            }
            var s = host.AddComponent<WorldStreamer>();
            s.vehicle = vehicle;
            s.vehicleBody = body;
            s.contentTier = contentTier;
            s.source = src;
            s.settings.highContent = contentTier == RegionScenes.HighTier;
            s.settings.memoryBudgetMB = memoryBudgetMB;
            s.Init(graph, idx, start);
            Debug.Log($"[STREAM] on: start {start.regionId}, {available}/{graph.Neighbors[idx].Length} neighbour tile scenes available ({fromPacks} from packs), " +
                      $"load radius {s.settings.BaseLoadRadiusM:F0} m, unload +{s.settings.hysteresisM:F0} m, max {s.settings.maxTiles} tiles, " +
                      $"budget {s.settings.memoryBudgetMB:F0} MB ({(s.settings.highContent ? "High" : "Low")} content, {(Application.isMobilePlatform ? "phone" : "desktop")})");
            return s;
        }

        /// <summary>
        /// The single hook of the driving scene (ADR 0273 §10, <c>DrivingLabBootstrap.Start</c>, one statement): installs the
        /// streamer when requested by <see cref="EnabledOverride"/>, <c>stream=1</c>, or a desktop start whose tile graph
        /// metadata requires neighbour context without an explicit stream argument, and
        /// the start region has an available neighbour tile scene; otherwise returns null and the scene is exactly as before
        /// (closed region edge). Everything the bootstrap used to wire by hand is done here, so Game.Gameplay keeps one line:
        /// <list type="bullet">
        /// <item>content tier and memory budget from <see cref="StreamingContentChoice"/> (D44: desktop = PC quality tier,
        /// phone = start scene name <c>_High</c>);</item>
        /// <item>pinned recovery tile from the safety net's <paramref name="safePoses"/> (ADR 0273 §8), and the same buffer
        /// moved on every origin rebase (the safety net itself does not listen to <see cref="FloatingOrigin.Moved"/>);</item>
        /// <item><paramref name="onOriginMoved"/> (route autopilot path) subscribed to <see cref="FloatingOrigin.Moved"/> for the
        /// streamer's lifetime;</item>
        /// <item>the start region's <see cref="WorldBoundary"/> rectangle widened to the union of the available tiles
        /// (<see cref="TileGraph.LocalUnionBounds"/>) BEFORE the safety net reads it in its Start, so an open seam is not
        /// "out of bounds" (see ADR 0273 §10 for the exact edge semantics and the follow-up for WorldSafetyNet).</item>
        /// </list>
        /// Allocates once (component, delegates, graph); nothing per frame.
        /// </summary>
        public static WorldStreamer TryInstallFromLaunch(GameObject host, WorldRegionRoot start, Transform vehicle, Rigidbody body,
            string streamArgument, SafePoseBuffer safePoses, float safeMinAge, System.Action<Vector3> onOriginMoved)
        {
            if (!IsRequested(streamArgument, start != null ? start.regionId : null, !Application.isMobilePlatform)) return null;
            if (host == null || start == null || vehicle == null) return null;
            // D44 (ADR 0273 §6 dopisek): on desktop the PC quality tier picks the content (High / Ultra -> _High_Tile), not the
            // start scene name; phones unchanged. Explicit Low fallback when no High tile scene is available.
            var content = ChooseContentForLaunch(start);
            var s = TryInstall(host, start, vehicle, body, content.contentTier, content.budgetMB, null);
            if (s == null) return null;
            s.UseSafePoses(safePoses, safeMinAge);
            s.AddOriginListener(onOriginMoved);
            s.routePath = onOriginMoved?.Target as IStreamedRoute;   // the hook passes RouteDriver.Offset
            s.m_Tiles[s.StartTile].routeChained = true;               // the start route already is the autopilot path
            s.routeDestination = RouteLinks.DestinationFromArgs(System.Environment.GetCommandLineArgs());
            s.WidenStartBoundary(start);
            return s;
        }

        /// <summary>
        /// Content tier and budget of a launch-time install (D44, <see cref="StreamingContentChoice"/>): quality tier now
        /// (GameBootstrap applied -tier / saved choice / PC hardware default before the world scene), start scene tier and
        /// whether a neighbour's High tile scene is in the build. Logs one <c>[STREAM] content</c> line with the tier and where
        /// it came from (a saved explicit choice wins over the hardware default, ADR 0269/0270). Install time only.
        /// </summary>
        static StreamingContent ChooseContentForLaunch(WorldRegionRoot start)
        {
            bool desktop = !Application.isMobilePlatform;
            string quality = Game.Rendering.QualityTiers.Current;
            bool startHigh = StreamingContentChoice.IsHighScene(start.gameObject.scene.name);
            // Review #168 P1-1/P1-2: High only when it covers every tile available in Low (start region included).
            string highMissing = null;
            bool highTiles = desktop && StreamingContentChoice.HighCoversLow(TileGraph.LoadDefault(), start.regionId, new BuildTileSource(), out highMissing);
            var c = StreamingContentChoice.Choose(desktop, quality, startHigh, highTiles, highMissing);
            string saved = Game.Rendering.QualityTiers.SavedTier;
            string origin = string.IsNullOrEmpty(saved) ? "no saved choice (launch -tier or PC hardware default)"
                : string.Equals(saved, quality, System.StringComparison.OrdinalIgnoreCase) ? "saved choice " + saved + " (menu / PC settings)"
                : "launch -tier (saved choice " + saved + ")";
            string line = $"[STREAM] content {c.contentTier}, budget {c.budgetMB:F0} MB: {c.reason}; quality tier {quality} from {origin}, start scene {start.gameObject.scene.name}";
            if (c.highFallback) Debug.LogWarning(line); else Debug.Log(line);
            return c;
        }

        /// <summary>Explicit switch / override, with the authored desktop default when no argument was supplied.</summary>
        public static bool IsRequested(string streamArgument, string region = null, bool desktop = false) =>
            EdgeClosureRules.StreamingRequested(streamArgument, region, desktop, EnabledOverride,
                desktop && string.IsNullOrEmpty(streamArgument) && !EnabledOverride.HasValue ? TileGraph.LoadDefault() : null);

        SafePoseBuffer m_SafePoses;
        float m_SafeMinAge;
        RecoveryPointProvider m_SafePoseProvider;   // cached: no allocation per decision
        System.Action<Vector3> m_OriginListener;

        /// <summary>Pins the tile of the newest safe pose older than <paramref name="minAge"/> and moves the buffer on rebase.</summary>
        public void UseSafePoses(SafePoseBuffer poses, float minAge)
        {
            m_SafePoses = poses;
            m_SafeMinAge = minAge;
            if (poses == null) return;
            if (m_SafePoseProvider == null) m_SafePoseProvider = NewestSafePose;
            recoveryPoint = m_SafePoseProvider;
        }

        bool NewestSafePose(out Vector3 worldPosition)
        {
            if (m_SafePoses != null && m_SafePoses.TryGet(Time.time, m_SafeMinAge, out var pose)) { worldPosition = pose.position; return true; }
            worldPosition = default;
            return false;
        }

        /// <summary>Subscribes <paramref name="listener"/> to <see cref="FloatingOrigin.Moved"/> until this streamer is destroyed.</summary>
        public void AddOriginListener(System.Action<Vector3> listener)
        {
            if (listener == null) return;
            if (m_OriginListener != null) FloatingOrigin.Moved -= m_OriginListener;
            m_OriginListener = listener;
            FloatingOrigin.Moved += m_OriginListener;
        }

        /// <summary>Unsubscribes the listener of <see cref="AddOriginListener"/> (OnDestroy; tests).</summary>
        public void RemoveOriginListener()
        {
            if (m_OriginListener != null) FloatingOrigin.Moved -= m_OriginListener;
            m_OriginListener = null;
        }

        /// <summary>
        /// Widens the start region's drivable rectangle (<see cref="WorldBoundary.minEN"/>/<see cref="WorldBoundary.maxEN"/>,
        /// region-local) to the union of the start tile and every available tile (ADR 0273 §10). The streamer's own tile
        /// rectangles were taken in <see cref="Init"/> and are not affected.
        /// </summary>
        public bool WidenStartBoundary(WorldRegionRoot start)
        {
            if (start == null || Graph == null || StartTile < 0) return false;
            var b = start.GetComponent<WorldBoundary>();
            if (b == null) b = start.gameObject.AddComponent<WorldBoundary>();
            var include = new bool[Graph.Count];
            int n = 0;
            for (int i = 0; i < include.Length; i++)
            {
                include[i] = i == StartTile || !Policy.IsUnavailable(i);   // unavailable = not in the build: never loads
                if (include[i]) n++;   // diagnostics: available tiles (the union takes those connected to the start)
            }
            if (!Graph.LocalUnionBounds(StartTile, include, out double minE, out double minN, out double maxE, out double maxN, withOrigin: false)) return false;
            // The other tiles' rectangles shrunk by the start tile's own inset (tile rectangle -> drivable rectangle, per
            // side), so a side without a neighbour keeps exactly the drivable edge of the import.
            var st = m_Tiles[StartTile];
            var td = Graph.Tiles[StartTile];
            float inW = Mathf.Max(0f, st.min.x - (float)(td.xmin - td.anchorX)), inS = Mathf.Max(0f, st.min.y - (float)(td.ymin - td.anchorY));
            float inE = Mathf.Max(0f, (float)(td.xmax - td.anchorX) - st.max.x), inN = Mathf.Max(0f, (float)(td.ymax - td.anchorY) - st.max.y);
            var min = new Vector2(Mathf.Min(st.min.x, (float)minE + inW), Mathf.Min(st.min.y, (float)minN + inS));
            var max = new Vector2(Mathf.Max(st.max.x, (float)maxE - inE), Mathf.Max(st.max.y, (float)maxN - inN));
            b.minEN = min;
            b.maxEN = max;
            Debug.Log(string.Format(CultureInfo.InvariantCulture,
                "[STREAM] safety-net rectangle of {0} widened to the union of {1} tiles: E {2:F0}..{3:F0} N {4:F0}..{5:F0} m (region-local; ADR 0273 §10)",
                Graph.Tiles[StartTile].id, n, min.x, max.x, min.y, max.y));
            return true;
        }

        /// <summary>Initialises with the graph and the start tile (public for tests that build a streamer by hand).</summary>
        public void Init(TileGraph graph, int startTile, WorldRegionRoot start)
        {
            Graph = graph;
            if (source == null) source = new BuildTileSource();
            Policy = new StreamingPolicy(graph, settings);
            StartTile = startTile;
            m_Tiles = new Tile[graph.Count];
            m_EdgeState = new TileState[graph.Count]; m_EdgeDrivable = new EdgeRect[graph.Count]; m_EdgeTile = new EdgeRect[graph.Count];
            for (int i = 0; i < m_Tiles.Length; i++)
                m_Tiles[i] = new Tile { index = i, sceneName = RegionScenes.TileSceneNameFor(graph.Tiles[i].id, contentTier) };
            // World anchor of the start scene as imported (root at (0, -Az, 0) - originShift).
            m_Wx = start.anchorX + start.originShift.x;
            m_Wy = start.anchorY + start.originShift.z;
            m_Wz = start.anchorZ + start.originShift.y;
            var t = m_Tiles[startTile];
            t.fromStartScene = true;
            t.scene = start.gameObject.scene;
            Register(t, start, FindStartRoute(start.gameObject.scene));
            t.nextChunk = t.chunks.Length;   // already active
            Policy.InitResident(startTile);
            for (int i = 0; i < m_Tiles.Length; i++)
                if (i != startTile && !source.IsAvailable(graph.Tiles[i].id, contentTier)) Policy.SetUnavailable(i);
            Policy.SetPinned(startTile);
            Place(t);
            SetRouteLinks(RouteLinks.LoadDefault(graph));
        }

        /// <summary>Route links to continue the autopilot with (Init loads the shipped ones; tests replace them after Init).</summary>
        public void SetRouteLinks(RouteLinks links)
        {
            Links = links;
            m_LinkChained = new bool[links != null ? links.Count : 0];
        }

        /// <summary>Static visual QA: adopt an already loaded tile and apply the player's seam rules.
        /// Does not start loading or bypass runtime activation/collision readiness.</summary>
        public void AdoptVisualQaTile(WorldRegionRoot root)
        {
            if (Application.isPlaying) throw new System.InvalidOperationException("Static QA adoption is edit-mode only");
            int i = root != null ? Graph.IndexOf(root.regionId) : -1;
            if (i < 0 || i == StartTile || m_Tiles[i].root != null)
                throw new System.ArgumentException("QA tile must be a new region in the streaming graph");
            var t = m_Tiles[i];
            t.scene = root.gameObject.scene;
            Register(t, root, FindStartRoute(t.scene));
            Place(t);
            foreach (var chunk in t.chunks) chunk.SetActive(true);
            t.nextChunk = t.chunks.Length;
            if (t.cooker != null) t.cooker.Cook();
            if (t.instances != null) t.instances.enabled = true;
            Physics.SyncTransforms();
            Policy.SetUnavailable(i, false);
            Policy.SetState(i, TileState.Ready);
            RefreshEdgesAround(i);
            if (t.edgeRoot != null) t.edgeRoot.SetActive(true);
        }

        void OnEnable()
        {
            Active = this;
            SceneManager.sceneLoaded += OnSceneLoaded;
            m_PrevPriority = Application.backgroundLoadingPriority;
            Application.backgroundLoadingPriority = loadingPriority;
        }

        void OnDisable()
        {
            SceneManager.sceneLoaded -= OnSceneLoaded;
            Application.backgroundLoadingPriority = m_PrevPriority;
            if (Active == this) Active = null;
        }

        Transform FindStartRoute(Scene scene)
        {
            scene.GetRootGameObjects(m_Roots);
            foreach (var go in m_Roots) if (go.TryGetComponent(out WorldRoute _)) return go.transform;
            return null;
        }

        // ------------------------------------------------------------------ frame loop

        void Update()
        {
            if (Policy == null || vehicle == null) return;
            LogUpdateGap();
            ProgressLoads();
            ProgressActivation();
            ProgressUnloads();
            // UnloadUnusedAssets is an async operation too. Do not enqueue a new scene load/unload behind it.
            if (m_UnloadAssetsOp != null) return;
            if (Time.unscaledTime >= m_NextDecide)
            {
                m_NextDecide = Time.unscaledTime + decideIntervalS;
                Decide();
            }
        }

        void LogUpdateGap()
        {
            double now = Time.realtimeSinceStartupAsDouble;
            int gc0 = System.GC.CollectionCount(0), gc1 = System.GC.CollectionCount(1), gc2 = System.GC.CollectionCount(2);
            if (m_LastUpdateReal >= 0 && now - m_LastUpdateReal >= 1.0)
            {
                int loading = 0, activating = 0, unloading = 0;
                for (int i = 0; i < m_Tiles.Length; i++)
                {
                    var s = Policy.StateOf(i);
                    if (s == TileState.Loading) loading++;
                    else if (s == TileState.Activating) activating++;
                    else if (s == TileState.Unloading) unloading++;
                }
                Debug.LogWarning(string.Format(CultureInfo.InvariantCulture,
                    "[STREAM] update gap t={0:F3}s gap={1:F0}ms focused={2} background={3} loading={4} activating={5} unloading={6} cleanup={7} gcDelta={8}/{9}/{10}",
                    now, (now - m_LastUpdateReal) * 1000.0, Application.isFocused, Application.runInBackground,
                    loading, activating, unloading, m_UnloadAssetsOp != null,
                    gc0 - m_LastGc0, gc1 - m_LastGc1, gc2 - m_LastGc2));
            }
            m_LastUpdateReal = now;
            m_LastGc0 = gc0; m_LastGc1 = gc1; m_LastGc2 = gc2;
        }

        void OnApplicationFocus(bool focused) => LogLifecycle("focus", focused);
        void OnApplicationPause(bool paused) => LogLifecycle("pause", paused);

        void LogLifecycle(string kind, bool value)
        {
            if (Policy == null) return;
            Debug.Log(string.Format(CultureInfo.InvariantCulture,
                "[STREAM] {0}={1} t={2:F3}s background={3} gc={4}/{5}/{6}", kind, value,
                Time.realtimeSinceStartupAsDouble, Application.runInBackground,
                System.GC.CollectionCount(0), System.GC.CollectionCount(1), System.GC.CollectionCount(2)));
        }

        void FixedUpdate()
        {
            if (m_RebasePending) Rebase(m_RebaseTile);
        }

        void Decide()
        {
            Vector3 p = vehicle.position;
            Vector3 v = vehicleBody != null ? vehicleBody.linearVelocity : Vector3.zero;
            double x = m_Wx + p.x, y = m_Wy + p.z;
            UpdatePin();
            int n = Policy.Decide(x, y, v.x, v.z, m_Cmd);
            m_Decided = true;
            for (int k = 0; k < n; k++)
            {
                if (m_Cmd[k].op == StreamOp.Load) BeginLoad(m_Tiles[m_Cmd[k].tile]);
                else BeginUnload(m_Tiles[m_Cmd[k].tile]);
            }
            if (n > 0 && Policy.OverBudget)
                Debug.LogWarning(string.Format(CultureInfo.InvariantCulture, "[STREAM] over budget: resident {0:F0} MB (ESTIMATED) > {1:F0} MB, loading the tile ahead anyway (ADR 0235 §4)",
                    Policy.ResidentMemoryMB(), settings.memoryBudgetMB));
            int cur = Policy.Current;
            if (!m_RebasePending && cur >= 0 && m_Tiles[cur].root != null && Policy.StateOf(cur) == TileState.Ready &&
                TilePlacement.ShouldRebase(Graph, cur, x, y, m_Wx, m_Wy, rebaseInsideM))
            {
                m_RebasePending = true;
                m_RebaseTile = cur;
            }
            ContinueRoute();
        }

        /// <summary>
        /// Appends the start route of every Ready tile that begins at the autopilot path end (chained, so a tile that became
        /// Ready earlier is picked up after the one before it), or a route link of the chosen destination
        /// (<see cref="routeDestination"/>) whose tile is Ready and whose first point meets the path end. A link with
        /// <c>replacesRoute</c> = tile X is appended instead of X's start route (same first point; e.g. the knyszyn control
        /// route ends at Rynek, the Tykocin link leaves the roundabout on DW671). No allocation unless a route is appended.
        /// </summary>
        void ContinueRoute()
        {
            if (routePath == null || !routePath.TryGetPathEnd(out Vector3 end)) return;
            float join2 = routeJoinM * routeJoinM;
            for (int guard = 0; guard < m_Tiles.Length + (Links != null ? Links.Count : 0); guard++)
            {
                int link = FindLinkAt(end, join2);
                if (link >= 0)
                {
                    m_LinkChained[link] = true;
                    int rt = Links.ReplacesTile[link];
                    if (rt >= 0) m_Tiles[rt].routeChained = true;   // its start route is not appended any more
                    routePath.AppendPath(Links.WorldPoints(link, Graph, m_Wx, m_Wy), Links.Links[link].maxspeedKmh);
                    Debug.Log(string.Format(CultureInfo.InvariantCulture, "[STREAM] route continued by link {0} in {1} (to {2}): +{3:F0} m",
                        Links.Links[link].id, Links.Links[link].tile, routeDestination, Links.Links[link].lengthM));
                    if (!routePath.TryGetPathEnd(out end)) return;
                    continue;
                }
                int hit = -1;
                for (int i = 0; i < m_Tiles.Length; i++)
                {
                    var t = m_Tiles[i];
                    if (t.routeChained || t.routeComp == null || t.route == null || Policy.StateOf(i) != TileState.Ready) continue;
                    if (Links != null && Links.IsRouteReplaced(i, routeDestination)) continue;
                    var pts = t.routeComp.points;
                    if (pts == null || pts.Length < 2) continue;
                    Vector3 a = t.route.TransformPoint(pts[0]);
                    float dx = a.x - end.x, dz = a.z - end.z;
                    if (dx * dx + dz * dz <= join2) { hit = i; break; }
                }
                if (hit < 0) return;
                var h = m_Tiles[hit];
                h.routeChained = true;
                routePath.AppendPath(h.routeComp.WorldPoints(), h.routeComp.speedLimitsKmh);
                Debug.Log(string.Format(CultureInfo.InvariantCulture, "[STREAM] route continued into {0}: +{1:F0} m", Graph.Tiles[hit].id, h.routeComp.Length));
                if (!routePath.TryGetPathEnd(out end)) return;
            }
        }

        /// <summary>First not yet appended link of the chosen destination whose tile is Ready and whose first point is within
        /// sqrt(<paramref name="join2"/>) of <paramref name="end"/>; -1 = none. No allocation.</summary>
        int FindLinkAt(Vector3 end, float join2)
        {
            if (Links == null || m_LinkChained == null) return -1;
            for (int i = 0; i < Links.Count; i++)
            {
                int ti = Links.TileOf[i];
                if (m_LinkChained[i] || ti < 0 || Links.Links[i].e.Length < 2 || !Links.Applies(i, routeDestination)) continue;
                if (Policy.StateOf(ti) != TileState.Ready) continue;
                Vector3 a = Links.WorldPoint(i, 0, Graph, m_Wx, m_Wy);
                float dx = a.x - end.x, dz = a.z - end.z;
                if (dx * dx + dz * dz <= join2) return i;
            }
            return -1;
        }

        int m_LoggedPin = -2;

        /// <summary>ADR 0273 §8: pin the tile of the point the safety net would restore to (no allocation).</summary>
        void UpdatePin()
        {
            int pin = StartTile;
            bool safe = false;
            if (recoveryPoint != null && recoveryPoint(out Vector3 rp))
            {
                int t = Graph.TileAt(m_Wx + rp.x, m_Wy + rp.z);
                if (t >= 0) { pin = t; safe = true; }
            }
            Policy.SetPinned(pin);
            if (pin != m_LoggedPin)
            {
                m_LoggedPin = pin;
                if (pin >= 0) Debug.Log($"[STREAM] pinned {Graph.Tiles[pin].id} ({(safe ? "newest safe pose" : "start tile: no safe pose yet")})");
            }
        }

        void BeginLoad(Tile t)
        {
            string region = Graph.Tiles[t.index].id;
            if (source.FromPack(region, contentTier))
            {
                // Pack: take a lease (verify + load the bundles) first; the policy keeps the tile Loading meanwhile.
                t.acquiring = true;
                t.loadStart = Time.realtimeSinceStartup;
                StartCoroutine(AcquireThenLoad(t, region));
                return;
            }
            StartLoad(t);
        }

        IEnumerator AcquireThenLoad(Tile t, string region)
        {
            bool ok = false;
            yield return source.Acquire(region, contentTier, r => ok = r);
            t.acquiring = false;
            if (!ok)
            {
                Debug.LogWarning($"[STREAM] {t.sceneName}: pack not usable (verify / load / no tile scene): seam stays closed");
                MarkMissing(t.index);
                yield break;
            }
            t.leased = true;
            if (Policy.StateOf(t.index) != TileState.Loading) { ReleaseLease(t); yield break; }
            Debug.Log(string.Format(CultureInfo.InvariantCulture, "[STREAM] pack {0}/{1} acquired in {2:F0} ms", region, contentTier,
                (Time.realtimeSinceStartup - t.loadStart) * 1000f));
            StartLoad(t);
        }

        void ReleaseLease(Tile t)
        {
            if (!t.leased) return;
            t.leased = false;
            source.Release(Graph.Tiles[t.index].id, contentTier);
        }

        void StartLoad(Tile t)
        {
            if (!Application.CanStreamedLevelBeLoaded(t.sceneName))
            {
                // Not in this APK: stay Unloaded; the seam stays closed (the road ends at the closure as before).
                Debug.LogWarning($"[STREAM] {t.sceneName} not in the build: seam stays closed");
                ReleaseLease(t);
                MarkMissing(t.index);
                return;
            }
            if (!t.leased) t.loadStart = Time.realtimeSinceStartup;   // a pack load counts from the start of its Acquire
            t.op = SceneManager.LoadSceneAsync(t.sceneName, LoadSceneMode.Additive);
            if (t.op == null) { ReleaseLease(t); MarkMissing(t.index); return; }
            t.op.allowSceneActivation = false;
            LoadCount++;
            Debug.Log($"[STREAM] load {t.sceneName} (resident {Policy.ResidentCount()} tiles)");
        }

        void MarkMissing(int tile)
        {
            // Never asked again: the policy skips unavailable tiles; the seam with it stays closed.
            Policy.SetState(tile, TileState.Unloaded);
            Policy.SetUnavailable(tile);
        }

        void ProgressLoads()
        {
            for (int i = 0; i < m_Tiles.Length; i++)
            {
                var t = m_Tiles[i];
                if (t.op == null || Policy.StateOf(i) != TileState.Loading) continue;
                // One activation at a time and never while another tile is still enabling its chunks.
                if (!t.op.allowSceneActivation && t.op.progress >= 0.9f && !AnyActivating())
                {
                    t.op.allowSceneActivation = true;
                    LastLoadMs = (Time.realtimeSinceStartup - t.loadStart) * 1000f;
                }
            }
        }

        bool AnyActivating()
        {
            for (int i = 0; i < m_Tiles.Length; i++) if (Policy.StateOf(i) == TileState.Activating) return true;
            return false;
        }

        void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            if (mode != LoadSceneMode.Additive || m_Tiles == null) return;
            for (int i = 0; i < m_Tiles.Length; i++)
            {
                var t = m_Tiles[i];
                if (t.sceneName != scene.name || Policy.StateOf(i) != TileState.Loading) continue;
                t.scene = scene;
                t.op = null;
                WorldRegionRoot root = null;
                Transform route = null;
                scene.GetRootGameObjects(m_Roots);
                foreach (var go in m_Roots)
                {
                    if (root == null && go.TryGetComponent(out WorldRegionRoot r)) root = r;
                    else if (route == null && go.TryGetComponent(out WorldRoute _)) route = go.transform;
                }
                if (root == null)
                {
                    Debug.LogError($"[STREAM] {scene.name} has no WorldRegionRoot: unloading");
                    Policy.SetState(i, TileState.Unloading);
                    SceneManager.UnloadSceneAsync(scene);
                    return;
                }
                Register(t, root, route);
                if (t.edgeRoot != null) t.edgeRoot.SetActive(false);
                Place(t);   // before the first render of the new scene
                t.activateStart = Time.realtimeSinceStartup;
                if (t.cooker != null) t.cooker.BeginCook();
                Policy.SetState(i, TileState.Activating);
                return;
            }
        }

        void ProgressActivation()
        {
            for (int i = 0; i < m_Tiles.Length; i++)
            {
                if (Policy.StateOf(i) != TileState.Activating) continue;
                var t = m_Tiles[i];
                m_Clock.Restart();
                // At least one chunk per frame, then while the budget lasts.
                while (t.nextChunk < t.chunks.Length)
                {
                    var c = t.chunks[t.nextChunk++];
                    if (c != null) c.SetActive(true);
                    if (m_Clock.Elapsed.TotalMilliseconds >= activationBudgetMs) break;
                }
                bool cooked = t.cooker == null || t.cooker.PollCook(collidersPerFrame);
                if (t.nextChunk < t.chunks.Length || !cooked) return;   // one activating tile at a time
                if (t.instances != null) t.instances.enabled = true;
                Physics.SyncTransforms();
                Policy.SetState(i, TileState.Ready);
                LastActivationMs = (Time.realtimeSinceStartup - t.activateStart) * 1000f;
                float dist = DistanceToTileM(i);
                Debug.Log(string.Format(CultureInfo.InvariantCulture, "[STREAM] ready {0}: load {1:F0} ms, activation {2:F0} ms ({3} chunks), vehicle {4:F0} m from the tile, resident {5} tiles / {6:F0} MB (ESTIMATED)",
                    t.sceneName, LastLoadMs, LastActivationMs, t.chunks.Length, dist, Policy.ResidentCount(), Policy.ResidentMemoryMB()));
                RefreshEdgesAround(i);
                if (t.edgeRoot != null) t.edgeRoot.SetActive(true);
                return;
            }
        }

        void BeginUnload(Tile t)
        {
            int i = t.index;
            // Close the seams of the neighbours first (their closures come back before the geometry goes).
            t.openSides = TileSide.None; t.readyCorners = 0; t.coveredSides = TileSide.None;
            var nb = Graph.Neighbors[i];
            for (int k = 0; k < nb.Length; k++) RefreshEdges(nb[k], i);
            UnloadCount++;
            if (t.fromStartScene)
            {
                // The start scene also holds the truck, camera and lighting: only its region root (and route) go.
                if (t.root != null) Destroy(t.root.gameObject);
                if (t.route != null) Destroy(t.route.gameObject);
                Clear(t);
                Policy.SetState(i, TileState.Unloaded);
                m_UnloadAssetsPending = true;
                Debug.Log($"[STREAM] unload start region {Graph.Tiles[i].id} (root destroyed)");
                return;
            }
            Clear(t);
            t.op = t.scene.IsValid() && t.scene.isLoaded ? SceneManager.UnloadSceneAsync(t.scene) : null;
            if (t.op == null) { Policy.SetState(i, TileState.Unloaded); ReleaseLease(t); }
            Debug.Log($"[STREAM] unload {t.sceneName}");
        }

        void ProgressUnloads()
        {
            if (m_UnloadAssetsOp != null)
            {
                if (!m_UnloadAssetsOp.isDone) return;
                Debug.Log(string.Format(CultureInfo.InvariantCulture,
                    "[STREAM] cleanup done t={0:F3}s wall={1:F1}ms", Time.realtimeSinceStartupAsDouble,
                    (Time.realtimeSinceStartupAsDouble - m_UnloadAssetsStart) * 1000.0));
                m_UnloadAssetsOp = null;
            }
            for (int i = 0; i < m_Tiles.Length; i++)
            {
                var t = m_Tiles[i];
                if (Policy.StateOf(i) != TileState.Unloading) continue;
                if (t.op != null && !t.op.isDone) continue;
                t.op = null;
                Policy.SetState(i, TileState.Unloaded);
                ReleaseLease(t);   // the scene is gone: its pack bundles may go (ref-counted, ADR 0273 §4)
                m_UnloadAssetsPending = true;
            }
            // Scene unload does not free the meshes / textures. Reclaim only after all scene work has finished.
            if (m_UnloadAssetsPending && Time.unscaledTime - m_LastUnloadAssets >= unloadAssetsMinIntervalS && !AnySceneWork())
            {
                m_UnloadAssetsPending = false;
                m_LastUnloadAssets = Time.unscaledTime;
                m_UnloadAssetsStart = Time.realtimeSinceStartupAsDouble;
                Debug.Log(string.Format(CultureInfo.InvariantCulture, "[STREAM] cleanup start t={0:F3}s", m_UnloadAssetsStart));
                m_UnloadAssetsOp = Resources.UnloadUnusedAssets();
            }
        }

        bool AnySceneWork()
        {
            for (int i = 0; i < m_Tiles.Length; i++)
            {
                var s = Policy.StateOf(i);
                if (s == TileState.Loading || s == TileState.Activating || s == TileState.Unloading) return true;
            }
            return false;
        }

        // ------------------------------------------------------------------ placement / floating origin

        void Place(Tile t)
        {
            if (t.root == null) return;
            var d = Graph.Tiles[t.index];
            var p = TilePlacement.For(m_Wx, m_Wy, m_Wz, d);
            var pos = new Vector3(p.posX, p.posY, p.posZ);
            t.root.PlaceAt(pos, new Vector3(p.shiftX, p.shiftY, p.shiftZ));
            // WorldRoute points are region-local with heights above the anchor, relative to a scene root at the origin of
            // the imported scene: (root position) + (0, Az, 0).
            if (t.route != null) t.route.position = pos + new Vector3(0f, (float)d.anchorZ, 0f);
        }

        /// <summary>Moves the world anchor to tile <paramref name="tile"/> (FixedUpdate, before physics).</summary>
        void Rebase(int tile)
        {
            m_RebasePending = false;
            if (tile < 0 || m_Tiles[tile].root == null) return;
            m_Clock.Restart();
            var d = Graph.Tiles[tile];
            TilePlacement.RebaseOffset(m_Wx, m_Wy, d.anchorX, d.anchorY, out float ox, out float oz);
            var offset = new Vector3(ox, 0f, oz);
            m_Wx = d.anchorX; m_Wy = d.anchorY;
            for (int s = 0; s < SceneManager.sceneCount; s++)
            {
                var scene = SceneManager.GetSceneAt(s);
                if (!scene.isLoaded) continue;
                scene.GetRootGameObjects(m_Roots);
                for (int r = 0; r < m_Roots.Count; r++)
                {
                    var go = m_Roots[r];
                    if (IsManaged(go)) continue;
                    if (go.transform is RectTransform) continue;   // screen-space UI
                    // Dynamic bodies: take the physics pose before the move and set it shifted after it, so neither the
                    // interpolated render pose nor the transform sync can put the body back at the old place.
                    go.GetComponentsInChildren(false, m_Bodies);
                    m_BodyPos.Clear();
                    for (int b = 0; b < m_Bodies.Count; b++) m_BodyPos.Add(m_Bodies[b].position);
                    go.transform.position += offset;
                    for (int b = 0; b < m_Bodies.Count; b++)
                        if (!m_Bodies[b].isKinematic) m_Bodies[b].position = m_BodyPos[b] + offset;
                }
            }
            for (int i = 0; i < m_Tiles.Length; i++) if (m_Tiles[i].root != null) Place(m_Tiles[i]);
            Physics.SyncTransforms();
            m_SafePoses?.Offset(offset);   // the safety net's buffer (TryInstallFromLaunch); the net does not listen itself
            FloatingOrigin.Notify(offset);
            RebaseCount++;
            LastRebaseMs = (float)m_Clock.Elapsed.TotalMilliseconds;
            Debug.Log(string.Format(CultureInfo.InvariantCulture, "[STREAM] origin rebase #{0} to {1}: offset ({2:F1}, {3:F1}) m, {4:F2} ms",
                RebaseCount, d.id, ox, oz, LastRebaseMs));
        }

        bool IsManaged(GameObject go)
        {
            for (int i = 0; i < m_Tiles.Length; i++)
            {
                var t = m_Tiles[i];
                if (t.root != null && t.root.gameObject == go) return true;
                if (t.route != null && t.route.gameObject == go) return true;
            }
            return false;
        }

        // ------------------------------------------------------------------ edges

        void Register(Tile t, WorldRegionRoot root, Transform route)
        {
            t.root = root;
            t.route = route;
            t.routeComp = route != null ? route.GetComponent<WorldRoute>() : null;
            t.boundary = root.GetComponent<WorldBoundary>();
            t.cooker = root.GetComponent<WorldCollisionCooker>();
            t.instances = root.GetComponent<WorldInstances>();
            if (t.boundary != null && t.boundary.maxEN.x > t.boundary.minEN.x) { t.min = t.boundary.minEN; t.max = t.boundary.maxEN; }
            else WorldBoundary.TryChunkBounds(root, out t.min, out t.max);
            var chunks = new List<GameObject>();
            Transform edge = null;
            foreach (Transform c in root.transform)
            {
                if (c.name.StartsWith("Chunk_", System.StringComparison.Ordinal)) chunks.Add(c.gameObject);
                else if (c.name == "WorldEdge") edge = c;
            }
            t.chunks = chunks.ToArray();
            t.nextChunk = 0;
            CollectEdge(t, edge);
        }

        void CollectEdge(Tile t, Transform edge)
        {
            var closures = new List<GameObject>(); var cs = new List<TileSide>(); var ce = new List<float>(); var cn = new List<float>();
            var groups = new List<GameObject>(); var gb = new List<Vector4>();
            var far = new List<GameObject>(); var fs = new List<TileSide>();
            var pieces = new List<GameObject>(); var ps = new List<TileSide>();
            t.apronWhole = null;
            t.edgeRoot = edge != null ? edge.gameObject : null;
            if (edge != null)
            {
                var data = t.boundary != null ? t.boundary.closures : System.Array.Empty<WorldBoundary.Closure>();
                foreach (Transform c in edge)
                {
                    string n = c.name;
                    if (n.StartsWith("ClosureGroup_", System.StringComparison.Ordinal))
                    {
                        if (c.TryGetComponent(out MeshFilter mf) && mf.sharedMesh != null)
                        {
                            var b = mf.sharedMesh.bounds;   // region space (WorldEdge has an identity transform under the root)
                            groups.Add(c.gameObject); gb.Add(new Vector4(b.min.x, b.min.z, b.max.x, b.max.z));
                        }
                    }
                    else if (n.StartsWith("Closure_", System.StringComparison.Ordinal))
                    {
                        Vector3 lp = c.localPosition; float heading = c.localEulerAngles.y;
                        TileSide exitSide = TileSide.None;
                        int idx = ParseIndex(n);
                        if (idx >= 0 && idx < data.Length) { lp = data[idx].localPos; heading = data[idx].headingDeg; exitSide = data[idx].exitSide; }
                        closures.Add(c.gameObject); ce.Add(lp.x); cn.Add(lp.z);
                        cs.Add(exitSide != TileSide.None ? exitSide : EdgeSides.ClosureSide(lp.x, lp.z, heading, t.min.x, t.min.y, t.max.x, t.max.y));
                    }
                    else if (n == "Apron") t.apronWhole = c.gameObject;
                    else if (EdgeSides.ApronPieceSide(n) != TileSide.None) { pieces.Add(c.gameObject); ps.Add(EdgeSides.ApronPieceSide(n)); }
                    else if (n == "WorldFarField")
                        foreach (Transform f in c)
                        {
                            var side = EdgeSides.FarSectorSide(f.name);
                            if (side != TileSide.None)
                            {
                                far.Add(f.gameObject); fs.Add(side);
                                // Apply before WorldEdge becomes visible, even with no Ready seams.
                                f.gameObject.SetActive(EdgeSides.FarSectorMayShow(side, Graph.NeighborSides[t.index]));
                            }
                        }
                }
            }
            t.closures = closures.ToArray(); t.closureSide = cs.ToArray(); t.closureE = ce.ToArray(); t.closureN = cn.ToArray();
            t.closureOpen = new bool[t.closures.Length];
            t.groups = groups.ToArray(); t.groupBounds = gb.ToArray();
            t.farSectors = far.ToArray(); t.farSide = fs.ToArray();
            t.apronPieces = pieces.ToArray(); t.apronSide = ps.ToArray();
            t.apronCorners = false;
            for (int i = 0; i < t.apronSide.Length; i++) t.apronCorners |= EdgeSides.CornerBit(t.apronSide[i]) != 0;
            t.openSides = TileSide.None; t.readyCorners = 0; t.coveredSides = TileSide.None;
        }

        static int ParseIndex(string name)
        {
            int v = 0, i = "Closure_".Length, digits = 0;
            for (; i < name.Length && name[i] >= '0' && name[i] <= '9'; i++, digits++) v = v * 10 + (name[i] - '0');
            return digits > 0 ? v : -1;
        }

        static void Clear(Tile t)
        {
            t.edgeRoot = null;
            t.root = null; t.route = null; t.routeComp = null; t.boundary = null; t.cooker = null; t.instances = null;
            t.chunks = System.Array.Empty<GameObject>(); t.nextChunk = 0;
            t.closures = System.Array.Empty<GameObject>(); t.groups = System.Array.Empty<GameObject>();
            t.farSectors = System.Array.Empty<GameObject>(); t.apronPieces = System.Array.Empty<GameObject>(); t.apronWhole = null;
            t.openSides = TileSide.None; t.readyCorners = 0; t.coveredSides = TileSide.None;
        }

        void RefreshEdgesAround(int tile)
        {
            RefreshEdges(tile, -1);
            var nb = Graph.Neighbors[tile];
            for (int k = 0; k < nb.Length; k++) RefreshEdges(nb[k], -1);
        }

        /// <summary>Opens the sides of <paramref name="tile"/> whose neighbour is Ready (both must be Ready), closes the rest.
        /// <paramref name="leaving"/> = a neighbour about to unload (treated as not ready).</summary>
        void RefreshEdges(int tile, int leaving)
        {
            var t = m_Tiles[tile];
            if (t.root == null) return;
            // open: seams (closures) - both tiles Ready. covered / corners: sides and corners where a Ready tile stands,
            // whatever the state of THIS tile (ADR 0308): the apron and the far-field sectors of a tile that is still
            // activating were all drawn, so the forest mounds / curtains of its far field stood in the tile the truck
            // was driving in until the seam opened.
            TileSide open = TileSide.None, covered = TileSide.None;
            int corners = 0;
            {
                var nb = Graph.Neighbors[tile];
                for (int k = 0; k < nb.Length; k++)
                {
                    var side = Graph.NeighborSides[tile][k];
                    bool nbReady = nb[k] != leaving && Policy.StateOf(nb[k]) == TileState.Ready && m_Tiles[nb[k]].root != null;
                    if (side == TileSide.N || side == TileSide.E || side == TileSide.S || side == TileSide.W)
                    {
                        if (nbReady) covered |= side;
                        if (EdgeClosureRules.SeamReady(Policy.StateOf(tile), Policy.StateOf(nb[k]), m_Tiles[nb[k]].root != null, nb[k] == leaving)) open |= side;
                    }
                    else if (nbReady) corners |= EdgeSides.CornerBit(side);      // diagonal neighbour (ADR 0308)
                }
            }
            if (open == t.openSides && open == TileSide.None && covered == t.coveredSides && covered == TileSide.None
                && corners == t.readyCorners && corners == 0) return;
            t.openSides = open; t.readyCorners = corners; t.coveredSides = covered;
            for (int i = 0; i < t.closures.Length; i++)
            {
                t.closureOpen[i] = EdgeClosureRules.IsOpen(t.closureSide[i], open);
                if (t.closures[i] != null) t.closures[i].SetActive(!t.closureOpen[i]);
            }
            for (int i = 0; i < t.groups.Length; i++)
            {
                var b = t.groupBounds[i];
                bool hide = EdgeSides.GroupMayHide(b.x, b.y, b.z, b.w, t.closureE, t.closureN, t.closureOpen, t.closures.Length);
                if (t.groups[i] != null) t.groups[i].SetActive(!hide);
            }
            for (int i = 0; i < t.farSectors.Length; i++)
                if (t.farSectors[i] != null)
                    t.farSectors[i].SetActive(EdgeSides.FarSectorMayShow(t.farSide[i], Graph.NeighborSides[tile])   // Codex s24: neighbour sectors hidden from start
                        && EdgeSides.FarSectorVisible(t.farSide[i], covered, corners));                          // ADR 0308: covered sides / corners
            if (t.apronPieces.Length > 0)
            {
                if (t.apronWhole != null) t.apronWhole.SetActive(covered == TileSide.None && corners == 0);
                for (int i = 0; i < t.apronPieces.Length; i++)
                    if (t.apronPieces[i] != null) t.apronPieces[i].SetActive(EdgeSides.ApronPieceVisible(t.apronSide[i], covered, corners, t.apronCorners));
            }
            else if ((covered != TileSide.None || corners != 0) && !t.warnedApron)
            {
                t.warnedApron = true;
                Debug.LogWarning($"[STREAM] {Graph.Tiles[tile].id}: scene has no Apron_N/E/S/W pieces (imported before ADR 0235) - the apron overlaps the neighbour; reimport with scripts/import-region.ps1");
            }
            Debug.Log($"[STREAM] edges {Graph.Tiles[tile].id}: open {open}, covered {covered}, diagonal mask {corners}");
        }

        // ------------------------------------------------------------------ queries (safety net, tests)

        float DistanceToTileM(int tile)
        {
            Vector3 p = vehicle.position;
            return (float)Graph.DistanceTo(tile, m_Wx + p.x, m_Wy + p.z);
        }

        /// <summary>
        /// Distance from a world position to the OUTER edge of the drivable union of Ready tiles [m] (positive inside), for
        /// the world safety net (ADR 0082; ADR 0273 §10 pkt 5): a seam with a Ready (or Loading / Activating) cardinal
        /// neighbour is not an edge, an Unloaded / Unloading neighbour's seam is (<see cref="CorridorEdge"/>). Before the
        /// first decision an available Unloaded tile counts as Loading (the spawn may stand next to a seam the first decision
        /// is about to load). False when no tile is Ready.
        /// No allocations (buffers from <see cref="Init"/>).
        /// </summary>
        public bool TryInsideDistance(Vector3 worldPos, out float inside)
        {
            inside = float.MinValue;
            if (m_Tiles == null) return false;
            for (int i = 0; i < m_Tiles.Length; i++)
            {
                var t = m_Tiles[i];
                var st = Policy.StateOf(i);
                if (st == TileState.Ready && t.root == null) st = TileState.Activating;
                else if (st == TileState.Unloaded && !m_Decided && !Policy.IsUnavailable(i)) st = TileState.Loading;
                m_EdgeState[i] = st;
                if (st != TileState.Ready) continue;
                Vector3 o = t.root.transform.position;   // region-local (0, 0) = the tile's anchor
                var td = Graph.Tiles[i];
                m_EdgeDrivable[i] = new EdgeRect(o.x + t.min.x, o.z + t.min.y, o.x + t.max.x, o.z + t.max.y);
                m_EdgeTile[i] = new EdgeRect(o.x + (float)(td.xmin - td.anchorX), o.z + (float)(td.ymin - td.anchorY),
                                             o.x + (float)(td.xmax - td.anchorX), o.z + (float)(td.ymax - td.anchorY));
            }
            return CorridorEdge.InsideDistance(Graph, m_EdgeState, m_EdgeDrivable, m_EdgeTile, worldPos.x, worldPos.z, out inside);
        }

        /// <summary>ADR 0300: region root of a Ready tile = its region-local frame (local (x, z) = region-local (E, N);
        /// moved by every origin rebase together with the vehicle). Null when the tile is not Ready / not placed.</summary>
        public Transform FrameOf(int tile)
        {
            if (m_Tiles == null || tile < 0 || tile >= m_Tiles.Length || Policy == null) return null;
            var t = m_Tiles[tile];
            return t.root != null && Policy.StateOf(tile) == TileState.Ready ? t.root.transform : null;
        }

        /// <summary>World-space start route of a resident tile (null when the tile is not resident or has none).</summary>
        public WorldRoute RouteOf(string regionId)
        {
            int i = Graph != null ? Graph.IndexOf(regionId) : -1;
            if (i < 0 || m_Tiles[i].route == null) return null;
            return m_Tiles[i].route.GetComponent<WorldRoute>();
        }

        public TileState StateOf(string regionId)
        {
            int i = Graph != null ? Graph.IndexOf(regionId) : -1;
            return i >= 0 ? Policy.StateOf(i) : TileState.Unloaded;
        }

        void OnDestroy()
        {
            if (Active == this) Active = null;
            RemoveOriginListener();
            // Scene change (menu, other region): the tile scenes go with it; give back every pack lease still held.
            if (m_Tiles != null) for (int i = 0; i < m_Tiles.Length; i++) ReleaseLease(m_Tiles[i]);
        }
    }
}
