using System;
using System.Collections;
using System.Collections.Generic;
using Game.Controls;
using Game.UI;
using Game.UI.Layout;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0276 (integration s23 P2, menu.jpg): the diagnostics overlay covered the start-menu title and first button.
    /// Real uGUI objects: the start menu block has the geometry the pure tests assume (<c>MenuOverlayLayoutTests</c>), and
    /// with both on one camera (monitor 16:9, 21:9, 4K, phone) no overlay graphic overlaps a menu graphic on screen.
    /// </summary>
    public class MenuOverlayUiTests
    {
        public struct ScreenCase
        {
            public string Name; public int W, H; public float Dpi; public bool Desktop;
            public override string ToString() => Name;
        }

        static readonly ScreenCase[] k_Screens =
        {
            new ScreenCase { Name = "monitor-1920x1080", W = 1920, H = 1080, Dpi = 96f, Desktop = true },
            new ScreenCase { Name = "monitor-21x9-2560x1080", W = 2560, H = 1080, Dpi = 96f, Desktop = true },
            new ScreenCase { Name = "monitor-4k-3840x2160", W = 3840, H = 2160, Dpi = 96f, Desktop = true },
            new ScreenCase { Name = "phone-2340x1080-A16", W = 2340, H = 1080, Dpi = 385f, Desktop = false },
            new ScreenCase { Name = "phone-1920x1080-dpi-unknown", W = 1920, H = 1080, Dpi = 0f, Desktop = false },
        };

        static IEnumerable<ScreenCase> Screens => k_Screens;

        /// <summary>Same value as <c>MenuOverlayLayoutTests.MenuBlock3Starts</c> (EditMode; kept in sync by this test).</summary>
        static readonly Rect k_Block3StartsPc = Rect.MinMaxRect(-800f, -302f, 800f, 496f);

        Camera m_Cam;
        RenderTexture m_Rt;
        static readonly Vector3[] s_Corners = new Vector3[4];

        static List<(string, Action)> Starts() => new List<(string, Action)>
        {
            ("DrivingLab — plac testowy", () => { }),
            ("Trasa G3-A — baza, brama, Bieżeństwa", () => { }),
            ("Trasa G3-B — Andersa, Rondo Putry", () => { }),
        };

        static List<BootRegionChoice> Regions() => new List<BootRegionChoice>
        {
            new BootRegionChoice("knyszyn", "Knyszyn — rondo DK65/DW671, Rynek", "Knyszyn · trasa 2,0 km · start na początku trasy", true, () => { }),
        };

        void MakeCamera(ScreenCase s)
        {
            var go = new GameObject("MenuOverlayCam");
            m_Cam = go.AddComponent<Camera>();
            m_Cam.clearFlags = CameraClearFlags.SolidColor;
            m_Cam.nearClipPlane = 0.05f; m_Cam.farClipPlane = 10f;
            m_Cam.cullingMask = 1 << 5;
            m_Rt = new RenderTexture(s.W, s.H, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            m_Cam.targetTexture = m_Rt;
        }

        [TearDown]
        public void TearDown()
        {
            foreach (var o in UnityEngine.Object.FindObjectsByType<DiagnosticsOverlay>(FindObjectsSortMode.None)) UnityEngine.Object.Destroy(o.gameObject);
            foreach (var m in UnityEngine.Object.FindObjectsByType<BootMenu>(FindObjectsSortMode.None)) UnityEngine.Object.Destroy(m.gameObject);
            if (m_Cam != null) { m_Cam.targetTexture = null; UnityEngine.Object.Destroy(m_Cam.gameObject); }
            if (m_Rt != null) { m_Rt.Release(); UnityEngine.Object.Destroy(m_Rt); }
        }

        Rect ScreenRect(RectTransform rt)
        {
            rt.GetWorldCorners(s_Corners);
            Vector2 min = new Vector2(float.MaxValue, float.MaxValue), max = new Vector2(float.MinValue, float.MinValue);
            for (int i = 0; i < 4; i++)
            {
                Vector2 p = m_Cam.WorldToScreenPoint(s_Corners[i]);
                min = Vector2.Min(min, p); max = Vector2.Max(max, p);
            }
            return Rect.MinMaxRect(min.x, min.y, max.x, max.y);
        }

        static bool Overlap(Rect a, Rect b, float eps) =>
            a.xMin < b.xMax - eps && b.xMin < a.xMax - eps && a.yMin < b.yMax - eps && b.yMin < a.yMax - eps;

        [UnityTest]
        public IEnumerator MenuBlock_HasTheGeometryThePureTestsUse()
        {
            MakeCamera(k_Screens[0]);
            var menu = BootMenu.Create(m_Cam, StartMenuOptions.Load(), Starts(), null, null, Regions(), () => { });
            menu.OverrideScreen(new Vector2(1920f, 1080f), new Rect(0f, 0f, 1920f, 1080f), 96f, true);
            yield return null;
            Rect b = menu.BlockBounds;
            Assert.AreEqual(k_Block3StartsPc.xMin, b.xMin, 0.5f);
            Assert.AreEqual(k_Block3StartsPc.xMax, b.xMax, 0.5f);
            Assert.AreEqual(k_Block3StartsPc.yMin, b.yMin, 0.5f, "lowest item (footer of the right column)");
            Assert.AreEqual(k_Block3StartsPc.yMax, b.yMax, 0.5f, "title top");
            Assert.AreEqual(0f, menu.BlockShift, "no overlay: the menu keeps its place");
        }

        [UnityTest]
        public IEnumerator Overlay_NeverCoversTheMenu([ValueSource(nameof(Screens))] ScreenCase s)
        {
            MakeCamera(s);
            var safe = new Rect(0f, 0f, s.W, s.H);
            var overlay = DiagnosticsOverlay.Create(m_Cam, null, null);
            overlay.OverrideScreen(new Vector2(s.W, s.H), safe, s.Dpi, s.Desktop);
            var menu = BootMenu.Create(m_Cam, StartMenuOptions.Load(), Starts(), null, null, Regions(), s.Desktop ? (Action)(() => { }) : null);
            menu.OverrideScreen(new Vector2(s.W, s.H), safe, s.Dpi, s.Desktop);
            for (int i = 0; i < 3; i++) yield return null;   // measure the panel, publish, both sides apply
            Canvas.ForceUpdateCanvases();

            var layout = overlay.AppliedLayout;
            Assert.IsTrue(layout.Fits, s.Name + ": shared layout found no place");
            if (s.Desktop && s.H >= 1080) Assert.AreEqual(OverlayPanelPlace.TopLeft, layout.Panel, s.Name + ": on a monitor the panel stays visible");

            var overlayRects = new List<(string, Rect)>();
            if (overlay.PanelRect.gameObject.activeInHierarchy) overlayRects.Add(("panel", ScreenRect(overlay.PanelRect)));
            for (int i = 0; i < MenuOverlayLayout.ButtonCount; i++) overlayRects.Add(("button " + i, ScreenRect(overlay.ButtonRect(i))));
            int menuGraphics = 0;
            foreach (var g in menu.SafeAreaRect.GetComponentsInChildren<Graphic>(false))
            {
                if (string.IsNullOrEmpty(g is Text t ? t.text : "x")) continue;   // empty labels draw nothing
                Rect m = ScreenRect(g.rectTransform);
                menuGraphics++;
                foreach (var (name, r) in overlayRects)
                    Assert.IsFalse(Overlap(m, r, 0.5f), $"{s.Name}: overlay {name} {r} covers menu item {g.transform.parent.name}/{g.name} {m}");
            }
            Assert.Greater(menuGraphics, 10, "menu items found");
            var title = menu.SafeAreaRect.GetComponentsInChildren<Text>(false);
            Assert.IsTrue(Array.Exists(title, x => x.name == "Title"), "title present");
        }
    }
}
