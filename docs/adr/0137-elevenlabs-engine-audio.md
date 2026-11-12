# ADR 0137 — Silnik z nagrań ElevenLabs obok syntezy (przełącznik w ustawieniach)
Status: Proposed (agent audio, s12), 2026-11-12. Ocena brzmienia: właściciel (telefon, głośnik i słuchawki).

## Kontekst
Właściciel wygenerował 248 plików WAV (62 ID × 4 warianty, 48 kHz stereo 16-bit) w ElevenLabs Sound Effects v3, według
`docs/owner/ELEVENLABS-PROMPTS.md`. Dotąd silnik był w 100 % syntezą (ADR 0007, 0017). Analiza (`tools/audio/el_analyze.py`,
`artifacts/audio-el/analysis/`):
- Pętle stałych obrotów (sekcja A, 96 plików) **trzymają stały ton**: na spektrogramach są poziome linie, bez wkręcania,
  a mediana wahania linii dominującej w oknach 1 s wynosi 9 %. **Liczby obrotów z promptu model jednak nie odwzorowuje.**
  Dominująca linia leży przy 36–72 Hz, czyli ok. 700–1450 obr/min jako częstotliwość zapłonów R6 (obr/min / 20),
  mediana 933 obr/min. Tak samo jest dla promptów 600 i 2100 obr/min; korelacja prompt → pomiar r = 0,24.
- Szwy pętli są czyste: skok końca do początku < 1 × p99,9 |dx| w 96/96. Brak przesterowania (0 próbek ≥ 0,999).
  Poziomy rozrzucone w dwóch grupach (ok. −20 i −40 LUFS), więc trzeba normalizować.
- `TURBO_SPOOL` nie ma tonalnego gwizdu. Pozostałe zdarzenia B (start, stop, klekot, wastegate, hamulec wydechowy,
  retarder) są użyteczne.

## Decyzja
1. **Siatka z pomiaru, nie z nazwy pliku.** Każda komórka siatki (perspektywa × obciążenie off/on × 600…2100 obr/min
   co 300) bierze najlepszą stabilną pętlę danej perspektywy i obciążenia z całej puli. O wyborze decyduje ranking
   w `el_prepare.py`: wyrazistość linii, stabilność, drabina harmonicznych, a jak najmniejsze przestrojenie daje
   karę log2. Pętla jest przestrajana **offline**: okresowy resampling FFT N→M próbek zachowuje szew. Ton zmierzony
   po przestrojeniu trafia w obr/min / 20 z dokładnością ±2,5 % (`el_verify.py`, 24/24). Runtime nadal stroi
   `pitch = rpm / clipRpmExact` między punktami siatki (`EngineLayerGrid`, bez zmian algorytmu).
2. **Szew:** ostatnie 40 ms przechodzą crossfade'em equal-power w pierwsze. Pomiar po obróbce: skok < 0,7 × p99,9,
   szpilka HF na zawinięciu < 6 dB, 0 FAIL na 36 pętlach.
3. **Głośność:** każda komórka ma zmierzoną głośność (BS.1770, LUFS) komórki syntezy o tych samych
   obrotach/obciążeniu/perspektywie. Dzięki temu stałe miksu `EngineAudio`/`TruckAudioController` znaczą to samo
   w obu zestawach. Miękki limiter ≤ 1,1 dB (tylko kabina, pełne obciążenie, 2100).
4. **Crossfade equal-power** dla banków ElevenLabs (`EngineSoundBank.incoherent`). Komórki to różne nagrania, więc
   wyrównanie fazy wału nic nie daje. Test: suma kwadratów wzmocnień = 1 ± 0,02 na całym zakresie.
