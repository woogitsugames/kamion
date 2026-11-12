using Game.Core;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>ADR 0142: one-slot UI -> vehicle audio mailbox (settings preview of horn / doors).</summary>
    public sealed class AudioCuesTests
    {
        [Test]
        public void Request_IsTakenOnce_ThenEmpty()
        {
            AudioCues.TryTake(out _);
            Assert.IsFalse(AudioCues.TryTake(out var none));
            Assert.AreEqual(AudioCue.None, none);
            AudioCues.Request(AudioCue.DoorOpen);
            AudioCues.Request(AudioCue.HornTap); // latest request wins
            Assert.IsTrue(AudioCues.TryTake(out var cue));
            Assert.AreEqual(AudioCue.HornTap, cue);
            Assert.IsFalse(AudioCues.TryTake(out _), "a cue is consumed by one audio update");
        }
    }
}
