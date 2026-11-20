using System;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.Editor.VisualQA
{
    public static class WorldNeighbourQa
    {
        // D95: the roundabout is ~40 m from a tile seam. A single-tile capture showed the closed edge and a straight,
        // differently shaded apron stub in place of the real road. Load actual tile scenes; never hide a closure over void.
        public static void Prepare(string qualityTier)
        {
            var start = UnityEngine.Object.FindAnyObjectByType<Game.World.WorldRegionRoot>();
            var graph = Game.World.Streaming.TileGraph.LoadDefault();
            string requested = EditorTools.Arg("-qaNeighbours",
                start != null && Game.World.Streaming.EdgeClosureRules.NeedsNeighbourContext(graph, start.regionId) ? "knyszyn-w" : "");
            if (string.IsNullOrWhiteSpace(requested)) return;
            if (start == null) throw new InvalidOperationException("QA neighbours require an imported world scene");
            int index = graph != null ? graph.IndexOf(start.regionId) : -1;
            if (index < 0) throw new InvalidOperationException("QA start region is missing from tile_graph.json");
            var host = new GameObject("VisualQaNeighbourContext");
            var streamer = host.AddComponent<Game.World.Streaming.WorldStreamer>();
            streamer.enabled = false; // static capture: no async load, route driving or origin rebases
            streamer.Init(graph, index, start);
            string content = Game.World.RegionScenes.UsesHighContent(qualityTier) ? "High" : "Low";
            foreach (string id in requested.Split(',').Select(s => s.Trim()).Where(s => s.Length > 0))
            {
                int next = graph.IndexOf(id);
                if (next < 0 || !graph.Neighbors[index].Contains(next))
                    throw new ArgumentException("QA context must be a graph neighbour: " + id);
                string path = Game.World.RegionScenes.TileScenePathFor(id, content);
                if (!File.Exists(Path.Combine(EditorTools.ProjectRoot, path)))
                    throw new FileNotFoundException("Import the QA neighbour in the same content tier first", path);
                var scene = EditorSceneManager.OpenScene(path, OpenSceneMode.Additive);
                var root = scene.GetRootGameObjects().Select(go => go.GetComponent<Game.World.WorldRegionRoot>())
                    .SingleOrDefault(r => r != null && r.regionId == id);
                if (root == null) throw new InvalidOperationException("QA neighbour scene has no region root: " + path);
                streamer.AdoptVisualQaTile(root);
                Debug.Log($"[VISUALQA] real neighbour {id}, content {content}; seam opened after collision cook");
            }
        }

    }
}
