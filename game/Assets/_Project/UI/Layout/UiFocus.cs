using System;
using System.Collections.Generic;
using Game.Controls;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

namespace Game.UI.Layout
{
    /// <summary>
    /// Mouse and pad navigation of the menus (ADR 0265). One EventSystem with the Input System UI module (mouse, keyboard
    /// arrows / Enter / Esc, pad stick / d-pad / A / B: the module's default actions), an explicit navigation order
    /// (<see cref="MenuNavGrid"/>), the first item selected on a monitor, and a visible focus: a thin frame like the
    /// selection on a truck display - amber when selected (pad / keyboard), muted when the mouse is over it. No glow, no
    /// animation (docs/06 section 7).
    /// </summary>
    public static class UiFocus
    {
        /// <summary>ADR 0283: the palette accent (8.2:1 on the panel, WCAG 1.4.11 needs 3:1).</summary>
        public static readonly Color FocusColor = UiPalette.Accent;
        public static readonly Color HoverColor = UiPalette.Hover;
        /// <summary>Frame thickness [canvas units]. WORKING_VALUE.</summary>
        public const float FrameWidth = 3f;

        /// <summary>Creates the EventSystem with the Input System UI module once (menus, settings, HUD share it).</summary>
        public static void EnsureEventSystem()
        {
            if (UnityEngine.Object.FindAnyObjectByType<EventSystem>() != null) return;
            var go = new GameObject("EventSystem", typeof(EventSystem));
            go.AddComponent<InputSystemUIInputModule>().AssignDefaultActions();
        }

        /// <summary>Tint that never darkens the flat button colours on hover / selection (the frame shows the focus).</summary>
        public static void FlatColors(Selectable s)
        {
            var c = s.colors;
            c.normalColor = Color.white;
            c.highlightedColor = Color.white;
            c.selectedColor = Color.white;
            c.pressedColor = new Color(0.82f, 0.82f, 0.82f, 1f);
            c.disabledColor = new Color(0.75f, 0.75f, 0.75f, 0.55f);
            c.colorMultiplier = 1f;
            c.fadeDuration = 0.05f;
            s.colors = c;
        }

        /// <summary>Menu item: flat colours + focus frame; <paramref name="onCancel"/> = Esc / pad B while it is selected.</summary>
        public static FocusFrame Decorate(Selectable s, Action onCancel = null)
        {
            FlatColors(s);
            var f = s.gameObject.GetComponent<FocusFrame>();
            if (f == null) f = s.gameObject.AddComponent<FocusFrame>();
            f.onCancel = onCancel;
            return f;
        }

        /// <summary>HUD button: pointer only (never takes the pad / keyboard selection, ADR 0265) + hover frame.</summary>
        public static void PointerOnly(Selectable s)
        {
            // UnityEngine.UI.Navigation spelled out: inside Game.UI.* the simple name is the namespace Game.UI.Navigation (CS0118).
            s.navigation = new UnityEngine.UI.Navigation { mode = UnityEngine.UI.Navigation.Mode.None };
            FlatColors(s);
            if (s.gameObject.GetComponent<FocusFrame>() == null) s.gameObject.AddComponent<FocusFrame>();
        }

        /// <summary>Remembers <paramref name="go"/> as the first item and, on a monitor, selects it (on a touch screen
        /// the frame appears only once a pad / keyboard navigates).</summary>
        public static void SelectFirst(GameObject go, bool select)
        {
            var es = EventSystem.current != null ? EventSystem.current : UnityEngine.Object.FindAnyObjectByType<EventSystem>();
            if (es == null || go == null) return;
            es.firstSelectedGameObject = go;
            if (select) es.SetSelectedGameObject(go);
        }

        /// <summary>
        /// Explicit navigation for a menu in columns of rows (<see cref="MenuNavGrid"/>). Null entries in a row are
        /// dropped; empty rows are kept as gaps so the column heights still line up.
        /// </summary>
        public static void ApplyGrid(List<List<Selectable[]>> columns)
        {
            int nc = columns.Count;
            var lengths = new int[nc][];
            var items = new Selectable[nc][][];
            for (int c = 0; c < nc; c++)
            {
                var rows = columns[c];
                lengths[c] = new int[rows.Count];
                items[c] = new Selectable[rows.Count][];
                for (int r = 0; r < rows.Count; r++)
                {
                    var list = new List<Selectable>();
                    if (rows[r] != null) foreach (var s in rows[r]) if (s != null) list.Add(s);
                    items[c][r] = list.ToArray();
                    lengths[c][r] = list.Count;
                }
            }
            for (int c = 0; c < nc; c++)
            for (int r = 0; r < items[c].Length; r++)
            for (int i = 0; i < items[c][r].Length; i++)
            {
                var nav = new UnityEngine.UI.Navigation { mode = UnityEngine.UI.Navigation.Mode.Explicit, wrapAround = false };
                nav.selectOnUp = Pick(items, lengths, c, r, i, NavDir.Up);
                nav.selectOnDown = Pick(items, lengths, c, r, i, NavDir.Down);
                nav.selectOnLeft = Pick(items, lengths, c, r, i, NavDir.Left);
                nav.selectOnRight = Pick(items, lengths, c, r, i, NavDir.Right);
                items[c][r][i].navigation = nav;
            }
        }

