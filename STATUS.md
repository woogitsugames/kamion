# STATUS recorder-s24 (ADR 0345 — nagranie przejazdu z dźwiękiem gry)

- [24.11] Worktree gotowy. ffmpeg: h264_nvenc NIE działa (sterownik 582.78 < 610 wymagany przez NVENC API 13.1 tej wersji ffmpeg);
  działa ddagrab + h264_mf (NVIDIA H.264 Encoder MFT, nv12). Istniejący `-audio_capture` (ADR 0286) = bufor stały, zapis tylko na końcu.
- Kod: Game.Core.Recording (AudioRingBuffer, WavFormat, WavStreamWriter), Game.Gameplay.GameAudioRecorder (-record_audio),
  CabinBusFilter → PushFromBus, NavStreamFollower → linia `[NAV] arrived` (z -nav_log). Testy EditMode AudioRecorderTests (9).
- NASTĘPNY KROK: `pwsh scripts/unity-slot.ps1 -Acquire -Owner recorder-s24; pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter AudioRecorderTests; pwsh scripts/unity-slot.ps1 -Release -Owner recorder-s24`
