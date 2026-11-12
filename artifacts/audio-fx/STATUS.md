# STATUS audio-fx (ADR 0142) — agent audio, s13

## 2026-11-12 krok 1: rozpoznanie
- Przejrzane arkusze analizy sekcji B–G (audio-el, audio-regen01), kod TruckAudioController/EngineAudio/AmbientAudio/importer.
- Zdarzenia z fizyki/sterowania już w kodzie: zwolnienie hamulca, postojowy, osuszacz, AMT, kierunkowskaz, opony, wiatr, sprężarka.
- Brak w grze: drzwi, klakson, wycieraczki, deszcz (brak interakcji/pogody) -> API + odsłuch w ustawieniach.
- NASTĘPNY KROK: `cd tools/audio; uv run python el_fx.py` (przetwarzanie wybranych plików C–G).
