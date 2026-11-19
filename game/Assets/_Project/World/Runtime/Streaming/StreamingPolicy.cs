using System;

namespace Game.World.Streaming
{
    /// <summary>Life cycle of one tile in the streamer (ADR 0235).</summary>
    public enum TileState
    {
        /// <summary>Not in memory.</summary>
        Unloaded = 0,
        /// <summary>LoadSceneAsync running (or waiting for activation).</summary>
        Loading = 1,
        /// <summary>Scene activated, chunks being enabled / collision being cooked. Edges still closed.</summary>
        Activating = 2,
        /// <summary>Everything enabled and collision cooked: the shared edges may open.</summary>
        Ready = 3,
        /// <summary>UnloadSceneAsync running; memory not yet free.</summary>
        Unloading = 4,
    }

    public enum StreamOp { Load = 1, Unload = 2 }

    public struct StreamCommand
    {
        public StreamOp op;
        public int tile;
        public override string ToString() => op + " " + tile;
    }

    /// <summary>
    /// Settings of the streaming decision (ADR 0235). All WORKING_VALUE unless a source is named.
    /// The load radius is derived, not tuned: the truck must not reach a tile before it is loaded, activated and its
    /// collision cooked, so radius = max speed x (load + activation + cooking time) + margin.
    /// </summary>
    [Serializable]
    public sealed class StreamingSettings
    {
        /// <summary>Speed used for the load radius [m/s]: 25 m/s = 90 km/h, the speed-limiter setting for N3 lorries
        /// (Council Directive 92/6/EEC as amended by 2002/85/EC). The game truck has no limiter yet, so a faster vehicle
        /// uses its own speed (see <see cref="LoadRadiusFor"/>).</summary>
        public float maxSpeedMs = 25f;
        /// <summary>Async scene load of one tile on the A16 [s]. UNVERIFIED (not measured; the streamer logs it).</summary>
        public float loadTimeS = 8f;
        /// <summary>Spread activation of chunks [s]. WORKING_VALUE.</summary>
        public float activationTimeS = 1f;
        /// <summary>Collision cooking [s]: region C 265 meshes = 250-259 ms on the A16 (PERFORMANCE_BUDGETS.md), x 4 margin.</summary>
        public float cookTimeS = 1f;
        /// <summary>Extra distance on top of speed x time [m]. WORKING_VALUE.</summary>
        public float marginM = 150f;
        /// <summary>Unload only this much further away than the load radius [m] (hysteresis against load/unload thrash
        /// when driving along a tile edge). WORKING_VALUE.</summary>
        public float hysteresisM = 300f;
        /// <summary>The current tile changes only when the vehicle is this far outside the old one [m]. WORKING_VALUE.</summary>
        public float currentHysteresisM = 30f;
        /// <summary>Most tiles in memory at once (current + 3 at a corner). WORKING_VALUE.</summary>
        public int maxTiles = 4;
        /// <summary>Sum of the world memory of resident tiles [MB]; set per platform and tier by <see cref="BudgetForTier"/>.
        /// WORKING_VALUE.</summary>
        public float memoryBudgetMB = 200f;
        /// <summary>The High content tier streams (World_&lt;id&gt;_High_Tile): count worldMemoryHighMB instead of the Low value
        /// (ADR 0273). A graph without High values falls back to Low x <see cref="HighOverLowFallback"/>.</summary>
        public bool highContent;
        /// <summary>High / Low WORLD_MEMORY when a tile has no High value: max ratio of the tabulated imports
        /// (Maczka 420.4 / 153.2 = 2.74, ADR 0234 §7) - conservative. ESTIMATED.</summary>
        public const float HighOverLowFallback = 2.75f;
        /// <summary>When the budget leaves no room, the single best tile ahead is still loaded (a closed road is worse
        /// than a PSS overshoot that the device run measures). WORKING_VALUE decision, ADR 0235 §4.</summary>
        public bool allowOneOverBudget = true;
        /// <summary>Simultaneous loads including chunk activation and collision cooking.</summary>
        public int maxConcurrentLoads = 1;

        public float BaseLoadRadiusM => maxSpeedMs * (loadTimeS + activationTimeS + cookTimeS) + marginM;

        /// <summary>Load radius for the current speed: never below the base radius.</summary>
        public float LoadRadiusFor(float speedMs) =>
            Math.Max(maxSpeedMs, Math.Abs(speedMs)) * (loadTimeS + activationTimeS + cookTimeS) + marginM;

