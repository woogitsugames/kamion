using Game.Cameras;
using Game.Controls;
using Game.Core;
using Game.Rendering;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0340 addendum 2 (critic day27 set 3): the bracket that hangs a monitor mirror head on the cab, the class II
    /// texture floor of the PC High / Ultra tiers and the (default off) grading switch of the mirror pictures shown as HUD windows.
    /// </summary>
    public class MirrorMount0340Tests
    {
        [TearDown]
        public void Reset()
        {
            MirrorOverrides.MainMinHeight = null; MirrorOverrides.Post = null; MirrorOverrides.Legacy = false; MirrorOverrides.Resolution = null;
            MirrorOverrides.TierMainMinWidth = 0; MirrorOverrides.TierMainMinHeight = 0; MirrorOverrides.TierPost = false;
            MirrorOverrides.TierWindowTexelsPerPixel = 0f; MirrorOverrides.WindowPixelHeight = 0f;
        }

        static readonly Rect k_Head = new Rect(-14f, -220f, 228f, 690f);   // 1080p head with the wide glass (window 200 x 456)

        [Test]
        public void Mount_BesideTheHead_TubeIsHorizontal_StrutMeetsItAtTheFoot()
        {
            var anchor = new Vector2(k_Head.xMax + 80f, 250f);
            MirrorWindowLayout.SolveMount(k_Head, anchor, out var m);
            Assert.IsTrue(m.Show); Assert.IsTrue(m.Strut);
            Assert.AreEqual(1, m.Side);
            Assert.AreEqual(anchor, m.Foot);
            Assert.AreEqual(anchor.y, m.TubeFrom.y, 1e-3f, "level with the mount: a horizontal tube");
            Assert.AreEqual(k_Head.xMax - MirrorWindowLayout.MountRootInset, m.TubeFrom.x, 1e-3f, "the root is under the head's outline");
            Assert.Less(m.StrutFrom.y, m.TubeFrom.y, "the strut leaves the head lower down");
            Assert.AreEqual(m.TubeFrom.x, m.StrutFrom.x, 1e-3f);
            Assert.AreEqual(1f, m.Alpha, 1e-4f);

            MirrorWindowLayout.SolveMount(k_Head, new Vector2(k_Head.xMin - 80f, 250f), out var l);
            Assert.IsTrue(l.Show); Assert.AreEqual(-1, l.Side);
            Assert.AreEqual(k_Head.xMin + MirrorWindowLayout.MountRootInset, l.TubeFrom.x, 1e-3f);
        }

        [Test]
        public void Mount_BehindTheHead_OrFarAway_ShowsNothing_AndFadesInBetween()
        {
            MirrorWindowLayout.SolveMount(k_Head, k_Head.center, out var behind);
            Assert.IsFalse(behind.Show, "the head covers its own mount");
            MirrorWindowLayout.SolveMount(k_Head, new Vector2(k_Head.xMax + 0.5f * MirrorWindowLayout.MountMinGap, 100f), out var touching);
            Assert.IsFalse(touching.Show, "no room for a bracket");
            float reach = MirrorWindowLayout.MountReach * k_Head.width;
            MirrorWindowLayout.SolveMount(k_Head, new Vector2(k_Head.xMax + 1.2f * reach, 100f), out var far);
            Assert.IsFalse(far.Show, "never stretched across the view");
            float prev = 1.01f;
            for (int i = 10; i <= 20; i++)
            {
                MirrorWindowLayout.SolveMount(k_Head, new Vector2(k_Head.xMax - MirrorWindowLayout.MountRootInset + i * 0.05f * reach, 100f), out var m);
                Assert.LessOrEqual(m.Alpha, prev + 1e-5f, "fades monotonically");
                prev = m.Alpha;
            }
            Assert.Less(prev, 0.02f, "gone at the full reach");
            MirrorWindowLayout.SolveMount(k_Head, new Vector2(float.NaN, 0f), out var nan);
            Assert.IsFalse(nan.Show);
        }

        [Test]
        public void Mount_AboveOrBelowTheHeadSide_RootStaysOffTheRoundedCorners_StrutFlipsWhenNoRoomBelow()
        {
            float lo = k_Head.yMin + MirrorWindowLayout.MountEdgePad, hi = k_Head.yMax - MirrorWindowLayout.MountEdgePad;
            MirrorWindowLayout.SolveMount(k_Head, new Vector2(k_Head.xMax + 90f, k_Head.yMax + 200f), out var above);
            Assert.AreEqual(hi, above.TubeFrom.y, 1e-3f);
            MirrorWindowLayout.SolveMount(k_Head, new Vector2(k_Head.xMax + 90f, k_Head.yMin - 200f), out var below);
            Assert.AreEqual(lo, below.TubeFrom.y, 1e-3f);
            Assert.Greater(below.StrutFrom.y, below.TubeFrom.y, "no room under the tube: the strut comes from above");
            Assert.That(below.StrutFrom.y, Is.InRange(lo, hi));
            MirrorWindowLayout.SolveMount(k_Head, new Vector2(k_Head.xMax + MirrorWindowLayout.MountMinGap + 2f, 250f), out var near);
            Assert.IsTrue(near.Show); Assert.IsFalse(near.Strut, "a mount right beside the head: the tube alone");
        }

        [Test]
        public void AimRight_NeverTurnsTheLitSideDown()
        {
            float len = MirrorWindowLayout.AimRight(Vector2.zero, new Vector2(30f, 40f), out float sx, out float deg);
            Assert.AreEqual(50f, len, 1e-3f); Assert.AreEqual(1f, sx); Assert.AreEqual(53.13f, deg, 0.01f);
            foreach (var to in new[] { new Vector2(-30f, 40f), new Vector2(-60f, 0f), new Vector2(-30f, -40f), new Vector2(70f, -20f), new Vector2(40f, 0f) })
            {
                len = MirrorWindowLayout.AimRight(Vector2.zero, to, out sx, out deg);
                Assert.That(deg, Is.InRange(-90f, 90f), "the sprite is mirrored, not turned over");
                // the sprite's +x (pivot -> far end) after scale and rotation points at the target
                Vector2 dir = Quaternion.Euler(0f, 0f, deg) * new Vector3(sx, 0f, 0f);
                Assert.AreEqual(to.normalized.x, dir.x, 1e-4f); Assert.AreEqual(to.normalized.y, dir.y, 1e-4f);
                Assert.AreEqual(to.magnitude, len, 1e-3f);
            }
            Assert.AreEqual(0f, MirrorWindowLayout.AimRight(Vector2.one, Vector2.one, out _, out _));
        }

        [TestCase(55f)]
        [TestCase(70f)]
        [TestCase(75f)]
        public void RightMount_OutsideTheCabView_BothShaftsEnterFromTheScreenEdge(float fov)
        {
            var go = new GameObject("cab view");
            try
            {
                var cam = go.AddComponent<Camera>();
                cam.fieldOfView = fov;
                var screen = new Rect(0f, 0f, 1920f, 1080f);
                var head = new Rect(1620f, 340f, 228f, 690f);
                // A pillar forward and to the right of a left-hand-drive eye point.
                Vector3 vp = RenderTextureMirror.ViewportOf(cam, new Vector3(1.65f, 0.22f, 0.70f), screen.width / screen.height);
                Assert.Greater(vp.x, 1f);
                var anchor = new Vector2(vp.x * screen.width, vp.y * screen.height);
                MirrorWindowLayout.SolveMount(head, anchor, out var right, screen, 1);
                Assert.IsTrue(right.Show && right.Strut);
                Assert.AreEqual(1, right.Side);
                Assert.AreEqual(0f, right.FootAlpha);
                Assert.AreEqual(1f, right.Alpha);
                Assert.Less(right.TubeFrom.x, head.xMax);
                Assert.Less(right.StrutFrom.y, right.TubeFrom.y);
                Assert.GreaterOrEqual(right.TubeTo.x, screen.xMax + MirrorWindowLayout.MountTube);
                Assert.GreaterOrEqual(right.StrutTo.x, screen.xMax + MirrorWindowLayout.MountTube);
                Assert.Greater(RimHeight(right.TubeFrom, right.TubeTo, screen.xMax) -
                    RimHeight(right.StrutFrom, right.StrutTo, screen.xMax), MirrorWindowLayout.MountStrut);

                var reflectedHead = new Rect(screen.width - head.xMax, head.yMin, head.width, head.height);
                MirrorWindowLayout.SolveMount(reflectedHead, new Vector2(screen.width - anchor.x, anchor.y), out var left, screen, -1);
                Assert.IsTrue(left.Show && left.Strut);
                Assert.AreEqual(-1, left.Side);
                Assert.AreEqual(screen.width - right.TubeFrom.x, left.TubeFrom.x, 1e-3f);
                Assert.AreEqual(screen.width - right.TubeTo.x, left.TubeTo.x, 1e-3f);
                Assert.AreEqual(RimHeight(right.StrutFrom, right.StrutTo, screen.xMax), RimHeight(left.StrutFrom, left.StrutTo, screen.xMin), 1e-3f);
            }
            finally { Object.DestroyImmediate(go); }
        }

        static float RimHeight(Vector2 from, Vector2 to, float rim) =>
            Mathf.LerpUnclamped(from.y, to.y, (rim - from.x) / (to.x - from.x));

        [Test]
        public void RightMount_CrossesTheRimAtTheSameHeightAsTheFoot()
        {
            var frame = new Rect(-1600f, -600f, 1900f, 1440f);
            var anchor = new Vector2(frame.xMax - 0.01f, 250f);
            MirrorWindowLayout.SolveMount(k_Head, anchor, out var inside, frame, 1);
            MirrorWindowLayout.SolveMount(k_Head, new Vector2(frame.xMax + 0.01f, anchor.y), out var outside, frame, 1);
            Assert.IsTrue(inside.Show && inside.Strut && outside.Show && outside.Strut);
            Assert.That(inside.FootAlpha, Is.InRange(0.0001f, 0.001f));
            Assert.AreEqual(0f, outside.FootAlpha);
            Assert.AreEqual(inside.Alpha, outside.Alpha, 1e-3f);
            Assert.AreEqual(inside.Foot.y, RimHeight(outside.TubeFrom, outside.TubeTo, frame.xMax), 0.1f);
            Assert.AreEqual(inside.Foot.y, RimHeight(outside.StrutFrom, outside.StrutTo, frame.xMax), 0.1f);
        }

        [Test]
        public void CabLayout_ReservesRoomAtPhysicalEdgesWithAsymmetricSafeArea()
        {
            float reserve = 14f + MirrorWindowLayout.MountEdgeGap;
            const float leftGutter = 102.4f;
            var input = new DesktopHudInput
            {
                Width = 2560f - leftGutter, ScreenWidth = 2560f, Height = 1440f,
                MirrorLeft = true, MirrorRight = true, MirrorWide = true,
                MirrorAspect = 0.445f,
                MirrorOuterLimits = new Vector2(reserve - leftGutter, reserve),
            };
            DesktopHudLayout.Solve(input, out var layout);
            Assert.IsTrue(layout.ShowMirrorLeft && layout.ShowMirrorRight && layout.ShowMirrorWide);
            Assert.GreaterOrEqual(layout.MirrorLeft.xMin + leftGutter, reserve - 1e-3f);
            Assert.GreaterOrEqual(input.Width - layout.MirrorRight.xMax, reserve - 1e-3f);
            Assert.AreEqual(layout.MirrorLeft.size, layout.MirrorRight.size);
            Assert.Less(layout.MirrorLeft.xMax, layout.ClearView.xMin);
            Assert.Greater(layout.MirrorRight.xMin, layout.ClearView.xMax);
        }

        [Test]
        public void MainHeightFor_GivesAtLeastTheFloorInBothDimensions()
        {
            Assert.AreEqual(384, VehicleCameraBudget.MainHeightFor(384, 0.445f, 0, 0), "off");
            int h = VehicleCameraBudget.MainHeightFor(384, 0.445f, 512, 1024);
            Assert.GreaterOrEqual(h, 1024);
            Assert.GreaterOrEqual(Mathf.RoundToInt(h * 0.445f), 512, "the TRAKT class II glass (0.445): wide enough too");
            Assert.AreEqual(1024, VehicleCameraBudget.MainHeightFor(384, 0.55f, 512, 1024), "a 0.55 glass: 563 x 1024");
            Assert.AreEqual(1100, VehicleCameraBudget.MainHeightFor(1100, 0.55f, 512, 1024), "never below the tier / window height");
            Assert.AreEqual(VehicleCameraBudget.MaxMainMirrorHeight, VehicleCameraBudget.MainHeightFor(384, 0.2f, 512, 1024), "capped");
        }

        [Test]
        public void MainMirrorHeight_FollowsTierOverrideAndLegacy()
        {
            int tier = VehicleCameraBudget.MirrorHeight;
            Assert.AreEqual(tier, VehicleCameraBudget.MainMirrorHeight(0.445f), "no floor on this tier");
            MirrorOverrides.TierMainMinWidth = 512; MirrorOverrides.TierMainMinHeight = 1024;
            Assert.AreEqual(Mathf.Max(tier, 1151), VehicleCameraBudget.MainMirrorHeight(0.445f));
            MirrorOverrides.MainMinHeight = 0;
            Assert.AreEqual(tier, VehicleCameraBudget.MainMirrorHeight(0.445f), "rq_mirror_main=0: A/B against the floor");
            MirrorOverrides.MainMinHeight = null; MirrorOverrides.Legacy = true;
            Assert.AreEqual(VehicleCameraBudget.MirrorHeight, VehicleCameraBudget.MainMirrorHeight(0.445f), "rq_mirror_legacy");
            MirrorOverrides.Legacy = false;
            MirrorOverrides.TierPost = true;
            Assert.IsTrue(VehicleCameraBudget.MirrorPost);
            MirrorOverrides.Post = false;
            Assert.IsFalse(VehicleCameraBudget.MirrorPost);
            MirrorOverrides.Post = null; MirrorOverrides.Legacy = true;
            Assert.IsFalse(VehicleCameraBudget.MirrorPost, "rq_mirror_legacy = the ungraded picture");
        }

        [Test]
        public void PcTiers_HighAndUltraHaveTheFloorAndGrading_LowMediumUnchanged()
        {
            var t = PcTierTable.Defaults();
            Assert.AreEqual(0, t[(int)PcTier.Low].mirrorMainMinHeight);
            Assert.AreEqual(0, t[(int)PcTier.Medium].mirrorMainMinHeight);
            foreach (var tier in new[] { PcTier.High, PcTier.Ultra })
            {
                Assert.GreaterOrEqual(t[(int)tier].mirrorMainMinWidth, 512, tier.ToString());
                Assert.GreaterOrEqual(t[(int)tier].mirrorMainMinHeight, 1024, tier.ToString());
            }
            // measured (ADR 0340 addendum 2): grading the mirror picture changes its mean by +3 % for +0.3..0.7 ms per pair - off
            foreach (var s in t) Assert.IsFalse(s.mirrorPost);
            Assert.IsEmpty(PcTierTable.Validate(t));
            t[(int)PcTier.Ultra].mirrorMainMinHeight = 512;
            Assert.IsTrue(PcTierTable.Validate(t).Exists(x => x.Contains("mirrorMainMinHeight decreases")));
        }

        [Test]
        public void ViewportOf_MatchesThePerspectiveProjection()
        {
            var go = new GameObject("cam");
            try
            {
                var cam = go.AddComponent<Camera>();
                cam.fieldOfView = 70f; cam.transform.SetPositionAndRotation(new Vector3(1f, 2f, 3f), Quaternion.Euler(6f, 20f, 0f));
                float aspect = 16f / 9f;
                Vector3 ahead = cam.transform.TransformPoint(new Vector3(0f, 0f, 5f));
                Vector3 v = RenderTextureMirror.ViewportOf(cam, ahead, aspect);
                Assert.AreEqual(0.5f, v.x, 1e-4f); Assert.AreEqual(0.5f, v.y, 1e-4f); Assert.AreEqual(5f, v.z, 1e-3f);
                float ty = Mathf.Tan(35f * Mathf.Deg2Rad);
                Vector3 corner = cam.transform.TransformPoint(new Vector3(-ty * aspect * 4f, ty * 4f, 4f));
                v = RenderTextureMirror.ViewportOf(cam, corner, aspect);
                Assert.AreEqual(0f, v.x, 1e-3f, "left edge"); Assert.AreEqual(1f, v.y, 1e-3f, "top edge");
                Assert.LessOrEqual(RenderTextureMirror.ViewportOf(cam, cam.transform.TransformPoint(new Vector3(0f, 0f, -2f)), aspect).z, 0f, "behind the camera");
            }
            finally { Object.DestroyImmediate(go); }
        }
    }
}
