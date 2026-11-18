using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using Game.Core.About;
using Xunit;

namespace AboutRunner.Tests
{
    /// <summary>
    /// ADR 0230: the "Informacje" screen text against docs/LICENSES.md. Every row of the summary table
    /// ("Tabela zbiorcza źródeł") that requires attribution in the build must be mapped in
    /// tools/licenses/attribution_requirements.json, and each mapped notice must be VISIBLE (not a # comment).
    /// Same data and rule as tools/licenses/tests/test_attributions.py (pytest).
    /// </summary>
    public class LicensesCompletenessTests
    {
        static readonly string Repo = FindRepo();
        static readonly string Resources = Path.Combine(Repo, "game", "Assets", "_Project", "UI", "Resources");

        static string FindRepo()
        {
            var d = new DirectoryInfo(AppContext.BaseDirectory);
            while (d != null && !File.Exists(Path.Combine(d.FullName, "CLAUDE.md"))) d = d.Parent;
            return d?.FullName ?? throw new InvalidOperationException("repo root (CLAUDE.md) not found");
        }

        static string Resolve(string resourcePath)
        {
            string p = Path.Combine(Resources, resourcePath.Replace('/', Path.DirectorySeparatorChar) + ".txt");
            return File.Exists(p) ? File.ReadAllText(p) : null;
        }

        static string Visible() => AttributionDocument.Parse(Resolve(AttributionDocument.ResourcePath)).VisibleText(Resolve);

        static JsonElement Requirements()
        {
            string p = Path.Combine(Repo, "tools", "licenses", "attribution_requirements.json");
            return JsonDocument.Parse(File.ReadAllText(p)).RootElement;
        }

        /// <summary>Summary table rows of docs/LICENSES.md: number -> cells.</summary>
        static Dictionary<int, string[]> SummaryRows()
        {
            string text = File.ReadAllText(Path.Combine(Repo, "docs", "LICENSES.md"));
            int start = text.IndexOf("## Tabela zbiorcza źródeł", StringComparison.Ordinal);
            Assert.True(start >= 0, "summary table heading missing in docs/LICENSES.md");
            var rows = new Dictionary<int, string[]>();
            foreach (string line in text.Substring(start).Split('\n').Skip(1))
            {
                if (line.StartsWith("## ", StringComparison.Ordinal)) break;
                var m = Regex.Match(line, @"^\|\s*(\d+)\s*\|");
                if (m.Success)
                    rows[int.Parse(m.Groups[1].Value)] = line.Trim().Trim('|').Split('|').Select(c => c.Trim()).ToArray();
            }
            return rows;
        }

        static bool NeedsAttribution(string[] cells)
        {
            string required = cells[3].ToLowerInvariant(), inBuild = cells[5].ToLowerInvariant();
            bool shown = required.StartsWith("tak") || required.StartsWith("j.w.") || required.Contains("tekst licencji");
            return shown && !inBuild.StartsWith("nie");
        }

        [Fact]
        public void SummaryTable_IsParsed()
        {
            var rows = SummaryRows();
            Assert.True(rows.Count >= 40, $"only {rows.Count} rows");
            Assert.StartsWith("OpenStreetMap", rows[1][1]);
            Assert.All(rows.Values, c => Assert.True(c.Length >= 7, "row with fewer than 7 cells: " + string.Join("|", c)));
        }

        [Fact]
        public void EveryRowRequiringAttribution_IsMapped()
        {
            var mapped = Requirements().GetProperty("rows").EnumerateObject().Select(p => int.Parse(p.Name)).ToHashSet();
            var missing = SummaryRows().Where(r => NeedsAttribution(r.Value)).Select(r => r.Key).Where(n => !mapped.Contains(n)).ToList();
            Assert.True(missing.Count == 0, "docs/LICENSES.md rows requiring attribution without a notice in " +
                                            "attribution_requirements.json: " + string.Join(", ", missing));
        }

        [Fact]
        public void MappedRows_ExistInSummaryTable()
        {
            var rows = SummaryRows();
            foreach (var p in Requirements().GetProperty("rows").EnumerateObject())
                Assert.True(rows.ContainsKey(int.Parse(p.Name)), "attribution_requirements.json maps missing row " + p.Name);
        }

        [Fact]
        public void MappedNotices_AreVisibleAndNotEmpty()
        {
            string text = Visible();
            foreach (var row in Requirements().GetProperty("rows").EnumerateObject())
            {
                var needles = row.Value.EnumerateArray().Select(e => e.GetString()).ToList();
                Assert.NotEmpty(needles);
                foreach (var n in needles)
                {
                    Assert.False(string.IsNullOrWhiteSpace(n), "empty notice for row " + row.Name);
                    Assert.True(text.Contains(n), $"row {row.Name}: '{n}' is not visible on the Informacje screen");
                }
            }
        }

        [Fact]
        public void LicenceNotices_OdblAndCcBySa_AreVisible()
        {
            string text = Visible();
            foreach (var n in Requirements().GetProperty("always_visible").EnumerateArray().Select(e => e.GetString()))
                Assert.True(text.Contains(n), $"'{n}' is not visible on the Informacje screen");
            // ODbL 4.3: notice that the data is available under this licence; CC BY-SA 3(a)(1)(c): licence URI.
            Assert.Contains("Open Database License", text);
            Assert.Contains("opendatacommons.org/licenses/odbl/1-0/", text);
            Assert.Contains("creativecommons.org/licenses/by-sa/4.0/", text);
        }

        [Fact]
        public void ForbiddenMarkers_MatchParser()
        {
            var fromJson = Requirements().GetProperty("forbidden_visible").EnumerateArray().Select(e => e.GetString()).ToArray();
            Assert.Equal(AttributionDocument.ForbiddenVisibleMarkers, fromJson);
        }

        [Fact]
        public void RealText_HasNoEmptyEntries()
        {
            var problems = AttributionDocument.Parse(Resolve(AttributionDocument.ResourcePath)).Problems(Resolve);
            Assert.DoesNotContain(problems, p => p.StartsWith("heading without text", StringComparison.Ordinal));
        }

        [Fact]
        public void Problems_FlagHeadingsWithoutText()
        {
            var p = AttributionDocument.Parse("= A\n== Empty\n== Full\ntext\n= B\n= C\n== Last\n").Problems(null);
            Assert.Contains(p, x => x == "heading without text: Entry: Empty");
            Assert.Contains(p, x => x == "heading without text: Section: B");
            Assert.Contains(p, x => x == "heading without text: Entry: Last");
            Assert.DoesNotContain(p, x => x.EndsWith(": Full") || x.EndsWith(": A") || x.EndsWith(": C"));
        }

        [Fact]
        public void CityOpenData_IsNotOnScreen()
        {
            // docs/LICENSES.md "Dane Miasta Białystok": BIP re-use terms forbid modifying the content; not in the build.
            string text = Visible();
            Assert.DoesNotContain("arcgis", text, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("Prezydent Miasta Białegostoku", text);
        }
    }
}
