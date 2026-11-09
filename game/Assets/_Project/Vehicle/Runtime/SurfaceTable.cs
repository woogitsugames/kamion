namespace Game.Vehicle.Runtime
{
    /// <summary>Ground surface kinds known to the driving lab. Values are stable ids (telemetry, audio).</summary>
    public enum SurfaceKind
    {
        DryAsphalt = 0,
        WetAsphalt = 1,
        Concrete = 2,
        Cobbles = 3,
        Gravel = 4,
        Grass = 5,
    }

    public struct SurfaceProps
    {
        /// <summary>Peak-friction scale relative to the tire's reference surface (dry asphalt = 1).</summary>
        public double Friction;
        /// <summary>Rolling-resistance multiplier (dry asphalt = 1).</summary>
        public double RollingResistance;
        public int Id;
    }

    /// <summary>
    /// Surface coefficient table used by <see cref="UnityGroundQuery"/>; fed into
    /// <c>GroundHit.FrictionScale/RollingResistanceScale</c> of the physics core.
    ///
    /// Provenance (all WORKING_VALUE, see docs/VEHICLE_REFERENCE_DATA.md):
    /// - dry asphalt 1.0 / 1.0, wet asphalt 0.625 / 1.05, concrete 1.0 / 0.95: copied from the physics runner
    ///   (tools/physics-runner/Sim/AnalyticGround.cs, SurfaceProps.FromName) so Unity and the runner agree.
    /// - cobbles, gravel, grass: placeholders chosen by the Stage 1 integration agent for the driving lab,
    ///   ordering only (cobbles &lt; asphalt, gravel &lt; cobbles, grass lowest; rolling resistance rising),
    ///   no source checked. Owner vehicle-physics should replace them with sourced values and move the table
    ///   into the core (request in docs/plan/STAGE-1.md).
    /// </summary>
    public static class SurfaceTable
    {
        static readonly SurfaceProps[] k_Table =
        {
            new SurfaceProps { Friction = 1.00,  RollingResistance = 1.00, Id = (int)SurfaceKind.DryAsphalt },
            new SurfaceProps { Friction = 0.625, RollingResistance = 1.05, Id = (int)SurfaceKind.WetAsphalt },
            new SurfaceProps { Friction = 1.00,  RollingResistance = 0.95, Id = (int)SurfaceKind.Concrete },
            new SurfaceProps { Friction = 0.85,  RollingResistance = 1.30, Id = (int)SurfaceKind.Cobbles },
            new SurfaceProps { Friction = 0.70,  RollingResistance = 3.00, Id = (int)SurfaceKind.Gravel },
            new SurfaceProps { Friction = 0.55,  RollingResistance = 5.00, Id = (int)SurfaceKind.Grass },
        };

        public static SurfaceProps Get(SurfaceKind kind)
        {
            int i = (int)kind;
            return i >= 0 && i < k_Table.Length ? k_Table[i] : k_Table[0];
        }

        public static string DisplayNamePl(int id)
        {
            switch ((SurfaceKind)id)
            {
                case SurfaceKind.DryAsphalt: return "asfalt suchy";
                case SurfaceKind.WetAsphalt: return "asfalt mokry";
                case SurfaceKind.Concrete: return "beton";
                case SurfaceKind.Cobbles: return "kostka";
                case SurfaceKind.Gravel: return "żwir";
                case SurfaceKind.Grass: return "trawa";
                default: return "?";
            }
        }
    }
}
