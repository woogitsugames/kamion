# ADR 0145 — Opony w ciasnym skręcie: szuranie (scrub) zamiast pisku, pisk dopiero przy poślizgu
Status: Proposed (agent audio, s14), 2026-11-12. Ocena brzmienia: właściciel (telefon, głośnik i słuchawki).
Kontynuacja ADR 0142 (efekty ElevenLabs). Nagrania: `docs/owner/ELEVENLABS-REGEN-03.md`.

## Kontekst
Właściciel (s14): „pisk opon przy mocnym skręcie jest zły”. Pisk nigdy nie był nagraniem. To synteza
`sfx_layers.tyre_squeal_loop` v1: ton 930 Hz z harmonicznymi (w 99 % ramek wąska linia > 18 dB nad lokalnym tłem).
Sterowanie (ADR 0007): `LayerMath.SquealGain` od 0,8 do 1,4 znormalizowanego poślizgu kombinowanego, liczonego jako
**maksimum ze wszystkich kół ciągnika i naczepy**, przy każdej prędkości powyżej 1,5 m/s.

## 1. Pomiar: kiedy pisk się włączał
Runner fizyki (`tools/physics-runner`, krok 0,01 s, 4 podkroki), zestaw z naczepą tridem, sucha nawierzchnia, kierowca
`circle` (pure pursuit + PI). Scenariusze: `artifacts/tyre-scrub/scenarios/`. Analiza: `tools/audio/tyre_slip_scan.py`
(te same pola `WheelState.SlipRatio` / `SlipAngle`, które czyta `TruckAudioController`). Ustalony stan = ostatnie 40 %.
Pełna tabela: `artifacts/tyre-scrub/slip_scan_before.md`.

| przejazd (40 t) | maks. kąt znoszenia ciągnik / naczepa | poślizg kombinowany (norm.) ciągnik / naczepa | pisk przed | szuranie po | pisk po |
|---|---|---|---|---|---|
| R 9 m, 5 km/h | 0,8° / 21,7° | 0,18 / 3,78 | 0,00 (bramka 1,5 m/s) | 1,00 | 0 |
| R 9 m, 10 km/h | 1,4° / 19,9° | 0,26 / 3,47 | **0,51** | 1,00 | 0 |
| R 12 m, 10 km/h | 1,3° / 9,4° | 0,24 / 1,64 | **0,51** | 1,00 | 0 |
| R 12 m, 15 km/h | 2,0° / 9,5° | 0,36 / 1,65 | **1,00** | 1,00 | 0 |
| R 20 m, 15 km/h | 1,3° / 4,6° | 0,23 / 0,81 | 0,00 | 0,97 | 0 |
| R 30 m, 35 km/h | 3,6° / 5,9° | 0,62 / 1,03 | **0,25** | 0,15 | 0 |
| R 50 m, 50 km/h (3,9 m/s²) | 4,5° / 5,7° | 0,78 / 1,00 | 0,19 | 0,00 | 0 |
| zmiana pasa 80 km/h | 0,1° / 0,0° | 0,03 / 0,01 | 0 | 0 | 0 |
| mokry łuk, hamowanie 0,5 bez ABS (blokada) | — | 8,3 (kappa = 1) | 0,8 → 1 | ~0 | 0,8 → 1 (do 18 km/h) |

Wniosek: w ciasnym skręcie piszczało **naczepa**. Skrajne osie tridemu (1 i 3) są ciągnięte bokiem pod kątem 8–10° (R 12 m)
do 18–22° (R 9 m). Środkowa oś ma kąt bliski zeru, a ciągnik nie przekracza 2°. To geometria wieloosiowego zespołu bez
osi skrętnej. Prawdziwy ciągnik z naczepą słychać wtedy jako niskie szuranie i skrzypienie gumy, nie jako gwizd. Pisk
pojawia się dopiero przy prawdziwym poślizgu przy większej prędkości. Stary próg (4,6° na dowolnym kole, od 5,4 km/h)
dawał pełny gwizd w każdym ciasnym skręcie powyżej ~15 km/h i połowę już przy 10 km/h.

## 2. Decyzja: dwie warstwy
`LayerMath` (stałe `WORKING_VALUE`, lustro w Pythonie: `tyre_slip_scan.py`):
- **Szuranie** `ScrubGain(α, v)`: α = największy |kąt znoszenia| osi **naczepy** (gdy sprzęgnięta), w przeciwnym razie osi
  ciągnika. Włącza się od 1°, pełne od 5° (smoothstep). Bramka prędkości: narasta 0,3 → 1,2 m/s (na postoju cisza),
  wygasa 6 → 11 m/s (22–40 km/h). Wysokość `ScrubPitch` = 0,85–1,15 wg prędkości ślizgu bieżnika v·sin α (pełna przy 1 m/s).
  Udział nawierzchni `SurfaceScrubbable` = sucha 1,0, mokra 0,7, beton 1,0, kostka 0,8, żwir 0,5, trawa 0,3.
  Wygładzanie 0,12 s w górę i 0,25 s w dół. Po ciszy pętla startuje z losowego miejsca (`PerspectiveLoop.Rephase`),
  więc 6-sekundowe nagranie nie zaczyna się za każdym razem tak samo.
