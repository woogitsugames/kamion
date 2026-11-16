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
            public GameObject[] chunks;
            public int nextChunk;
            public float loadStart, activateStart;
            public Vector2 min, max;
            public TileSide openSides;
            // edge objects (ADR 0169 closures, ADR 0085 far field, apron)
            public GameObject[] closures; public TileSide[] closureSide; public float[] closureE, closureN; public bool[] closureOpen;
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
        /// streamer only when it is switched on - <see cref="EnabledOverride"/> or the launch argument <c>stream=1</c> - and
        /// the start region has an available neighbour tile scene; otherwise returns null and the scene is exactly as before
        /// (closed region edge). Everything the bootstrap used to wire by hand is done here, so Game.Gameplay keeps one line:
        /// <list type="bullet">
        /// <item>content tier from the start scene name (<c>_High</c>), memory budget from the quality tier and platform;</item>
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
            if (!IsRequested(streamArgument)) return null;
            if (host == null || start == null || vehicle == null) return null;
            string tier = start.gameObject.scene.name.EndsWith("_High", System.StringComparison.Ordinal) ? RegionScenes.HighTier : RegionScenes.LowTier;
            float budget = StreamingSettings.BudgetForTier(Game.Rendering.QualityTiers.Current, !Application.isMobilePlatform);
            var s = TryInstall(host, start, vehicle, body, tier, budget, null);
            if (s == null) return null;
            s.UseSafePoses(safePoses, safeMinAge);
            s.AddOriginListener(onOriginMoved);
            s.WidenStartBoundary(start);
            return s;
        }

        /// <summary>Streaming switch: <see cref="EnabledOverride"/> when set, else launch argument <c>stream</c> == "1".</summary>
        public static bool IsRequested(string streamArgument) => EnabledOverride ?? streamArgument == "1";

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
            ProgressLoads();
            ProgressActivation();
            ProgressUnloads();
            if (Time.unscaledTime >= m_NextDecide)
            {
                m_NextDecide = Time.unscaledTime + decideIntervalS;
                Decide();
            }
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
                return;
            }
        }

        void BeginUnload(Tile t)
        {
            int i = t.index;
            // Close the seams of the neighbours first (their closures come back before the geometry goes).
            t.openSides = TileSide.None;
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
            // Scene unload does not free the meshes / textures: Resources.UnloadUnusedAssets, throttled, never while loading.
            if (m_UnloadAssetsPending && Time.unscaledTime - m_LastUnloadAssets >= unloadAssetsMinIntervalS && !AnyLoadingOrActivating())
            {
                m_UnloadAssetsPending = false;
                m_LastUnloadAssets = Time.unscaledTime;
                Resources.UnloadUnusedAssets();
            }
        }

        bool AnyLoadingOrActivating()
        {
            for (int i = 0; i < m_Tiles.Length; i++)
            {
                var s = Policy.StateOf(i);
                if (s == TileState.Loading || s == TileState.Activating) return true;
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
                        int idx = ParseIndex(n);
                        if (idx >= 0 && idx < data.Length) { lp = data[idx].localPos; heading = data[idx].headingDeg; }
                        closures.Add(c.gameObject); ce.Add(lp.x); cn.Add(lp.z);
                        cs.Add(EdgeSides.ClosureSide(lp.x, lp.z, heading, t.min.x, t.min.y, t.max.x, t.max.y));
                    }
                    else if (n == "Apron") t.apronWhole = c.gameObject;
                    else if (EdgeSides.ApronPieceSide(n) != TileSide.None) { pieces.Add(c.gameObject); ps.Add(EdgeSides.ApronPieceSide(n)); }
                    else if (n == "WorldFarField")
                        foreach (Transform f in c)
                        {
                            var side = EdgeSides.FarSectorSide(f.name);
                            if (side != TileSide.None) { far.Add(f.gameObject); fs.Add(side); }
                        }
                }
            }
            t.closures = closures.ToArray(); t.closureSide = cs.ToArray(); t.closureE = ce.ToArray(); t.closureN = cn.ToArray();
            t.closureOpen = new bool[t.closures.Length];
            t.groups = groups.ToArray(); t.groupBounds = gb.ToArray();
            t.farSectors = far.ToArray(); t.farSide = fs.ToArray();
            t.apronPieces = pieces.ToArray(); t.apronSide = ps.ToArray();
            t.openSides = TileSide.None;
        }

        static int ParseIndex(string name)
        {
            int v = 0, i = "Closure_".Length, digits = 0;
            for (; i < name.Length && name[i] >= '0' && name[i] <= '9'; i++, digits++) v = v * 10 + (name[i] - '0');
            return digits > 0 ? v : -1;
        }

        static void Clear(Tile t)
        {
            t.root = null; t.route = null; t.boundary = null; t.cooker = null; t.instances = null;
            t.chunks = System.Array.Empty<GameObject>(); t.nextChunk = 0;
            t.closures = System.Array.Empty<GameObject>(); t.groups = System.Array.Empty<GameObject>();
            t.farSectors = System.Array.Empty<GameObject>(); t.apronPieces = System.Array.Empty<GameObject>(); t.apronWhole = null;
            t.openSides = TileSide.None;
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
            TileSide open = TileSide.None;
            if (Policy.StateOf(tile) == TileState.Ready)
            {
                var nb = Graph.Neighbors[tile];
                for (int k = 0; k < nb.Length; k++)
                {
                    var side = Graph.NeighborSides[tile][k];
                    if (side != TileSide.N && side != TileSide.E && side != TileSide.S && side != TileSide.W) continue;
                    if (nb[k] != leaving && Policy.StateOf(nb[k]) == TileState.Ready && m_Tiles[nb[k]].root != null) open |= side;
                }
            }
            if (open == t.openSides && open == TileSide.None) return;
            t.openSides = open;
            for (int i = 0; i < t.closures.Length; i++)
            {
                t.closureOpen[i] = (open & t.closureSide[i]) != 0;
                if (t.closures[i] != null) t.closures[i].SetActive(!t.closureOpen[i]);
            }
            for (int i = 0; i < t.groups.Length; i++)
            {
                var b = t.groupBounds[i];
                bool hide = EdgeSides.GroupMayHide(b.x, b.y, b.z, b.w, t.closureE, t.closureN, t.closureOpen, t.closures.Length);
                if (t.groups[i] != null) t.groups[i].SetActive(!hide);
            }
            for (int i = 0; i < t.farSectors.Length; i++)
                if (t.farSectors[i] != null) t.farSectors[i].SetActive((open & t.farSide[i]) == 0);
            if (t.apronPieces.Length > 0)
            {
                if (t.apronWhole != null) t.apronWhole.SetActive(open == TileSide.None);
                for (int i = 0; i < t.apronPieces.Length; i++)
                    if (t.apronPieces[i] != null) t.apronPieces[i].SetActive(open != TileSide.None && (open & t.apronSide[i]) == 0);
            }
            else if (open != TileSide.None && !t.warnedApron)
            {
                t.warnedApron = true;
                Debug.LogWarning($"[STREAM] {Graph.Tiles[tile].id}: scene has no Apron_N/E/S/W pieces (imported before ADR 0235) - the apron overlaps the neighbour; reimport with scripts/import-region.ps1");
            }
            Debug.Log($"[STREAM] edges {Graph.Tiles[tile].id}: open {open}");
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