5. **Zdarzenia:** start (ext/kabina) i stop są wyzwalane przejściem obrotów przez 400/250 obr/min. Fizyka robi
   `Engine.Restart` (skok do jałowych) i zgaśnięcie. Pętle milkną na czas korbowania: 1,2 s ciszy, potem 1,0 s
   wejścia (`WORKING_VALUE`). Po stopie są ucinane w 0,2 s, bo nagranie stopu niesie wybieg. Klekot jałowy:
   pełny przy 600 obr/min, znika do 1300. Wastegate zastępuje syntetyczny „lift-off”. Hamulec wydechowy to jedno
   nagranie (zmierzone 1443 obr/min) przestrojone do 1000/1400/1800/2200. Retarder: nagranie ElevenLabs.
   **Gwizd turbo zostaje z syntezy**, bo jest sterowany doładowaniem z fizyki, a `TURBO_SPOOL` się nie nadaje.
6. **Hamulec silnikowy w czasie zmiany biegu (uwaga z ADR 0134):** `TruckAudioController.EngineBrake` zwraca 0, gdy
   AMT jest w stanie `ShiftTorqueRamp/ShiftNeutral/ShiftSync/ShiftEngage`. `Amt.SyncBrakeRequest` jest tylko na gałęzi
   `truck-feel`; po jej scaleniu lider może zawęzić bramkę do tego sygnału (TODO w kodzie). Bramka działa w obu zestawach.
7. **Przełącznik do porównania:** `Game.Core.AudioPreferences` (PlayerPrefs `audio.engineSource`). W panelu ustawień
   jest **DŹWIĘK → Silnik: synteza / ElevenLabs**, zmiana działa na żywo (jedna przebudowa puli głosów, bez alokacji
   w pętli). Argument startowy `-e engine_audio el|synth`. **Domyślnie ElevenLabs**, z cichym powrotem do syntezy,
   gdy zestaw nie jest zaimportowany. Synteza zostaje w repo bez zmian.
8. **Pliki:** do gita (LFS) trafiają tylko wybrane i przetworzone pliki: `game/Assets/_Project/Audio/ElevenLabs/Clips/**`
   (48 kHz mono 16-bit, 21 MB WAV) i `el_manifest.json` z pochodzeniem (plik źródłowy, zmierzone obroty, przestrojenie,
   wzmocnienie, prompt). Surowe 248 plików zostaje u właściciela w `art-source/audio/elevenlabs/`, poza gitem.
   Import: `VehicleAudioImporter.ImportElevenLabs` buduje `EngineBank_el_*` i `EngineBrakeBank_el_*` w Generated/Resources.
   Ustawienia importu: pętle ADPCM Compressed In Memory, jak ADR 0007, bo dekodowanie ~12 głosów na Helio G99 jest
   tanie. Zdarzenia jednorazowe: Vorbis q 0,7 Decompress On Load, czyli dekodowanie raz przy ładowaniu. Wszystko mono.

## Konsekwencje
- Przy 1800–2100 obr/min przestrojenie wynosi ×1,4–1,9, przy 600 ×0,68. Szum spalania zmienia wtedy barwę
  i to może być słychać. Prośba o pętle opisane słowami (bez liczb), gwizd jako pętlę, przejazd przez obroty
  i stop z kabiny: `docs/owner/ELEVENLABS-REGEN-01.md` (40 generacji ≈ 8 000 kredytów).
- Barwa skacze między komórkami z różnych nagrań: 13 źródeł na 24 komórki. Ocenić może tylko ucho właściciela.
  Przejazd R4 z REGEN-01 da siatkę z jednego nagrania.
- RAM (szacunek z liczby próbek): pętle ElevenLabs 10,0 M próbek → ADPCM (4 bit) ≈ 4,8 MB, zdarzenia 0,9 M próbek → PCM ≈ 1,7 MB. Oba zestawy są w bibliotece,
  aktywny jest jeden (Resources ładuje oba, ok. +6,5 MB). Do zmierzenia na A16 (PSS).
- Licencja: `docs/LICENSES.md` → `audio-elevenlabs-sfx-v3`. Plan Pro, użytek komercyjny wg ToS z 2026-11-12.
  Service-Specific Terms SFX: `UNVERIFIED`.
- Sekcje C–G (skrzynia, pneumatyka, opony, kabina, otoczenie) są przeanalizowane: pętle bez klików, nic nie
  przesterowane. Wpięcie wymaga osobnego zadania.
