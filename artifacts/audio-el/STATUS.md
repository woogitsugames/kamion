# audio-el STATUS (ADR 0137)

- 2026-11-12 krok 1a: tools/audio/el_analyze.py, analiza 128+ plikow ElevenLabs (artifacts/audio-el/analysis). Wynik: model ignoruje obroty z promptu, dominujaca linia 40-66 Hz (~850-1320 obr/min ekw.) dla wszystkich 600..2100.
  NASTEPNY KROK: `cd tools/audio; uv run python el_analyze.py` (pelny skan z arkuszami) -> wybor wariantow -> el_prepare.py
