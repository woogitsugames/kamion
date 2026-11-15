using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using Game.Core;
using Game.Gameplay;
using Game.Vehicle.Runtime;
using Game.World;
using Game.World.Streaming;
using NUnit.Framework;
using Unity.Profiling;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0235 scenario for the lead: route autopilot from dk65-03 into dk65-04 (seam y = 599295, portal x = 768695)
    /// with the neighbour streamed additively. Records every frame (dt, GC bytes allocated in the frame, tile states,
    /// vehicle position) to artifacts/streaming-0235/dk65-03-04-frames.csv. Asserts: dk65-04 Ready before the truck
    /// reaches the seam, the seam closures disabled at the crossing, no safety-net reset, the truck 300 m into dk65-04,
    /// one origin rebase with the truck back near (0, 0, 0). Frame time / GC numbers are logged, not asserted (the editor
    /// is not the phone: the gate is the A16 run).
    /// Needs World_dk65-03 and World_dk65-04_Tile in the build (scripts/import-region.ps1 for both after ADR 0235).
    /// </summary>
    public class WorldStreamingPlayModeTests
    {
        const string StartScene = "World_dk65-03";
        const double SeamY = 599295.0;

        [UnityTest, Timeout(300000)]
        public IEnumerator Dk65_03_To_04_RouteAutopilot_LoadsTheNeighbourAdditively()
        {
            string tileScene = RegionScenes.TileSceneNameFor("dk65-04");
            if (!Application.CanStreamedLevelBeLoaded(StartScene) || !Application.CanStreamedLevelBeLoaded(tileScene))
                Assert.Ignore($"{StartScene} / {tileScene} not in the build - run scripts/import-region.ps1 -Region dk65-03 and -Region dk65-04");
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(StartScene, LoadSceneMode.Single);
            yield return null;
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            Assert.IsNotNull(boot); Assert.IsNotNull(body);
            var streamer = boot.Streamer;
            Assert.IsNotNull(streamer, "world scene with a neighbour tile scene in the build installs the streamer");
            Assert.AreEqual(TileState.Ready, streamer.StateOf("dk65-03"));
            int rebases0 = FloatingOrigin.ShiftCount;

            boot.SetRouteSpawn(12f);
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
            Assert.IsTrue(boot.StartRouteDriver("50"));

            using var gc = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC Allocated In Frame");
            var ci = CultureInfo.InvariantCulture;
            // Preallocated rows: the test itself must not allocate in the measured frames (the GC column is the evidence).
            const int MaxRows = 20000;
            var rT = new float[MaxRows]; var rDt = new float[MaxRows]; var rGc = new long[MaxRows]; var rS3 = new int[MaxRows]; var rS4 = new int[MaxRows];
            var rX = new double[MaxRows]; var rY = new double[MaxRows]; var rV = new float[MaxRows]; var rR = new int[MaxRows];
            int rows = 0;
            var dts = new List<float>(MaxRows);
            float t0 = Time.time;
            bool appended = false, crossed = false;
            float readyMarginM = float.NaN;
            int gcFrames = 0; long gcMax = 0;
            int resets0 = boot.SafetyNet != null ? boot.SafetyNet.ResetCount : 0;
            while (Time.time - t0 < 180f)
            {
                yield return null;
                Vector3 p = body.transform.position;
                double x = streamer.AnchorX + p.x, y = streamer.AnchorY + p.z;
                var s04 = streamer.StateOf("dk65-04");
                if (float.IsNaN(readyMarginM) && s04 == TileState.Ready) readyMarginM = (float)(SeamY - y);
                if (!appended && s04 == TileState.Ready)
                {
                    var r04 = streamer.RouteOf("dk65-04");
                    Assert.IsNotNull(r04, "tile scene carries its start route");
                    boot.RouteDriver.AppendPath(r04.WorldPoints(), r04.speedLimitsKmh);
                    appended = true;
                }
                if (!crossed && y >= SeamY)
                {
                    crossed = true;
                    Assert.AreEqual(TileState.Ready, s04, "dk65-04 must be ready before the truck reaches the seam");
                    AssertSeamOpen(streamer);
                }
                long g = gc.LastValue;
                if (g > 0) { gcFrames++; if (g > gcMax) gcMax = g; }
                dts.Add(Time.unscaledDeltaTime * 1000f);
                if (rows < MaxRows)
                {
                    rT[rows] = Time.time - t0; rDt[rows] = Time.unscaledDeltaTime * 1000f; rGc[rows] = g;
                    rS3[rows] = (int)streamer.StateOf("dk65-03"); rS4[rows] = (int)s04; rX[rows] = x; rY[rows] = y; rV[rows] = body.SpeedKmh;
                    rR[rows] = boot.SafetyNet != null ? boot.SafetyNet.ResetCount - resets0 : -1;
                    rows++;
                }
                if (y >= SeamY + 300.0) break;
            }
            string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "artifacts", "streaming-0235"));
            Directory.CreateDirectory(dir);
            var csv = new StringBuilder("t_s,dt_ms,gc_bytes,state_03,state_04,x_epsg,y_epsg,speed_kmh,resets\n");
            for (int i = 0; i < rows; i++)
                csv.AppendFormat(ci, "{0:F3},{1:F2},{2},{3},{4},{5:F2},{6:F2},{7:F1},{8}\n", rT[i], rDt[i], rGc[i], rS3[i], rS4[i], rX[i], rY[i], rV[i], rR[i]);
            File.WriteAllText(Path.Combine(dir, "dk65-03-04-frames.csv"), csv.ToString());
            dts.Sort();
            float P(float q) => dts.Count > 0 ? dts[Mathf.Clamp(Mathf.CeilToInt(q * dts.Count) - 1, 0, dts.Count - 1)] : 0f;
            Debug.Log(string.Format(ci, "[STREAM-TEST] frames {0}: dt p50 {1:F1} / p95 {2:F1} / p99 {3:F1} / max {4:F1} ms; GC frames {5} (max {6} B); " +
                "dk65-04 ready {7:F0} m before the seam; load {8:F0} ms, activation {9:F0} ms, rebase {10:F2} ms",
                dts.Count, P(0.5f), P(0.95f), P(0.99f), P(1f), gcFrames, gcMax, readyMarginM, streamer.LastLoadMs, streamer.LastActivationMs, streamer.LastRebaseMs));

            Assert.IsTrue(crossed, "the truck reached the seam with dk65-04 within 180 s");
            Assert.Greater(readyMarginM, 0f, "ready before the seam");
            Vector3 pe = body.transform.position;
            Assert.GreaterOrEqual(streamer.AnchorY + pe.z, SeamY + 300.0 - 1.0, "300 m into dk65-04");
            if (boot.SafetyNet != null) Assert.AreEqual(resets0, boot.SafetyNet.ResetCount, "no safety-net reset across the seam");
            Assert.Greater(FloatingOrigin.ShiftCount, rebases0, "origin moved to dk65-04");
            Assert.Less(new Vector2(pe.x, pe.z).magnitude, 1500f, "truck near the new origin after the rebase");
        }

        static void AssertSeamOpen(WorldStreamer streamer)
        {
            // Closures of dk65-03 on its north side and of dk65-04 on its south side are disabled once both are Ready.
            foreach (var root in Object.FindObjectsByType<WorldRegionRoot>(FindObjectsSortMode.None))
            {
                var edge = root.transform.Find("WorldEdge");
                var b = root.GetComponent<WorldBoundary>();
                if (edge == null || b == null) continue;
                TileSide seam = root.regionId == "dk65-03" ? TileSide.N : root.regionId == "dk65-04" ? TileSide.S : TileSide.None;
                if (seam == TileSide.None) continue;
                foreach (Transform c in edge)
                {
                    if (!c.name.StartsWith("Closure_") || c.name.StartsWith("ClosureGroup_")) continue;
                    var side = EdgeSides.ClosureSide(c.localPosition.x, c.localPosition.z, c.localEulerAngles.y, b.minEN.x, b.minEN.y, b.maxEN.x, b.maxEN.y);
                    if (side == seam) Assert.IsFalse(c.gameObject.activeSelf, $"{root.regionId}/{c.name} still closes the seam");
                }
            }
        }
    }
}
