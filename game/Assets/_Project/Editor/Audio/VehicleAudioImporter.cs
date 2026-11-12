using System;
using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;
using TruckSim.Audio;
using UnityEditor;
using UnityEngine;

namespace Game.Editor.Audio
{
    /// <summary>
    /// Builds the vehicle audio assets from tools/audio's output (docs/AUDIO_DESIGN.md §5 "Import do Unity"):
    /// reads art-source/audio/generated/manifest.json, copies the WAVs into Assets/_Project/Audio/Generated/Clips
    /// (gitignored; the Library caches the compressed imports), and writes four <see cref="EngineSoundBank"/>s plus a
    /// <see cref="VehicleAudioLibrary"/> into Assets/_Project/Audio/Generated/Resources/VehicleAudio.
    /// Import settings (<see cref="VehicleAudioPostprocessor"/>): ADPCM, Compressed In Memory for the engine loops
    /// (≈ 13 MB RAM), Decompress On Load for short one-shots, preload on, mono, original 48 kHz.
    /// Regenerate the WAVs with: cd tools/audio; uv run python render_all.py
    /// Batchmode: -executeMethod Game.Editor.Audio.VehicleAudioImporter.ImportBatch
    /// </summary>
    public static class VehicleAudioImporter
    {
        public const string GeneratedDir = "Assets/_Project/Audio/Generated";
        public const string ClipsDir = GeneratedDir + "/Clips";
        public const string ResourcesDir = GeneratedDir + "/Resources/VehicleAudio";
        public static string ManifestPath => Path.Combine(EditorTools.RepoRoot, "art-source", "audio", "generated", "manifest.json");
        /// <summary>ElevenLabs layers (ADR 0137): WAVs tracked in git under this folder, manifest from tools/audio/el_prepare.py.</summary>
        public const string ElevenLabsDir = "Assets/_Project/Audio/ElevenLabs";
        public static string ElevenLabsManifestPath => Path.Combine(EditorTools.ProjectRoot, ElevenLabsDir, "el_manifest.json");

        [Serializable] class Manifest
        {
            public string generator;
            public int sample_rate;
            public int[] rpm_grid, ebrake_rpm_grid;
            public Clip[] clips;
            public Sfx[] sfx;
        }
        [Serializable] class Clip { public string name, file, kind, perspective, layer; public int rpm, cycles, samples; public float load, rpm_exact; }
        [Serializable] class Sfx { public string name, file; public bool loop; public int samples; }

        public static void ImportBatch()
        {
            int exit = 0;
            try { Debug.Log("AUDIOIMPORT_RESULT: " + (Import() ? "OK" : "NO_MANIFEST")); }
            catch (Exception e) { Debug.LogException(e); Debug.Log("AUDIOIMPORT_RESULT: FAILED"); exit = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        /// <summary>Imports when the library asset is missing or older than the manifest. Returns true when the library exists afterwards.</summary>
        public static bool ImportIfNeeded()
        {
            string lib = Path.Combine(EditorTools.ProjectRoot, ResourcesDir, "VehicleAudioLibrary.asset");
            if (!File.Exists(ManifestPath)) return File.Exists(lib);
            if (File.Exists(lib) && File.GetLastWriteTimeUtc(lib) >= File.GetLastWriteTimeUtc(ManifestPath)
                && (!File.Exists(ElevenLabsManifestPath) || File.GetLastWriteTimeUtc(lib) >= File.GetLastWriteTimeUtc(ElevenLabsManifestPath))) return true;
            return Import();
        }

        [MenuItem("Kamion/Audio/Import vehicle audio (tools/audio manifest)")]
        public static bool Import()
        {
            if (!File.Exists(ManifestPath))
            {
                Debug.LogWarning($"[AUDIO] {ManifestPath} not found. Run: cd tools/audio; uv run python render_all.py");
                return false;
            }
            var man = JsonUtility.FromJson<Manifest>(File.ReadAllText(ManifestPath));
            if (man?.clips == null || man.clips.Length == 0) throw new InvalidDataException("manifest.json has no clips");

            // 1) copy WAVs (only when changed) -------------------------------------------------------------
            int copied = 0;
            var assetPathOf = new Dictionary<string, string>();
            void Copy(string name, string repoRelative, string sub)
            {
                string src = Path.Combine(EditorTools.RepoRoot, repoRelative.Replace('/', Path.DirectorySeparatorChar));
                if (!File.Exists(src)) throw new FileNotFoundException("manifest lists a missing WAV", src);
                string assetPath = $"{ClipsDir}/{sub}/{name}.wav";
                string dst = Path.Combine(EditorTools.ProjectRoot, assetPath);
                Directory.CreateDirectory(Path.GetDirectoryName(dst));
                var si = new FileInfo(src);
                var di = new FileInfo(dst);
                if (!di.Exists || di.Length != si.Length || di.LastWriteTimeUtc < si.LastWriteTimeUtc) { File.Copy(src, dst, true); copied++; }
                assetPathOf[name] = assetPath;
            }
            foreach (var c in man.clips) Copy(c.name, c.file, (c.kind == "ebrake" ? "ebrake/" : "engine/") + c.perspective);
            foreach (var s in man.sfx) Copy(s.name, s.file, "sfx");
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, ResourcesDir));
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);

