using System.Collections.Generic;
using Game.Editor.Audio;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0285: vehicle audio import settings per platform. Windows (Standalone) = PCM Decompress On Load for every clip
    /// of both sound sets; the default (Android) settings keep the mobile compression (ADPCM loops, ADPCM / Vorbis 0.7
    /// one-shots) so the phone build is unchanged.
    /// </summary>
    public sealed class VehicleAudioPcImportTests
    {
        static readonly string[] Roots = { VehicleAudioImporter.ClipsDir, VehicleAudioImporter.ElevenLabsDir + "/Clips" };

        static List<(string path, AudioImporter imp)> Clips(string root)
        {
            var list = new List<(string, AudioImporter)>();
            foreach (var guid in AssetDatabase.FindAssets("t:AudioClip", new[] { root }))
            {
                string p = AssetDatabase.GUIDToAssetPath(guid);
                if (AssetImporter.GetAtPath(p) is AudioImporter imp) list.Add((p, imp));
            }
            return list;
        }

        [TestCaseSource(nameof(Roots))]
        public void Standalone_IsPcmDecompressOnLoad_ForLoopsAndOneShots(string root)
        {
            var clips = Clips(root);
            Assert.Greater(clips.Count, 20, $"no vehicle clips imported under {root}");
            int loops = 0, oneShots = 0;
            foreach (var (p, imp) in clips)
            {
                Assert.IsTrue(VehicleAudioPostprocessor.Owns(p), p);
                Assert.IsTrue(imp.ContainsSampleSettingsOverride(VehicleAudioPostprocessor.PcGroup), $"no Standalone override: {p}");
                var s = imp.GetOverrideSampleSettings(VehicleAudioPostprocessor.PcGroup);
                Assert.AreEqual(AudioCompressionFormat.PCM, s.compressionFormat, p);
                Assert.AreEqual(AudioClipLoadType.DecompressOnLoad, s.loadType, p);
                Assert.AreEqual(AudioSampleRateSetting.PreserveSampleRate, s.sampleRateSetting, p);
                Assert.IsTrue(s.preloadAudioData, p);
                if (VehicleAudioPostprocessor.IsOneShot(p)) oneShots++; else loops++;
            }
            Assert.Greater(loops, 0, "loops covered");
            Assert.Greater(oneShots, 0, "one-shots covered");
        }

        [TestCaseSource(nameof(Roots))]
        public void Default_KeepsMobileCompression(string root)
        {
            bool el = root.StartsWith(VehicleAudioImporter.ElevenLabsDir);
            foreach (var (p, imp) in Clips(root))
            {
                var d = imp.defaultSampleSettings;
                bool oneShot = VehicleAudioPostprocessor.IsOneShot(p);
                Assert.AreEqual(oneShot ? AudioClipLoadType.DecompressOnLoad : AudioClipLoadType.CompressedInMemory, d.loadType, p);
                Assert.AreEqual(el && oneShot ? AudioCompressionFormat.Vorbis : AudioCompressionFormat.ADPCM, d.compressionFormat, p);
                Assert.IsTrue(imp.forceToMono, p);
                Assert.IsFalse(imp.ContainsSampleSettingsOverride(BuildTargetGroup.Android), $"Android must use the defaults: {p}");
            }
        }

        [Test]
        public void ImportedClip_IsMono48k()
        {
            var clips = Clips(VehicleAudioImporter.ClipsDir);
            Assert.Greater(clips.Count, 0);
            var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(clips[0].path);
            Assert.AreEqual(1, clip.channels, clips[0].path);
            Assert.AreEqual(48000, clip.frequency, clips[0].path);
        }

        /// <summary>The importer has Normalize on (Unity default, applies to the Force To Mono downmix). The sources are
        /// already mono and their levels are mixed per clip (LUFS per grid cell), so the import must not peak-normalise:
        /// the decoded clip peak stays at the WAV peak.</summary>
        [Test]
        public void Import_KeepsSourceLevel_NoPeakNormalisation()
        {
            int checkedClips = 0;
            foreach (var (p, imp) in Clips(VehicleAudioImporter.ClipsDir))
            {
                if (!VehicleAudioPostprocessor.IsOneShot(p)) continue; // Decompress On Load: GetData works
                float filePeak = WavPeak(System.IO.Path.Combine(Game.Editor.Build.EditorTools.ProjectRoot, p));
                if (filePeak <= 0f || filePeak > 0.5f) continue;     // quiet sources only (-6 dBFS or lower)
                var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(p);
                var data = new float[clip.samples * clip.channels];
                Assert.IsTrue(clip.GetData(data, 0), p);
                float peak = 0f;
                foreach (float v in data) peak = Mathf.Max(peak, Mathf.Abs(v));
                float diffDb = 20f * Mathf.Log10(peak / filePeak);
                Assert.Less(Mathf.Abs(diffDb), 1.0f, $"{p}: imported peak {peak:F3} vs WAV {filePeak:F3} ({diffDb:F1} dB)");
                if (++checkedClips >= 5) break;
            }
            Assert.Greater(checkedClips, 0, "no quiet one-shot found to check");
        }

        /// <summary>Peak of a 16-bit PCM WAV (first data chunk), linear 0..1.</summary>
        static float WavPeak(string file)
        {
            var b = System.IO.File.ReadAllBytes(file);
            int i = 12;
            while (i + 8 <= b.Length)
            {
                int len = System.BitConverter.ToInt32(b, i + 4);
                if (b[i] == 'd' && b[i + 1] == 'a' && b[i + 2] == 't' && b[i + 3] == 'a')
                {
                    int peak = 0;
                    for (int k = i + 8; k + 1 < i + 8 + len && k + 1 < b.Length; k += 2)
                        peak = System.Math.Max(peak, System.Math.Abs((int)System.BitConverter.ToInt16(b, k)));
                    return peak / 32768f;
                }
                i += 8 + len + (len & 1);
            }
            return 0f;
        }

        [Test]
        public void PcSettings_OverridesOnlyCompression()
        {
            var d = new AudioImporterSampleSettings
            {
                loadType = AudioClipLoadType.CompressedInMemory, compressionFormat = AudioCompressionFormat.ADPCM,
                quality = 0.5f, sampleRateSetting = AudioSampleRateSetting.PreserveSampleRate, preloadAudioData = false,
            };
            var s = VehicleAudioPostprocessor.PcSettings(d);
            Assert.AreEqual(AudioCompressionFormat.PCM, s.compressionFormat);
            Assert.AreEqual(AudioClipLoadType.DecompressOnLoad, s.loadType);
            Assert.IsTrue(s.preloadAudioData);
        }
    }
}