        public float LookAheadS => loadTimeS + activationTimeS + cookTimeS;

        /// <summary>
        /// World budget per quality tier on a phone [MB] (WORKING_VALUE, ADR 0235 §4): PSS target minus the PSS of region C
        /// minus its WORLD_MEMORY. A16 Low: 1000 - (899.8..926.2 - 124.2) = 198..224 -> 200; A16 Medium: target 1.2 GB -> 400;
        /// High / Ultra (S24+, 2.0 GB): 600.
        /// </summary>
        public static float BudgetForTier(string tier) => BudgetForTier(tier, false);

        /// <summary>
        /// World budget per platform and quality tier [MB] (WORKING_VALUE, ADR 0273 §6). Desktop (D73 main platform, D74
        /// classes: minimum 8 GB RAM / 2 GB VRAM, recommended 12 GB RAM): the worst 3-tile set of the corridor (C + Maczka +
        /// Kleeberga: Low 434.1, High 1044.2 MB, tile_graph.json) + the pinned respawn tile (worst case C: Low 124.2, High
        /// 267.0) + ~10 %: Low 640, Medium 800 (Low content + one corner tile), High 1450, Ultra 2000.
        /// Owner decision 18.11 (ADR 0273 dopisek D81, ADR 0290): the DK19 tiles of D81 made the worst set bojary +
        /// mickiewicza + wygoda + pinned C = Low 796.2 / High 1935.2 MB -> Low 850, High 2000 (measured on the GTX 1070,
        /// class "zalecany": High corridor VRAM 1.07-1.87 GB of 8 GB, private 2.1-3.3 GB; Low VRAM 0.45 GB;
        /// artifacts/pc/DOM/20261118-*, artifacts/d3d-ab). ADR 0309: Medium 800 -> 850, the same Low content and corridor
        /// envelope as Low; desktop ladder 850 / 850 / 2000 / 2000 MB (WORKING_VALUE). Phone: see
        /// <see cref="BudgetForTier(string)"/>.
        /// </summary>
        public static float BudgetForTier(string tier, bool desktop)
        {
            if (desktop)
            {
                switch (tier)
                {
                    case "Low": return 850f;
                    case "Medium": return 850f;
                    case "High": return 2000f;
                    case "Ultra": return 2000f;
                    default: return 850f;
                }
            }
            switch (tier)
            {
                case "Low": return 200f;
                case "Medium": return 400f;
                case "High": case "Ultra": return 600f;
                default: return 200f;
            }
        }

        /// <summary>World memory of a tile for the configured content tier [MB].</summary>
        public float MemoryOf(TileData t)
        {
            if (!highContent) return t.worldMemoryMB;
            return t.worldMemoryHighMB > 0f ? t.worldMemoryHighMB : t.worldMemoryMB * HighOverLowFallback;
        }
    }

    /// <summary>
    /// Which tile to load or unload for a vehicle position and velocity (ADR 0235). Pure C#, no Unity objects, no
    /// allocations after construction: safe to call from the driving loop. The streamer reports the real state of each
    /// tile back with <see cref="SetState"/>.
    /// Rules:
    /// - the current tile (the one under the vehicle, with <see cref="StreamingSettings.currentHysteresisM"/>) is kept;
    /// - a neighbour (edge or corner) is wanted when it is within the load radius of the vehicle, or within the margin
    ///   of the look-ahead segment p -> p + v x (load + activation + cook time);
    /// - a resident tile is unloaded when it is not wanted and further than load radius + hysteresis;
    /// - loads go nearest first, one at a time, within <see cref="StreamingSettings.maxTiles"/> and the memory budget;
    ///   a resident tile in the hysteresis band (not wanted, not yet far) is evicted for a wanted one when needed;
    /// - the pinned tile (<see cref="Pinned"/>, ADR 0273 §8: the tile the safety net would put the truck back into) is
    ///   never unloaded or evicted; its memory counts against the budget.
    /// </summary>
    public sealed class StreamingPolicy
    {
        public readonly TileGraph Graph;
        public readonly StreamingSettings Settings;

