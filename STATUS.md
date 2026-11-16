# STATUS audio-pc-s23 (agent audio, s23)

Zadanie: dźwięk na Windows (D73) — ustawienia importu Standalone, wyjście audio PC, pomiar LUFS/clipping/pamięci w playerze.

- [krok 1] worktree z origin/main eebb9813c; render_all.py: 191 WAV bit-identyczne z wersją w repo (deterministyczne), podglądy OGG różnią się bajtowo (koder Vorbis) → cofnięte.
- [krok 2] importer: override Standalone PCM Decompress On Load (domyślne/Android bez zmian), GetVersion=2; `Audio/PcAudioRuntime.cs` (reset wyjścia PC dsp 512 / 64 głosy, argumenty -audio_*, przechwyt miksu listenera do WAV); test EditMode `VehicleAudioPcImportTests`.
- NASTĘPNY KROK: `pwsh scripts/unity-slot.ps1 -Acquire -Owner audio-pc-s23; pwsh scripts/test.ps1 -Platform EditMode -Filter VehicleAudioPcImportTests; pwsh scripts/unity-slot.ps1 -Release -Owner audio-pc-s23`
