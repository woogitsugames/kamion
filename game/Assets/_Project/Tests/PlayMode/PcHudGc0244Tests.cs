using System.Collections;
using Game.UI.Driving;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0244 (driving-loop GC audit), extension for the monitor HUD of ADR 0265: on a PC (touch controls hidden, mirror
    /// windows from <c>MirrorWindowLayout</c>, desktop canvas scale) the per-frame <see cref="DrivingHud"/> refresh must not
    /// allocate. 500 refreshes with varying cluster values on 16:9 and 21:9, mirror windows on, expect 0 GC.Alloc samples
    /// (<see cref="GcAllocCounter"/>, the mechanism of <c>HudTextAllocTests</c>, which covers the touch HUD).
    /// </summary>
    public class PcHudGc0244Tests
    {
        DrivingHud m_Hud;
        RenderTexture m_Mirror;

        [TearDown]
        public void TearDown()
        {
            if (m_Hud != null) Object.Destroy(m_Hud.gameObject);
            if (m_Mirror != null) { m_Mirror.Release(); Object.Destroy(m_Mirror); }
        }

        [UnityTest]
        public IEnumerator DesktopHud_MirrorWindows_500Refreshes_ZeroGcAlloc()
        {
            m_Mirror = new RenderTexture(110, 200, 16);   // class II glass aspect 0.55 (RenderTextureMirror default)
            float cruise = 0f; int lever = 0, signal = 0;
            var ctx = new DrivingHudContext
            {
                IsGyroMode = () => false,
                LeftMirrorTexture = () => m_Mirror,
                RightMirrorTexture = () => m_Mirror,
                BrakeCruiseKmh = () => cruise,
                RetarderLever = () => lever,
                TurnSignalLever = () => signal,
                TurnSignalLit = () => signal != 0,
            };
            m_Hud = DrivingHud.Create(null, ctx, overlay: true);
            yield return null;

            foreach (var px in new[] { new Vector2(1920f, 1080f), new Vector2(2560f, 1080f) })
            {
                m_Hud.OverrideScreen(px, new Rect(0f, 0f, px.x, px.y), 96f, desktop: true);
                m_Hud.RefreshNow();
                yield return null;
                Assert.IsFalse(m_Hud.TouchControlsShown, px + ": monitor HUD (touch controls hidden)");
                Assert.IsTrue(m_Hud.Layout.ShowMirrorLeft && m_Hud.Layout.ShowMirrorRight, px + ": mirror windows shown");

                for (int i = 0; i < 20; i++) m_Hud.RefreshNow();   // warm-up (prebuilt strings, first SetActive)
                int allocs = GcAllocCounter.Count(() =>
                {
                    for (int i = 0; i < 500; i++)
                    {
                        cruise = i % 3 == 0 ? 0f : 30f + (i % 61);
                        lever = i % 6;
                        signal = (i / 25) % 4 - 1;   // -1, 0, 1, 2
                        m_Hud.RefreshNow();
                    }
                });
                yield return null;
                Assert.AreEqual(0, allocs, $"{px}: 500 monitor-HUD refreshes allocated {allocs} GC.Alloc samples (expected 0)");
            }
        }

        /// <summary>
        /// ADR 0283: the monitor strip (speed / gear / air, telltale row, warning tiles) and the extended row (key I) refresh
        /// without allocation, also while the extended detail and the mirror preferences change (re-layout on
        /// <see cref="Game.Controls.HudPreferences.Version"/>), on 16:9 and 32:9.
        /// </summary>
        [UnityTest]
        public IEnumerator DesktopStrip_Extended_PrefsChanging_ZeroGcAlloc()
        {
            var saved = Game.Controls.HudPreferences.Current;
            m_Mirror = new RenderTexture(110, 200, 16);
            float cruise = 0f; int lever = 0, signal = 0; bool abs = false;
            var ctx = new DrivingHudContext
            {
                IsGyroMode = () => false,
                LeftMirrorTexture = () => m_Mirror,
                RightMirrorTexture = () => m_Mirror,
                BrakeCruiseKmh = () => cruise,
                RetarderLever = () => lever,
                TurnSignalLever = () => signal,
                TurnSignalLit = () => signal != 0,
                AbsFault = () => abs,
            };
            try
            {
                var ext = saved; ext.Detail = Game.Controls.HudDetail.Extended;
                Game.Controls.HudPreferences.Set(ext);
                m_Hud = DrivingHud.Create(null, ctx, overlay: true);
                yield return null;
                foreach (var px in new[] { new Vector2(1920f, 1080f), new Vector2(5120f, 1440f) })
                {
                    m_Hud.OverrideScreen(px, new Rect(0f, 0f, px.x, px.y), 96f, desktop: true);
                    m_Hud.RefreshNow();
                    yield return null;
                    Assert.IsTrue(m_Hud.DesktopVisibility.Extended, px + ": extended detail");
                    Assert.IsTrue(m_Hud.DesktopLayout.ShowStrip, px + ": strip");
                    Assert.IsTrue(m_Hud.Layout.ShowMirrorLeft && m_Hud.Layout.ShowMirrorRight, px + ": mirror windows");
                    var a = ext; var b = ext; b.MirrorSize = 0.5f; b.MirrorDrop = 0.4f;
                    for (int i = 0; i < 20; i++) { abs = i % 2 == 0; m_Hud.RefreshNow(); }
                    Game.Controls.HudPreferences.Set(b); m_Hud.RefreshNow();
                    Game.Controls.HudPreferences.Set(a); m_Hud.RefreshNow();   // warm-up of the re-layout path
                    int allocs = GcAllocCounter.Count(() =>
                    {
                        for (int i = 0; i < 500; i++)
                        {
                            cruise = i % 3 == 0 ? 0f : 30f + (i % 61);
                            lever = i % 6;
                            signal = (i / 25) % 4 - 1;
                            abs = (i / 50) % 2 == 0;
                            m_Hud.RefreshNow();
                        }
                    });
                    yield return null;
                    Assert.AreEqual(0, allocs, $"{px}: 500 strip refreshes allocated {allocs} GC.Alloc samples (expected 0)");
                }
            }
            finally
            {
                Game.Controls.HudPreferences.Set(saved);
            }
        }
    }
}
