using System;
using System.IO;
using System.Linq;
using Game.Core.About;
using Xunit;

namespace AboutRunner.Tests
{
    /// <summary>Parser contract + the real screen text (same assertions as Game.Tests.AttributionDocumentTests in EditMode).</summary>
    public class AttributionDocumentTests
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

        static AttributionDocument Real() => AttributionDocument.Parse(Resolve(AttributionDocument.ResourcePath));

        [Fact]
        public void Parse_SplitsHeadingsParagraphsIncludesAndDropsComments()
        {
            var d = AttributionDocument.Parse("# note UNVERIFIED\r\n= Mapy\n== OSM\nline 1\n# hidden\nline 2\n\nnext\n@include Fonts/X\n");
            var k = d.Blocks.Select(b => b.Kind).ToArray();
            Assert.Equal(new[] { AttributionBlockKind.Section, AttributionBlockKind.Entry, AttributionBlockKind.Paragraph,
                                 AttributionBlockKind.Paragraph, AttributionBlockKind.Include }, k);
            Assert.Equal("Mapy", d.Blocks[0].Text);
            Assert.Equal("OSM", d.Blocks[1].Text);
            Assert.Equal("line 1\nline 2", d.Blocks[2].Text);
            Assert.Equal("next", d.Blocks[3].Text);
            Assert.Equal("Fonts/X", d.Blocks[4].Text);
            Assert.Equal(new[] { "Fonts/X" }, d.Includes());
            Assert.DoesNotContain("UNVERIFIED", d.VisibleText(_ => "x"));
        }

        [Fact]
        public void Parse_EmptyAndBom()
        {
            Assert.Empty(AttributionDocument.Parse(null).Blocks);
            Assert.Empty(AttributionDocument.Parse("").Blocks);
            var d = AttributionDocument.Parse("﻿= A");
            Assert.Equal(AttributionBlockKind.Section, d.Blocks[0].Kind);
            Assert.Equal("A", d.Blocks[0].Text);
        }

        [Fact]
        public void Problems_FlagVisibleMarkersAndMissingIncludes()
        {
            var d = AttributionDocument.Parse("= A\nadres: [ADRES]\n@include Missing\n");
            var p = d.Problems(_ => null);
            Assert.Contains(p, x => x.Contains("[ADRES"));
            Assert.Contains(p, x => x.Contains("missing include Missing"));
            Assert.Contains("document is empty", AttributionDocument.Parse("# only\n").Problems(null));
        }

        [Theory]
        [InlineData(1)]
        [InlineData(7)]
        [InlineData(64)]
        [InlineData(3000)]
        public void Chunk_KeepsTextAndLimit(int max)
        {
            string text = string.Join("\n", Enumerable.Range(0, 400).Select(i => i % 9 == 0 ? "" : new string((char)('a' + i % 26), 1 + i % 5)));
            var c = AttributionDocument.Chunk(text, max);
            Assert.All(c, s => Assert.True(s.Length <= max, $"chunk {s.Length} > {max}"));
            if (max >= 5) Assert.Equal(text, string.Join("\n", c));
            else Assert.Equal(text.Replace("\n", ""), string.Concat(c).Replace("\n", ""));
        }

        [Fact]
        public void Chunk_HardCutsLongLines()
        {
            var c = AttributionDocument.Chunk(new string('x', 10) + "\nab", 4);
            Assert.Equal(new[] { "xxxx", "xxxx", "xx", "ab" }, c);
            Assert.Equal(new[] { "xxxx", "xxxx" }, AttributionDocument.Chunk(new string('x', 8), 4));
        }

        // ------------------------------------------------------------------ the real screen text

        [Fact]
        public void RealText_HasNoProblems()
        {
            var d = Real();
            Assert.NotEmpty(d.Blocks);
            Assert.Empty(d.Problems(Resolve));
        }

        [Theory]
        [InlineData("© OpenStreetMap contributors")]
        [InlineData("Open Database License (ODbL) 1.0")]
        [InlineData("www.openstreetmap.org/copyright")]
        [InlineData("Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl)")]
        [InlineData("CC BY 4.0")]
        [InlineData("research G3 s8-signs")]
        [InlineData("Mapillary contributors")]
        [InlineData("The Inter Project Authors")]
        [InlineData("SIL OPEN FONT LICENSE Version 1.1")]
        [InlineData("Unity glTFast copyright © 2023 Unity Technologies and the Unity glTFast authors")]
        [InlineData("TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION")]
        public void RealText_ShowsRequiredNotice(string needle)
        {
            Assert.Contains(needle, Real().VisibleText(Resolve));
        }

        [Fact]
        public void RealText_ChunksFitUiText()
        {
            foreach (var inc in Real().Includes())
                Assert.All(AttributionDocument.Chunk(Resolve(inc), AttributionDocument.UiChunkChars),
                           s => Assert.True(s.Length <= AttributionDocument.UiChunkChars));
        }
    }
}
