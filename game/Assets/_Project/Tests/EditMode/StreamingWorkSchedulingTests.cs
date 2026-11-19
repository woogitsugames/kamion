using Game.Gameplay;
using Game.World.Streaming;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>Scheduling regressions found while investigating the DK65-10 player gap (2026-11-19).</summary>
    public class StreamingWorkSchedulingTests
    {
        static StreamingPolicy Corner(int concurrent = 1, int maxTiles = 4)
        {
            // Four 2048 m tiles meeting at (2048, 2048); all are wanted near that corner.
            var tiles = new TileData[4];
            for (int i = 0; i < tiles.Length; i++)
            {
                int x = i % 2, y = i / 2;
                tiles[i] = new TileData
                {
                    id = "t" + i, xmin = x * 2048, xmax = (x + 1) * 2048,
                    ymin = y * 2048, ymax = (y + 1) * 2048, worldMemoryMB = 10,
                };
                var neighbors = new NeighborData[3];
                int k = 0;
                for (int j = 0; j < tiles.Length; j++)
                {
                    if (j == i) continue;
                    int dx = j % 2 - x, dy = j / 2 - y;
                    string side = (dy > 0 ? "N" : dy < 0 ? "S" : "") + (dx > 0 ? "E" : dx < 0 ? "W" : "");
                    neighbors[k++] = new NeighborData { id = "t" + j, side = side };
                }
                tiles[i].neighbors = neighbors;
            }
            var policy = new StreamingPolicy(new TileGraph(new TileGraphData { tiles = tiles }),
                new StreamingSettings { maxConcurrentLoads = concurrent, maxTiles = maxTiles });
            policy.InitResident(0);
            return policy;
        }

        [Test]
        public void ActivationHoldsLoadSlotUntilReady()
        {
            var policy = Corner();
            var commands = new StreamCommand[8];
            Assert.AreEqual(1, policy.Decide(2000, 2000, 0, 0, commands));
            int first = commands[0].tile;
            Assert.AreEqual(StreamOp.Load, commands[0].op);
            Assert.AreEqual(0, policy.Decide(2000, 2000, 0, 0, commands));
            policy.SetState(first, TileState.Activating);
            Assert.AreEqual(0, policy.Decide(2000, 2000, 0, 0, commands), "cooking and activation still own the slot");
            policy.SetState(first, TileState.Ready);
            Assert.AreEqual(1, policy.Decide(2000, 2000, 0, 0, commands));
            Assert.AreEqual(StreamOp.Load, commands[0].op);
            Assert.AreNotEqual(first, commands[0].tile);
        }

        [Test]
        public void ExplicitConcurrencyCountsLoadingAndActivatingTogether()
        {
            var policy = Corner(concurrent: 2);
            var commands = new StreamCommand[8];
            policy.SetState(1, TileState.Activating);
            Assert.AreEqual(1, policy.Decide(2000, 2000, 0, 0, commands));
            Assert.AreEqual(StreamOp.Load, commands[0].op);
            Assert.AreEqual(0, policy.Decide(2000, 2000, 0, 0, commands));
        }

        [Test]
        public void FarActivatingTileIsNotDestroyedWhileCooking()
        {
            var policy = Corner();
            var commands = new StreamCommand[8];
            policy.SetState(3, TileState.Activating);
            Assert.AreEqual(0, policy.Decide(1024, 1024, 0, 0, commands));
            Assert.AreEqual(TileState.Activating, policy.StateOf(3));
            policy.SetState(3, TileState.Ready);
            Assert.AreEqual(1, policy.Decide(1024, 1024, 0, 0, commands));
            Assert.AreEqual(StreamOp.Unload, commands[0].op);
            Assert.AreEqual(3, commands[0].tile);
        }

        [Test]
        public void BudgetEvictionAlsoWaitsForActivationToFinish()
        {
            // Tile 1 is wanted; tile 3 is not wanted but is within the unload hysteresis band.
            var policy = Corner(concurrent: 2, maxTiles: 2);
            var commands = new StreamCommand[8];
            policy.SetState(3, TileState.Activating);
            Assert.AreEqual(0, policy.Decide(2000, 1500, 0, 0, commands));
            Assert.AreEqual(TileState.Activating, policy.StateOf(3));
            policy.SetState(3, TileState.Ready);
            Assert.AreEqual(1, policy.Decide(2000, 1500, 0, 0, commands));
            Assert.AreEqual(StreamOp.Unload, commands[0].op);
            Assert.AreEqual(3, commands[0].tile);
        }

        [Test]
        public void PeriodicScreenshotsSkipDebtAfter166SecondGap()
        {
            float next = 2080;
            Assert.IsTrue(DesktopAutoShot.TryTakePeriodicShot(2245, 10, -1, ref next));
            for (int i = 0; i < 60; i++)
                Assert.IsFalse(DesktopAutoShot.TryTakePeriodicShot(2245 + i / 60f, 10, -1, ref next),
                    "no screenshot burst or repeated rounded filenames after resume");
            Assert.IsFalse(DesktopAutoShot.TryTakePeriodicShot(2254, 10, -1, ref next));
            Assert.IsTrue(DesktopAutoShot.TryTakePeriodicShot(2255, 10, -1, ref next));
        }

        [Test]
        public void PeriodicScreenshotsRespectDisabledEarlyAndQuitWindows()
        {
            float next = 30;
            Assert.IsFalse(DesktopAutoShot.TryTakePeriodicShot(29, 10, -1, ref next));
            Assert.IsFalse(DesktopAutoShot.TryTakePeriodicShot(30, 0, -1, ref next));
            Assert.IsFalse(DesktopAutoShot.TryTakePeriodicShot(30, -1, -1, ref next));
            Assert.IsFalse(DesktopAutoShot.TryTakePeriodicShot(30, 10, 31, ref next));
            Assert.AreEqual(30f, next);
            Assert.IsTrue(DesktopAutoShot.TryTakePeriodicShot(30, 10, 32, ref next));
        }
    }
}
