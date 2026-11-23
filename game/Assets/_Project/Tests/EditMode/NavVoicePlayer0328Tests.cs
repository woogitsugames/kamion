using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using Game.Core.Navigation;
using Game.Editor.Audio;
using Game.Editor.Build;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0328: GPS voice "Kamion GPS" - every clip <see cref="NavVoice"/> can order exists in the pack (manifest, WAV,
    /// imported AudioClip, bank lookup), the playback queue never overlaps announcements and the player plays in order.
    /// </summary>
    public sealed class NavVoicePlayer0328Tests
    {
        static readonly string[] Streets =
        {
            "Generała Władysława Andersa", "Generała Stanisława Maczka", "Aleja Tysiąclecia Państwa Polskiego", "Bitwy Białostockiej",
            "Białostoczek", "Kombatantów", "Michała Motoszko", "Stefana Batorego", "Władysława Bełzy", "Wileńska", "Sokólska",
            "Grodzieńska", "Brzeska", "Buska", "Kowieńska", "Lidzka", "Olsztyńska", "Racławicka", "Sitarska", "Skidelska",
            "Wołkowyska", "Łańcucka", "Świsłocka",
        };

        /// <summary>Every key the NavVoice functions can return (same choice as <see cref="NavVoice.PlanBand"/>).</summary>
        static HashSet<VoiceClip> OrderableKeys()
        {
            var s = new HashSet<VoiceClip>();
            foreach (Maneuver m in System.Enum.GetValues(typeof(Maneuver)))
            {
                for (int band = 0; band <= NavVoice.NowBand; band++)
                {
                    if (m == Maneuver.Arrive) { s.Add(new VoiceClip(10, 11)); continue; }
                    if (m == Maneuver.Continue) { s.Add(new VoiceClip(10, 5)); continue; }
                    byte blk = NavVoice.BandBlock[band];
                    int idx;
                    if (blk == 6)
                    {
                        idx = NavVoice.ManIndexKm(m, band == 0);
                        if (idx == 0) { blk = 5; idx = NavVoice.ManIndex(m); }
                    }
                    else idx = NavVoice.ManIndex(m);
                    if (idx > 0) s.Add(new VoiceClip(blk, (byte)idx));
                }
                var t = NavVoice.ThenClip(m);
                if (t.Block != 0) s.Add(t);
            }
            foreach (float turn in new[] { 0f, 90f, 179f })
                for (byte exit = 0; exit <= 7; exit++) s.Add(NavVoice.RoundaboutExitClip(turn, exit));
            for (byte lanes = 1; lanes <= 6; lanes++)
                for (uint mask = 1; mask < (1u << lanes); mask++)
                {
                    var l = NavVoice.LaneClip(lanes, mask);
                    if (l.Block != 0) s.Add(l);
                }
            foreach (var n in Streets) { var c = NavVoice.StreetClip(n); Assert.AreNotEqual(0, c.Block, n); s.Add(c); }
            s.Add(NavVoice.RoundaboutNameClip("Rondo Krzysztofa Jakuba Putry"));
            s.Add(NavVoice.RoundaboutNameClip("Rondo Pamięci Bieżeństwa"));
            return s;
        }

        [Test]
        public void Orderable_Keys_Count_Is_96()
        {
            // B01..B05 x 8, B06 x 10, B07 x 7, B08 x 7, B09 x 5, B10 #5 #11, B12 x 12, B13 x 11, B14 x 2 (tools/audio/gps/pack.py)
            Assert.AreEqual(96, OrderableKeys().Count);
        }

        [Test]
        public void Manifest_Covers_Every_Orderable_Key_With_A_Valid_Wav()
        {
            var man = GpsVoiceImporter.ReadManifest();
            Assert.IsNotNull(man, GpsVoiceImporter.ManifestPath);
            var have = new Dictionary<VoiceClip, GpsVoiceImporter.Clip>();
            foreach (var c in man.clips)
            {
                var k = new VoiceClip((byte)c.block, (byte)c.index);
                Assert.IsFalse(have.ContainsKey(k), "duplicate key " + c.key);
                have[k] = c;
                Assert.AreEqual($"GPS_B{c.block:00}_{c.index:00}", c.key);
                Assert.IsFalse(string.IsNullOrEmpty(c.text), c.key);
                Assert.That(c.lufs, Is.InRange(-17.5f, -15.5f), c.key + " loudness");
            }
            foreach (var k in OrderableKeys())
            {
                Assert.IsTrue(have.TryGetValue(k, out var c), "no clip for " + k);
                string wav = Path.Combine(EditorTools.ProjectRoot, GpsVoiceImporter.VoiceDir, c.file);
                Assert.IsTrue(File.Exists(wav), wav);
                var bytes = File.ReadAllBytes(wav);
                Assert.Greater(bytes.Length, 1000, wav + " (LFS pointer instead of audio?)");
                using var sha = SHA256.Create();
                string hex = System.BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant();
                Assert.AreEqual(c.sha256, hex, wav);
            }
            Assert.AreEqual(OrderableKeys().Count, man.clips.Length, "pack has clips the code never orders");
        }

        [Test]
        public void Imported_Bank_Resolves_Every_Orderable_Key()
        {
            Assert.IsTrue(GpsVoiceImporter.Import());
            var bank = AssetDatabase.LoadAssetAtPath<NavVoiceBank>(GpsVoiceImporter.BankPath);
            Assert.IsNotNull(bank);
            Assert.IsNotNull(MonoScript.FromScriptableObject(bank), "NavVoiceBank must live in NavVoiceBank.cs (player serialisation)");
            bank.Build();
            foreach (var k in OrderableKeys())
            {
                var clip = bank.Get(k);
                Assert.IsNotNull(clip, "bank misses " + k);
                Assert.AreEqual(1, clip.channels, k.ToString());
                Assert.That(clip.length, Is.InRange(0.3f, 4f), k.ToString());
            }
            Assert.IsNull(bank.Get(11, 1), "B11 is not ordered by the code and not in the pack");
            Assert.IsNull(bank.Get(0, 0));
            var imp = (AudioImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(bank.Get(new VoiceClip(4, 1))));
            Assert.AreEqual(AudioClipLoadType.DecompressOnLoad, imp.defaultSampleSettings.loadType);
            Assert.AreEqual(AudioCompressionFormat.PCM, imp.GetOverrideSampleSettings(VehicleAudioPostprocessor.PcGroup).compressionFormat);
        }

        [Test]
        public void Queue_Plays_In_Order_And_Newer_Pending_Announcement_Replaces_Older()
        {
            var q = new NavVoiceClipQueue();
            q.Begin(); q.Add(new VoiceClip(4, 1)); q.Add(new VoiceClip(12, 1));
            Assert.IsTrue(q.TryNext(out var c, out bool first));
            Assert.AreEqual(new VoiceClip(4, 1), c); Assert.IsTrue(first);
            // a new announcement while the first one speaks: the first finishes, then the new one
            q.Begin(); q.Add(new VoiceClip(1, 1));
            Assert.IsTrue(q.TryNext(out c, out bool n2)); Assert.AreEqual(new VoiceClip(12, 1), c); Assert.IsFalse(n2);
            // another announcement before the waiting one started: the waiting one is dropped
            q.Begin(); q.Add(new VoiceClip(8, 2)); q.Add(new VoiceClip(9, 1));
            Assert.IsTrue(q.TryNext(out c, out bool n3)); Assert.AreEqual(new VoiceClip(8, 2), c); Assert.IsTrue(n3);
            Assert.IsTrue(q.TryNext(out c, out _)); Assert.AreEqual(new VoiceClip(9, 1), c);
            Assert.IsFalse(q.TryNext(out _, out _));
            Assert.AreEqual(1, q.Dropped);
        }

        [Test]
        public void Queue_Is_Bounded_And_Ignores_Empty_Keys()
        {
            var q = new NavVoiceClipQueue();
            q.Begin();
            Assert.IsFalse(q.Add(default));
            for (int i = 0; i < NavVoiceClipQueue.Capacity; i++) Assert.IsTrue(q.Add(new VoiceClip(2, 1)));
            Assert.IsFalse(q.Add(new VoiceClip(2, 2)));
            Assert.AreEqual(NavVoiceClipQueue.Capacity, q.Count);
        }

        [Test]
        public void Player_Hooks_Announcer_And_Plays_Clips_In_Order_Without_Overlap()
        {
            var bank = ScriptableObject.CreateInstance<NavVoiceBank>();
            var a = AudioClip.Create("a", 4410, 1, 44100, false);
            var b = AudioClip.Create("b", 4410, 1, 44100, false);
            bank.blocks = new byte[] { 4, 12 }; bank.indices = new byte[] { 1, 1 }; bank.clips = new[] { a, b };
            var go = new GameObject("navvoice-test");
            try
            {
                var ann = new NavVoiceAnnouncer();
                var p = NavVoicePlayer.Install(go, ann, bank);
                Assert.IsNotNull(p);
                Assert.IsTrue(ann.Active, "player subscribes to Spoken");
                var buf = new[] { new VoiceClip(4, 1), new VoiceClip(7, 99), new VoiceClip(12, 1) };
                p.Enqueue(buf, 3);
                var seen = new List<AudioClip>();
                AudioClip last = null;
                for (int i = 0; i < 200 && seen.Count < 2; i++)
                {
                    p.Step(0.02f);
                    if (p.Source.clip != last) { last = p.Source.clip; seen.Add(last); }
                    if (p.Speaking) p.Source.Stop();   // EditMode: end the clip at once, the gap logic still applies
                }
                CollectionAssert.AreEqual(new[] { a, b }, seen);
                Assert.AreEqual(1, p.Missing, "unknown key skipped");
                Assert.AreEqual(2, p.Played);
                Assert.AreEqual(0f, p.Source.spatialBlend, "2D cab voice");
            }
            finally
            {
                Object.DestroyImmediate(go);
                Object.DestroyImmediate(bank);
                Object.DestroyImmediate(a); Object.DestroyImmediate(b);
            }
        }
    }
}
