using System;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.World.Streaming;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.Editor.VisualQA
{
    public static class WorldNeighbourQa
    {
        // D95: the roundabout is ~40 m from a tile seam. A single-tile capture showed the closed edge and a straight,
        // differently shaded apron stub in place of the real road. Load actual tile scenes; never hide a closure over void.
        //
        // world-edge-s24 (ADR 0353): "-qaNeighbours auto" is the default. Every edge neighbour on a side where the tile
        // closes a road is loaded, so axial route frames no longer end in the red-white closure of an inner seam that the
        // streamed game opens ~380 m before the driver gets there. A neighbour not imported in this content tier is
        // skipped with a warning (its seam stays closed, as in a build without that tile). Outer edges of the world stay
        // closed. "-qaNeighbours none" renders the tile alone (closure QA: edge-* cameras); an explicit list keeps the
        // old strict behaviour (missing tile = error).
        public const string Auto = "auto", None = "none";

        public static void Prepare(string qualityTier)
        {
            string requested = EditorTools.Arg("-qaNeighbours", Auto).Trim();
            if (requested.Length == 0 || string.Equals(requested, None, StringComparison.OrdinalIgnoreCase)) return;
            bool auto = string.Equals(requested, Auto, StringComparison.OrdinalIgnoreCase);

            var start = UnityEngine.Object.FindAnyObjectByType<Game.World.WorldRegionRoot>();
            var graph = TileGraph.LoadDefault();
            if (start == null)
            {
                if (auto) return; // Boot / lab scenes: nothing to stitch
                throw new InvalidOperationException("QA neighbours require an imported world scene");
            }
            int index = graph != null ? graph.IndexOf(start.regionId) : -1;
            if (index < 0)
            {
                if (auto) { Debug.Log($"[VISUALQA] neighbours auto: {start.regionId} is not in tile_graph.json, single tile"); return; }
                throw new InvalidOperationException("QA start region is missing from tile_graph.json");
            }

            string content = Game.World.RegionScenes.UsesHighContent(qualityTier) ? "High" : "Low";
            string[] ids;
            if (auto)
            {
                var closed = ClosedSides(start, graph, index);
                // Camera positions in absolute EPSG:2180 (the start tile sits at the scene origin: no rebase in QA).
                var tileData = graph.Tiles[index];
                var cams = UnityEngine.Object.FindObjectsByType<Game.Rendering.ControlCamera>(FindObjectsInactive.Include, FindObjectsSortMode.None);
                var camE = cams.Select(c => tileData.anchorX + c.transform.position.x).ToArray();
                var camN = cams.Select(c => tileData.anchorY + c.transform.position.z).ToArray();
                float radius = new StreamingSettings().BaseLoadRadiusM;
                ids = EdgeClosureRules.QaNeighbourIds(graph, index, closed, camE, camN, radius)
                    .Where(id => Imported(id, content, warn: true)).ToArray();
                Debug.Log($"[VISUALQA] neighbours auto: {start.regionId} closes roads on {closed}, {cams.Length} cameras, load radius {radius:F0} m; loading [{string.Join(",", ids)}]");
            }
            else ids = requested.Split(',').Select(s => s.Trim()).Where(s => s.Length > 0).ToArray();
            if (ids.Length == 0) return;

            var host = new GameObject("VisualQaNeighbourContext");
            var streamer = host.AddComponent<WorldStreamer>();
            streamer.enabled = false; // static capture: no async load, route driving or origin rebases
            streamer.Init(graph, index, start);
            foreach (string id in ids)
            {
                int next = graph.IndexOf(id);
                if (next < 0 || !graph.Neighbors[index].Contains(next))
                    throw new ArgumentException("QA context must be a graph neighbour: " + id);
                string path = Game.World.RegionScenes.TileScenePathFor(id, content);
                if (!Imported(id, content, warn: false))
                    throw new FileNotFoundException("Import the QA neighbour in the same content tier first", path);
                var scene = EditorSceneManager.OpenScene(path, OpenSceneMode.Additive);
                var root = scene.GetRootGameObjects().Select(go => go.GetComponent<Game.World.WorldRegionRoot>())
                    .SingleOrDefault(r => r != null && r.regionId == id);
                if (root == null) throw new InvalidOperationException("QA neighbour scene has no region root: " + path);
                streamer.AdoptVisualQaTile(root);
                Debug.Log($"[VISUALQA] real neighbour {id}, content {content}; seam opened after collision cook");
            }
        }

        static bool Imported(string id, string content, bool warn)
        {
            string path = Game.World.RegionScenes.TileScenePathFor(id, content);
            bool ok = File.Exists(Path.Combine(EditorTools.ProjectRoot, path));
            if (!ok && warn) Debug.LogWarning($"[VISUALQA] neighbour {id} not imported ({path}); its seam stays closed");
            return ok;
        }

        /// <summary>Sides of the start tile with at least one road closure (same side rule as the streamer).</summary>
        static TileSide ClosedSides(Game.World.WorldRegionRoot start, TileGraph graph, int index)
        {
            var boundary = start.GetComponentInChildren<Game.World.WorldBoundary>(true);
            if (boundary == null || boundary.closures == null) return TileSide.None;
            TileSide sides = TileSide.None;
            foreach (var c in boundary.closures)
            {
                var s = c.exitSide != TileSide.None ? c.exitSide
                    : EdgeSides.ClosureSide(c.localPos.x, c.localPos.z, c.headingDeg,
                        boundary.minEN.x, boundary.minEN.y, boundary.maxEN.x, boundary.maxEN.y);
                sides |= s;
            }
            return sides;
        }
    }
}
