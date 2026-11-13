using System;
using System.IO;
using System.Reflection;
using System.Text.RegularExpressions;
using Game.Editor.Build;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0174: per-region street library. Region C (reference) reads only art-source/world/{props,signs,textures};
    /// another region reads Data/raw/derived/&lt;id&gt;/{props,signs,textures} with a per-file fallback to the shared library.
    /// The importer lives in Game.World.Import.Editor (not referenced by this assembly; asmdef changes are lead-only),
    /// so the API is reached by reflection.
    /// </summary>
    public class WorldLibraryTests
    {
        const string C = "bialystok-industrial-c";
        const string Other = "bialystok-dojlidy";

        static MethodInfo Method(string name)
        {
            var t = Type.GetType("Game.World.Import.WorldLibrary, Game.World.Import.Editor");
            Assert.NotNull(t, "Game.World.Import.WorldLibrary not found");
            var m = t.GetMethod(name, BindingFlags.Public | BindingFlags.Static);
            Assert.NotNull(m, name);
            return m;
        }

        static string Resolve(string region, string kind, string file) =>
            Path.GetFullPath((string)Method("Resolve").Invoke(null, new object[] { region, kind, file }));

        static string Shared(string kind, string file) =>
            Path.GetFullPath(Path.Combine(EditorTools.RepoRoot, "art-source", "world", kind, file));

        [Test]
        public void SharedRegion_MatchesGenerator()
        {
            var t = Type.GetType("Game.World.Import.WorldLibrary, Game.World.Import.Editor");
            Assert.NotNull(t);
            string cs = (string)t.GetField("SharedRegion").GetValue(null);
            string py = File.ReadAllText(Path.Combine(EditorTools.RepoRoot, "tools", "worldgen", "roads", "build_world.py"));
            var m = Regex.Match(py, @"^SHARED_LIBRARY_REGION\s*=\s*""([^""]+)""", RegexOptions.Multiline);
            Assert.IsTrue(m.Success, "SHARED_LIBRARY_REGION not found in build_world.py");
            Assert.AreEqual(m.Groups[1].Value, cs);
            Assert.AreEqual(C, cs);
        }

        [Test]
        public void ReferenceRegion_ReadsOnlyArtSource()
        {
            foreach (var (kind, file) in new[] { ("props", "street_props.glb"), ("props", "props_meta.json"), ("signs", "B-20.png"), ("textures", "plot_kit.png") })
                Assert.AreEqual(Shared(kind, file), Resolve(C, kind, file), $"{kind}/{file}");
        }

        [Test]
        public void OtherRegion_UsesOwnLibrary_FallsBackPerFile()
        {
            string dir = Path.Combine(EditorTools.RepoRoot, "Data", "raw", "derived", Other, "props");
            if (!File.Exists(Path.Combine(dir, "street_props.glb")))
                Assert.Ignore($"{dir} not generated (build_world.py --region {Other})");
            Assert.AreEqual(Path.GetFullPath(Path.Combine(dir, "street_props.glb")), Resolve(Other, "props", "street_props.glb"));
            Assert.AreEqual(Shared("textures", "no_such_texture_0174.png"), Resolve(Other, "textures", "no_such_texture_0174.png"));
            // Vegetation / landmarks / PBR sets are shared for every region.
            Assert.AreEqual(Shared("vegetation", "trees.glb"), Resolve(Other, "vegetation", "trees.glb"));
        }
    }
}