        readonly TileState[] m_State;
        readonly double[] m_Score;      // distance used for ordering (min of point and look-ahead distance)
        readonly double[] m_Dist;       // distance from the vehicle to the tile rectangle
        readonly bool[] m_Wanted;
        readonly bool[] m_Unavailable;  // tile scene not in this build: never wanted (its seam stays closed)
        readonly int[] m_Order;         // candidate indices sorted by score

        public int Current { get; private set; } = -1;
        /// <summary>Tile that must stay in memory (-1 = none): the respawn / recovery tile, set by the streamer before
        /// each decision (ADR 0273 §8). A pinned tile that is unloaded is not loaded back by this rule - only kept.</summary>
        public int Pinned { get; private set; } = -1;
        /// <summary>A wanted tile was skipped for the budget on the last decision (logged by the streamer).</summary>
        public bool BudgetBlocked { get; private set; }
        /// <summary>The last decision loaded a tile beyond the memory budget (allowOneOverBudget).</summary>
        public bool OverBudget { get; private set; }

        public StreamingPolicy(TileGraph graph, StreamingSettings settings)
        {
            Graph = graph ?? throw new ArgumentNullException(nameof(graph));
            Settings = settings ?? new StreamingSettings();
            int n = graph.Count;
            m_State = new TileState[n];
            m_Score = new double[n];
            m_Dist = new double[n];
            m_Wanted = new bool[n];
            m_Unavailable = new bool[n];
            m_Order = new int[n];
        }

        public TileState StateOf(int tile) => m_State[tile];

        /// <summary>Pins one tile (or -1 for none); out-of-range values clear the pin.</summary>
        public void SetPinned(int tile) => Pinned = tile >= 0 && tile < m_State.Length ? tile : -1;
        public void SetState(int tile, TileState s) => m_State[tile] = s;

        /// <summary>The tile of the start scene: already in memory and ready.</summary>
        public void InitResident(int tile)
        {
            m_State[tile] = TileState.Ready;
            Current = tile;
        }

        /// <summary>Marks a tile whose scene is not in the build: never loaded, never counted.</summary>
        public void SetUnavailable(int tile, bool unavailable = true) => m_Unavailable[tile] = unavailable;
        public bool IsUnavailable(int tile) => m_Unavailable[tile];

        public bool IsResident(int tile) => m_State[tile] != TileState.Unloaded;

        public int ResidentCount()
        {
            int c = 0;
            for (int i = 0; i < m_State.Length; i++) if (m_State[i] != TileState.Unloaded) c++;
            return c;
        }

        public float ResidentMemoryMB()
        {
            float m = 0f;
            for (int i = 0; i < m_State.Length; i++) if (m_State[i] != TileState.Unloaded) m += Settings.MemoryOf(Graph.Tiles[i]);
            return m;
        }

        int CountState(TileState s)
        {
            int c = 0;
            for (int i = 0; i < m_State.Length; i++) if (m_State[i] == s) c++;
            return c;
        }

        /// <summary>True when the neighbour of <paramref name="tile"/> on <paramref name="side"/> exists and is Ready.</summary>
        public bool NeighborReady(int tile, TileSide side)
        {
            int j = Graph.NeighborOn(tile, side);
            return j >= 0 && m_State[j] == TileState.Ready;
        }

        /// <summary>Updates the current tile for a position (EPSG:2180) with hysteresis; returns it (-1 = off every tile).</summary>
        public int UpdateCurrent(double x, double y)
        {
            if (Current >= 0 && Graph.Contains(Current, x, y, Settings.currentHysteresisM)) return Current;
            int t = Graph.TileAt(x, y);
            if (t >= 0) Current = t;
            return Current;
        }

