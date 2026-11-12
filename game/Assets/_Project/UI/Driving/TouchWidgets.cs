using System;
using Game.Controls;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Game.UI.Driving
{
    /// <summary>
    /// On-screen steering wheel: forwards pointer positions (relative to its centre, and in millimetres on the screen for
    /// the drag gesture) to <see cref="TouchSteeringWheel"/>. Touches anywhere on this object or its children (the
    /// invisible grab area that extends the drawing to the safe-area edges, ADR 0135) grab the wheel. Draws the command
    /// (<see cref="rotating"/>) and where the cab wheel actually is (<see cref="columnMark"/>).
    /// </summary>
    public sealed class SteeringWheelWidget : MonoBehaviour, IPointerDownHandler, IDragHandler, IPointerUpHandler
    {
        public TouchSteeringWheel wheel;
        public RectTransform rotating;
        /// <summary>Optional: marker rotated to the cab-wheel angle in on-screen degrees (lags the finger like the heavy wheel).</summary>
        public RectTransform columnMark;
        int m_Pointer = int.MinValue;

        static Vector2 Mm(PointerEventData e) => SteeringMath.PixelsToMm(e.position, DeviceDisplay.Dpi);

        Vector2 FromCentre(PointerEventData e) => FromCentre(e.position, e.pressEventCamera);

        Vector2 FromCentre(Vector2 screen, Camera cam)
        {
            var rt = (RectTransform)transform;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(rt, screen, cam, out Vector2 local);
            // Local coordinates are canvas units; the angle does not depend on scale, the min radius is in px-equivalents.
            return local - rt.rect.center;
        }

        public void OnPointerDown(PointerEventData e)
        {
            if (wheel == null || m_Pointer != int.MinValue) return;
            m_Pointer = e.pointerId;
            wheel.PointerDown(FromCentre(e), Mm(e));
        }

        public void OnDrag(PointerEventData e)
        {
            if (wheel == null || e.pointerId != m_Pointer) return;
            wheel.PointerDrag(FromCentre(e), Mm(e));
        }

        public void OnPointerUp(PointerEventData e)
        {
            if (wheel == null || e.pointerId != m_Pointer) return;
            m_Pointer = int.MinValue;
            wheel.PointerUp();
        }

        /// <summary>Releases a relayed grab (relay disabled mid-gesture).</summary>
        public void ReleaseRelayed() { if (m_Pointer != int.MinValue) { m_Pointer = int.MinValue; wheel?.PointerUp(); } }

        void OnDisable()
        {
            if (m_Pointer != int.MinValue) { m_Pointer = int.MinValue; wheel?.PointerUp(); }
        }

        /// <summary>
        /// ADR 0151: a thumb that lands on a neighbouring control (turn-signal bar right above the rim) and slides sideways
        /// steers: the press position starts the gesture, so the travel before the drag threshold is not lost.
        /// False when the wheel is already held by another finger or inactive.
        /// </summary>
        public bool BeginRelayed(PointerEventData e)
        {
            if (wheel == null || !isActiveAndEnabled || m_Pointer != int.MinValue) return false;
            m_Pointer = e.pointerId;
            wheel.PointerDown(FromCentre(e.pressPosition, e.pressEventCamera), SteeringMath.PixelsToMm(e.pressPosition, DeviceDisplay.Dpi));
            wheel.PointerDrag(FromCentre(e), Mm(e));
            return true;
        }
        void LateUpdate()
        {
            if (wheel == null) return;
            if (rotating != null) rotating.localRotation = Quaternion.Euler(0f, 0f, -wheel.WheelDeg); // UI z+ is counter-clockwise
            if (columnMark != null) columnMark.localRotation = Quaternion.Euler(0f, 0f, -wheel.ColumnScreenDeg);
        }
    }

    /// <summary>
    /// ADR 0151 (owner Fold video 2026-11-12, 20.1 s: the thumb landed on "AWAR." 2.5 mm above the rim and 12.6 mm of
    /// sideways travel steered nothing): on the turn-signal bar a press that turns into a mostly sideways drag is handed to
    /// the steering wheel and the button does not fire; a tap still works as a button. Buttons have no drag handler, so
    /// the drag bubbles up to this component on the bar.
    /// </summary>
    public sealed class WheelDragRelay : MonoBehaviour, IBeginDragHandler, IDragHandler, IEndDragHandler
    {
        public SteeringWheelWidget target;
        bool m_Active;

        public void OnBeginDrag(PointerEventData e)
        {
            Vector2 d = e.position - e.pressPosition;
            if (target == null || Mathf.Abs(d.x) < Mathf.Abs(d.y)) return;   // vertical = not a steering slide
            m_Active = target.BeginRelayed(e);
            if (m_Active) e.eligibleForClick = false;                           // no turn signal on release
        }

        public void OnDrag(PointerEventData e) { if (m_Active) target.OnDrag(e); }

        public void OnEndDrag(PointerEventData e)
        {
            if (!m_Active) return;
            m_Active = false;
            target.OnPointerUp(e);
        }

        void OnDisable()
        {
            if (m_Active && target != null) target.ReleaseRelayed();
            m_Active = false;
        }

    }

    /// <summary>
    /// Analog pedal: value = finger height inside the pedal (0 bottom .. 1 top) while pressed, 0 when released.
    /// Sliding the finger up/down modulates it (no lift-off needed).
    /// </summary>
    public sealed class PedalWidget : MonoBehaviour, IPointerDownHandler, IDragHandler, IPointerUpHandler
    {
        public Action<float> onValue;
        public RectTransform fill;
        public float Value { get; private set; }
        int m_Pointer = int.MinValue;

        void Set(PointerEventData e)
        {
            var rt = (RectTransform)transform;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(rt, e.position, e.pressEventCamera, out Vector2 local);
            var r = rt.rect;
            // Bottom 12 % = light touch (small value), top = full.
            Value = Mathf.Clamp01((local.y - r.yMin) / Mathf.Max(1f, r.height) * 1.08f);
            onValue?.Invoke(Value);
        }

        public void OnPointerDown(PointerEventData e)
        {
            if (m_Pointer != int.MinValue) return;
            m_Pointer = e.pointerId;
            Set(e);
        }

        public void OnDrag(PointerEventData e) { if (e.pointerId == m_Pointer) Set(e); }

        public void OnPointerUp(PointerEventData e)
        {
            if (e.pointerId != m_Pointer) return;
            m_Pointer = int.MinValue;
            Value = 0f;
            onValue?.Invoke(0f);
        }

        void OnDisable() { if (m_Pointer != int.MinValue) { m_Pointer = int.MinValue; Value = 0; onValue?.Invoke(0f); } }

        void LateUpdate()
        {
            if (fill != null) fill.anchorMax = new Vector2(1f, Value);
        }
    }

    /// <summary>Transparent full-screen area behind the controls: drag = look around / orbit, scroll = zoom.</summary>
    public sealed class LookPadWidget : MonoBehaviour, IDragHandler, IScrollHandler, IPointerClickHandler
    {
        public Action<Vector2> onDrag;
        public Action<float> onZoom;
        public Action onDoubleTap;

        public void OnDrag(PointerEventData e) => onDrag?.Invoke(e.delta);
        public void OnScroll(PointerEventData e) => onZoom?.Invoke(Mathf.Sign(e.scrollDelta.y));
        public void OnPointerClick(PointerEventData e) { if (e.clickCount >= 2) onDoubleTap?.Invoke(); }
    }
}
