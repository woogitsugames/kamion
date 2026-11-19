using System;
using System.Collections.Generic;
using Game.Editor.Build;
using Game.World;
using Game.World.Streaming;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0235: additive tile streaming - tile graph data, the pure decision (which tile to load / unload for a
    /// position and velocity, hysteresis, tile count, memory budget, queue), tile placement for the floating origin and
    /// the edge sides that open a seam. No scenes: the streamer's async part is covered by WorldStreamingPlayModeTests.
    /// </summary>
    public class WorldStreamingPolicyTests
    {
        // ------------------------------------------------------------------ helpers

        /// <summary>Synthetic grid of 2048 m tiles: cols x rows, ids "t{c}{r}", memory per tile from <paramref name="mem"/>.</summary>
        static TileGraph Grid(int cols, int rows, Func<int, int, float> mem = null)
        {
            var tiles = new List<TileData>();
            for (int r = 0; r < rows; r++)
                for (int c = 0; c < cols; c++)
                {
                    double x0 = c * 2048.0, y0 = r * 2048.0;
                    tiles.Add(new TileData
                    {
                        id = $"t{c}{r}", xmin = x0, ymin = y0, xmax = x0 + 2048.0, ymax = y0 + 2048.0,
                        anchorX = x0 + 1024.0, anchorY = y0 + 1024.0, anchorZ = 100.0 + r,
                        worldMemoryMB = mem != null ? mem(c, r) : 50f,
                    });
                }
            foreach (var a in tiles)
            {
                var ns = new List<NeighborData>();
                foreach (var b in tiles)
                {
                    if (a == b) continue;
                    int dc = (int)Math.Round((b.xmin - a.xmin) / 2048.0), dr = (int)Math.Round((b.ymin - a.ymin) / 2048.0);
                    if (Math.Abs(dc) > 1 || Math.Abs(dr) > 1) continue;
                    string s = (dr > 0 ? "N" : dr < 0 ? "S" : "") + (dc > 0 ? "E" : dc < 0 ? "W" : "");
                    ns.Add(new NeighborData { id = b.id, side = s, seamM = s.Length == 1 ? 2048f : 0f });
                }
                a.neighbors = ns.ToArray();
            }
            return new TileGraph(new TileGraphData { schema = TileGraph.Schema, tiles = tiles.ToArray() });
        }

        /// <summary>
        /// Minimal stand-in for the streamer: executes the commands, a load becomes Ready after the full
        /// load + activation + cook time, an unload completes after <paramref name="unloadS"/>.
        /// </summary>
        sealed class FakeStreamer
        {
            public readonly StreamingPolicy P;
            readonly float[] m_Done;
            readonly StreamCommand[] m_Cmd = new StreamCommand[8];
            public int Loads, Unloads, MaxResident;
            public float MaxMemory;
            public readonly List<string> Log = new List<string>();
            readonly float m_ReadyAfter, m_UnloadS;

            public FakeStreamer(StreamingPolicy p, float unloadS = 1f)
            {
                P = p; m_Done = new float[p.Graph.Count];
                m_ReadyAfter = p.Settings.loadTimeS + p.Settings.activationTimeS + p.Settings.cookTimeS;
                m_UnloadS = unloadS;
            }

            public void Step(float t, double x, double y, float vx, float vy)
            {
                for (int i = 0; i < m_Done.Length; i++)
                {
                    var s = P.StateOf(i);
                    if (s == TileState.Loading && t >= m_Done[i]) P.SetState(i, TileState.Ready);
                    if (s == TileState.Unloading && t >= m_Done[i]) P.SetState(i, TileState.Unloaded);
                }
                int n = P.Decide(x, y, vx, vy, m_Cmd);
                for (int k = 0; k < n; k++)
                {
                    var c = m_Cmd[k];
                    if (c.op == StreamOp.Load) { Loads++; m_Done[c.tile] = t + m_ReadyAfter; }
                    else { Unloads++; m_Done[c.tile] = t + m_UnloadS; }
                    Log.Add($"{t:F2}s {c.op} {P.Graph.Tiles[c.tile].id} at ({x:F0},{y:F0})");
                }
                MaxResident = Math.Max(MaxResident, P.ResidentCount());
                MaxMemory = Math.Max(MaxMemory, P.ResidentMemoryMB());
            }
        }

        // ------------------------------------------------------------------ data

        [Test]
        public void ShippedGraph_LoadsThroughJsonUtility_AndHoldsTheD67Corridor()
        {
            var g = TileGraph.LoadDefault();
            Assert.IsNotNull(g, "Resources/WorldStreaming/tile_graph.json (tools/worldgen/streaming/tile_graph.py)");
            Assert.GreaterOrEqual(g.Count, 21);
            int c = g.IndexOf("bialystok-industrial-c");
            Assert.GreaterOrEqual(c, 0);
            Assert.AreEqual(777995.0, g.Tiles[c].anchorX, 0.01);
            Assert.AreEqual(TileSide.W, g.SideOf(c, g.IndexOf("bialystok-maczka")));
            CorridorData d67 = null;
            foreach (var cor in g.Corridors) if (cor.tiles.Length > 0 && cor.tiles[0] == "bialystok-industrial-c") d67 = cor;
            Assert.IsNotNull(d67, "corridor C -> Knyszyn");
            Assert.AreEqual(17, d67.tiles.Length);
            Assert.AreEqual("knyszyn", d67.tiles[d67.tiles.Length - 1]);
            for (int i = 1; i < d67.tiles.Length; i++)
                Assert.AreNotEqual(TileSide.None, g.SideOf(g.IndexOf(d67.tiles[i - 1]), g.IndexOf(d67.tiles[i])), d67.tiles[i]);
        }

        [Test]
        public void ShippedGraph_SidesAreSymmetric()
        {
            var g = TileGraph.LoadDefault();
            for (int i = 0; i < g.Count; i++)
                for (int k = 0; k < g.Neighbors[i].Length; k++)
                {
                    int j = g.Neighbors[i][k];
                    Assert.AreEqual(TileGraph.Opposite(g.NeighborSides[i][k]), g.SideOf(j, i), $"{g.Tiles[i].id} / {g.Tiles[j].id}");
                }
        }

        [Test]
        public void Settings_LoadRadius_IsSpeedTimesTimePlusMargin()
        {
            var s = new StreamingSettings();
            Assert.AreEqual(25f * 10f + 150f, s.BaseLoadRadiusM, 1e-3f);
            Assert.AreEqual(400f, s.LoadRadiusFor(10f), 1e-3f, "slower than the limiter: base radius");
            Assert.AreEqual(30f * 10f + 150f, s.LoadRadiusFor(30f), 1e-3f, "faster: own speed");
            Assert.AreEqual(200f, StreamingSettings.BudgetForTier("Low"));
            Assert.AreEqual(400f, StreamingSettings.BudgetForTier("Medium"));
            Assert.AreEqual(StreamingSettings.BudgetForTier("High"), StreamingSettings.BudgetForTier("High", false), "phone overload");
        }

        [Test]
        public void SegmentDistance_ClipsAndMeasures()
        {
            var g = Grid(2, 1);
            Assert.AreEqual(0.0, g.SegmentDistanceTo(1, 1000, 1000, 3000, 1000), 1e-9, "segment entering the tile");
            Assert.AreEqual(48.0, g.SegmentDistanceTo(1, 1000, 1000, 2000, 1000), 1e-9);
            Assert.AreEqual(100.0, g.SegmentDistanceTo(1, 2148, -100, 3000, -100), 1e-9, "below the tile");
        }

        // ------------------------------------------------------------------ decisions

        [Test]
        public void MidTile_NothingButTheCurrentTile()
        {
            var p = new StreamingPolicy(Grid(3, 1), new StreamingSettings());
            p.InitResident(1);
            var cmd = new StreamCommand[8];
            Assert.AreEqual(0, p.Decide(3072, 1024, 20f, 0f, cmd));
            Assert.AreEqual(1, p.Current);
        }

        [Test]
        public void DrivingEast_NeighbourIsReadyBeforeTheSeam_AndTheTileBehindUnloadsWithHysteresis()
        {
            var g = Grid(3, 1);
            var p = new StreamingPolicy(g, new StreamingSettings());
            p.InitResident(0);
            var f = new FakeStreamer(p);
            double x = 1024, y = 1024; float v = 25f, dt = 0.25f;
            double readyAtX = double.NaN, unloadAtX = double.NaN;
            for (float t = 0f; x < 5000; t += dt, x += v * dt)
            {
                f.Step(t, x, y, v, 0f);
                if (double.IsNaN(readyAtX) && p.StateOf(1) == TileState.Ready) readyAtX = x;
                if (double.IsNaN(unloadAtX) && p.StateOf(0) == TileState.Unloading) unloadAtX = x;
                for (int i = 0; i < g.Count; i++)
                    if (g.Contains(i, x, y)) Assert.AreEqual(TileState.Ready, p.StateOf(i), $"vehicle at x={x:F0} touches {g.Tiles[i].id} before it is ready\n" + string.Join("\n", f.Log));
            }
            Assert.Less(readyAtX, 2048.0, "tile 1 ready before the seam");
            Assert.Greater(unloadAtX, 2048.0 + 700.0 - 1.0, "tile 0 unloads only beyond load radius + hysteresis");
            Assert.LessOrEqual(f.MaxResident, 2);
        }

        [Test]
        public void DrivingAlongTheSeam_DoesNotThrash()
        {
            var g = Grid(2, 1);
            var p = new StreamingPolicy(g, new StreamingSettings());
            p.InitResident(0);
            var f = new FakeStreamer(p);
            float t = 0f;
            // Zig-zag across the seam x = 2048 (+-200 m) for 10 minutes at 15 m/s.
            double x = 1900; float vx = 15f;
            for (int i = 0; i < 2400; i++, t += 0.25f)
            {
                x += vx * 0.25f;
                if (x > 2248 || x < 1848) vx = -vx;
                f.Step(t, x, 1024 + i * 0.1, vx, 0f);
            }
            Assert.AreEqual(1, f.Loads, string.Join("\n", f.Log));
            Assert.AreEqual(0, f.Unloads, string.Join("\n", f.Log));
        }

        [Test]
        public void Corner_LoadsNearestFirst_OneAtATime_WithinMaxTiles()
        {
            var g = Grid(2, 2);
            var s = new StreamingSettings { maxTiles = 3 };
            var p = new StreamingPolicy(g, s);
            int c0 = g.IndexOf("t00");
            p.InitResident(c0);
            var cmd = new StreamCommand[8];
            // 100 m from the east edge, 300 m from the north edge, standing still.
            int n = p.Decide(1948, 1748, 0f, 0f, cmd);
            Assert.AreEqual(1, n);
            Assert.AreEqual(g.IndexOf("t10"), cmd[0].tile, "east (100 m) before north (300 m)");
            Assert.AreEqual(0, p.Decide(1948, 1748, 0f, 0f, cmd), "one load at a time");
            p.SetState(cmd[0].tile, TileState.Ready);
            n = p.Decide(1948, 1748, 0f, 0f, cmd);
            Assert.AreEqual(g.IndexOf("t01"), cmd[0].tile);
            p.SetState(cmd[0].tile, TileState.Ready);
            Assert.AreEqual(0, p.Decide(1948, 1748, 0f, 0f, cmd), "diagonal (316 m) wanted but maxTiles = 3 and nothing to evict");
            Assert.IsTrue(p.BudgetBlocked);
        }

        [Test]
        public void MemoryBudget_AllowsOneHeavyTileAhead_ButNotASecond()
        {
            // C-like 124 MB current, Maczka-like 153 MB west, 157 MB beyond: budget 200 (A16 Low).
            float[] mem = { 157f, 153f, 124f };
            var g = Grid(3, 1, (c, r) => mem[c]);
            var p = new StreamingPolicy(g, new StreamingSettings { memoryBudgetMB = 200f });
            p.InitResident(2);
            var cmd = new StreamCommand[8];
            int n = p.Decide(4196, 1024, -25f, 0f, cmd);   // 100 m east of the seam with tile 1, driving west
            Assert.AreEqual(1, n);
            Assert.AreEqual(1, cmd[0].tile);
            Assert.IsTrue(p.OverBudget, "277 MB > 200 MB: logged as over budget");
            p.SetState(1, TileState.Ready);
            // Into tile 1, 100 m from tile 0, tile 2 still within the hysteresis band: the third tile cannot load.
            n = p.Decide(2148, 1024, -25f, 0f, cmd);
            Assert.AreEqual(1, n);
            Assert.AreEqual(StreamOp.Unload, cmd[0].op, "tile 2 (behind, not wanted) is evicted for tile 0");
            Assert.AreEqual(2, cmd[0].tile);
            Assert.AreEqual(0, p.Decide(2148, 1024, -25f, 0f, cmd), "no load while the evicted tile is still unloading");
            p.SetState(2, TileState.Unloaded);
            n = p.Decide(2148, 1024, -25f, 0f, cmd);
            Assert.AreEqual(1, n);
            Assert.AreEqual(StreamOp.Load, cmd[0].op);
            Assert.AreEqual(0, cmd[0].tile);
        }

        [Test]
        public void LookAhead_LoadsTheTileInTheDirectionOfTravelEarlier()
        {
            var g = Grid(3, 1);
            var s = new StreamingSettings();
            var p = new StreamingPolicy(g, s);
            p.InitResident(1);
            var cmd = new StreamCommand[8];
            // 600 m from the east seam: at 5 m/s outside the 400 m radius and the 50 m look-ahead; at 50 m/s (faster than
            // the limiter) the radius grows to 50 x 10 + 150 = 650 m: wanted.
            Assert.AreEqual(0, p.Decide(4096 - 600, 1024, 5f, 0f, cmd));
            Assert.AreEqual(1, p.Decide(4096 - 600, 1024, 50f, 0f, cmd));
            Assert.AreEqual(2, cmd[0].tile);
        }

        [Test]
        public void ShippedCorridor_DrivenAt90KmH_NeverEntersATileThatIsNotReady()
        {
            var g = TileGraph.LoadDefault();
            CorridorData d67 = null;
            foreach (var cor in g.Corridors) if (cor.tiles[0] == "bialystok-industrial-c") d67 = cor;
            Assert.IsNotNull(d67);
            // Polyline through the route portals of the corridor (inside each tile the straight chord between its entry
            // and exit portal stays in the tile: both are on its boundary and the tile is convex).
            var pts = new List<Vector2d>();
            int c = g.IndexOf(d67.tiles[0]);
            pts.Add(new Vector2d(g.Tiles[c].anchorX, g.Tiles[c].anchorY));
            for (int i = 1; i < d67.tiles.Length; i++)
                foreach (var po in g.Portals)
                    if (po.from == d67.tiles[i - 1] && po.to == d67.tiles[i]) pts.Add(new Vector2d(po.x, po.y));
            int k = g.IndexOf("knyszyn");
            pts.Add(new Vector2d(g.Tiles[k].anchorX, g.Tiles[k].anchorY));
            Assert.AreEqual(d67.tiles.Length + 1, pts.Count, "one portal per corridor seam");

            foreach (string tier in new[] { "Low", "Medium" })
            {
                var p = new StreamingPolicy(g, new StreamingSettings { memoryBudgetMB = StreamingSettings.BudgetForTier(tier) });
                p.InitResident(c);
                var f = new FakeStreamer(p);
                float t = 0f, v = 25f, dt = 0.25f;
                int over = 0;
                for (int i = 1; i < pts.Count; i++)
                {
                    double ex = pts[i].x - pts[i - 1].x, ey = pts[i].y - pts[i - 1].y, len = Math.Sqrt(ex * ex + ey * ey);
                    float vx = (float)(ex / len * v), vy = (float)(ey / len * v);
                    for (double s = 0; s < len; s += v * dt, t += dt)
                    {
                        double x = pts[i - 1].x + ex / len * s, y = pts[i - 1].y + ey / len * s;
                        f.Step(t, x, y, vx, vy);
                        if (p.OverBudget) over++;
                        for (int j = 0; j < g.Count; j++)
                            if (g.Contains(j, x, y, -0.5))
                                Assert.AreEqual(TileState.Ready, p.StateOf(j), $"[{tier}] t={t:F1}s in {g.Tiles[j].id} before ready\n" + string.Join("\n", f.Log));
                    }
                }
                Assert.LessOrEqual(f.MaxResident, p.Settings.maxTiles, tier);
                TestContext.WriteLine($"[{tier}] budget {p.Settings.memoryBudgetMB} MB: loads {f.Loads}, unloads {f.Unloads}, max resident {f.MaxResident} tiles / {f.MaxMemory:F1} MB (ESTIMATED), over-budget decisions {over}, drive {t / 60f:F1} min");
            }
        }

        struct Vector2d { public double x, y; public Vector2d(double x, double y) { this.x = x; this.y = y; } }

        [Test]
        public void Decide_AllocatesNothing()
        {
            // GcAllocCounter (Recorder "GC.Alloc", pattern of ADR 0244 / PR #118): GC.GetAllocatedBytesForCurrentThread is 0
            // under Mono in the editor, so the old byte delta could never fail there.
            var g = TileGraph.LoadDefault();
            var p = new StreamingPolicy(g, new StreamingSettings());
            int c = g.IndexOf("dk65-03");
            p.InitResident(c);
            var cmd = new StreamCommand[8];
            int step = 0;
            Action frames = () =>
            {
                for (int i = 0; i < 2000; i++, step++)
                {
                    int n = p.Decide(768700 + step * 0.01, 599200 + step * 0.05, 0f, 20f, cmd);
                    for (int k = 0; k < n; k++) p.SetState(cmd[k].tile, cmd[k].op == StreamOp.Load ? TileState.Ready : TileState.Unloaded);
                }
            };
            GcAllocCounter.AssertZero(frames, warmup: frames, message: "StreamingPolicy.Decide must not allocate (ADR 0235, CLAUDE.md)");
        }

        // ------------------------------------------------------------------ placement / floating origin

        [Test]
        public void Placement_NeighbourRoot_MapsTheSeamPointToTheSameUnityPosition()
        {
            var g = TileGraph.LoadDefault();
            var a = g.Tiles[g.IndexOf("dk65-03")];
            var b = g.Tiles[g.IndexOf("dk65-04")];
            var goA = new GameObject("A"); var goB = new GameObject("B");
            try
            {
                var ra = goA.AddComponent<WorldRegionRoot>(); var rb = goB.AddComponent<WorldRegionRoot>();
                ra.anchorX = a.anchorX; ra.anchorY = a.anchorY; ra.anchorZ = a.anchorZ;
                rb.anchorX = b.anchorX; rb.anchorY = b.anchorY; rb.anchorZ = b.anchorZ;
                // The start scene of dk65-03 as imported: W = its anchor.
                var pa = TilePlacement.For(a.anchorX, a.anchorY, a.anchorZ, a);
                var pb = TilePlacement.For(a.anchorX, a.anchorY, a.anchorZ, b);
                Assert.AreEqual(new Vector3(0f, (float)-a.anchorZ, 0f), new Vector3(pa.posX, pa.posY, pa.posZ), "imported root position unchanged");
                Assert.AreEqual(Vector3.zero, new Vector3(pa.shiftX, pa.shiftY, pa.shiftZ));
                ra.PlaceAt(new Vector3(pa.posX, pa.posY, pa.posZ), new Vector3(pa.shiftX, pa.shiftY, pa.shiftZ));
                rb.PlaceAt(new Vector3(pb.posX, pb.posY, pb.posZ), new Vector3(pb.shiftX, pb.shiftY, pb.shiftZ));
                Assert.AreEqual(2048f, pb.posZ, 1e-3f, "dk65-04 lies one tile north");
                Assert.AreEqual(0f, pb.posX, 1e-3f);
                Assert.AreEqual((float)-a.anchorZ, pb.posY, 1e-3f, "heights are absolute: same vertical offset as the start tile");
                // Seam point of the route (portal dk65-03 -> dk65-04) and an arbitrary height.
                Vector3 ua = ra.ToUnity(768695.0, 599295.0, 120.0), ub = rb.ToUnity(768695.0, 599295.0, 120.0);
                Assert.Less((ua - ub).magnitude, 0.002f, $"{ua} vs {ub}");
                // Region-local point of tile B → its child position in world space equals ToUnity.
                Vector3 local = new Vector3((float)(768695.0 - b.anchorX), 120f, (float)(599295.0 - b.anchorY));
                Assert.Less((goB.transform.TransformPoint(local) - ub).magnitude, 0.002f);

                // Rebase to tile B: both roots keep the same relative geometry, B's root back at its import position.
                var qa = TilePlacement.For(b.anchorX, b.anchorY, a.anchorZ, a);
                var qb = TilePlacement.For(b.anchorX, b.anchorY, a.anchorZ, b);
                Assert.AreEqual(0f, qb.posX, 1e-4f); Assert.AreEqual(0f, qb.posZ, 1e-4f);
                Assert.AreEqual(-2048f, qa.posZ, 1e-3f);
                TilePlacement.RebaseOffset(a.anchorX, a.anchorY, b.anchorX, b.anchorY, out float ox, out float oz);
                Assert.AreEqual(0f, ox, 1e-4f); Assert.AreEqual(-2048f, oz, 1e-3f);
                Assert.AreEqual(pb.posZ + oz, qb.posZ, 1e-3f, "rebase offset moves the root to its new placement");
            }
            finally { UnityEngine.Object.DestroyImmediate(goA); UnityEngine.Object.DestroyImmediate(goB); }
        }

        [Test]
        public void Rebase_OnlyWellInsideTheNewTile()
        {
            var g = Grid(2, 1);
            Assert.IsFalse(TilePlacement.ShouldRebase(g, 1, 2048 + 50, 1024, 1024, 1024, 100), "50 m into the new tile: not yet");
            Assert.IsTrue(TilePlacement.ShouldRebase(g, 1, 2048 + 150, 1024, 1024, 1024, 100));
            Assert.IsFalse(TilePlacement.ShouldRebase(g, 1, 2048 + 150, 1024, 3072, 1024, 100), "already there");
        }

        // ------------------------------------------------------------------ edge sides

        [Test]
        public void ClosureSide_FollowsTheRoadHeading_NotTheNearestEdge()
        {
            // Rectangle -1024..1024; closure 60 m inside the north edge but 40 m from the east edge, road heading north.
            Assert.AreEqual(TileSide.N, EdgeSides.ClosureSide(984f, 964f, 0f, -1024f, -1024f, 1024f, 1024f));
            Assert.AreEqual(TileSide.E, EdgeSides.ClosureSide(964f, 984f, 90f, -1024f, -1024f, 1024f, 1024f));
            Assert.AreEqual(TileSide.W, EdgeSides.ClosureSide(-964f, 0f, 270f, -1024f, -1024f, 1024f, 1024f));
            Assert.AreEqual(TileSide.S, EdgeSides.ClosureSide(0f, -964f, 185f, -1024f, -1024f, 1024f, 1024f));
        }

        [Test]
        public void ApronSide_SplitsCornersDiagonally()
        {
            Assert.AreEqual(TileSide.None, EdgeSides.ApronSide(0f, 0f, -1024f, -1024f, 1024f, 1024f));
            Assert.AreEqual(TileSide.N, EdgeSides.ApronSide(0f, 1100f, -1024f, -1024f, 1024f, 1024f));
            Assert.AreEqual(TileSide.E, EdgeSides.ApronSide(1200f, 1100f, -1024f, -1024f, 1024f, 1024f), "corner, further east");
            Assert.AreEqual(TileSide.N, EdgeSides.ApronSide(1100f, 1200f, -1024f, -1024f, 1024f, 1024f), "corner, further north");
            Assert.AreEqual(TileSide.W, EdgeSides.FarSectorSide("FarField_far_west"));
            Assert.AreEqual(TileSide.S, EdgeSides.ApronPieceSide("Apron_S"));
        }

        [Test]
        public void ApronCornerPieces_HideUnderAReadyDiagonalTile_0308()
        {
            // DK65 staircase 06 -> 07 (W) -> 08 (N of 07 = NW of 06): 06 has W open and its NW diagonal ready.
            Assert.AreEqual(TileSide.NW, EdgeSides.ApronCorner(-1100f, 1200f, -1024f, -1024f, 1024f, 1024f));
            Assert.AreEqual(TileSide.None, EdgeSides.ApronCorner(0f, 1200f, -1024f, -1024f, 1024f, 1024f));
            Assert.AreEqual(TileSide.SE, EdgeSides.ApronPieceSide("Apron_SE"));
            int nw = EdgeSides.CornerBit(TileSide.NW);
            Assert.AreEqual(0, EdgeSides.CornerBit(TileSide.N));
            // scene with corner pieces: only the corner over the diagonal tile goes, the north strip stays
            Assert.IsFalse(EdgeSides.ApronPieceVisible(TileSide.NW, TileSide.W, nw, true));
            Assert.IsTrue(EdgeSides.ApronPieceVisible(TileSide.N, TileSide.W, nw, true));
            Assert.IsTrue(EdgeSides.ApronPieceVisible(TileSide.NE, TileSide.W, nw, true));
            Assert.IsFalse(EdgeSides.ApronPieceVisible(TileSide.SW, TileSide.W, nw, true), "a corner next to an open side");
            Assert.IsFalse(EdgeSides.ApronPieceVisible(TileSide.W, TileSide.W, nw, true));
            // the diagonal tile alone (the tile between them not loaded yet) already hides the corner
            Assert.IsFalse(EdgeSides.ApronPieceVisible(TileSide.NW, TileSide.None, nw, true));
            Assert.IsTrue(EdgeSides.ApronPieceVisible(TileSide.E, TileSide.None, nw, true));
            // no neighbour at all: the undivided apron is drawn instead of the pieces
            Assert.IsFalse(EdgeSides.ApronPieceVisible(TileSide.N, TileSide.None, 0, true));
            // older import (corner quadrants are halves of the side pieces): the side next to the diagonal tile goes whole
            Assert.IsFalse(EdgeSides.ApronPieceVisible(TileSide.N, TileSide.W, nw, false));
            Assert.IsTrue(EdgeSides.ApronPieceVisible(TileSide.E, TileSide.W, nw, false));
            Assert.IsTrue(EdgeSides.ApronPieceVisible(TileSide.S, TileSide.W, nw, false));
            // far-field sectors reach into the diagonal tile as well
            Assert.IsFalse(EdgeSides.FarSectorVisible(TileSide.N, TileSide.W, nw));
            Assert.IsFalse(EdgeSides.FarSectorVisible(TileSide.W, TileSide.W, 0));
            Assert.IsTrue(EdgeSides.FarSectorVisible(TileSide.E, TileSide.W, nw));
            Assert.IsTrue(EdgeSides.FarSectorVisible(TileSide.N, TileSide.W, 0));
        }

        [Test]
        public void UnionInsideDistance_IgnoresOpenSeams_AndCountsMissingCorners()
        {
            // Point 10 m from the north edge, 500 m from the others.
            float closed = EdgeSides.UnionInsideDistance(0f, 1014f, -1024f, -1024f, 1024f, 1024f, TileSide.None, 0);
            Assert.AreEqual(10f, closed, 1e-3f);
            float open = EdgeSides.UnionInsideDistance(0f, 1014f, -1024f, -1024f, 1024f, 1024f, TileSide.N, 0);
            Assert.AreEqual(1024f, open, 1e-3f, "north seam open: nearest closed edge is E/W/S");
            // Near the NE corner with N and E open but the NE diagonal missing: the corner point is the limit.
            float corner = EdgeSides.UnionInsideDistance(1018f, 1016f, -1024f, -1024f, 1024f, 1024f, TileSide.NE, EdgeSides.CornerBit(TileSide.NE));
            Assert.AreEqual(10f, corner, 1e-3f);
            Assert.Less(EdgeSides.UnionInsideDistance(0f, 1030f, -1024f, -1024f, 1024f, 1024f, TileSide.None, 0), 0f, "outside a closed side");
        }

        [Test]
        public void ClosureGroup_HidesOnlyWhenAllItsClosuresAreOpen()
        {
            float[] e = { 0f, 30f, 500f }, n = { 960f, 960f, 960f };
            bool[] open = { true, false, true };
            Assert.IsFalse(EdgeSides.GroupMayHide(-10f, 950f, 40f, 970f, e, n, open, 3));
            open[1] = true;
            Assert.IsTrue(EdgeSides.GroupMayHide(-10f, 950f, 40f, 970f, e, n, open, 3));
            Assert.IsFalse(EdgeSides.GroupMayHide(-900f, -900f, -800f, -800f, e, n, open, 3), "group with no known closure stays");
        }

        // ------------------------------------------------------------------ scenes in the build

        [Test]
        public void TileSceneNames_AndBuildList_CarryTheTileSceneWithItsRegion()
        {
            Assert.AreEqual("World_dk65-04_Tile", RegionScenes.TileSceneNameFor("dk65-04"));
            Assert.AreEqual("WorldC_High_Tile", RegionScenes.TileSceneNameFor(RegionScenes.RegionC, RegionScenes.HighTier));
            Assert.AreEqual("Assets/_Generated/World/dk65-04/World_dk65-04_Tile.unity", RegionScenes.TileScenePathFor("dk65-04"));
            var have = new HashSet<string>
            {
                RegionScenes.ScenePathFor("dk65-03"), RegionScenes.ScenePathFor("dk65-04"), RegionScenes.TileScenePathFor("dk65-04"),
            };
            var missing = new List<string>();
            var scenes = RegionBuildList.ComposeScenes(new[] { "Assets/Boot.unity" }, new[] { "dk65-03", "dk65-04" }, false, have.Contains, missing);
            CollectionAssert.AreEqual(new[] { "Assets/Boot.unity", RegionScenes.ScenePathFor("dk65-03"), RegionScenes.ScenePathFor("dk65-04"),
                RegionScenes.TileScenePathFor("dk65-04") }, scenes, "dk65-03 imported before ADR 0235 has no tile scene: no error");
            Assert.IsEmpty(missing);
        }

        [Test]
        public void UnavailableTile_IsNeverLoaded_AndItsSeamStaysClosed()
        {
            var g = Grid(2, 1);
            var p = new StreamingPolicy(g, new StreamingSettings());
            p.InitResident(0);
            p.SetUnavailable(1);
            var cmd = new StreamCommand[8];
            Assert.AreEqual(0, p.Decide(2000, 1024, 25f, 0f, cmd));
            Assert.IsFalse(p.NeighborReady(0, TileSide.E));
        }

        // ------------------------------------------------------------------ ADR 0273: pinned respawn tile, PC budgets, packs

        [Test]
        public void PinnedTile_IsNeverUnloaded_WhileAnUnpinnedOneIs()
        {
            foreach (bool pin in new[] { true, false })
            {
                var g = Grid(4, 1);
                var p = new StreamingPolicy(g, new StreamingSettings());
                p.InitResident(0);
                if (pin) p.SetPinned(0);
                var f = new FakeStreamer(p);
                double x = 1024; float v = 25f, dt = 0.25f;
                for (float t = 0f; x < 7500; t += dt, x += v * dt) f.Step(t, x, 1024, v, 0f);
                if (pin) Assert.AreEqual(TileState.Ready, p.StateOf(0), "pinned start tile stays (no reset over a void)\n" + string.Join("\n", f.Log));
                else Assert.AreEqual(TileState.Unloaded, p.StateOf(0), "without the pin the tile 6 km behind is gone");
                Assert.LessOrEqual(f.MaxResident, p.Settings.maxTiles);
            }
        }

        [Test]
        public void PinnedTile_CountsInTheBudget_ButTheTileAheadStillLoads()
        {
            // A16 Low: pinned C-like 124 MB far behind, current 60 MB, next 60 MB: 244 > 200, still one ahead (closed road worse).
            float[] mem = { 124f, 60f, 60f, 60f };
            var g = Grid(4, 1, (c, r) => mem[c]);
            var p = new StreamingPolicy(g, new StreamingSettings { memoryBudgetMB = 200f });
            p.InitResident(0);
            p.SetPinned(0);
            p.SetState(1, TileState.Ready);
            p.SetState(0, TileState.Ready);
            var cmd = new StreamCommand[8];
            p.UpdateCurrent(2048 + 1500, 1024);
            int n = p.Decide(2048 + 1900, 1024, 25f, 0f, cmd);   // 148 m before the seam with tile 2
            Assert.AreEqual(1, n);
            Assert.AreEqual(StreamOp.Load, cmd[0].op);
            Assert.AreEqual(2, cmd[0].tile);
            Assert.IsTrue(p.OverBudget);
            Assert.AreEqual(TileState.Ready, p.StateOf(0), "the pinned tile is not evicted to make room");
            p.SetPinned(-1);
            Assert.AreEqual(-1, p.Pinned);
            p.SetPinned(99);
            Assert.AreEqual(-1, p.Pinned, "out of range clears the pin");
        }

        [Test]
        public void Budgets_DesktopTiers_CoverTheWorstCorridorSetPlusPinnedC_PhoneUnchanged()
        {
            Assert.AreEqual(200f, StreamingSettings.BudgetForTier("Low", false));
            Assert.AreEqual(400f, StreamingSettings.BudgetForTier("Medium", false));
            Assert.AreEqual(600f, StreamingSettings.BudgetForTier("Ultra", false));
            Assert.AreEqual(850f, StreamingSettings.BudgetForTier("Low", true));   // owner 18.11 (ADR 0290)
            Assert.AreEqual(800f, StreamingSettings.BudgetForTier("Medium", true));
            Assert.AreEqual(2000f, StreamingSettings.BudgetForTier("High", true));
            Assert.AreEqual(2000f, StreamingSettings.BudgetForTier("Ultra", true));
            var g = TileGraph.LoadDefault();
            int c = g.IndexOf("bialystok-industrial-c");
            foreach (bool high in new[] { false, true })
            {
                var st = new StreamingSettings { highContent = high };
                float worst3 = 0f;
                for (int i = 0; i < g.Count; i++)
                {
                    float a = 0f, b = 0f;   // two heaviest neighbours
                    foreach (int j in g.Neighbors[i])
                    {
                        float m = st.MemoryOf(g.Tiles[j]);
                        if (m > a) { b = a; a = m; } else if (m > b) b = m;
                    }
                    worst3 = Math.Max(worst3, st.MemoryOf(g.Tiles[i]) + a + b);
                }
                float need = worst3 + st.MemoryOf(g.Tiles[c]);
                float budget = StreamingSettings.BudgetForTier(high ? "High" : "Low", true);
                TestContext.WriteLine($"{(high ? "High" : "Low")}: worst 3 tiles {worst3:F1} MB + pinned C {st.MemoryOf(g.Tiles[c]):F1} = {need:F1} <= {budget}");
                Assert.LessOrEqual(need, budget, high ? "PC High" : "PC Low");
            }
        }

        [Test]
        public void MemoryOf_HighContentUsesHighValues_OrAConservativeFallback()
        {
            var t = new TileData { worldMemoryMB = 100f, worldMemoryHighMB = 230f };
            Assert.AreEqual(100f, new StreamingSettings().MemoryOf(t));
            Assert.AreEqual(230f, new StreamingSettings { highContent = true }.MemoryOf(t));
            t.worldMemoryHighMB = 0f;   // graph without High values
            Assert.AreEqual(100f * StreamingSettings.HighOverLowFallback, new StreamingSettings { highContent = true }.MemoryOf(t), 1e-3f);
            var g = TileGraph.LoadDefault();
            for (int i = 0; i < g.Count; i++) Assert.Greater(g.Tiles[i].worldMemoryHighMB, g.Tiles[i].worldMemoryMB, g.Tiles[i].id);
        }

        [Test]
        public void ShippedCorridor_PcTiers_PinnedStart_NeverOverBudgetNorInATileNotReady()
        {
            // Worst case of ADR 0273 §8: no safe pose ever, so the start tile C stays pinned for the whole corridor.
            var g = TileGraph.LoadDefault();
            CorridorData d67 = null;
            foreach (var cor in g.Corridors) if (cor.tiles[0] == "bialystok-industrial-c") d67 = cor;
            var pts = new List<Vector2d>();
            int c = g.IndexOf(d67.tiles[0]);
            pts.Add(new Vector2d(g.Tiles[c].anchorX, g.Tiles[c].anchorY));
            for (int i = 1; i < d67.tiles.Length; i++)
                foreach (var po in g.Portals)
                    if (po.from == d67.tiles[i - 1] && po.to == d67.tiles[i]) pts.Add(new Vector2d(po.x, po.y));
            int k = g.IndexOf("knyszyn");
            pts.Add(new Vector2d(g.Tiles[k].anchorX, g.Tiles[k].anchorY));
            foreach (string tier in new[] { "Low", "Medium", "High", "Ultra" })
            {
                var p = new StreamingPolicy(g, new StreamingSettings
                {
                    memoryBudgetMB = StreamingSettings.BudgetForTier(tier, true),
                    highContent = tier == "High" || tier == "Ultra",
                });
                p.InitResident(c);
                p.SetPinned(c);
                var f = new FakeStreamer(p);
                float t = 0f, v = 25f, dt = 0.25f;
                int over = 0;
                for (int i = 1; i < pts.Count; i++)
                {
                    double ex = pts[i].x - pts[i - 1].x, ey = pts[i].y - pts[i - 1].y, len = Math.Sqrt(ex * ex + ey * ey);
                    float vx = (float)(ex / len * v), vy = (float)(ey / len * v);
                    for (double s = 0; s < len; s += v * dt, t += dt)
                    {
                        double x = pts[i - 1].x + ex / len * s, y = pts[i - 1].y + ey / len * s;
                        f.Step(t, x, y, vx, vy);
                        if (p.OverBudget) over++;
                        for (int j = 0; j < g.Count; j++)
                            if (g.Contains(j, x, y, -0.5))
                                Assert.AreEqual(TileState.Ready, p.StateOf(j), $"[PC {tier}] t={t:F1}s in {g.Tiles[j].id} before ready\n" + string.Join("\n", f.Log));
                    }
                }
                Assert.AreEqual(TileState.Ready, p.StateOf(c), $"[PC {tier}] pinned C kept");
                Assert.AreEqual(0, over, $"[PC {tier}] no over-budget load");
                Assert.LessOrEqual(f.MaxMemory, p.Settings.memoryBudgetMB, $"[PC {tier}]");
                TestContext.WriteLine($"[PC {tier}] budget {p.Settings.memoryBudgetMB} MB: loads {f.Loads}, unloads {f.Unloads}, max {f.MaxResident} tiles / {f.MaxMemory:F1} MB (ESTIMATED)");
            }
        }
    }
}
