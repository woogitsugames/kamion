using Game.Cameras;
using Game.Controls;
using Game.UI;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Game.Gameplay
{
    /// <summary>
    /// Installs the full PC inputs (ADR 0264) into a <see cref="DrivingLabBootstrap"/>: the rebindable keyboard and the
    /// gamepad take the old fixed-key keyboard's place in the <see cref="DriverInputMixer"/> (ahead of the touch wheel),
    /// the binding overrides and pad tuning are loaded from <see cref="InputBindingsStore"/>, and the view commands
    /// (camera, mirrors, look, horn) are applied each frame. Attached automatically after a scene load so the shared
    /// composition root (and its parallel edits, ADR 0261 / 0262) is not touched; the lead may replace the hook with
    /// one explicit <c>AddComponent&lt;PcInputBridge&gt;()</c> line in the bootstrap (ADR 0264, "Scalenie").
    /// Allocation-free per frame.
    /// </summary>
    [DefaultExecutionOrder(-150)]   // after the bootstrap's Awake (-200); before its Update reads the mixer
    public sealed class PcInputBridge : MonoBehaviour
    {
        /// <summary>Set by the bootstrap (one line, see ADR 0264) to toggle the mirror insets; null = command ignored.</summary>
        public static System.Action ToggleMirrorInsets;

        public DrivingLabBootstrap Bootstrap { get; private set; }
        public DrivingActions Actions { get; private set; }
        public GamepadDriverInput Pad { get; private set; }
        public KeyboardBindingsDriverInput Keys { get; private set; }
        public PadKeyboardFeel Feel { get; private set; }
        public InputBindingsStore Store { get; private set; }
        string m_Path;
        CameraRig m_Rig;
        bool m_Installed;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Hook()
        {
            SceneManager.sceneLoaded -= OnSceneLoaded;
            SceneManager.sceneLoaded += OnSceneLoaded;
            AttachAll();
        }

        static void OnSceneLoaded(Scene s, LoadSceneMode m) => AttachAll();

        static void AttachAll()
        {
            foreach (var b in FindObjectsByType<DrivingLabBootstrap>(FindObjectsSortMode.None))
                if (b.GetComponent<PcInputBridge>() == null) b.gameObject.AddComponent<PcInputBridge>();
        }

        void Start()
        {
            Bootstrap = GetComponent<DrivingLabBootstrap>();
            if (Bootstrap == null) { enabled = false; return; }
            Feel = PadKeyboardFeel.LoadDefault();
            m_Path = InputBindingsStore.DefaultPath;
            Store = InputBindingsStore.LoadFromFile(m_Path, Feel);
            Actions = new DrivingActions();
            if (!Actions.LoadOverrides(Store.OverridesJson)) Store.OverridesJson = "";
            Actions.Enable();
            Pad = new GamepadDriverInput(Actions.Gamepad, Feel, Store.Tuning);
            Keys = new KeyboardBindingsDriverInput(Actions.Keyboard, Feel, Store.Tuning);
            var mixer = Bootstrap.Mixer;
            mixer.InsertBefore(Bootstrap.Keyboard, Pad);
            mixer.InsertBefore(Bootstrap.Keyboard, Keys);
            Bootstrap.Keyboard.Enabled = false;   // same default keys, now rebindable with ramps by speed (ADR 0264)
            m_Installed = true;
            ControlSettingsPanel.OpenInputBindings = OpenBindings;
            Debug.Log("[CONTROLS] pc-input installed schema=" + Store.Schema + " overrides=" + (Store.OverridesJson.Length > 0 ? "yes" : "no"));
        }

        void Update()
        {
            if (!m_Installed) return;
            // View commands of the frame just sampled by the bootstrap's Update (it runs first, order -200).
            var v = Pad.View; var k = Keys.View;
            if (m_Rig == null && Bootstrap.mainCamera != null) Bootstrap.mainCamera.TryGetComponent(out m_Rig);
            if (m_Rig != null)
            {
                if (v.CycleCamera || k.CycleCamera) m_Rig.NextMode();
                Vector2 look = v.LookDegS + k.LookDegS;
                if (look.sqrMagnitude > 0f && m_Rig.lookDegPerPixel > 1e-6f)
                    m_Rig.AddLookDelta(look * (Time.unscaledDeltaTime / m_Rig.lookDegPerPixel));
            }
            if ((v.ToggleMirrorInsets || k.ToggleMirrorInsets) && ToggleMirrorInsets != null) ToggleMirrorInsets();
            if (v.ToggleHudDetail || k.ToggleHudDetail) HudPreferences.ToggleDetail();   // ADR 0283: key I (rebindable), key press only
            if (v.Horn || k.Horn) Game.Core.AudioCues.HornHeld = true;   // the bootstrap writes the K key each frame; OR the bindings in
        }

        void OpenBindings(Transform parent)
        {
            if (!m_Installed) return;
            InputBindingsPanel.Create(parent, Actions, Store, Feel, Save, ApplyTuning);
        }

        /// <summary>Copies the overrides from the actions into the store and writes the file (settings screen edits).</summary>
        public void Save()
        {
            Store.OverridesJson = Actions.SaveOverrides();
            try { Store.SaveToFile(m_Path); }
            catch (System.Exception e) { Debug.LogWarning("[CONTROLS] input bindings not saved: " + e.Message); }
        }

        void ApplyTuning()
        {
            Pad.Tuning = Store.Tuning;
            Keys.Tuning = Store.Tuning;
            Save();
        }

        void OnDestroy()
        {
            if (ControlSettingsPanel.OpenInputBindings == (System.Action<Transform>)OpenBindings) ControlSettingsPanel.OpenInputBindings = null;
            Actions?.Dispose();
        }
    }
}
