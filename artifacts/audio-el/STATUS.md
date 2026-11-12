# audio-el STATUS (ADR 0137)

- 2026-11-12 krok 1a: tools/audio/el_analyze.py, analiza 128+ plikow ElevenLabs (artifacts/audio-el/analysis). Wynik: model ignoruje obroty z promptu, dominujaca linia 40-66 Hz (~850-1320 obr/min ekw.) dla wszystkich 600..2100.
  NASTEPNY KROK: `cd tools/audio; uv run python el_analyze.py` (pelny skan z arkuszami) -> wybor wariantow -> el_prepare.py
- krok 2: tools/audio/el_prepare.py + el_verify.py -> 24 komorki silnika (ext/cab x off/on x 600..2100), 8 hamulec wydechowy, 8 sfx; el_verify: 0 FAIL (ton +-2.5%, szew <1, brak klikow). WAV w game/Assets/_Project/Audio/ElevenLabs (LFS).
  NASTEPNY KROK: wpiecie w VehicleAudioImporter + EngineAudio/TruckAudioController (przelacznik audio.engineSource)
- krok 3 (kod): AudioPreferences (Game.Core, PlayerPrefs audio.engineSource, arg engine_audio=el|synth), przelacznik DZWIEK/Silnik w ControlSettingsPanel, EngineAudio: zestaw ElevenLabs + start/stop/klekot/wastegate, bramka hamulca silnikowego na zmianie biegu, importer el_manifest, testy PlayMode ElevenLabsEngineAudioTests. NIE skompilowane jeszcze (PHONE_RUN).
  NASTEPNY KROK: pwsh scripts/unity-slot.ps1 -Acquire -Owner claude-audio-el ; import + testy PlayMode -Filter ElevenLabs
- krok 4-5: ADR 0137, LICENSES (audio-elevenlabs-sfx-v3, Pro 99 USD), docs/owner/ELEVENLABS-REGEN-01.md (10 promptow x4), demo A/B artifacts/audio-el/demo/{el,synth}_{cab,ext}.mp3 (tools/audio/el_demo.py). Unity czeka na PHONE_RUN.
  NASTEPNY KROK: pwsh scripts/unity-slot.ps1 -Acquire -Owner claude-audio-el ; Unity -executeMethod Game.Editor.Audio.VehicleAudioImporter.ImportBatch ; pwsh scripts/test.ps1 -Platform PlayMode -Filter "ElevenLabsEngineAudioTests|AudioLayersTests"
- krok 6: porownanie z analiza GPT -> artifacts/audio-el/COMPARE-GPT.md (tools/audio/el_rpmtest.py: drabina R6 przy rpm z promptu 2/96). Zmiana zrodel cab_off 1200/1500 -> CAB_OFF_1800 (3). REGEN-01 + R6 (4 pozycje C-F), 56 generacji.
  NASTEPNY KROK: czekam na slot Unity (PHONE_RUN): import + testy PlayMode
- krok 7: Unity: import OK (ElevenLabs 32 petle + 10 sfx), PlayMode 19/19 (ElevenLabsEngineAudioTests 4/4, AudioLayers, ControlSettingsPanel, DrivingLabScene), EditMode ControlSettingsTests 19/19. Banki EngineBank_el_* + .meta zacommitowane (Generated jest sledzony w repo).
  NASTEPNY KROK (lider): scalic audio-el; APK -> owner A/B w Ustawieniach DZWIEK/Silnik lub adb -e engine_audio el|synth; po scaleniu truck-feel bramkowac EngineBrake na Amt.SyncBrakeRequest
