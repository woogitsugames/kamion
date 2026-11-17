using System;
using System.Collections.Generic;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// The imported world regions the start menu can offer and the build can ship (ADR 0229): id, Polish label, start
    /// distance on the region's start route. Data: <c>Resources/Regions/region_catalog.json</c> (authored ids, labels,
    /// order, aliases and named sets; route length and start distance refreshed by scripts/export-region-catalog.py from
    /// Data/Regions/&lt;id&gt;/route_start.json). The same file resolves the build argument <c>-Regions</c>
    /// (Game.Editor.Build.RegionBuildList), so the menu and the build never disagree about names.
    /// Loaded once in the Boot scene; nothing here runs in the driving loop.
    /// </summary>
    [Serializable]
    public sealed class RegionCatalog
    {
        public const string ResourcePath = "Regions/region_catalog";
        public const string Schema = "truck-sim-pl/region-catalog/1";
        /// <summary>Region ids are also tried with this prefix, so "dojlidy" means "bialystok-dojlidy".</summary>
        public const string CityPrefix = "bialystok-";
        /// <summary>Token for every region of the catalog.</summary>
        public const string AllToken = "all";

        [Serializable]
        public sealed class Region
        {
            public string id = "";
            public string label = "";
            public string group = "";
            /// <summary>Length of the start route (route_start.json length_m) [m]; 0 = unknown.</summary>
            public float routeLengthM;
            /// <summary>Spawn distance along the start route [m]; &lt; 0 = <see cref="RegionStart.DefaultStartS"/>.</summary>
            public float startS = -1f;
            /// <summary>ADR 0231 §5a: corner tile without any standalone start (corridor stretch too short for a start
            /// behind the entry closure); streamed as part of the corridor only, the start menu does not offer it.</summary>
            public bool noStart;
        }

        [Serializable]
        public sealed class Alias
        {
            public string alias = "";
            public string region = "";
        }

        [Serializable]
        public sealed class Set
        {
            public string name = "";
            public string[] regions = Array.Empty<string>();
        }

        public string schema = "";
        public Region[] regions = Array.Empty<Region>();
        public Alias[] aliases = Array.Empty<Alias>();
        public Set[] sets = Array.Empty<Set>();

        /// <summary>Parses the catalog JSON; throws <see cref="FormatException"/> on a wrong schema, an empty or duplicate id.</summary>
        public static RegionCatalog Parse(string json)
        {
            if (string.IsNullOrWhiteSpace(json)) throw new FormatException("empty region catalog");
            var c = JsonUtility.FromJson<RegionCatalog>(json);
            if (c == null) throw new FormatException("region catalog: not JSON");
            if (c.schema != Schema) throw new FormatException("region catalog schema '" + c.schema + "', expected " + Schema);
            c.regions ??= Array.Empty<Region>();
            c.aliases ??= Array.Empty<Alias>();
            c.sets ??= Array.Empty<Set>();
            var seen = new HashSet<string>(StringComparer.Ordinal);
            foreach (var r in c.regions)
            {
                if (r == null || string.IsNullOrEmpty(r.id)) throw new FormatException("region catalog: entry without id");
                if (!seen.Add(r.id)) throw new FormatException("region catalog: duplicate id " + r.id);
                if (string.IsNullOrEmpty(r.label)) r.label = r.id;
            }
            return c;
        }

        /// <summary>The catalog shipped in Resources, or null when missing / broken (logged).</summary>
        public static RegionCatalog Load()
        {
            var ta = Resources.Load<TextAsset>(ResourcePath);
            if (ta == null) { Debug.LogWarning("[REGIONS] Resources/" + ResourcePath + ".json missing"); return null; }
            try { return ParseOrNull(ta.text); }
            finally { Resources.UnloadAsset(ta); }
        }

        /// <summary>
        /// <see cref="Parse"/> that never throws: any exception (a wrong schema, but also the ArgumentException of
        /// JsonUtility on broken JSON) is logged and gives null, so the menu is built without the region row (ADR 0267).
        /// </summary>
        public static RegionCatalog ParseOrNull(string json)
        {
            try { return Parse(json); }
            catch (Exception e) { Debug.LogError("[REGIONS] region catalog unreadable, no region row: " + e.GetType().Name + ": " + e.Message); return null; }
        }

        public int IndexOf(string id)
        {
            for (int i = 0; i < regions.Length; i++) if (regions[i].id == id) return i;
            return -1;
        }

        public Region Find(string id)
        {
            int i = IndexOf(id);
            return i >= 0 ? regions[i] : null;
        }

        /// <summary>One region name to its catalog id: exact id, alias, or id with <see cref="CityPrefix"/>; null when unknown.</summary>
        public string ResolveId(string token)
        {
            if (string.IsNullOrEmpty(token)) return null;
            string t = token.Trim().ToLowerInvariant();
            if (IndexOf(t) >= 0) return t;
            foreach (var a in aliases) if (a != null && string.Equals(a.alias, t, StringComparison.OrdinalIgnoreCase)) return a.region;
            if (IndexOf(CityPrefix + t) >= 0) return CityPrefix + t;
            return null;
        }

        Set FindSet(string name)
        {
            foreach (var s in sets) if (s != null && string.Equals(s.name, name, StringComparison.OrdinalIgnoreCase)) return s;
            return null;
        }

        static readonly char[] k_Separators = { ',', ';', ' ', '\t', '\n', '\r', '\u00A0' };   // ADR 0267: also a no-break space

        /// <summary>
        /// Region list of a build specification, in order, without duplicates. Tokens (separated by commas, semicolons or
        /// white space): a region id, an alias ("c"), an id without "bialystok-" ("dojlidy"), a set name ("d67"), "all",
        /// a range "a..b" (catalog order, both ends included) or a lone "..." / "…" between two names (the same range).
        /// Unknown names are reported in <paramref name="errors"/> and skipped.
        /// </summary>
        public List<string> Resolve(string spec, List<string> errors)
        {
            var result = new List<string>();
            if (string.IsNullOrWhiteSpace(spec)) return result;
            var tokens = spec.Split(k_Separators, StringSplitOptions.RemoveEmptyEntries);
            string pendingRangeFrom = null;
            for (int i = 0; i < tokens.Length; i++)
            {
                string t = tokens[i].Trim();
                if (t == "..." || t == "…")
                {
                    pendingRangeFrom = result.Count > 0 ? result[result.Count - 1] : null;
                    if (pendingRangeFrom == null) errors?.Add("'" + t + "' without a region before it");
                    continue;
                }
                int dots = t.IndexOf("..", StringComparison.Ordinal);
                if (dots > 0 && dots + 2 < t.Length)
                {
                    AddRange(ResolveId(t.Substring(0, dots)), ResolveId(t.Substring(dots + 2).TrimStart('.')), t, result, errors);
                    pendingRangeFrom = null;
                    continue;
                }
                if (string.Equals(t, AllToken, StringComparison.OrdinalIgnoreCase))
                {
                    foreach (var r in regions) AddUnique(result, r.id);
                    pendingRangeFrom = null;
                    continue;
                }
                var set = FindSet(t);
                if (set != null)
                {
                    foreach (var r in set.regions)
                    {
                        string id = ResolveId(r);
                        if (id != null) AddUnique(result, id); else errors?.Add("set " + set.name + ": unknown region '" + r + "'");
                    }
                    pendingRangeFrom = null;
                    continue;
                }
                string one = ResolveId(t);
                if (one == null) { errors?.Add("unknown region '" + t + "' (catalog: Resources/" + ResourcePath + ".json)"); pendingRangeFrom = null; continue; }
                if (pendingRangeFrom != null) AddRange(pendingRangeFrom, one, pendingRangeFrom + "..." + one, result, errors);
                else AddUnique(result, one);
                pendingRangeFrom = null;
            }
            if (pendingRangeFrom != null) errors?.Add("'...' without a region after it");
            return result;
        }

        void AddRange(string from, string to, string token, List<string> result, List<string> errors)
        {
            int a = IndexOf(from), b = IndexOf(to);
            if (a < 0 || b < 0) { errors?.Add("range '" + token + "': unknown end"); return; }
            int step = a <= b ? 1 : -1;
            for (int i = a; ; i += step)
            {
                AddUnique(result, regions[i].id);
                if (i == b) break;
            }
        }

        static void AddUnique(List<string> list, string id)
        {
            if (!list.Contains(id)) list.Add(id);
        }
    }
}