        /// <summary>
        /// One decision for the vehicle at (x, y) [EPSG:2180 m] moving at (vx, vy) [m/s, east / north]. Writes up to
        /// <paramref name="output"/>.Length commands and returns their count. Loads are marked Loading and unloads
        /// Unloading immediately (the streamer must execute every returned command).
        /// </summary>
        public int Decide(double x, double y, float vx, float vy, StreamCommand[] output)
        {
            BudgetBlocked = false;
            OverBudget = false;
            int cur = UpdateCurrent(x, y);
            int n = Graph.Count;
            float speed = (float)Math.Sqrt(vx * vx + vy * vy);
            double loadR = Settings.LoadRadiusFor(speed);
            double unloadR = loadR + Settings.hysteresisM;
            double ax = x + vx * Settings.LookAheadS, ay = y + vy * Settings.LookAheadS;

            for (int i = 0; i < n; i++)
            {
                m_Wanted[i] = false;
                m_Dist[i] = Graph.DistanceTo(i, x, y);
                m_Score[i] = m_Dist[i];
            }
            if (cur >= 0)
            {
                m_Wanted[cur] = true;
                m_Score[cur] = -1.0;
                var nb = Graph.Neighbors[cur];
                for (int k = 0; k < nb.Length; k++)
                {
                    int j = nb[k];
                    if (m_Unavailable[j]) continue;
                    double seg = Graph.SegmentDistanceTo(j, x, y, ax, ay);
                    m_Score[j] = Math.Min(m_Dist[j], seg);
                    m_Wanted[j] = m_Dist[j] <= loadR || seg <= Settings.marginM;
                }
            }

            int count = 0;
            // 1. Unload resident tiles that are far behind (beyond the hysteresis band). Never the current tile.
            for (int i = 0; i < n && count < output.Length; i++)
            {
                if (i == cur || i == Pinned || m_Wanted[i]) continue;
                var s = m_State[i];
                // Do not destroy a cooker with an outstanding bake: OnDestroy must Complete its job.
                if (s == TileState.Ready && m_Dist[i] > unloadR)
                {
                    output[count++] = new StreamCommand { op = StreamOp.Unload, tile = i };
                    m_State[i] = TileState.Unloading;
                }
            }

            // 2. Wanted tiles not in memory, nearest first (insertion sort, no allocation).
            int m = 0;
            for (int i = 0; i < n; i++)
            {
                if (!m_Wanted[i] || m_State[i] != TileState.Unloaded) continue;
                int p = m;
                while (p > 0 && m_Score[m_Order[p - 1]] > m_Score[i]) { m_Order[p] = m_Order[p - 1]; p--; }
                m_Order[p] = i;
                m++;
            }
            if (m == 0 || CountState(TileState.Loading) + CountState(TileState.Activating) >= Settings.maxConcurrentLoads) return count;
            // Memory frees only when an unload completes, so a tile still unloading keeps counting.
            int best = m_Order[0];
            float mem = ResidentMemoryMB();
            int resident = ResidentCount();
            bool fitsCount = resident + 1 <= Settings.maxTiles;
            bool fitsMem = mem + Settings.MemoryOf(Graph.Tiles[best]) <= Settings.memoryBudgetMB;
            if (fitsCount && fitsMem)
            {
                if (count < output.Length) { output[count++] = new StreamCommand { op = StreamOp.Load, tile = best }; m_State[best] = TileState.Loading; }
                return count;
            }
            // 3. Make room: evict the farthest resident tile in the hysteresis band (not wanted, not current).
            int evict = -1;
            for (int i = 0; i < n; i++)
            {
                if (i == cur || i == Pinned || m_Wanted[i]) continue;
                if (m_State[i] != TileState.Ready) continue;
                if (evict < 0 || m_Dist[i] > m_Dist[evict]) evict = i;
            }
            if (evict >= 0)
            {
                if (count < output.Length) { output[count++] = new StreamCommand { op = StreamOp.Unload, tile = evict }; m_State[evict] = TileState.Unloading; }
                return count;   // load on a later decision, once the memory is free
            }
            BudgetBlocked = true;
            // 4. Nothing to evict: the best tile ahead still loads when only the memory budget is exceeded, the tile
            // count allows it, and nothing else is loading beyond the budget (current + this one at most over budget).
            if (fitsCount && !fitsMem && Settings.allowOneOverBudget && !AnyOverBudgetBeyondCurrent(cur) && count < output.Length)
            {
                output[count++] = new StreamCommand { op = StreamOp.Load, tile = best };
                m_State[best] = TileState.Loading;
                OverBudget = true;
            }
            return count;
        }

        /// <summary>True when the resident set without the current (and pinned) tile already exceeds the budget on its own share.</summary>
        bool AnyOverBudgetBeyondCurrent(int cur)
        {
            float mem = ResidentMemoryMB();
            float own = cur >= 0 ? Settings.MemoryOf(Graph.Tiles[cur]) : 0f;
            if (Pinned >= 0 && Pinned != cur && m_State[Pinned] != TileState.Unloaded) own += Settings.MemoryOf(Graph.Tiles[Pinned]);
            return cur >= 0 && mem > own && mem > Settings.memoryBudgetMB;
        }
    }
}
