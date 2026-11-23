using UnityEngine;

namespace Game.Core.Navigation
{
    /// <summary>
    /// Playback queue of the GPS voice (ADR 0328), pure logic (no audio): clips of one announcement play in order and are
    /// never interrupted; announcements never overlap. An announcement that has not started yet is replaced by a newer one
    /// (the newest guidance wins - e.g. "za 300 m" still waiting when "teraz" arrives), the one already speaking finishes.
    /// Fixed capacity, no allocation.
    /// </summary>
    public sealed class NavVoiceClipQueue
    {
        public const int Capacity = 16;
        readonly VoiceClip[] m_Clip = new VoiceClip[Capacity];
        readonly int[] m_Ann = new int[Capacity];
        int m_Head, m_Count, m_NextAnn, m_OpenAnn = -1, m_PlayingAnn = -1;

        public int Count => m_Count;
        /// <summary>Announcement whose clip was dequeued last (-1 = none yet / cleared).</summary>
        public int PlayingAnnouncement => m_PlayingAnn;
        public int Dropped { get; private set; }

        public void Clear() { m_Head = 0; m_Count = 0; m_OpenAnn = -1; m_PlayingAnn = -1; }

        /// <summary>Starts a new announcement: queued clips of announcements that have not started are dropped.</summary>
        public int Begin()
        {
            int keep = 0;
            for (int i = 0; i < m_Count; i++)
            {
                int s = (m_Head + i) % Capacity;
                if (m_Ann[s] != m_PlayingAnn) { Dropped++; continue; }
                int d = (m_Head + keep) % Capacity;
                m_Clip[d] = m_Clip[s]; m_Ann[d] = m_Ann[s];
                keep++;
            }
            m_Count = keep;
            m_OpenAnn = m_NextAnn++;
            return m_OpenAnn;
        }

        /// <summary>Adds a clip to the open announcement (one is begun implicitly). False when full or the key is empty.</summary>
        public bool Add(VoiceClip c)
        {
            if (c.Block == 0 || c.Index == 0) return false;
            if (m_OpenAnn < 0) Begin();
            if (m_Count >= Capacity) { Dropped++; return false; }
            int s = (m_Head + m_Count) % Capacity;
            m_Clip[s] = c; m_Ann[s] = m_OpenAnn;
            m_Count++;
            return true;
        }

        /// <summary>Next clip to play; <paramref name="newAnnouncement"/> = it starts an announcement (gap before it is longer).</summary>
        public bool TryNext(out VoiceClip c, out bool newAnnouncement)
        {
            if (m_Count == 0) { c = default; newAnnouncement = false; return false; }
            c = m_Clip[m_Head];
            int ann = m_Ann[m_Head];
            newAnnouncement = ann != m_PlayingAnn;
            m_PlayingAnn = ann;
            m_Head = (m_Head + 1) % Capacity;
            m_Count--;
            return true;
        }
    }

