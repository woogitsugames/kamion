using System;
using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;

namespace Game.World.Import
{
    /// <summary>
    /// ADR 0174: where the importer reads the generated street library (street_props.glb + props_meta.json, sign faces,
    /// furniture / plot textures) of a region. Mirror of tools/worldgen/roads/build_world.py props_library_dir() (ADR 0166):
    /// the reference region C owns the shared library in git (art-source/world/{props,signs,textures}); every other region
    /// writes its own next to its world output, Data/raw/derived/&lt;id&gt;/{props,signs,textures} (not in git).
    /// A file the region library does not contain falls back to the shared one (textures the street generator does not
    /// write, e.g. vehicle_lod_details_*). Region C never looks outside art-source, so its import is unchanged.
    /// Vegetation, landmarks, PBR sets and Megascans stay shared for every region.
    /// </summary>
    public static class WorldLibrary
    {
        /// <summary>build_world.SHARED_LIBRARY_REGION - keep the two in sync.</summary>
        public const string SharedRegion = "bialystok-industrial-c";

        static readonly HashSet<string> s_PerRegionKinds = new HashSet<string>(StringComparer.Ordinal) { "props", "signs", "textures" };

        public static string SharedPath(string kind, string file) =>
            Path.Combine(EditorTools.RepoRoot, "art-source", "world", kind, file);

        /// <summary>Region library directory of one kind, or null for the reference region / shared-only kinds.</summary>
        public static string RegionDir(string region, string kind)
        {
            if (string.IsNullOrEmpty(region) || region == SharedRegion || !s_PerRegionKinds.Contains(kind)) return null;
            return Path.Combine(EditorTools.RepoRoot, "Data", "raw", "derived", region, kind);
        }

        /// <summary>Path of <paramref name="file"/> in the library of <paramref name="kind"/> used by <paramref name="region"/>.</summary>
        public static string Resolve(string region, string kind, string file)
        {
            string dir = RegionDir(region, kind);
            if (dir != null)
            {
                string p = Path.Combine(dir, file);
                if (File.Exists(p)) return p;
            }
            return SharedPath(kind, file);
        }

        /// <summary>True when the region has its own generated prop library (street_props.glb).</summary>
        public static bool HasRegionProps(string region) =>
            RegionDir(region, "props") is string d && File.Exists(Path.Combine(d, "street_props.glb"));
    }
}