            // 2) banks ------------------------------------------------------------------------------------
            AudioClip Load(string name)
            {
                var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(assetPathOf[name]);
                if (clip == null) throw new InvalidDataException("not imported as AudioClip: " + assetPathOf[name]);
                return clip;
            }
            EngineSoundBank Bank(string file, string kind, string persp, float spatial)
            {
                var sel = new List<Clip>();
                foreach (var c in man.clips) if (c.kind == kind && c.perspective == persp) sel.Add(c);
                var rpms = new SortedSet<int>(); var loads = new SortedSet<float>();
                foreach (var c in sel) { rpms.Add(c.rpm); loads.Add(kind == "ebrake" ? 0f : c.load); }
                var rp = new List<int>(rpms); var lp = new List<float>(loads);
                int n = rp.Count * lp.Count;
                var bank = LoadOrCreate<EngineSoundBank>($"{ResourcesDir}/{file}.asset");
                bank.rpmPoints = rp.ConvertAll(r => (float)r).ToArray();
                bank.loadPoints = lp.ToArray();
                bank.clips = new AudioClip[n];
                bank.clipRpmExact = new float[n];
                bank.clipCycles = new int[n];
                bank.spatialBlend = spatial;
                foreach (var c in sel)
                {
                    int i = lp.IndexOf(kind == "ebrake" ? 0f : c.load) * rp.Count + rp.IndexOf(c.rpm);
                    bank.clips[i] = Load(c.name);
                    bank.clipRpmExact[i] = c.rpm_exact;
                    bank.clipCycles[i] = c.cycles;
                }
                if (!bank.Validate(out string err)) throw new InvalidDataException(err);
                EditorUtility.SetDirty(bank);
                return bank;
            }
            var lib = LoadOrCreate<VehicleAudioLibrary>($"{ResourcesDir}/VehicleAudioLibrary.asset");
            lib.exteriorEngine = Bank("EngineBank_ext", "engine", "ext", 1f);
            lib.cabEngine = Bank("EngineBank_cab", "engine", "cab", 0f);
            lib.exteriorEngineBrake = Bank("EngineBrakeBank_ext", "ebrake", "ext", 1f);
            lib.cabEngineBrake = Bank("EngineBrakeBank_cab", "ebrake", "cab", 0f);
            AudioClip Sfx(string name) => assetPathOf.ContainsKey(name) ? Load(name) : null;
            lib.turboWhistleLoop = Sfx("turbo_whistle_loop");
            lib.turboLiftoff = Sfx("turbo_liftoff");
            lib.airBrakeRelease = Sfx("air_brake_release");
            lib.parkingBrakeSet = Sfx("parking_brake_set");
            lib.airDryerPurge = Sfx("air_dryer_purge");
            lib.gearshiftAir = Sfx("gearshift_air");
            lib.roadRollLoop = Sfx("road_roll_loop");
            lib.windLoop = Sfx("wind_loop");
            lib.gearWhineLoop = Sfx("gear_whine_loop");
            // cabin perspectives + the audio-layers pass (all optional: an older manifest just leaves them null)
            lib.airBrakeReleaseCab = Sfx("air_brake_release_cab");
            lib.parkingBrakeSetCab = Sfx("parking_brake_set_cab");
            lib.airDryerPurgeCab = Sfx("air_dryer_purge_cab");
            lib.gearshiftAirCab = Sfx("gearshift_air_cab");
            lib.roadRollLoopCab = Sfx("road_roll_cab_loop");
            lib.windLoopCab = Sfx("wind_cab_loop");
            lib.parkingBrakeRelease = Sfx("parking_brake_release");
            lib.parkingBrakeReleaseCab = Sfx("parking_brake_release_cab");
            lib.airDryerPurgeB = Sfx("air_dryer_purge_b");
            lib.airDryerPurgeBCab = Sfx("air_dryer_purge_b_cab");
            VehicleAudioLibrary.PerspectivePair Pair(string ext, string cab) =>
                new VehicleAudioLibrary.PerspectivePair { ext = Sfx(ext), cab = Sfx(cab) };
            lib.tyreSurface = new[]
            {
                Pair("road_roll_loop", "road_roll_cab_loop"), Pair("tyre_wet_loop", "tyre_wet_cab_loop"),
                Pair("tyre_concrete_loop", "tyre_concrete_cab_loop"), Pair("tyre_cobbles_loop", "tyre_cobbles_cab_loop"),
                Pair("tyre_gravel_loop", "tyre_gravel_cab_loop"), Pair("tyre_grass_loop", "tyre_grass_cab_loop"),
            };
            lib.tyreSqueal = Pair("tyre_squeal_loop", "tyre_squeal_cab_loop");
            lib.retarder = Pair("retarder_loop", "retarder_cab_loop");
            lib.compressor = Pair("compressor_loop", "compressor_cab_loop");
            lib.ambientBed = Pair("ambient_bed_loop", "ambient_bed_cab_loop");
            lib.forklift = Pair("forklift_loop", "forklift_cab_loop");
            lib.crowCaw = Pair("bird_crow_caw", "bird_crow_caw_cab");
            lib.indicatorTick = Pair("indicator_tick", "indicator_tick_cab");
            lib.indicatorTock = Pair("indicator_tock", "indicator_tock_cab");
            lib.birdSparrow = Sfx("bird_sparrow");
            lib.birdTit = Sfx("bird_tit");
            int el = ImportElevenLabs(lib);
            lib.sourceInfo = $"{man.clips.Length} engine loops + {man.sfx.Length} sfx, {man.generator}; ElevenLabs {el} clips";
            EditorUtility.SetDirty(lib);
            AssetDatabase.SaveAssets();
            Debug.Log($"[AUDIO] vehicle audio imported: {man.clips.Length} loops, {man.sfx.Length} sfx, {copied} WAVs copied → {ResourcesDir}");
            return true;
        }

