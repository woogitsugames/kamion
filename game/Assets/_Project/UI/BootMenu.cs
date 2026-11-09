using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

namespace Game.UI
{
    /// <summary>Boot menu: a centred column with one large button per entry (start choices and the control settings).</summary>
    public sealed class BootMenu : MonoBehaviour
    {
        public static BootMenu Create(Camera cam, params (string label, Action action)[] entries)
        {
            var go = new GameObject("BootMenu");
            var menu = go.AddComponent<BootMenu>();
            var canvas = go.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceCamera;
            canvas.worldCamera = cam;
            canvas.planeDistance = cam != null ? Mathf.Max(cam.nearClipPlane * 2f, 0.5f) : 1f;
            canvas.sortingOrder = 1100;
            var scaler = go.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.matchWidthOrHeight = 1f;
            go.AddComponent<GraphicRaycaster>();
            var font = UiFonts.Default;
            // One column, centred: a muted header, then one wide button per entry (touch targets, no decoration).
            float w = 760f, h = 104f, gap = 16f;
            float total = entries.Length * h + (entries.Length - 1) * gap;
            var head = new GameObject("Header", typeof(RectTransform)).GetComponent<RectTransform>();
            head.gameObject.layer = 5;
            head.SetParent(go.transform, false);
            head.anchorMin = head.anchorMax = new Vector2(0.5f, 0.5f);
            head.pivot = new Vector2(0.5f, 0f);
            head.anchoredPosition = new Vector2(0f, total * 0.5f + 16f);
            head.sizeDelta = new Vector2(w, 48f);
            var ht = head.gameObject.AddComponent<Text>();
            ht.font = font; ht.fontSize = 28; ht.alignment = TextAnchor.LowerLeft;
            ht.color = new Color(0.95f, 0.66f, 0.18f); ht.text = "WYBIERZ START"; ht.raycastTarget = false;
            for (int i = 0; i < entries.Length; i++)
            {
                var e = entries[i];
                var rt = new GameObject(e.label, typeof(RectTransform)).GetComponent<RectTransform>();
                rt.gameObject.layer = 5;
                rt.SetParent(go.transform, false);
                rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f);
                rt.pivot = new Vector2(0.5f, 1f);
                rt.anchoredPosition = new Vector2(0f, total * 0.5f - i * (h + gap));
                rt.sizeDelta = new Vector2(w, h);
                var img = rt.gameObject.AddComponent<Image>();
                img.color = new Color(0.16f, 0.17f, 0.18f, 0.95f);
                var b = rt.gameObject.AddComponent<Button>();
                b.targetGraphic = img;
                var action = e.action;
                b.onClick.AddListener(() => action());
                var t = new GameObject("Label", typeof(RectTransform)).GetComponent<RectTransform>();
                t.SetParent(rt, false);
                t.anchorMin = Vector2.zero; t.anchorMax = Vector2.one; t.offsetMin = new Vector2(32f, 0f); t.offsetMax = Vector2.zero;
                var text = t.gameObject.AddComponent<Text>();
                text.font = font; text.fontSize = 36; text.alignment = TextAnchor.MiddleLeft;
                text.color = new Color(0.95f, 0.95f, 0.91f); text.text = e.label; text.raycastTarget = false;
            }
            if (FindAnyObjectByType<EventSystem>() == null)
                new GameObject("EventSystem", typeof(EventSystem)).AddComponent<InputSystemUIInputModule>().AssignDefaultActions();
            return menu;
        }
    }
}
