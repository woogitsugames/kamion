using System.Collections.Generic;
using Game.Editor.Audio;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0284: vehicle audio import settings per platform. Windows (Standalone) = PCM Decompress On Load for every clip
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