        /// <summary>
        /// Adds the ElevenLabs set (ADR 0137) to the library: engine and exhaust-brake banks (incoherent crossfade) and
        /// the event clips. Returns the number of clips, 0 when el_manifest.json is absent (fields stay null, the game
        /// falls back to the procedural engine).
        /// </summary>
        static int ImportElevenLabs(VehicleAudioLibrary lib)
        {
            lib.elExteriorEngine = lib.elCabEngine = lib.elExteriorEngineBrake = lib.elCabEngineBrake = null;
            lib.elEngineStart = lib.elEngineStop = lib.elIdleClatter = lib.elRetarder = lib.elTurboWastegate = default;
            if (!File.Exists(ElevenLabsManifestPath)) return 0;
            var man = JsonUtility.FromJson<Manifest>(File.ReadAllText(ElevenLabsManifestPath));
            string AssetPath(string repoRelative) => repoRelative.StartsWith("game/", StringComparison.Ordinal) ? repoRelative.Substring(5) : repoRelative;
            AudioClip Load(string repoRelative)
            {
                var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(AssetPath(repoRelative));
                if (clip == null) throw new InvalidDataException("ElevenLabs clip not imported: " + repoRelative);
                return clip;
            }
            EngineSoundBank Bank(string file, string kind, string persp, float spatial)
            {
                var sel = new List<Clip>();
                foreach (var c in man.clips) if (c.kind == kind && c.perspective == persp) sel.Add(c);
                var rpms = new SortedSet<int>(); var loads = new SortedSet<float>();
                foreach (var c in sel) { rpms.Add(c.rpm); loads.Add(kind == "ebrake" ? 0f : c.load); }
                var rp = new List<int>(rpms); var lp = new List<float>(loads);
                int n = rp.Count * lp.Count;
                var bank = LoadOrCreate<EngineSoundBank>($"{ResourcesDir}/{file}.asset");
                bank.rpmPoints = rp.ConvertAll(r => (float)r).ToArray();
                bank.loadPoints = lp.ToArray();
                bank.clips = new AudioClip[n];
                bank.clipRpmExact = new float[n];
                bank.clipCycles = new int[n];
                bank.spatialBlend = spatial;
                bank.incoherent = true;
                foreach (var c in sel)
                {
                    int i = lp.IndexOf(kind == "ebrake" ? 0f : c.load) * rp.Count + rp.IndexOf(c.rpm);
                    bank.clips[i] = Load(c.file);
                    bank.clipRpmExact[i] = c.rpm_exact;
                    bank.clipCycles[i] = c.cycles;
                }
                if (!bank.Validate(out string err)) throw new InvalidDataException(err);
                EditorUtility.SetDirty(bank);
                return bank;
            }
            lib.elExteriorEngine = Bank("EngineBank_el_ext", "engine", "ext", 1f);
            lib.elCabEngine = Bank("EngineBank_el_cab", "engine", "cab", 0f);
            lib.elExteriorEngineBrake = Bank("EngineBrakeBank_el_ext", "ebrake", "ext", 1f);
            lib.elCabEngineBrake = Bank("EngineBrakeBank_el_cab", "ebrake", "cab", 0f);
            var sfx = new Dictionary<string, string>();
            foreach (var s in man.sfx) sfx[s.name] = s.file;
            AudioClip Sfx(string name) => sfx.TryGetValue(name, out var f) ? Load(f) : null;
            VehicleAudioLibrary.PerspectivePair Pair(string ext, string cab) =>
                new VehicleAudioLibrary.PerspectivePair { ext = Sfx(ext), cab = Sfx(cab) };
            lib.elEngineStart = Pair("el_engine_start_ext", "el_engine_start_cab");
            lib.elEngineStop = Pair("el_engine_stop_ext", "el_engine_stop_cab");
            lib.elIdleClatter = Pair("el_idle_clatter_loop", "el_idle_clatter_cab_loop");
            lib.elRetarder = Pair("el_retarder_loop", "el_retarder_cab_loop");
            lib.elTurboWastegate = Pair("el_turbo_wastegate", "el_turbo_wastegate_cab");
            Debug.Log($"[AUDIO] ElevenLabs set imported: {man.clips.Length} loops, {man.sfx.Length} sfx ({man.generator})");
            return man.clips.Length + man.sfx.Length;
        }