- **Pisk** `SquealGain(s, v)`: s = największy poślizg kombinowany (wszystkie koła, jak dotąd). Włącza się od 1,3, pełny
  od 2,0. Bramka prędkości 5 → 9 m/s (18–32 km/h). Poniżej tej prędkości poślizg jest słyszany jako szuranie.
  Wysokość 0,9–1,15.
- Źródło szurania na zewnątrz stoi przy osiach naczepy (z = −6 m od tylnej osi ciągnika).
- Poziomy: klipy znormalizowane (BS.1770) do stałych LUFS, takich samych dla nagrań i syntezy. Pisk: zewnątrz −16, kabina
  −20. Szuranie: zewnątrz −18, kabina −22. Głośność runtime: `squealVolume` 0,55 → **0,60** na klipie −16 LUFS zamiast
  −10,5 (pełny pisk ~−20 LUFS, czyli −4,7 dB względem starego gwizdu (−15,7 LUFS)). `scrubVolume` **0,25** (pełne szuranie ~−30 LUFS,
  mniej więcej poziom silnika pod obciążeniem przy 600 obr./min). Współczynniki kabiny 1,0.

## 3. Nagrania REGEN-03 (532 kredyty, zmierzone przez właściciela z salda)
`tools/audio/el_regen03.py` mierzy każdy wariant po obróbce pętli (mono, górnoprzepustowy 25 Hz, najstabilniejsze okno
6 s, szew 40 ms). Mierzy też linię tonu (`tone_db`: najwyższa linia widma nad lokalną medianą ±25 Hz w 400–6000 Hz,
PASS < 12 dB) i jej trwałość (`tone_frac`: udział ramek z wąską linią > 18 dB, PASS < 0,5; stary pisk v1 = **0,99**).
Kryteria PASS dalej: rytm (ACF obwiedni 1–6 kHz przy 0,2–2 s < 0,45, jak w `siren_scan.py`), szew (skok < 1, iglica HF
< 6 dB), brak przesterowania. Koszt = dryf poziomu + 4·udział < 150 Hz + kara za ton + kara za rytm. Raport:
`artifacts/tyre-scrub/regen03/regen03.txt`, arkusz `regen03_sheet.png` (obejrzany).

| ID | wybór | dlaczego (liczby z `regen03.txt`) |
|---|---|---|
| `TYRE_SCRUB_TIGHT_TURN` | **(2)**, okno 0,75 s | dryf 3,3 dB, ton 3,5 dB, ACF 0,17, szew 0,00. (3) to regularne skrzypnięcia co 0,55 s (ACF 0,49), brzmi jak maszyna. (4) FAIL na szwie HF |
| `TYRE_SCRUB_TIGHT_TURN_CAB` | **(3)**, okno 0 s | dryf 2,7 dB, ton 3,8 dB, ACF 0,14. (1) ACF 0,68 |
| `TYRE_SQUEAL_HARD` | **(2)**, okno 3,5 s | szorstki, niski pisk z wahaniem: linia 741 Hz tylko 7,4 dB, `tone_frac` 0,48. (1) iglica szwu 9,2 dB, (4) ton 10,1 dB i `tone_frac` 0,51 |
| `TYRE_SQUEAL_HARD_CAB` | **(3)**, okno 2,0 s | dryf 0,7 dB, ACF 0,42. Słaba linia 935 Hz (7,4 dB). (1) i (4) FAIL na szwie |

Wersje kabinowe: górnoprzepustowy 100 Hz, bo w promptach kabinowych jest diesel na biegu jałowym, a silnik gra osobno.
`el_fx.py` (grupa fx, `REGEN03_SLOTS`) wybiera warianty sam przy każdym uruchomieniu. ID bez wariantu PASS (albo bez plików)
jest pomijane i gra synteza. Wynik: 47 klipów, 0 FAIL. Kontrola szwu 3× pętla: `regen03/loops_3x.png` (szwów nie widać).
W pętli szurania (2) zostają dwa krótkie przyciszenia (0,7 i 1,4 s okna). `Rephase` przy każdym nowym skręcie zmniejsza
szansę, że będą słyszalne jako powtórka.

**Oba zestawy:** nagrania REGEN-03 zastępują syntezę w zestawie *synteza* i w zestawie *ElevenLabs* (jak klakson i drzwi
w 0142). Powód: skarga dotyczyła syntetycznego pisku, a synteza szurania jest tylko zastępstwem.

