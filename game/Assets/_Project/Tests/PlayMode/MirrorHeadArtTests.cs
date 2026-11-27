using Game.UI.Driving;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0340 / 0344 addenda (critic build #10): the procedural art of the monitor mirror head and of the
    /// warning tile - generated once, usable, and the glass film leaves the middle of the mirror readable (D70).</summary>
    public class MirrorHeadArtTests
    {
        [Test]
        public void Film_VeilEverywhere_DirtAtTheRim_MiddleStaysUsable()
        {
            MirrorWindowArt.FilmHeadStats(out float midMax, out float rimMean);
            Assert.LessOrEqual(midMax, MirrorWindowArt.FilmMidMax, "middle third of the glass");
            Assert.GreaterOrEqual(midMax, MirrorWindowArt.FilmVeil - 0.01f, "the contrast veil covers the whole glass");
            Assert.Greater(rimMean, 2.5f * MirrorWindowArt.FilmVeil, "dirt is held along the rim");
            Assert.That(MirrorWindowArt.FilmVeil, Is.InRange(0.03f, 0.10f), "contrast lowered slightly, not a fogged glass");
        }

        [Test]
        public void HeadArmAndLensSprites_AreBuiltOnce_WithUsableSlices()
        {
            var head = MirrorWindowArt.Head();
            Assert.AreSame(head, MirrorWindowArt.Head());
            Assert.Greater(head.border.x, 0f);
            Assert.Less(head.border.x + head.border.z, head.rect.width, "a stretchable centre is left");
            var arm = MirrorWindowArt.Arm();
            Assert.AreEqual(MirrorWindowArt.ArmLength / MirrorWindowArt.ArmHeight, arm.rect.width / arm.rect.height, 0.02f);
            var lens = DrivingHud.TelltaleLens();
            Assert.AreSame(lens, DrivingHud.TelltaleLens());
            Assert.Less(lens.border.y + lens.border.w, lens.rect.height);
            // the 52-unit telltale row can hold the sliced lens without overlapping borders (2 px per unit)
            Assert.LessOrEqual((lens.border.y + lens.border.w) / 2f, Game.Controls.DesktopHudLayout.TelltaleSize.y);
        }
    }
}