        static T LoadOrCreate<T>(string path) where T : ScriptableObject
        {
            var a = AssetDatabase.LoadAssetAtPath<T>(path);
            if (a != null) return a;
            a = ScriptableObject.CreateInstance<T>();
            AssetDatabase.CreateAsset(a, path);
            return a;
        }
    }

    /// <summary>
    /// Import settings for the vehicle audio (applies only under Audio/Generated/Clips and Audio/ElevenLabs/Clips).
    /// Loops: ADPCM, Compressed In Memory (cheap decode for ~12 engine voices on the Helio G99, ADR 0007).
    /// One-shots: ADPCM Decompress On Load (procedural), Vorbis q 0.7 Decompress On Load (ElevenLabs events: longer,
    /// broadband, decoded once at load so no runtime Vorbis cost; ADR 0137).
    /// </summary>
    public sealed class VehicleAudioPostprocessor : AssetPostprocessor
    {
        void OnPreprocessAudio()
        {
            bool el = assetPath.StartsWith(VehicleAudioImporter.ElevenLabsDir + "/Clips/", StringComparison.Ordinal);
            if (!el && !assetPath.StartsWith(VehicleAudioImporter.ClipsDir + "/", StringComparison.Ordinal)) return;
            var imp = (AudioImporter)assetImporter;
            bool oneShot = assetPath.Contains("/sfx/") && !assetPath.EndsWith("_loop.wav", StringComparison.Ordinal);
            imp.forceToMono = true;
            imp.loadInBackground = false;
            var s = imp.defaultSampleSettings;
            s.loadType = oneShot ? AudioClipLoadType.DecompressOnLoad : AudioClipLoadType.CompressedInMemory;
            s.compressionFormat = el && oneShot ? AudioCompressionFormat.Vorbis : AudioCompressionFormat.ADPCM;
            if (el && oneShot) s.quality = 0.7f;
            s.sampleRateSetting = AudioSampleRateSetting.PreserveSampleRate;
            s.preloadAudioData = true;
            imp.defaultSampleSettings = s;
        }
    }
}
