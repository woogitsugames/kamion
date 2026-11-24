# STATUS recorder-s24 (ADR 0345 — nagranie przejazdu z dźwiękiem gry)

- [24.11] Worktree gotowy. ffmpeg: h264_nvenc NIE działa (sterownik 582.78 < 610 wymagany przez NVENC API 13.1 tej wersji ffmpeg);
  działa ddagrab + h264_mf (NVIDIA H.264 Encoder MFT, nv12). Istniejący `-audio_capture` (ADR 0286) = bufor stały, zapis tylko na końcu.
- Kod: Game.Core.Recording (AudioRingBuffer, WavFormat, WavStreamWriter), Game.Gameplay.GameAudioRecorder (-record_audio),
  CabinBusFilter → PushFromBus, NavStreamFollower → linia `[NAV] arrived` (z -nav_log). Testy EditMode AudioRecorderTests (9).
- NASTĘPNY KROK: `pwsh scripts/unity-slot.ps1 -Acquire -Owner recorder-s24; pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter AudioRecorderTests; pwsh scripts/unity-slot.ps1 -Release -Owner recorder-s24`
- [16:4x] EditMode AudioRecorderTests 9/9 (artifacts/tests/editmode-20261124-163829.xml). scripts/record-drive.ps1 napisany
  (ddagrab + h264_mf High u_vbr 40M / nvenc / x264, start po [NAV] status, stop po [NAV] arrived, mux adelay/atrim + drift).
- NASTĘPNY KROK: test na buildzie #7: `pwsh scripts/record-drive.ps1 -Exe ..\win-build\artifacts\win\kamion-0.1.0-a8352917be-regions\Kamion.exe -LegacyAudioCapture -MaxSeconds 150 -Out artifacts/recorder-s24/b7-legacy`