    /// <summary>
    /// Plays the GPS voice (ADR 0328): subscribes to <see cref="NavVoiceAnnouncer.Spoken"/> and plays the clips through one
    /// 2D AudioSource in the cab (no mixer in the project, ADR 0270: level = <see cref="Volume"/> x the UI channel of the
    /// player settings, <see cref="AudioMixLevels.Ui"/>). Clips of an announcement follow each other with
    /// <see cref="ClipGapS"/>, announcements with at least <see cref="AnnouncementGapS"/>; nothing overlaps
    /// (<see cref="NavVoiceClipQueue"/>). <see cref="Duck01"/> rises while speaking, for ducking the engine (not wired yet).
    /// No allocation per frame.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class NavVoicePlayer : MonoBehaviour
    {
        /// <summary>Pause between clips of one announcement [s] - WORKING_VALUE, tools/audio/gps/process_pack.py DEMO_GAP_S.</summary>
        public const float ClipGapS = 0.08f;
        /// <summary>Minimum pause between two announcements [s] - WORKING_VALUE.</summary>
        public const float AnnouncementGapS = 0.6f;

        [Range(0f, 1f)] public float Volume = 0.9f;
        public bool Muted;

        public NavVoiceBank Bank { get; private set; }
        public readonly NavVoiceClipQueue Queue = new NavVoiceClipQueue();
        /// <summary>Clips ordered but missing from the bank (skipped).</summary>
        public int Missing { get; private set; }
        public int Played { get; private set; }
        public bool Speaking => m_Src != null && m_Src.isPlaying;
        /// <summary>The AudioSource (tests / diagnostics).</summary>
        public AudioSource Source => m_Src;
        /// <summary>Clip taken from the queue, waiting for its gap; null = none.</summary>
        public AudioClip Pending => m_Pending;
        /// <summary>0..1, follows "speaking or about to speak" with 50 ms attack / 400 ms release.</summary>
        public float Duck01 { get; private set; }

        AudioSource m_Src;
        NavVoiceAnnouncer m_Announcer;
        System.Action<VoiceClip[], int> m_Handler;

        /// <summary>Adds (or reuses) the player on <paramref name="host"/> and hooks it to <paramref name="announcer"/>.
        /// Returns null (GPS stays silent, one warning) when the bank is not imported.</summary>
        public static NavVoicePlayer Install(GameObject host, NavVoiceAnnouncer announcer, NavVoiceBank bank = null)
        {
            bank = bank != null ? bank : NavVoiceBank.LoadDefault();
            if (bank == null || bank.Count == 0)
            {
                Debug.LogWarning("[NAVVOICE] no GPS voice bank (" + NavVoiceBank.ResourcePath + ") - run Kamion/Audio/Import GPS voice");
                return null;
            }
            if (!host.TryGetComponent(out NavVoicePlayer p)) p = host.AddComponent<NavVoicePlayer>();
            p.Configure(bank, announcer);
            Debug.Log("[NAVVOICE] player ready: " + bank.Count + " clips (" + bank.sourceInfo + ")");
            return p;
        }

        public void Configure(NavVoiceBank bank, NavVoiceAnnouncer announcer)
        {
            Bank = bank;
            bank.Build();
            if (m_Src == null)
            {
                var go = new GameObject("GpsVoice");
                go.transform.SetParent(transform, false);
                m_Src = go.AddComponent<AudioSource>();
                m_Src.playOnAwake = false;
                m_Src.loop = false;
                m_Src.spatialBlend = 0f;      // the head unit speaker is in the cab, in front of the driver: 2D
                m_Src.priority = 16;          // above engine layers and ambience (64 real voices on PC, ADR 0286)
                m_Src.bypassReverbZones = true;
                m_Src.dopplerLevel = 0f;
            }
            if (m_Announcer != null && m_Handler != null) m_Announcer.Spoken -= m_Handler;
            m_Announcer = announcer;
            if (m_Handler == null) m_Handler = Enqueue;
            if (announcer != null) announcer.Spoken += m_Handler;
        }

        /// <summary>One announcement (the buffer of <see cref="NavVoiceAnnouncer.Spoken"/>, copied into the queue).</summary>
        public void Enqueue(VoiceClip[] clips, int n)
        {
            if (Muted || clips == null) return;
            Queue.Begin();
            for (int i = 0; i < n && i < clips.Length; i++) Queue.Add(clips[i]);
        }

        public void Stop()
        {
            Queue.Clear();
            m_Pending = null;
            if (m_Src != null) m_Src.Stop();
        }

        void OnDestroy()
        {
            if (m_Announcer != null && m_Handler != null) m_Announcer.Spoken -= m_Handler;
        }

        void Update() => Step(Time.unscaledDeltaTime);

        /// <summary>One playback step (Update; tests call it directly).</summary>
        public void Step(float dt)
        {
            if (m_Src == null) return;
            m_Src.volume = Muted ? 0f : Volume * AudioMixLevels.Ui;
            bool busy = m_Src.isPlaying;
            float duckTarget = busy || m_Pending != null || Queue.Count > 0 ? 1f : 0f;
            Duck01 = Mathf.MoveTowards(Duck01, duckTarget, dt / (duckTarget > Duck01 ? 0.05f : 0.4f));
            if (busy) { m_Idle = 0f; return; }
            m_Idle += dt;
            while (m_Pending == null && Queue.TryNext(out VoiceClip c, out bool newAnn))
            {
                var clip = Bank != null ? Bank.Get(c) : null;
                if (clip == null) { Missing++; continue; }
                m_Pending = clip;
                m_PendingGap = newAnn && Played > 0 ? AnnouncementGapS : ClipGapS;
            }
            if (m_Pending != null && m_Idle >= m_PendingGap)
            {
                m_Src.clip = m_Pending;
                m_Src.Play();
                m_Pending = null;
                m_Idle = 0f;
                Played++;
            }
        }

        AudioClip m_Pending;
        float m_PendingGap;
        float m_Idle = 10f;    }
}
