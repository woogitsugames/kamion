using Game.Controls;
using Game.UI.Driving;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0151 (owner Fold video 2026-11-12, 20.1 s): a thumb that lands on the turn-signal bar right above the rim and
    /// slides sideways steers; a vertical drag or a tap does not; a busy wheel is not stolen.
    /// </summary>
    public class WheelDragRelayTests
    {
        GameObject m_Root, m_Bar;
        TouchSteeringWheel m_Wheel;
        SteeringWheelWidget m_Widget;
        WheelDragRelay m_Relay;

        [SetUp]
        public void SetUp()
        {
            m_Root = new GameObject("Wheel", typeof(RectTransform));
            ((RectTransform)m_Root.transform).sizeDelta = new Vector2(400f, 400f);
            m_Wheel = new TouchSteeringWheel { Grab = WheelGrab.Drag, DeadZone = 0f };
            m_Widget = m_Root.AddComponent<SteeringWheelWidget>();
            m_Widget.wheel = m_Wheel;
            m_Bar = new GameObject("TurnSignals", typeof(RectTransform));
            m_Relay = m_Bar.AddComponent<WheelDragRelay>();
            m_Relay.target = m_Widget;
        }

        [TearDown]
        public void TearDown()
        {
            Object.DestroyImmediate(m_Bar);
            Object.DestroyImmediate(m_Root);
        }

        static PointerEventData Drag(Vector2 press, Vector2 now, int id = 7)
            => new PointerEventData(null) { pointerId = id, pressPosition = press, position = now, eligibleForClick = true };

        static float Mm(float px) => SteeringMath.PixelsToMm(new Vector2(px, 0f), DeviceDisplay.Dpi).x;

        [Test]
        public void SidewaysSlideFromTheBar_SteersFromThePressPoint_AndCancelsTheButton()
        {
            var e = Drag(new Vector2(150f, 520f), new Vector2(250f, 530f));
            m_Relay.OnBeginDrag(e);
            Assert.IsTrue(m_Wheel.Held, "wheel grabbed");
            Assert.IsFalse(e.eligibleForClick, "turn signal must not fire on release");
            Assert.AreEqual(Mm(100f) * m_Wheel.DragDegPerMm, m_Wheel.WheelDeg, 0.05f, "travel counted from the press point");
            e.position = new Vector2(300f, 530f);
            m_Relay.OnDrag(e);
            Assert.AreEqual(Mm(150f) * m_Wheel.DragDegPerMm, m_Wheel.WheelDeg, 0.05f);
            m_Relay.OnEndDrag(e);
            Assert.IsFalse(m_Wheel.Held, "released with the thumb");
        }

        [Test]
        public void VerticalDragFromTheBar_DoesNotSteer()
        {
            var e = Drag(new Vector2(150f, 520f), new Vector2(160f, 600f));
            m_Relay.OnBeginDrag(e);
            Assert.IsFalse(m_Wheel.Held);
            Assert.IsTrue(e.eligibleForClick);
            Assert.AreEqual(0f, m_Wheel.WheelDeg, 1e-5f);
        }

        [Test]
        public void WheelAlreadyHeld_ByAnotherFinger_IsNotTakenOver()
        {
            m_Widget.OnPointerDown(Drag(new Vector2(100f, 100f), new Vector2(100f, 100f), 1));
            var e = Drag(new Vector2(150f, 520f), new Vector2(260f, 520f), 2);
            m_Relay.OnBeginDrag(e);
            Assert.IsTrue(e.eligibleForClick, "the bar keeps its own touch");
            m_Relay.OnEndDrag(e);
            Assert.IsTrue(m_Wheel.Held, "first finger still holds the wheel");
        }
    }
}
