using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace PhysicsRunner.Sim
{
    /// <summary>Validation scenario (tests/physics/scenarios/*.json).</summary>
    public sealed class Scenario
    {
        public int schemaVersion = 1;
        public string id = "";
        public string description = "";
        /// <summary>docs/04 section 6 item number(s) this scenario covers.</summary>
        public string spec = "";
        public string vehicle = "tractor_4x2_generic";
        public GroundSpec ground = new GroundSpec();
        public InitialSpec initial = new InitialSpec();
        public double duration = 10;
        public double dt = 0.01;
        public int substeps = 4;
        public DriverSpec driver = new DriverSpec();
        public CheckSpec[] checks = Array.Empty<CheckSpec>();

        public static Scenario Load(string path)
        {
            var s = JsonSerializer.Deserialize<Scenario>(File.ReadAllText(path), DefinitionSet.Json);
            if (s == null) throw new FormatException(path);
            if (s.schemaVersion != 1) throw new FormatException($"{path}: unsupported schemaVersion");
            return s;
        }

        public static List<Scenario> LoadAll(string dir)
        {
            var list = new List<Scenario>();
            var files = Directory.GetFiles(dir, "*.json");
            Array.Sort(files, StringComparer.Ordinal);
            foreach (var f in files) list.Add(Load(f));
            return list;
        }
    }

    public sealed class GroundSpec
    {
        public double gradePercent;
        public string surface = "dry_asphalt";
        public BoxSpec[] boxes = Array.Empty<BoxSpec>();
    }

    public sealed class BoxSpec
    {
        public double minX, maxX, minZ, maxZ, height;
        public string surface = "dry_asphalt";
    }

    public sealed class InitialSpec
    {
        public double speedKmh;
        /// <summary>Initial gear when moving (0 = neutral). Ignored when speed is 0.</summary>
        public int gear;
        public double headingDeg;
        public double x, z;
    }

    public sealed class DriverSpec
    {
        /// <summary>"timeline", "circle" or "speedhold".</summary>
        public string type = "timeline";
        public KeySpec[] keys = Array.Empty<KeySpec>();
        public double targetKmh;
        public double radius;
        /// <summary>+1 = turn right (clockwise seen from above), -1 = left.</summary>
        public int direction = 1;
        public double steer;
        public string selector = "D";
    }

    public sealed class KeySpec
    {
        public double t;
        public double throttle;
        public double brake;
        public double steer;
        public bool parkingBrake;
        public string selector = "D";
    }

    public sealed class CheckSpec
    {
        public string metric = "";
        /// <summary>Optional metric argument (e.g. target speed for time_to_kmh).</summary>
        public double arg;
        public double from;
        public double? min;
        public double? max;
        /// <summary>Source of the expected value / tolerance, or WORKING_VALUE rationale.</summary>
        public string source = "";
        /// <summary>SOURCED / DERIVED / WORKING_VALUE.</summary>
        public string status = "WORKING_VALUE";
    }
}
