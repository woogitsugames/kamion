// Re-records tools/nav-runner/Golden/golden_routes.json from the C# RoutePlanner (integration r6: the M35 file was
// produced by a Python port of the planner and did not match the C# code - 11/36 pairs; after the M27/M28 graph
// regeneration 28/36). Keeps id, label, from, to and because; rewrites lengthM, costS and the manoeuvre list.
using System;
using System.IO;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;
using Game.Core.Navigation;
using UnityEngine;

namespace NavRunner
{
    public static class GoldenWriter
    {
        public static int Write(RouteGraph g, string file)
        {
            var root = JsonNode.Parse(File.ReadAllText(file)).AsObject();
            root["note"] = "Golden routes for tools/nav-runner (M35). Source of truth: the region KRTG graph (OSM ODbL), NOT Google. " +
                           "Recorded from the C# RoutePlanner by `dotnet run -c Release --project tools/nav-runner/Runner -- --write-golden` " +
                           "(integration r6); re-record after every graph regeneration and review the diff.";
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            int failed = 0;
            foreach (var n in root["routes"].AsArray())
            {
                var r = n.AsObject();
                var from = r["from"].AsArray(); var to = r["to"].AsArray();
                var st = planner.Plan(new Vector2((float)from[0].GetValue<double>(), (float)from[1].GetValue<double>()), float.NaN,
                                      new Vector2((float)to[0].GetValue<double>(), (float)to[1].GetValue<double>()), p);
                if (st != PlanStatus.Ok) { Console.WriteLine($"{r["id"]}: PLAN {st}"); failed++; continue; }
                r["lengthM"] = Math.Round(p.Length, 1);
                r["costS"] = Math.Round(p.CostSeconds, 1);
                var mans = new JsonArray();
                for (int k = 0; k < p.ManCount; k++)
                    mans.Add(new JsonObject
                    {
                        ["type"] = p.ManType[k].ToString(),
                        ["turnDeg"] = Math.Round(p.ManTurn[k], 1),
                        ["exit"] = (int)p.ManExit[k],
                        ["street"] = g.Names[p.ManName[k]],
                    });
                r["maneuvers"] = mans;
            }
            var opts = new JsonSerializerOptions { WriteIndented = true, Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
            File.WriteAllText(file, root.ToJsonString(opts) + "\n");
            Console.WriteLine($"golden re-recorded: {root["routes"].AsArray().Count} pairs, {failed} not planned -> {file}");
            return failed == 0 ? 0 : 2;
        }
    }
}
