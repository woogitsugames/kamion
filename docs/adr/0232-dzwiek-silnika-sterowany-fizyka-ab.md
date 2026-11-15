# ADR 0232 — Dźwięk silnika i układu sterowany fizyką: barwa zależna od obciążenia, turbo, pneumatyka, odsłuch A/B
Status: Proposed (agent audio, chmura E, s21), 2026-11-15. Ocena brzmienia: właściciel (głośnik telefonu i słuchawki).
Kontynuacja ADR 0007 (warstwy sterowane fizyką), 0012 (kabina), 0134 (AMT + hamulec silnikowy), 0176 (retarder, AMT, osuszacz).
Zadanie: `docs/owner/CLOUD-E-PROMPT-S21.md` E5, BACKLOG B-098.

## Kontekst
Bank proceduralny (`tools/audio/render_all.py`, siatka obroty × obciążenie `off/mid/on` + siatka hamulca silnikowego) różnicował
warstwy obciążenia głównie poziomem: kształt impulsu wydechu, turbulencja i hamulec silnikowy miały wolne prawa obrotów,
niezwiązane z modelem fizyki. Komórka „off” przy biegu jałowym była silnikiem bez wtrysku, choć `Engine.ComputeTorque`
nigdy nie odcina dawki na jałowym. Gwizd turbo był prawie czystym tonem, a `turbo_liftoff`, `air_brake_release`
i `parking_brake_set` — szumem z ręcznie rysowaną obwiednią.

## Decyzja
Model syntezy `0232` (domyślny) obok zamrożonego `main` (bit w bit jak przed zmianą, przełącznik `--model main`, test
`test_main_model_is_unchanged`). Parametry fizyki czyta `tools/audio/physics_params.py` z tych samych JSON-ów, co gra
(`game/Assets/_Project/Vehicle/Physics/Definitions/Data/`); statusy liczb jak w tych plikach. Nowe stałe syntezy to `WORKING_VALUE`.

| element | model 0232 | źródło liczby |
|---|---|---|
| barwa wg obciążenia (`engine_synth`) | front impulsu wydechu tym stromszy, im większa dawka (`sharp = fuel^0,6`); na wybiegu impuls miękki i dłuższy; poziom warstw `off/mid` utrzymany jak w `main` | WORKING_VALUE |
| turbulencja przepływu | ~ dawka × gęstość ładunku (doładowanie) | WORKING_VALUE |
| bieg jałowy | komórki `off` blisko jałowego dostają dawkę regulatora = moment oporów / moment pełny przy `idleRpm`, zanik do jałowe + 150 obr/min; rozrzut wtryskiwaczy rośnie przy jałowym | stosunek z definicji silnika; zakres 150 obr/min WORKING_VALUE |
| hamulec silnikowy | amplituda impulsu dekompresji ~ krzywa `engineBrakeCurve` z fizyki (próg 0,15) zamiast `(0,35+0,65·n)^1,2` | definicja silnika |
| `turbo_whistle_loop` | ton łopatek (7 łopatek) ze wstęgami bocznymi rzędu wału w szumie przepływu sprężarki | WORKING_VALUE |
| `turbo_liftoff` | upust powietrza doładowującego: adiabatyczny wypływ 18 L / 1,8 bar(g) przez 14 mm (model wypływu z ADR 0176) + wybieg sprężarki ze stałą `boostTimeConstant` | stała czasowa z fizyki; reszta WORKING_VALUE, ciśnienie UNVERIFIED |
| `air_brake_release` | wypływ z komór przód 2,0 L i tył 2,8 L przez zawory 9 mm (tył opóźniony 25 ms) od `maxChamberPressureBar` | ciśnienie z definicji pojazdu |
| `parking_brake_set` | wypływ z komór sprężynowych 3,6 L przez 6,5 mm; stuk sprężyn tam, gdzie ciśnienie spada do `springReleaseStartBar` | ciśnienie z definicji pojazdu |

Bez zmian w C#: te same nazwy klipów i te same prawa miksu (`EngineAudio`, `TruckAudioController`, `LayerMath`, `DrivelineSfx`).
Nowe warstwy są wyrównane do głośności warstwy, którą zastępują (LUFS), ze szczytem ograniczonym. Retarder, fazy AMT,
osuszacz, opony, wiatr i sprężarka — bez zmian (ADR 0176 i wcześniejsze).

## Odsłuch A/B
`tools/audio/telemetry0232.py` uruchamia `tools/physics-runner` (ten sam model C# co gra, 100 Hz) na scenariuszach
`tools/audio/scenarios0232/*.json` i zapisuje kolumny dla dźwięku do `scenarios0232/telemetry/*.csv` (w gicie; ponowne
uruchomienie 2026-11-15 dało identyczne pliki). `render_ab0232.py` renderuje obie wersje przez offline'owe lustro miksu gry
(te same detektory zdarzeń w A i B — asercja) do `artifacts/audio-0232/` (FLAC 48 kHz mono 16 bit, ext + kabina, spektrogramy
z zaznaczonymi zdarzeniami, `metrics.json`, `README.md` ze znacznikami czasu). Sceny: ruszanie 40 t pod górę 3 %, biegi pustym
zestawem, zjazd z hamulcem silnikowym i retarderem, postój z pneumatyką.

## Dowody (pomiar)
- Banki (LUFS, ext, A → B): `off` 600 obr/min −39,9 → −37,8 (spalanie na jałowym), `on` 1300 −21,1 → −21,1, `on` 2100 −15,0 → −15,0;
  hamulec silnikowy 1000 obr/min −23,5 → −27,1, 2000 obr/min −18,4 → −19,1 (krzywa momentu hamującego). Pełna tabela w README A/B.
- Sceny: różnica LUFS A/B ≤ 0,4 LU; współczynnik kliknięcia (maks. skok próbki / 99,99 percentyl) 1,2–1,8 w obu wersjach.
- pytest `tools/audio/tests`: 103 testy zielone (deterministyczność, `main` niezmieniony, brak clippingu, poziom rośnie z obciążeniem
  i obrotami, nachylenie harmonicznych zależy od obciążenia tylko w 0232, poziom hamulca wg krzywej fizyki, ciągłość szwów pętli,
  okresowość gwizdu, czasy wypływu wg objętości i kryzy, telemetria fizyczna, detektory zdarzeń).

## Konsekwencje
- `render_all.py` bez argumentów daje bank 0232 → `pwsh scripts/build-lab.ps1` importuje go do gry (te same nazwy plików,
  manifest ma pole `synthesis_model`). Powrót: `uv run python render_all.py --model main`.
- Rejestr licencji: `docs/LICENSES.md` `audio-procedural-0232` (własna synteza, bez nagrań, bez marek, bez usług generatywnych).
- Otwarte: ocena właściciela (telefon + słuchawki), czy jałowy w B nie klekocze za mocno i czy hamulec silnikowy przy niskich
  obrotach nie jest za cichy; pomiar na telefonie po imporcie (lider).
