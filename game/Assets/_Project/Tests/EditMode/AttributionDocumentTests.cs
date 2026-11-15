using System.Linq;
using Game.Core.About;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// "Informacje" screen text (Resources/About/attributions.txt, LICENSES-AUDIT-S20 R-P0-1): parser contract and the
    /// notices every build must show. The same assertions run in plain .NET: tools/about-runner (dotnet test).
    /// </summary>
    public class AttributionDocumentTests
    {
        static string Resolve(string resourcePath)
        {
            var ta = Resources.Load<TextAsset>(resourcePath);
            return ta != null ? ta.text : null;
        }

        static AttributionDocument Real()
        {
            string text = Resolve(AttributionDocument.ResourcePath);
            Assert.IsNotNull(text, "Resources/" + AttributionDocument.ResourcePath + " missing");
            return AttributionDocument.Parse(text);
        }

        [Test]
        public void Parse_SplitsHeadingsParagraphsIncludesAndDropsComments()
        {
            var d = AttributionDocument.Parse("# note UNVERIFIED\r\n= Mapy\n== OSM\nline 1\n# hidden\nline 2\n\nnext\n@include Fonts/X\n");
            CollectionAssert.AreEqual(new[] { AttributionBlockKind.Section, AttributionBlockKind.Entry, AttributionBlockKind.Paragraph,
                                              AttributionBlockKind.Paragraph, AttributionBlockKind.Include }, d.Blocks.Select(b => b.Kind).ToArray());
            Assert.AreEqual("line 1\nline 2", d.Blocks[2].Text);
            Assert.AreEqual("Fonts/X", d.Blocks[4].Text);
            StringAssert.DoesNotContain("UNVERIFIED", d.VisibleText(_ => "x"));
        }

        [Test]
        public void Problems_FlagVisibleMarkersAndMissingIncludes()
        {
            var p = AttributionDocument.Parse("= A\nadres: [ADRES]\n@include Missing\n").Problems(_ => null);
            Assert.IsTrue(p.Any(x => x.Contains("[ADRES")));
            Assert.IsTrue(p.Any(x => x.Contains("missing include Missing")));
        }

        [Test]
        public void Chunk_KeepsTextAndLimit()
        {
            string text = string.Join("\n", Enumerable.Range(0, 400).Select(i => i % 9 == 0 ? "" : new string((char)('a' + i % 26), 1 + i % 5)));
            var c = AttributionDocument.Chunk(text, 64);
            Assert.IsTrue(c.All(s => s.Length <= 64));
            Assert.AreEqual(text, string.Join("\n", c));
        }

        [Test]
        public void RealText_HasNoProblems()
        {
            var d = Real();
            CollectionAssert.IsNotEmpty(d.Blocks);
            CollectionAssert.IsEmpty(d.Problems(Resolve));
        }

        [TestCase("© OpenStreetMap contributors")]
        [TestCase("Open Database License (ODbL) 1.0")]
        [TestCase("Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl)")]
        [TestCase("CC BY 4.0")]
        [TestCase("research G3 s8-signs")]
        [TestCase("Mapillary contributors")]
        [TestCase("SIL OPEN FONT LICENSE Version 1.1")]
        [TestCase("Unity glTFast copyright © 2023 Unity Technologies and the Unity glTFast authors")]
        [TestCase("TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION")]
        public void RealText_ShowsRequiredNotice(string needle)
        {
            StringAssert.Contains(needle, Real().VisibleText(Resolve));
        }
    }
}
