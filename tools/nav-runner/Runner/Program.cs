// nav-runner console: graph quality report, golden route dump (for review/CI), scenario + timing numbers.
// Exit code 0 = all scenario checks passed.
using System;
using System.Diagnostics;
using System.Text.Json;
using Game.Core.Navigation;
using NavRunner.Sim;
using UnityEngine;

namespace NavRunner
{
    public static class Program
    {
        public static int Main(string[] args)
        {
            const string region = "bialystok-industrial-c";
            var g = RouteGraph.Load(region);
            if (g == null) { Console.WriteLine("FAIL: region graph not loaded"); return 1; }
            // --write-golden [file]: re-record length, cost and manoeuvres of every golden pair from the C# planner (after a
            // graph regeneration); ids, endpoints and justifications stay. Review the diff before committing.
            if (args.Length > 0 && args[0] == "--write-golden")
                return GoldenWriter.Write(g, args.Length > 1 ? args[1] : "tools/nav-runner/Golden/golden_routes.json");
            Console.WriteLine($"region {region}: v{g.Version}, {g.NodeCount} nodes, {g.EdgeCount} edges, {g.RestrFrom.Length} restrictions");

            Console.WriteLine("--- graph quality report ---");
            Console.Write(GraphReport.Scan(g).ToText(g));

            Console.WriteLine("--- golden routes (dump for review) ---");
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            string goldenFile = args.Length > 0 ? args[0] : "tools/nav-runner/Golden/golden_routes.json";   // CI runs from the repo root
            int checkedRoutes = 0, failed = 0;
            try
            {
                using var doc = JsonDocument.Parse(System.IO.File.ReadAllText(goldenFile));
                foreach (var r in doc.RootElement.GetProperty("routes").EnumerateArray())
                {
                    var from = r.GetProperty("from"); var to = r.GetProperty("to");
                    var a = new Vector2(from[0].GetSingle(), from[1].GetSingle());
                    var b = new Vector2(to[0].GetSingle(), to[1].GetSingle());
                    var st = planner.Plan(a, float.NaN, b, p);
                    string id = r.GetProperty("id").GetString();
                    if (st != PlanStatus.Ok) { Console.WriteLine($"{id} {r.GetProperty("label").GetString()}: PLAN {st}"); failed++; continue; }
                    checkedRoutes++;
                    double lenTol = doc.RootElement.GetProperty("lengthTolM").GetDouble();
                    bool lenOk = Math.Abs(p.Length - r.GetProperty("lengthM").GetDouble()) <= lenTol;
                    var mans = r.GetProperty("maneuvers").EnumerateArray();
                    int mk = 0; bool manOk = p.ManCount == r.GetProperty("maneuvers").GetArrayLength();
                    foreach (var m in mans)
                    {
                        if (mk >= p.ManCount || p.ManType[mk].ToString() != m.GetProperty("type").GetString()
                            || p.ManExit[mk] != m.GetProperty("exit").GetInt32()
                            || g.Names[p.ManName[mk]] != m.GetProperty("street").GetString()) manOk = false;
                        mk++;
                    }
                    Console.WriteLine($"{id} {r.GetProperty("label").GetString()}: {p.Length:F1} m ({(lenOk ? "OK" : "LEN-MISMATCH")}), {p.ManCount} man ({(manOk ? "OK" : "MAN-MISMATCH")}), cost {p.CostSeconds:F0} s, expanded {planner.LastExpanded}");
                    if (!lenOk || !manOk) failed++;
                    for (int k = 0; k < p.ManCount; k++)
                        Console.WriteLine($"    {p.ManType[k]} {p.ManTurn[k]:F0}° exit {p.ManExit[k]} at {p.S[p.ManPoint[k]]:F0} m -> {g.Names[p.ManName[k]]}");
                }
            }
            catch (Exception ex) { Console.WriteLine("golden dump failed: " + ex.Message); failed++; }
            Console.WriteLine($"golden: {checkedRoutes} planned, {failed} mismatches");

            Console.WriteLine("--- timing / GC ---");
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            Vector2 A = new Vector2(-1.7f, -897.8f), B = new Vector2(-172f, -298f);
            planner.Plan(A, float.NaN, B, p);
            for (int i = 0; i < 50; i++) tr.Update(p, p.Points[i % p.Count], 0f, 10f, 0.02f, ref gd);
            var sw = new Stopwatch();   // created outside the measured window (a Stopwatch is a 40 B object)
            long before = GC.GetAllocatedBytesForCurrentThread();
            sw.Start();
            for (int i = 0; i < 20; i++) planner.Plan(i % 2 == 0 ? A : B, float.NaN, i % 2 == 0 ? B : A, p);
            sw.Stop();
            for (int i = 0; i < 2000; i++) tr.Update(p, p.Points[(i / 3) % p.Count] + new Vector2(1f, 0f), i * 0.5f, 10f, 0.02f, ref gd);
            long bytes = GC.GetAllocatedBytesForCurrentThread() - before;
            Console.WriteLine($"plan: {sw.Elapsed.TotalMilliseconds / 20.0:F3} ms/plan, expanded {planner.LastExpanded}; 10 plans + 2000 updates: {bytes} B GC");

            Console.WriteLine(failed == 0 ? "ALL OK" : "FAILURES PRESENT");
            return failed == 0 ? 0 : 2;   // the strict 0 B GC check lives in the xUnit ZeroGc_* tests
        }
    }
}