        static Selectable Pick(Selectable[][][] items, int[][] lengths, int c, int r, int i, NavDir d) =>
            MenuNavGrid.Neighbour(lengths, c, r, i, d, out int nc, out int nr, out int ni) ? items[nc][nr][ni] : null;

        // ---- focus owners: the topmost open menu / panel keeps the pad selection (menu -> settings -> back)
        struct Owner { public Component Root; public GameObject First; }
        static readonly List<Owner> s_Owners = new List<Owner>(4);

        /// <summary>A menu / panel opened: it owns the pad / keyboard focus until <see cref="Pop"/>.</summary>
        public static void Push(Component root, GameObject first, bool select)
        {
            Pop(root, false);
            s_Owners.Add(new Owner { Root = root, First = first });
            SelectFirst(first, select);
        }

        /// <summary>A menu / panel closed: the focus returns to the one below it.</summary>
        public static void Pop(Component root, bool selectBelow)
        {
            for (int i = s_Owners.Count - 1; i >= 0; i--)
                if (s_Owners[i].Root == null || s_Owners[i].Root == root) s_Owners.RemoveAt(i);
            if (!selectBelow) return;
            for (int i = s_Owners.Count - 1; i >= 0; i--)
                if (s_Owners[i].Root.gameObject.activeInHierarchy) { SelectFirst(s_Owners[i].First, true); break; }
        }

        /// <summary>
        /// True while any menu / panel owns the pad / keyboard focus (an active owner on the stack). The driving scene
        /// feeds it to <see cref="DriverInputMixer.MenuOpen"/>: menu buttons must not drive the truck (review #131 P1-1).
        /// Destroyed and inactive owners do not count. No allocation.
        /// </summary>
        public static bool HasModal
        {
            get
            {
                for (int i = s_Owners.Count - 1; i >= 0; i--)
                {
                    var root = s_Owners[i].Root;
                    if (root != null && root.gameObject.activeInHierarchy) return true;
                }
                return false;
            }
        }

        /// <summary>True when <paramref name="root"/> is the topmost active focus owner.</summary>
        public static bool IsTop(Component root)
        {
            for (int i = s_Owners.Count - 1; i >= 0; i--)
            {
                var o = s_Owners[i];
                if (o.Root == null || !o.Root.gameObject.activeInHierarchy) continue;
                return o.Root == root;
            }
            return false;
        }

        /// <summary>
        /// Call from the owner's Update: when nothing is selected (a mouse click on empty space, a closed panel) and the
        /// player navigates with the pad or the arrow keys, the first item is selected again, so the pad never gets stuck.
        /// No allocation.
        /// </summary>
        public static void RestoreIfLost(Component root, GameObject first)
        {
            var es = EventSystem.current;
            if (es == null || first == null || !first.activeInHierarchy) return;
            var sel = es.currentSelectedGameObject;
            if (sel != null && sel.activeInHierarchy) return;
            if (!NavigationPressed() || !IsTop(root)) return;
            es.SetSelectedGameObject(first);
        }

        static bool NavigationPressed()
        {
            var k = Keyboard.current;
            if (k != null && (k.upArrowKey.wasPressedThisFrame || k.downArrowKey.wasPressedThisFrame || k.leftArrowKey.wasPressedThisFrame
                              || k.rightArrowKey.wasPressedThisFrame || k.tabKey.wasPressedThisFrame)) return true;
            var g = Gamepad.current;
            return g != null && (g.dpad.up.wasPressedThisFrame || g.dpad.down.wasPressedThisFrame || g.dpad.left.wasPressedThisFrame
                                 || g.dpad.right.wasPressedThisFrame || g.leftStick.ReadValue().sqrMagnitude > 0.25f || g.buttonSouth.wasPressedThisFrame);
        }

