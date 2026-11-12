# STATUS audio-fx (ADR 0142) — agent audio, s13

## 2026-11-12 krok 1: rozpoznanie
- Przejrzane arkusze analizy sekcji B–G (audio-el, audio-regen01), kod TruckAudioController/EngineAudio/AmbientAudio/importer.
- Zdarzenia z fizyki/sterowania już w kodzie: zwolnienie hamulca, postojowy, osuszacz, AMT, kierunkowskaz, opony, wiatr, sprężarka.
- Brak w grze: drzwi, klakson, wycieraczki, deszcz (brak interakcji/pogody) -> API + odsłuch w ustawieniach.
- NASTĘPNY KROK: `cd tools/audio; uv run python el_fx.py` (przetwarzanie wybranych plików C–G).

## krok 2: przetwarzanie efektów (el_fx.py)
- `tools/audio/el_fx.py`: 38 klipów (25 ID źródłowych) -> ElevenLabs/Clips/sfx, grupa "fx" w el_manifest; 0 FAIL (szwy < 1, HF < 6 dB, krawędzie, szczyt ≤ −1,5 dBFS). Arkusz `verify/fx_sheet.png` obejrzany.
- Zakres rozszerzony przez lidera (opinia właściciela o APK 0138): (1) turbo — wiarygodny gwizd od doładowania, cichy w kabinie, syk upustowy; (2) kabina vs zewnątrz — silnik w kabinie ciszej względem opon/wiatru/otoczenia, poziomy z danych dB(A). REGEN-02: łatwa podmiana plików.
- NASTĘPNY KROK: wpięcie w C# (VehicleAudioLibrary, importer, TruckAudioController, AmbientAudio, PerspectiveLoop.SetClips).
