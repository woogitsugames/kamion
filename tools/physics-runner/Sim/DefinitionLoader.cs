using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    /// <summary>Loads vehicle/engine/gearbox/tire JSON definitions (System.Text.Json, public fields).</summary>
    public sealed class DefinitionSet
    {
        public readonly Dictionary<string, VehicleDefinition> Vehicles = new Dictionary<string, VehicleDefinition>();
        public readonly Dictionary<string, EngineDefinition> Engines = new Dictionary<string, EngineDefinition>();
        public readonly Dictionary<string, GearboxDefinition> Gearboxes = new Dictionary<string, GearboxDefinition>();
        public readonly Dictionary<string, TireDefinition> Tires = new Dictionary<string, TireDefinition>();

        public static readonly JsonSerializerOptions Json = new JsonSerializerOptions
        {
            IncludeFields = true,
            ReadCommentHandling = JsonCommentHandling.Skip,
            AllowTrailingCommas = true,
        };

        public static DefinitionSet LoadDirectory(string dir)
        {
            var set = new DefinitionSet();
            foreach (var f in Directory.GetFiles(dir, "*.json"))
            {
                string text = File.ReadAllText(f);
                string name = Path.GetFileName(f);
                if (name.EndsWith(".vehicle.json")) { var d = Deserialize<VehicleDefinition>(text, f); d.Validate(); set.Vehicles[d.id] = d; }
                else if (name.EndsWith(".engine.json")) { var d = Deserialize<EngineDefinition>(text, f); d.Validate(); set.Engines[d.id] = d; }
                else if (name.EndsWith(".gearbox.json")) { var d = Deserialize<GearboxDefinition>(text, f); d.Validate(); set.Gearboxes[d.id] = d; }
                else if (name.EndsWith(".tire.json")) { var d = Deserialize<TireDefinition>(text, f); d.Validate(); set.Tires[d.id] = d; }
            }
            return set;
        }

        static T Deserialize<T>(string text, string path)
        {
            var r = JsonSerializer.Deserialize<T>(text, Json);
            if (r == null) throw new FormatException($"Empty definition: {path}");
            return r;
        }

        public VehicleModel CreateModel(string vehicleId, SolverSettings settings)
        {
            var v = Vehicles[vehicleId];
            return new VehicleModel(v, Engines[v.engineId], Gearboxes[v.gearboxId], Tires, settings);
        }
    }

    public static class RepoPaths
    {
        /// <summary>Walks up from the current/base directory until it finds the repo root (CLAUDE.md + game/).</summary>
        public static string Root
        {
            get
            {
                foreach (var start in new[] { AppContext.BaseDirectory, Directory.GetCurrentDirectory() })
                {
                    var d = new DirectoryInfo(start);
                    while (d != null)
                    {
                        if (File.Exists(Path.Combine(d.FullName, "CLAUDE.md")) && Directory.Exists(Path.Combine(d.FullName, "game")))
                            return d.FullName;
                        d = d.Parent;
                    }
                }
                throw new DirectoryNotFoundException("Repo root not found");
            }
        }

        public static string DefinitionsDir => Path.Combine(Root, "game", "Assets", "_Project", "Vehicle", "Physics", "Definitions", "Data");
        public static string ScenariosDir => Path.Combine(Root, "tests", "physics", "scenarios");
        public static string ArtifactsDir => Path.Combine(Root, "artifacts", "physics");
    }
}
