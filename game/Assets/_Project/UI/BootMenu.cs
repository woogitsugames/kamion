using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

namespace Game.UI
{
    /// <summary>Minimal Boot menu: one large button per entry, bottom centre of the safe area.</summary>
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
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            float w = 560f, h = 110f, gap = 20f;
            float total = entries.Length * w + (entries.Length - 1) * gap;
            for (int i = 0; i < entries.Length; i++)
            {
                var e = entries[i];
                var rt = new GameObject(e.label, typeof(RectTransform)).GetComponent<RectTransform>();
                rt.gameObject.layer = 5;
                rt.SetParent(go.transform, false);
                rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0f);
                rt.pivot = Vector2.zero;
                rt.anchoredPosition = new Vector2(-total * 0.5f + i * (w + gap), 60f);
                rt.sizeDelta = new Vector2(w, h);
                var img = rt.gameObject.AddComponent<Image>();
                img.color = new Color(0.20f, 0.24f, 0.21f, 0.92f);
                var b = rt.gameObject.AddComponent<Button>();
                b.targetGraphic = img;
                var action = e.action;
                b.onClick.AddListener(() => action());
                var t = new GameObject("Label", typeof(RectTransform)).GetComponent<RectTransform>();
                t.SetParent(rt, false);
                t.anchorMin = Vector2.zero; t.anchorMax = Vector2.one; t.offsetMin = t.offsetMax = Vector2.zero;
                var text = t.gameObject.AddComponent<Text>();
                text.font = font; text.fontSize = 38; text.alignment = TextAnchor.MiddleCenter;
                text.color = new Color(0.95f, 0.95f, 0.91f); text.text = e.label; text.raycastTarget = false;
            }
            if (FindAnyObjectByType<EventSystem>() == null)
                new GameObject("EventSystem", typeof(EventSystem)).AddComponent<InputSystemUIInputModule>().AssignDefaultActions();
            return menu;
        }
    }
}
