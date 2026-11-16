# STATUS audio-pc-s23 (agent audio, s23)

Zadanie: dźwięk na Windows (D73) — ustawienia importu Standalone, wyjście audio PC, pomiar LUFS/clipping/pamięci w playerze.

- [krok 1] worktree z origin/main eebb9813c; render_all.py: 191 WAV bit-identyczne z wersją w repo (deterministyczne), podglądy OGG różnią się bajtowo (koder Vorbis) → cofnięte.
- [krok 2] importer: override Standalone PCM Decompress On Load (domyślne/Android bez zmian), GetVersion=2; `Audio/PcAudioRuntime.cs` (reset wyjścia PC dsp 512 / 64 głosy, argumenty -audio_*, przechwyt miksu listenera do WAV); test EditMode `VehicleAudioPcImportTests`.
- NASTĘPNY KROK: `pwsh scripts/unity-slot.ps1 -Acquire -Owner audio-pc-s23; pwsh scripts/test.ps1 -Platform EditMode -Filter VehicleAudioPcImportTests; pwsh scripts/unity-slot.ps1 -Release -Owner audio-pc-s23`
- [krok 3] EditMode `VehicleAudioPcImportTests` 7/7 PASS (Android target; w tym test braku normalizacji przy imporcie). Symulacja IMA ADPCM (`tools/audio/pc_adpcm_sim.py`): SNR gwizdu turbo 25,8 dB, silnik ext on 1800 38,4 dB, szum ADPCM ponad sygnałem > 5 kHz → PCM na PC.
- [krok 4] build Development Win64 OK (117 s). Pierwszy przebieg playera (bez slotu, 3 gry naraz) zawiesił się po 32 s; przebieg bazowy BEZ argumentów audio też nie zamyka się (zawieszenie w shutdown) → przechwyt kończy się przed quit_t. Od 19:26 playery tylko w slocie heavy (-MaxSlots 1).
- Pomiar (64 głosy): 70 źródeł, 46–50 grających, wszystkie realne; przy 32 głosach projektu ~14–18 byłoby wirtualnych → przebieg bazowy to potwierdzi.
- NASTĘPNY KROK: `pwsh -File artifacts/audio-pc-s23/run-all.ps1` (build + 3 przebiegi: lab_cab_pc, lab_chase_pc, lab_cab_base), potem `cd tools/audio; uv run python pc_capture.py ../../artifacts/audio-pc-s23/player/lab_cab_pc.wav ../../artifacts/audio-pc-s23/report --label lab_cab_pc`
