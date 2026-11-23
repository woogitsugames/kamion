using System;
using System.IO;
using Game.Core.Navigation;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;

namespace Game.Editor.Audio
{
    /// <summary>
    /// Builds the GPS voice bank (ADR 0328) from Assets/_Project/Audio/Voice/gps_manifest.json (tools/audio/gps/process_pack.py):
    /// one <see cref="NavVoiceBank"/> entry per manifest clip (key GPS_Bxx #i -> AudioClip under Audio/Voice/Gps, WAVs in git
    /// via LFS), written to Assets/_Project/Audio/Generated/Resources/GpsVoice/NavVoiceBank.asset (gitignored). Called by
    /// <see cref="VehicleAudioImporter.ImportIfNeeded"/> before every build. Batchmode:
    /// -executeMethod Game.Editor.Audio.GpsVoiceImporter.ImportBatch
    /// </summary>
    public static class GpsVoiceImporter
    {
        public const string VoiceDir = "Assets/_Project/Audio/Voice";
        public const string ClipsDir = VoiceDir + "/Gps";
        public const string BankPath = VehicleAudioImporter.GeneratedDir + "/Resources/GpsVoice/NavVoiceBank.asset";
        public static string ManifestPath => Path.Combine(EditorTools.ProjectRoot, VoiceDir, "gps_manifest.json");

        [Serializable] public class Manifest
        {
            public string generator, pack, processed;
            public Voice voice;
            public float target_lufs;
            public int clip_count;
            public Clip[] clips;
        }
        [Serializable] public class Voice { public string name, voice_id, tts_model, plan, date; }
        [Serializable] public class Clip { public string key, text, file, sha256; public int block, index; public float duration_s, lufs; }

        public static Manifest ReadManifest() =>
            File.Exists(ManifestPath) ? JsonUtility.FromJson<Manifest>(File.ReadAllText(ManifestPath)) : null;

        public static void ImportBatch()
        {
            int exit = 0;
            try { Debug.Log("GPSVOICEIMPORT_RESULT: " + (Import() ? "OK" : "NO_MANIFEST")); }
            catch (Exception e) { Debug.LogException(e); Debug.Log("GPSVOICEIMPORT_RESULT: FAILED"); exit = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        /// <summary>Imports when the bank is missing or older than the manifest. True when the bank exists afterwards.</summary>
        public static bool ImportIfNeeded()
        {
            string bank = Path.Combine(EditorTools.ProjectRoot, BankPath);
            if (!File.Exists(ManifestPath)) return File.Exists(bank);
            if (File.Exists(bank) && File.GetLastWriteTimeUtc(bank) >= File.GetLastWriteTimeUtc(ManifestPath)) return true;
            return Import();
        }

        [MenuItem("Kamion/Audio/Import GPS voice (Audio/Voice/gps_manifest.json)")]
        public static bool Import()
        {
            var man = ReadManifest();
            if (man == null) { Debug.LogWarning("[AUDIO] " + ManifestPath + " not found (tools/audio/gps/process_pack.py)"); return false; }
            if (man.clips == null || man.clips.Length == 0) throw new InvalidDataException("gps_manifest.json has no clips");
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            int n = man.clips.Length;
            var blocks = new byte[n];
            var indices = new byte[n];
            var clips = new AudioClip[n];
            for (int i = 0; i < n; i++)
            {
                var c = man.clips[i];
                string path = VoiceDir + "/" + c.file;
                clips[i] = AssetDatabase.LoadAssetAtPath<AudioClip>(path);
                if (clips[i] == null) throw new InvalidDataException("GPS clip not imported as AudioClip: " + path);
                if (c.block <= 0 || c.block > NavVoiceBank.MaxBlock || c.index <= 0 || c.index > NavVoiceBank.MaxIndex)
                    throw new InvalidDataException("GPS clip key out of range: " + c.key);
                blocks[i] = (byte)c.block;
                indices[i] = (byte)c.index;
            }
            Directory.CreateDirectory(Path.GetDirectoryName(Path.Combine(EditorTools.ProjectRoot, BankPath)));
            var bank = AssetDatabase.LoadAssetAtPath<NavVoiceBank>(BankPath);
            if (bank == null) { bank = ScriptableObject.CreateInstance<NavVoiceBank>(); AssetDatabase.CreateAsset(bank, BankPath); }
            bank.blocks = blocks;
            bank.indices = indices;
            bank.clips = clips;
            bank.sourceInfo = $"{n} clips, voice '{man.voice?.name}' ({man.voice?.tts_model}), {man.generator}";
            bank.Build();
            EditorUtility.SetDirty(bank);
            AssetDatabase.SaveAssets();
            Debug.Log($"[AUDIO] GPS voice imported: {n} clips -> {BankPath}");
            return true;
        }
    }

    /// <summary>
    /// Import settings of the GPS voice clips (Audio/Voice/Gps, ADR 0328): mono, Decompress On Load (short, decoded once,
    /// ~13 MB PCM for the 96 clips on PC), preload. Default (Android): Vorbis q 0.6; Standalone: PCM (ADR 0286).
    /// </summary>
    public sealed class GpsVoicePostprocessor : AssetPostprocessor
    {
        public override uint GetVersion() => 1;

        public static bool Owns(string assetPath) => assetPath.StartsWith(GpsVoiceImporter.ClipsDir + "/", StringComparison.Ordinal);

        void OnPreprocessAudio()
        {
            if (!Owns(assetPath)) return;
            var imp = (AudioImporter)assetImporter;
            imp.forceToMono = true;
            imp.loadInBackground = false;
            var s = imp.defaultSampleSettings;
            s.loadType = AudioClipLoadType.DecompressOnLoad;
            s.compressionFormat = AudioCompressionFormat.Vorbis;
            s.quality = 0.6f;
            s.sampleRateSetting = AudioSampleRateSetting.PreserveSampleRate;
            s.preloadAudioData = true;
            imp.defaultSampleSettings = s;
            imp.SetOverrideSampleSettings(VehicleAudioPostprocessor.PcGroup, VehicleAudioPostprocessor.PcSettings(s));
        }
    }
}