        /// <summary>Scrolls <paramref name="scroll"/> (vertical) just enough for <paramref name="item"/> to be fully visible.</summary>
        public static void ScrollIntoView(ScrollRect scroll, RectTransform item)
        {
            if (scroll == null || item == null || scroll.content == null || scroll.viewport == null || !scroll.vertical) return;
            var content = scroll.content;
            var view = scroll.viewport;
            var corners = new Vector3[4];
            item.GetWorldCorners(corners);
            float top = view.InverseTransformPoint(corners[1]).y, bottom = view.InverseTransformPoint(corners[0]).y;
            Rect vr = view.rect;
            const float pad = 12f;
            float dy = 0f;
            if (top > vr.yMax - pad) dy = top - (vr.yMax - pad);
            else if (bottom < vr.yMin + pad) dy = bottom - (vr.yMin + pad);
            if (Mathf.Abs(dy) < 0.5f) return;
            float maxY = Mathf.Max(0f, content.rect.height - vr.height);
            var p = content.anchoredPosition;
            p.y = Mathf.Clamp(p.y - dy, 0f, maxY);
            content.anchoredPosition = p;
            scroll.velocity = Vector2.zero;
        }
    }

    /// <summary>
    /// Thin focus frame around a menu item (ADR 0265): amber while selected (pad / keyboard / last click), muted while
    /// the mouse is over it. Four child images, built once; no per-frame work. Esc / pad B while selected calls
    /// <see cref="onCancel"/> (closes the panel). Selecting an item inside a scroll view scrolls it into view.
    /// </summary>
    public sealed class FocusFrame : MonoBehaviour, ISelectHandler, IDeselectHandler, IPointerEnterHandler, IPointerExitHandler, ICancelHandler
    {
        public Action onCancel;
        GameObject m_Frame;
        Image[] m_Edges;
        bool m_Selected, m_Hover;

        public bool Selected => m_Selected;
        public bool FrameVisible => m_Frame != null && m_Frame.activeSelf;

        void Build()
        {
            if (m_Frame != null) return;
            var root = new GameObject("FocusFrame", typeof(RectTransform)) { layer = gameObject.layer };
            var rt = (RectTransform)root.transform;
            rt.SetParent(transform, false);
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero;
            m_Edges = new Image[4];
            float w = UiFocus.FrameWidth;
            for (int i = 0; i < 4; i++)
            {
                var e = new GameObject("Edge" + i, typeof(RectTransform)) { layer = gameObject.layer };
                var ert = (RectTransform)e.transform;
                ert.SetParent(rt, false);
                switch (i)
                {
                    case 0: ert.anchorMin = new Vector2(0f, 1f); ert.anchorMax = Vector2.one; ert.offsetMin = new Vector2(0f, -w); ert.offsetMax = Vector2.zero; break;   // top
                    case 1: ert.anchorMin = Vector2.zero; ert.anchorMax = new Vector2(1f, 0f); ert.offsetMin = Vector2.zero; ert.offsetMax = new Vector2(0f, w); break;   // bottom
                    case 2: ert.anchorMin = Vector2.zero; ert.anchorMax = new Vector2(0f, 1f); ert.offsetMin = Vector2.zero; ert.offsetMax = new Vector2(w, 0f); break;   // left
                    default: ert.anchorMin = new Vector2(1f, 0f); ert.anchorMax = Vector2.one; ert.offsetMin = new Vector2(-w, 0f); ert.offsetMax = Vector2.zero; break; // right
                }
                var img = e.AddComponent<Image>();
                img.raycastTarget = false;
                m_Edges[i] = img;
            }
            root.SetActive(false);
            m_Frame = root;
        }

        void Show()
        {
            Build();
            bool on = m_Selected || m_Hover;
            if (on)
            {
                var c = m_Selected ? UiFocus.FocusColor : UiFocus.HoverColor;
                for (int i = 0; i < 4; i++) m_Edges[i].color = c;
            }
            if (m_Frame.activeSelf != on) m_Frame.SetActive(on);
        }

        public void OnSelect(BaseEventData e)
        {
            m_Selected = true; Show();
            var scroll = GetComponentInParent<ScrollRect>();
            if (scroll != null) UiFocus.ScrollIntoView(scroll, (RectTransform)transform);
        }

        public void OnDeselect(BaseEventData e) { m_Selected = false; Show(); }
        public void OnPointerEnter(PointerEventData e)
        {
            if (e is ExtendedPointerEventData x && x.pointerType == UIPointerType.Touch) return;   // a finger has no hover
            m_Hover = true; Show();
        }
        public void OnPointerExit(PointerEventData e) { m_Hover = false; Show(); }
        public void OnCancel(BaseEventData e) => onCancel?.Invoke();

        void OnDisable() { m_Hover = false; if (m_Frame != null) m_Frame.SetActive(false); m_Selected = false; }
    }
}
