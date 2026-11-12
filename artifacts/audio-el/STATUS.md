# audio-el STATUS (ADR 0137)

- 2026-11-12 krok 1a: tools/audio/el_analyze.py, analiza 128+ plikow ElevenLabs (artifacts/audio-el/analysis). Wynik: model ignoruje obroty z promptu, dominujaca linia 40-66 Hz (~850-1320 obr/min ekw.) dla wszystkich 600..2100.
  NASTEPNY KROK: `cd tools/audio; uv run python el_analyze.py` (pelny skan z arkuszami) -> wybor wariantow -> el_prepare.py
- krok 2: tools/audio/el_prepare.py + el_verify.py -> 24 komorki silnika (ext/cab x off/on x 600..2100), 8 hamulec wydechowy, 8 sfx; el_verify: 0 FAIL (ton +-2.5%, szew <1, brak klikow). WAV w game/Assets/_Project/Audio/ElevenLabs (LFS).
  NASTEPNY KROK: wpiecie w VehicleAudioImporter + EngineAudio/TruckAudioController (przelacznik audio.engineSource)
