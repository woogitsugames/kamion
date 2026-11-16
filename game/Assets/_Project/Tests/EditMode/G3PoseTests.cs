using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using Game.Gameplay;
using NUnit.Framework;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0246 photo-pair capture: pose file parser, launch arguments, file names, sizes, settle rule and the [G3POSE] lines
    /// scripts/g3-poses.ps1 parses. No UnityEngine API here: the same file also runs as a plain .NET test
    /// (dotnet test tests/g3poses/G3PoseTests.csproj).
    /// </summary>
    public class G3PoseTests
    {
        const string ResourceRel = "Assets/_Project/Gameplay/Resources/g3_poses.json";

        static string FindResource()
        {
            foreach (var start in new[] { Directory.GetCurrentDirectory(), AppContext.BaseDirectory })
            {
                var d = new DirectoryInfo(start);
                for (int i = 0; d != null && i < 12; i++, d = d.Parent)
                {
                    foreach (var rel in new[] { ResourceRel, "game/" + ResourceRel })
                    {
                        string p = Path.Combine(d.FullName, rel);
                        if (File.Exists(p)) return p;
                    }
                }
            }
            Assert.Fail("g3_poses.json not found above " + Directory.GetCurrentDirectory());
            return null;
        }

        static string Pose(int index, string id, string extra = "") =>
            "{\"index\":" + index + ",\"id\":\"" + id + "\",\"kind\":\"photo_match\",\"seat\":\"file\"," +
            "\"pos\":[10,20,130],\"look_at\":[10,60,131],\"fov_deg\":60,\"out_width\":1280,\"out_height\":960" + extra + "}";

        static string FileJson(int count, params string[] poses) =>
            "{\"schema\":\"kamion/g3-poses/1\",\"region\":\"r\",\"count\":" + count + ",\"poses\":[" + string.Join(",", poses) + "]}";

        static G3Pose P(int index, string id) => new G3Pose { index = index, id = id };

        // ---------------------------------------------------------------- the real pose file

        [Test]
        public void RealFile_Has42ValidPoses_FromThePhotoPairCameras()
        {
            var errors = new List<string>();
            var f = G3PoseSet.Parse(File.ReadAllText(FindResource()), errors);
            Assert.IsNotNull(f, string.Join("; ", errors));
            CollectionAssert.IsEmpty(errors);
            Assert.AreEqual("bialystok-industrial-c", f.region);
            Assert.AreEqual(42, f.count);
            Assert.AreEqual(42, f.poses.Length);
            int a = 0, b = 0;
            var ids = new HashSet<string>();
            for (int i = 0; i < f.poses.Length; i++)
            {
                var p = f.poses[i];
                Assert.AreEqual(i + 1, p.index, p.id);
                Assert.IsTrue(ids.Add(p.id), p.id);
                StringAssert.StartsWith("sbs-g3-", p.id);
                Assert.AreEqual("photo_match", p.kind, p.id);
                Assert.AreEqual("file", p.seat, p.id);
                Assert.AreEqual("Data/Regions/bialystok-industrial-c/sbs_cameras.json", p.source.cameras_file, p.id);
                Assert.AreEqual(i, p.source.cameras_index, p.id);
                Assert.Greater(p.reference.width, 0, p.id);
                Assert.Greater(p.reference.height, 0, p.id);
                Assert.IsFalse(string.IsNullOrEmpty(p.reference.photo), p.id);
                Assert.IsFalse(string.IsNullOrEmpty(p.reference.license), p.id);
                Assert.AreEqual(1280, p.out_width, p.id);
                Assert.AreEqual(Math.Round(1280.0 * p.reference.height / p.reference.width), p.out_height, p.id);
                if (p.segment == "G3-A") a++; else if (p.segment == "G3-B") b++; else Assert.Fail("segment " + p.segment);
            }
            Assert.AreEqual(22, a);
            Assert.AreEqual(20, b);
        }

        // ---------------------------------------------------------------- parser

        [Test]
        public void Parse_RejectsWrongSchemaCountAndEmpty()
        {
            var errors = new List<string>();
            Assert.IsNull(G3PoseSet.Parse(null, errors));
            Assert.IsNull(G3PoseSet.Parse("", errors));
            Assert.IsNull(G3PoseSet.Parse("not json", errors));
            Assert.IsNull(G3PoseSet.Parse(FileJson(1, Pose(1, "a")).Replace("g3-poses/1", "g3-poses/9"), errors));
            StringAssert.Contains("schema", errors[0]);
            Assert.IsNull(G3PoseSet.Parse(FileJson(2, Pose(1, "a")), errors));
            StringAssert.Contains("count", errors[0]);
            Assert.IsNull(G3PoseSet.Parse(FileJson(0), errors));
        }

        [Test]
        public void Parse_DropsInvalidPoses_KeepsValidOnes()
        {
            var errors = new List<string>();
            var f = G3PoseSet.Parse(FileJson(8,
                Pose(1, "ok"),
                Pose(2, "ok"),                                                       // duplicate id
                Pose(3, "fov").Replace("\"fov_deg\":60", "\"fov_deg\":0"),
                Pose(4, "short").Replace("[10,20,130]", "[10,20]"),
                Pose(5, "same").Replace("[10,60,131]", "[10,20,130]"),
                Pose(6, "vertical").Replace("[10,60,131]", "[10,20,100]"),
                Pose(7, "seat").Replace("\"seat\":\"file\"", "\"seat\":\"air\""),
                Pose(8, "nosize").Replace(",\"out_width\":1280,\"out_height\":960", "")), errors);
            Assert.IsNotNull(f);
            Assert.AreEqual(1, f.poses.Length);
            Assert.AreEqual("ok", f.poses[0].id);
            Assert.AreEqual(7, errors.Count, string.Join("; ", errors));
            Assert.IsTrue(errors.Exists(e => e.Contains("duplicate")));
            Assert.IsTrue(errors.Exists(e => e.Contains("fov_deg")));
            Assert.IsTrue(errors.Exists(e => e.Contains("look_at == pos")));
            Assert.IsTrue(errors.Exists(e => e.Contains("straight up")));
            Assert.IsTrue(errors.Exists(e => e.Contains("seat")));
            Assert.IsTrue(errors.Exists(e => e.Contains("output size")));
        }

        [Test]
        public void Parse_AcceptsReferenceSizeWithoutOutputSize()
        {
            var f = G3PoseSet.Parse(FileJson(1, Pose(1, "r").Replace(",\"out_width\":1280,\"out_height\":960",
                ",\"reference\":{\"width\":2048,\"height\":1152}")), new List<string>());
            Assert.IsNotNull(f);
            Assert.AreEqual(1, f.poses.Length);
            Assert.IsTrue(G3PoseCapture.TryOutputSize(f.poses[0], 1280, out int w, out int h));
            Assert.AreEqual(1280, w);
            Assert.AreEqual(720, h);
        }

        // ---------------------------------------------------------------- filter

        [Test]
        public void Matches_IndexRangeAndIdSubstring()
        {
            var p = P(7, "sbs-g3-a-1406533339711789");
            Assert.IsTrue(G3PoseSet.Matches(p, null));
            Assert.IsTrue(G3PoseSet.Matches(p, "  "));
            Assert.IsTrue(G3PoseSet.Matches(p, "7"));
            Assert.IsFalse(G3PoseSet.Matches(p, "8"));
            Assert.IsTrue(G3PoseSet.Matches(p, "1-9"));
            Assert.IsTrue(G3PoseSet.Matches(p, "9-1"));
            Assert.IsFalse(G3PoseSet.Matches(p, "8-12"));
            Assert.IsTrue(G3PoseSet.Matches(p, "140653"));
            Assert.IsTrue(G3PoseSet.Matches(p, "SBS_G3_A"));
            Assert.IsFalse(G3PoseSet.Matches(p, "g3-b"));
            Assert.IsTrue(G3PoseSet.Matches(p, "g3-b, 7"));
            Assert.IsTrue(G3PoseSet.Matches(p, "3-a"));   // not a number range: id substring
        }

        [Test]
        public void Select_KeepsFileOrder()
        {
            var f = new G3PoseFile { poses = new[] { P(1, "sbs-g3-a-x"), P(2, "sbs-g3-b-y"), P(3, "sbs-g3-a-z") } };
            var s = G3PoseSet.Select(f, "g3-a");
            Assert.AreEqual(2, s.Count);
            Assert.AreEqual("sbs-g3-a-x", s[0].id);
            Assert.AreEqual("sbs-g3-a-z", s[1].id);
            Assert.AreEqual(0, G3PoseSet.Select(null, "").Count);
        }

        // ---------------------------------------------------------------- launch arguments

        static Func<string, string> Args(params string[] kv)
        {
            var d = new Dictionary<string, string>();
            for (int i = 0; i + 1 < kv.Length; i += 2) d[kv[i]] = kv[i + 1];
            return k => d.TryGetValue(k, out var v) ? v : null;
        }

        [Test]
        public void Args_DisabledUnlessRequested()
        {
            Assert.IsFalse(G3PoseArgs.Parse(Args()).Enabled);
            Assert.IsFalse(G3PoseArgs.Parse(Args("g3pose", "0")).Enabled);
            Assert.IsFalse(G3PoseArgs.Parse(null).Enabled);
            Assert.IsFalse(G3PoseArgs.Parse(k => throw new InvalidOperationException()).Enabled);
            Assert.IsTrue(G3PoseArgs.Parse(Args("g3pose", "1")).Enabled);
            Assert.IsTrue(G3PoseArgs.Parse(Args("g3pose", "TRUE")).Enabled);
        }

        [Test]
        public void Args_ParsesValues_AndFallsBackWithWarnings()
        {
            var w = new List<string>();
            var a = G3PoseArgs.Parse(Args("g3pose", "1", "g3pose_run", "20261115-120000", "g3pose_only", " 1-5,cm924 ",
                "g3pose_width", "640", "g3pose_settle_s", "2.5", "g3pose_settle_frames", "40", "g3pose_wait_s", "30",
                "g3pose_warmup_s", "12", "lighting", "overcast"), w);
            CollectionAssert.IsEmpty(w);
            Assert.AreEqual("20261115-120000", a.RunId);
            Assert.AreEqual("1-5,cm924", a.Filter);
            Assert.AreEqual(640, a.Width);
            Assert.AreEqual(2.5f, a.SettleSeconds);
            Assert.AreEqual(40, a.SettleFrames);
            Assert.AreEqual(30f, a.MaxWaitSeconds);
            Assert.AreEqual(12f, a.WarmupSeconds);
            Assert.AreEqual("overcast", a.Lighting);

            w.Clear();
            var b = G3PoseArgs.Parse(Args("g3pose", "1", "g3pose_run", "../../etc", "g3pose_width", "99999",
                "g3pose_settle_s", "abc", "g3pose_wait_s", "0.5", "g3pose_settle_frames", "-3"), w);
            Assert.AreEqual("etc", b.RunId);   // dots and slashes removed: no path escape
            Assert.AreEqual(G3PoseArgs.DefaultWidth, b.Width);
            Assert.AreEqual(G3PoseArgs.DefaultSettleSeconds, b.SettleSeconds);
            Assert.AreEqual(G3PoseArgs.DefaultSettleFrames, b.SettleFrames);
            Assert.AreEqual(b.SettleSeconds, b.MaxWaitSeconds);   // raised to the settle time
            Assert.AreEqual(5, w.Count, string.Join("; ", w));

            Assert.AreEqual("run", G3PoseArgs.Parse(Args("g3pose", "1", "g3pose_run", "///")).RunId);
        }

        [Test]
        public void Args_DesktopOutputDirAndQuit()
        {
            var d = G3PoseArgs.Parse(Args("g3pose", "1"));
            Assert.AreEqual("", d.OutDir);
            Assert.IsFalse(d.Quit);
            var a = G3PoseArgs.Parse(Args("g3pose", "1", "g3pose_run", "r1", "g3pose_dir", " \"C:\\k amion\\artifacts\\g3-poses\\win\\t\\overcast\" ", "g3pose_quit", "1"));
            Assert.AreEqual("C:\\k amion\\artifacts\\g3-poses\\win\\t\\overcast", a.OutDir);   // kept as given (spaces, separators), quotes dropped
            Assert.IsTrue(a.Quit);
            Assert.IsFalse(G3PoseArgs.Parse(Args("g3pose", "1", "g3pose_quit", "0")).Quit);

            // Desktop: the given folder; mobile or no argument: persistentDataPath/g3poses/<run> as before.
            Assert.AreEqual(a.OutDir, G3PoseCapture.ResolveOutputDir("/data", a.RunId, a.OutDir, false));
            Assert.AreEqual(G3PoseCapture.OutputDir("/data", "r1"), G3PoseCapture.ResolveOutputDir("/data", a.RunId, a.OutDir, true));
            Assert.AreEqual(G3PoseCapture.OutputDir("/data", "r1"), G3PoseCapture.ResolveOutputDir("/data", "r1", "  ", false));
            Assert.AreEqual(G3PoseCapture.OutputDir("/data", "r1"), G3PoseCapture.ResolveOutputDir("/data", "r1", null, false));
        }

        [Test]
        public void ShouldRun_OnlyInDevelopmentBuildsWhenRequested()
        {
            var on = G3PoseArgs.Parse(Args("g3pose", "1"));
            Assert.IsTrue(G3PoseArgs.ShouldRun(on, true, out _));
            Assert.IsFalse(G3PoseArgs.ShouldRun(on, false, out string why));
            StringAssert.StartsWith("REFUSED", why);
            Assert.IsFalse(G3PoseArgs.ShouldRun(G3PoseArgs.Parse(Args()), true, out _));
            Assert.IsFalse(G3PoseArgs.ShouldRun(null, true, out _));
        }

        // ---------------------------------------------------------------- names and sizes

        [Test]
        public void FileName_IndexFirst_Sanitised()
        {
            Assert.AreEqual("07_sbs-g3-a-1406533339711789_overcast.png", G3PoseCapture.FileName(P(7, "sbs-g3-a-1406533339711789"), "overcast"));
            Assert.AreEqual("42_sbs-g3-a-cm92458760.png", G3PoseCapture.FileName(P(42, "sbs-g3-a-cm92458760"), null));
            Assert.AreEqual("03_abc.png", G3PoseCapture.FileName(P(3, "a/b\\c"), "  "));
            Assert.AreEqual("00_pose.png", G3PoseCapture.FileName(null, ""));
        }

        [Test]
        public void OutputDir_UnderPersistentDataPath()
        {
            Assert.AreEqual(Path.Combine("/data/files", "g3poses", "20261115-120000"), G3PoseCapture.OutputDir("/data/files", "20261115-120000"));
            Assert.AreEqual(Path.Combine("/data/files", "g3poses", "run"), G3PoseCapture.OutputDir("/data/files", "../"));
        }

        [Test]
        public void OutputAndRenderSize_LikeTheEditorPairs()
        {
            var p = new G3Pose { index = 1, id = "x", out_width = 1280, out_height = 960, reference = new G3PoseReference { width = 2048, height = 1536 } };
            Assert.IsTrue(G3PoseCapture.TryOutputSize(p, 1280, out int w, out int h));
            Assert.AreEqual(1280, w); Assert.AreEqual(960, h);
            Assert.IsTrue(G3PoseCapture.TryOutputSize(p, 640, out w, out h));
            Assert.AreEqual(640, w); Assert.AreEqual(480, h);
            var wide = new G3Pose { reference = new G3PoseReference { width = 3840, height = 2160 } };
            Assert.IsTrue(G3PoseCapture.TryOutputSize(wide, 1280, out w, out h));
            Assert.AreEqual(720, h);
            Assert.IsFalse(G3PoseCapture.TryOutputSize(new G3Pose(), 1280, out _, out _));
            Assert.IsFalse(G3PoseCapture.TryOutputSize(p, 0, out _, out _));

            G3PoseCapture.RenderSize(1280, 960, 0.75f, out int rw, out int rh);   // Low renderScale 0.75
            Assert.AreEqual(960, rw); Assert.AreEqual(720, rh);
            G3PoseCapture.RenderSize(1280, 720, 0.85f, out rw, out rh);           // Medium 0.85
            Assert.AreEqual(1088, rw); Assert.AreEqual(612, rh);
            G3PoseCapture.RenderSize(10, 10, 0.5f, out rw, out rh);
            Assert.AreEqual(16, rw); Assert.AreEqual(16, rh);
            G3PoseCapture.RenderSize(100, 50, float.NaN, out rw, out rh);
            Assert.AreEqual(100, rw); Assert.AreEqual(50, rh);
        }

        // ---------------------------------------------------------------- settle

        [Test]
        public void Settle_NeedsFramesTimeAndQuietStreaming()
        {
            var s = new G3PoseSettle { MinFrames = 10, MinSeconds = 0.5f, MaxSeconds = 5f, StableFrames = 3 };
            int n = 0;
            while (s.Step(0.1f, 0) == G3PoseSettle.State.Waiting) n++;
            Assert.AreEqual(9, n);   // settles on frame 10 (t = 1.0 s >= 0.5 s, 10 quiet frames)
            Assert.IsFalse(s.TimedOut);

            s.Reset();
            int settledAt = -1;
            for (int i = 0; i < 30 && settledAt < 0; i++) if (s.Step(0.05f, i < 15 ? 4 : 0) == G3PoseSettle.State.Settled) settledAt = i;
            Assert.AreEqual(17, settledAt);   // loads until frame 14, then 3 quiet frames (15, 16, 17)
            s.Reset();
            var st = G3PoseSettle.State.Waiting;
            for (int i = 0; i < 15; i++) st = s.Step(0.05f, 2);   // loads pending: never settles before 15 frames
            Assert.AreEqual(G3PoseSettle.State.Waiting, st);
            Assert.AreEqual(2, s.LastPending);
            st = s.Step(0.05f, 0); Assert.AreEqual(G3PoseSettle.State.Waiting, st);
            st = s.Step(0.05f, 0); Assert.AreEqual(G3PoseSettle.State.Waiting, st);
            st = s.Step(0.05f, -1); Assert.AreEqual(G3PoseSettle.State.Settled, st);   // 3 quiet frames (unknown = 0)
        }

        [Test]
        public void Settle_TimesOutWhenStreamingNeverQuiets()
        {
            var s = new G3PoseSettle { MinFrames = 1, MinSeconds = 0f, MaxSeconds = 1f, StableFrames = 3 };
            var st = G3PoseSettle.State.Waiting;
            int frames = 0;
            while (st == G3PoseSettle.State.Waiting && frames < 1000) { st = s.Step(0.1f, 1); frames++; }
            Assert.AreEqual(G3PoseSettle.State.TimedOut, st);
            Assert.IsTrue(s.TimedOut);
            Assert.That(frames, Is.InRange(10, 11));   // 10 x 0.1 s in float: 1.0 +/- 1 ulp
        }

        [Test]
        public void Settle_FromArgs()
        {
            var s = new G3PoseSettle(G3PoseArgs.Parse(Args("g3pose", "1", "g3pose_settle_frames", "7", "g3pose_settle_s", "3", "g3pose_wait_s", "9")));
            Assert.AreEqual(7, s.MinFrames); Assert.AreEqual(3f, s.MinSeconds); Assert.AreEqual(9f, s.MaxSeconds);
        }

        // ---------------------------------------------------------------- log lines (parsed by scripts/g3-poses.ps1)

        [Test]
        public void LogLines_MatchTheScriptPatterns()
        {
            var done = G3PoseCapture.DoneLine("20261115-120000", 41, 1, 2, "/sdcard/x");
            var m = Regex.Match(done, @"\[G3POSE\] DONE run=(\S+) captured=(\d+) failed=(\d+) timeout=(\d+) dir=(\S+)");
            Assert.IsTrue(m.Success, done);
            Assert.AreEqual("20261115-120000", m.Groups[1].Value);
            Assert.AreEqual("41", m.Groups[2].Value);

            var s = new G3PoseSettle { MinFrames = 1, MinSeconds = 0f, StableFrames = 1 };
            s.Step(0.25f, 0);
            var shot = G3PoseCapture.ShotLine(3, 42, P(3, "sbs-g3-a-1"), "03_sbs-g3-a-1.png", 1280, 960, 960, 720, 2, s);
            Assert.IsTrue(Regex.IsMatch(shot, @"\[G3POSE\] SHOT 3/42 id=sbs-g3-a-1 file=03_sbs-g3-a-1\.png size=1280x960 render=960x720 msaa=2 frames=1 wait_s=0\.25 tex_pending=0 settled=yes$"), shot);
            var fail = G3PoseCapture.FailLine(4, 42, "x", "line1\nline2");
            Assert.AreEqual("[G3POSE] FAIL 4/42 id=x reason=line1 line2", fail);
            StringAssert.StartsWith("[G3POSE] BEGIN run=r poses=2 total=42 tier=Low lighting=default width=1280 dir=", G3PoseCapture.BeginLine("r", 2, 42, "Low", "", 1280, "/d"));
        }
    }
}
