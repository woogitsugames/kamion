# STATUS recorder-s24 (ADR 0345 — nagranie przejazdu z dźwiękiem gry)

- [24.11] Worktree gotowy. ffmpeg: h264_nvenc NIE działa (sterownik 582.78 < 610 wymagany przez NVENC API 13.1 tej wersji ffmpeg);
  działa ddagrab + h264_mf (NVIDIA H.264 Encoder MFT, nv12). Istniejący `-audio_capture` (ADR 0286) = bufor stały, zapis tylko na końcu.
- Kod: Game.Core.Recording (AudioRingBuffer, WavFormat, WavStreamWriter), Game.Gameplay.GameAudioRecorder (-record_audio),
  CabinBusFilter → PushFromBus, NavStreamFollower → linia `[NAV] arrived` (z -nav_log). Testy EditMode AudioRecorderTests (9).
- NASTĘPNY KROK: `pwsh scripts/unity-slot.ps1 -Acquire -Owner recorder-s24; pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter AudioRecorderTests; pwsh scripts/unity-slot.ps1 -Release -Owner recorder-s24`
- [16:4x] EditMode AudioRecorderTests 9/9 (artifacts/tests/editmode-20261124-163829.xml). scripts/record-drive.ps1 napisany
  (ddagrab + h264_mf High u_vbr 40M / nvenc / x264, start po [NAV] status, stop po [NAV] arrived, mux adelay/atrim + drift).
- NASTĘPNY KROK: test na buildzie #7: `pwsh scripts/record-drive.ps1 -Exe ..\win-build\artifacts\win\kamion-0.1.0-a8352917be-regions\Kamion.exe -LegacyAudioCapture -MaxSeconds 150 -Out artifacts/recorder-s24/b7-legacy`
- [17:0x] Dev build z komponentem: artifacts/win/kamion-0.1.0-02aed4c673-regions-dev (tylko region C; świat C skopiowany z win-build
  _Generated, poza gitem). Test (heavy slot w kolejce): artifacts/recorder-s24/tests.ps1 → dev-record + b7-legacy, log tests.out.
- NASTĘPNY KROK: `pwsh -NoProfile -File artifacts/recorder-s24/tests.ps1 > artifacts/recorder-s24/tests.out` (jeśli przerwane), potem obejrzeć klatki MP4 + sync.log.
- [19:0x] GOTOWE. Release d2933ca96a (kafel C): pełny tor -record_audio OK (WAV 160 s, 0 drop, 1 przerwa 1,56 s wypełniona),
  MP4 kamion-test-1080p60.mp4 151 s, x264 slow crf 18 (1,8–2× czasu nagrania). NVENC: sterownik 582.78 < 610 → h264_mf + x264 offline.
  EditMode 10/10. Dowody: C:\Users\matma\Documents\Claude\kamion\artifacts\recorder-s24\ (rel-record, b7-legacy, dev-record).
  Okno zapory Windows (od dev buildu) nieodkliknięte — decyzja właściciela.
- NASTĘPNY KROK (lider, po scaleniu i buildzie #8): `pwsh scripts/record-drive.ps1 -Exe artifacts/win/kamion-0.1.0-<sha>-regions/Kamion.exe -Out artifacts/record/bialystok-tykocin`
