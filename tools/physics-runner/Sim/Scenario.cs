using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace PhysicsRunner.Sim
{
    /// <summary>
    /// Validation scenario (tests/physics/scenarios/*.json). A scenario with "variants" expands into one run per
    /// vehicle configuration (solo / empty / laden40 / cargo24), with id "&lt;id&gt;@&lt;variant&gt;"; checks may be
    /// restricted to a variant.
    /// </summary>
    public sealed class Scenario
    {
        public int schemaVersion = 1;
        public string id = "";
        public string description = "";
        /// <summary>docs/04 section 6 item number(s) this scenario covers.</summary>
        public string spec = "";
        public string vehicle = "tractor_4x2_generic";
        /// <summary>Vehicle configuration: "solo", "empty", "laden40", "cargo24".</summary>
        public string combination = "solo";
        public string[] variants = Array.Empty<string>();
        public string trailer = "curtainsider_tridem_13_6";
        public CargoSpec cargo = new CargoSpec();
        public GroundSpec ground = new GroundSpec();
        public InitialSpec initial = new InitialSpec();
        public OverrideSpec overrides = new OverrideSpec();
        public double duration = 10;
        public double dt = 0.01;
        public int substeps = 4;
        /// <summary>Store every n-th sample for metrics (long soak runs).</summary>
        public int sampleEvery = 1;
        /// <summary>"none" or "wheel_lift": end the run 0.3 s after the first wheel leaves the ground.</summary>
        public string endCondition = "none";
        public DriverSpec driver = new DriverSpec();
        public EventSpec[] events = Array.Empty<EventSpec>();
        public CheckSpec[] checks = Array.Empty<CheckSpec>();
        /// <summary>Set on expanded variants.</summary>
        public string variant = "";
        public string baseId = "";

        public static Scenario Load(string path)
        {
            var s = JsonSerializer.Deserialize<Scenario>(File.ReadAllText(path), DefinitionSet.Json);
            if (s == null) throw new FormatException(path);
            if (s.schemaVersion != 1) throw new FormatException($"{path}: unsupported schemaVersion");
            return s;
        }

        /// <summary>Loads all scenario files and expands variants.</summary>
        public static List<Scenario> LoadAll(string dir)
        {
            var list = new List<Scenario>();
            var files = Directory.GetFiles(dir, "*.json");
            Array.Sort(files, StringComparer.Ordinal);
            foreach (var f in files)
            {
                var s = Load(f);
                s.baseId = s.id;
                if (s.variants.Length == 0) { s.variant = s.combination; list.Add(s); continue; }
                foreach (var v in s.variants)
                {
                    var c = Load(f);
                    c.baseId = c.id;
                    c.id = c.id + "@" + v;
                    c.combination = v;
                    c.variant = v;
                    list.Add(c);
                }
            }
            return list;
        }

        public bool HasTrailer => combination != "solo";
    }

    public sealed class CargoSpec
    {
        /// <summary>Overrides the preset cargo mass when > 0.</summary>
        public double massKg;
        public double cogHeight;
        public double? cogZ;
        public double cogX;
    }

    public sealed class OverrideSpec
    {
        public bool? absEnabled;
        public bool? trailerAbsEnabled;
        public bool enduranceBrakes = true;
        /// <summary>false = EBS fault: no load-sensing (pneumatic back-up pressure on every axle).</summary>
        public bool loadSensing = true;
        /// <summary>Initial pressure of all reservoirs [bar] (default: charged to cut-out).</summary>
        public double? initialAirBar;
        /// <summary>false = start with the trailer standing on its landing gear, uncoupled.</summary>
        public bool coupled = true;
        /// <summary>Uncoupled start: kingpin distance behind the open fifth-wheel jaw [m].</summary>
        public double trailerGap = 2.0;
        /// <summary>Uncoupled start: lateral offset of the kingpin from the tractor centre line [m, + = right] (R5 hand-coupling).</summary>
        public double trailerOffset;
        /// <summary>Initial articulation (trailer yaw relative to tractor) [deg].</summary>
        public double articulationDeg;
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
        /// <summary>Initial gear when moving (0 = auto). Ignored when speed is 0.</summary>
        public int gear;
        public double headingDeg;
        public double x, z;
        public bool parkingBrake;
    }

    public sealed class DriverSpec
    {
        /// <summary>"timeline", "circle", "speedhold", "lanechange" or "soak" (repeating drive cycle).</summary>
        public string type = "timeline";
        public KeySpec[] keys = Array.Empty<KeySpec>();
        public double targetKmh;
        public double radius;
        /// <summary>+1 = turn right (clockwise seen from above), -1 = left.</summary>
        public int direction = 1;
        public double steer;
        public string selector = "D";
        public int retarderLever;
        /// <summary>circle: speed ramp [km/h per s] starting at rampStart [s] (rollover threshold search).</summary>
        public double rampKmhPerS;
        public double rampStart;
        /// <summary>circle / lanechange: at brakeAt [s] the driver brakes with brakeLevel and (optionally) freezes the steering.</summary>
        public double brakeAt = -1;
        public double brakeLevel = 1;
        public bool holdSteerOnBrake;
        /// <summary>lanechange: pure-pursuit look-ahead [s of travel] (longer = smoother, less driver-induced weave).</summary>
        public double lookaheadGain = 1.6;
        /// <summary>lanechange: start distance [m], transition length [m], offset [m], double lane change, hold length [m].</summary>
        public double startDistance = 30;
        public double length = 25;
        public double offset = 3.5;
        public bool doubleChange;
        public double holdLength = 20;
        /// <summary>speedhold: use only the endurance brakes (no service brake) when above target.</summary>
        public bool enduranceOnly;
        /// <summary>speedhold: brake pumping (on/off cycles) instead of continuous braking [s period, 0 = off].</summary>
        public double pumpPeriod;
        /// <summary>soak: cycle period [s].</summary>
        public double cyclePeriod = 90;
    }

    public sealed class KeySpec
    {
        public double t;
        public double throttle;
        public double brake;
        public double steer;
        public bool parkingBrake;
        public string selector = "D";
        public int retarderLever;
        public bool manual;
        public bool shiftUp, shiftDown;
    }

    public sealed class EventSpec
    {
        public double t;
        /// <summary>"couple_arm", "uncouple", "landing_gear_up", "landing_gear_down", "leak".</summary>
        public string type = "";
        /// <summary>leak: reservoir index (0 supply, 1 front, 2 rear, 3 park/trailer, 4 trailer reservoir).</summary>
        public int circuit;
        public double lpm;
    }

    public sealed class CheckSpec
    {
        public string metric = "";
        /// <summary>Optional metric argument (e.g. target speed for time_to_kmh).</summary>
        public double arg;
        public double from;
        public double to;
        public double? min;
        public double? max;
        /// <summary>Restricts the check to one variant ("" = all).</summary>
        public string variant = "";
        /// <summary>Source of the expected value / tolerance, or WORKING_VALUE rationale.</summary>
        public string source = "";
        /// <summary>SOURCED / DERIVED / WORKING_VALUE.</summary>
        public string status = "WORKING_VALUE";
    }
}