## 4. Synteza (zapas bez REGEN-03)
- `tyre_squeal_loop` v2 (4 s): trzy pasma szumu (~480/600 przenikane, 1150, 2100 Hz), rwane nieregularnie (AM 15–40 Hz,
  „stick-slip”), ziarno HF, szum toczenia. `tone_db` 3,1 dB, `tone_frac` 0,02 (v1: 0,99).
- `tyre_scrub_loop` (6 s): niski jęk gumy (formanty 180 / 420 Hz, powolne nieregularne narastanie), skrzypnięcia w
  odstępach z rozkładu wykładniczego (średnio 2,9/s, paczki 15–60 ms w paśmie 500–1800 Hz), drobny żwir. ACF 0,14.
  Obie pętle są okresowe z konstrukcji, kabina przez `cab_filter road`.

## 5. Odsłuch A/B
`tools/audio/tyre_scrub_ab.py` steruje warstwami telemetrią runnera (40 t), oś czasu 28 s: ciasny skręt R 12 m przy
10 km/h → prosta 80 km/h → łuk R 30 m przy 35 km/h → mokry łuk z blokadą kół. Kontekst w obu wersjach: toczenie po suchym
(synteza) i przybliżone tło silnika (najbliższa komórka siatki ElevenLabs, nie pełny miks `EngineAudio`).
Pliki (`artifacts/tyre-scrub/ab/`): `tyre_ab_ext.ogg`, `tyre_ab_cab.ogg` (najpierw A „przed”, 1 s ciszy, potem B „po”),
osobno `tyre_{before,after}_{ext,cab}.ogg`, `ab_layers_solo.ogg` (po 4 s: nagranie szurania zewn./kab., pisku zewn./kab.,
synteza szurania, pisk v2, pisk v1), `ab_spectrogram.png` (obejrzany: przed = harmoniczne 0,93/1,86/2,8 kHz w ciasnym
skręcie i na łuku R 30, po = szum szurania w skręcie i pisk tylko przy blokadzie), `ab_levels.txt`.
Poziom RMS na zewnątrz przed / po: ciasny skręt −14,7 / −18,0 dBFS, łuk R 30 −13,0 / −15,3, blokada −10,8 / −17,6
(wspólne wzmocnienie dla A i B).

## Kod
`LayerMath` (`ScrubGain`, `ScrubPitch`, `SquealGain` v2, `SurfaceScrubbable`), `TruckAudioController` (warstwa `m_Scrub`,
`ScrubLevel`, `ScrubSlipAngle`, `WorstCombinedSlip`, publiczne `AudioStep(dt)`, które woła `Update`),
`PerspectiveLoop.Rephase`, `VehicleAudioLibrary` (`tyreScrub`, `elTyreScrub`, `elTyreSqueal`), `VehicleAudioImporter`.
Python: `tyre_slip_scan.py`, `el_regen03.py`, `el_fx.py` (REGEN03_SLOTS), `sfx_layers.py`, `render_all.py`
(`TYRE_SLIP_LUFS`), `tyre_scrub_ab.py`.

## Wyniki testów
Unity 6000.3.28f1, worktree `tyre-scrub`, po `VehicleAudioImporter.ImportBatch` (AUDIOIMPORT_RESULT: OK):
- **PlayMode 27/27** (filtr `Audio|TyreScrub|DrivingLabScene|ControlSettingsPanel`): nowe `TyreScrubTests` 4/4,
  `AudioLayersTests` (zaktualizowany test pisku i nowy warunek „zaparkowany nie szura”), `ElevenLabsFxAudioTests`
  (w tym 0 B GC w 300 aktualizacjach), `ElevenLabsEngineAudioTests`, `DrivingLabSceneTests`. EditMode `Audio` 1/1.
  Wyniki: `artifacts/tyre-scrub/tests/playmode-20261112-192435.xml`.
- `TyreScrubTests` (40 t, fizyka w trybie Script, krok 0,01 s, `TruckAudioController.AudioStep`):
  postój z kierownicą w ruchu: szuranie 0,0000, pisk 0,0000. Prosta 28,6 km/h: szuranie 0, pisk 0, kąt naczepy 0,00°.
  Ciasny skręt R 12 m, średnio 8,6 km/h, przegub −37,9°: kąt znoszenia naczepy 9,7° (runner 9,4°), poślizg kombinowany
  1,69 (runner 1,64), **szuranie min. 1,000, pisk maks. 0,0000**, grają klipy `el_tyre_scrub_loop` i `el_tyre_squeal_loop`.
  **0 B GC** w 300 krokach audio z warstwą szurania.

## Konsekwencje
- Wszystkie progi i poziomy to `WORKING_VALUE` do oceny właściciela (telefon: głośnik i słuchawki).
- RAM: +4 pętle ElevenLabs po 6 s (ADPCM) i +2 pętle syntezy.
- Na urządzeniu nie mierzone (bez telefonów w tym zadaniu).
- Licencje: `docs/LICENSES.md` → `audio-elevenlabs-sfx-v3-regen03`, `audio-procedural-tyre-slip-v2`.
