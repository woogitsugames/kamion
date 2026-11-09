# AUDIO_DESIGN — dźwięk silnika i pojazdu

Status: **fundament silnika gotowy (synteza + runtime skeleton)**; jakość subiektywna: **AWAITING OWNER LISTENING TEST** (telefon: głośnik + słuchawki).
Właściciel toru: agent `audio`. Wymagania nadrzędne: `docs/08_AUDIO.md`, decyzje D8/D9 (`docs/11`).

Wszystkie wartości liczbowe modelu (rezonanse, amplitudy, czasy) to `WORKING_VALUE` — decyzje projektowe dla fikcyjnego silnika, **nie** pomiary żadnego istniejącego silnika.

---

## 1. Cel i legalność
- Fikcyjny nowoczesny silnik EU: rzędowa szóstka (R6), 4-suw, ~13 l, diesel, turbo, hamulec silnikowy (compression release / klapa wydechu).
- **100% własna synteza** (Python numpy/scipy, kod w `tools/audio/`). Zero nagrań producentów, zero sampli z gier/filmów/YouTube, zero plików z bibliotek — więc w rejestrze licencji jest tylko nasz generator (`docs/LICENSES.md` → sekcja Audio).
- Wynik jest deterministyczny (stałe ziarna RNG): `uv run python render_all.py` zawsze daje te same pliki.

## 2. Podejście: wybór architektury

| Opcja | Plusy | Minusy | Decyzja |
|---|---|---|---|
| **A. Pętle prerenderowane z syntezy fizycznej + crossfade rpm × obciążenie w runtime** (granular/loop-crossfade) | Tani CPU (natywny mikser Unity, resampling w C++), przewidywalny, łatwy profil mobile; cała „ciężka” DSP (rezonanse, szum modulowany, 8 modów bloku) offline bez limitu kosztu | Pamięć na banki, ograniczona liczba punktów siatki (pitch ±8%), nieregularność powtarza się co ~4 s | **Wybrane na v1** |
| B. Synteza addytywna / impulsowa w czasie rzeczywistym (`OnAudioFilterRead`, firing-order) | Nieskończona zmienność, idealne śledzenie rpm, zero pamięci | Koszt DSP na wątku audio na Helio G99 (A55/A76), ryzyko podtrzymań przy GC/IL2CPP, filtry rezonansowe + 6 cylindrów × zdarzenia = drogo; strojenie trudniejsze | Odłożone; możliwy hybryd (np. warstwa „nieregularności biegu jałowego”) po pomiarze na telefonie |
| C. FMOD | Gotowy granular/crossfade, edytor | Licencja indie do weryfikacji, kolejna zależność, i tak potrzebujemy własnych assetów | Nie teraz; A nie zamyka drogi do FMOD (te same pętle) |

Opcja A to standard w symulatorach; jakość zależy od jakości pętli i prawa crossfade’u — oba elementy są tu zweryfikowane liczbowo (§7). **Propozycja ADR 0006** (do zapisania przez lidera, `docs/adr/` nie jest w mojej własności): „Audio silnika = prerenderowana siatka pętli + Unity Audio, bez FMOD w v1”.

## 3. Model silnika (generator `tools/audio/engine_synth.py`)

### 3.1 Kinematyka
- Kolejność zapłonu **1-5-3-6-2-4**, zapłon co **120° OWK** → 3 zapłony na obrót.
- **f_zapłonu = rpm / 20 Hz**; cykl 720° = 2 obroty → **f_cyklu = rpm / 120 Hz** (rzędy „połówkowe”).

| rpm | f_cyklu [Hz] | f_zapłonu [Hz] | 2× | 3× |
|---|---|---|---|---|
| 600 (jałowy) | 5.0 | 30.0 | 60 | 90 |
| 1100 | 9.17 | 55.0 | 110 | 165 |
| 1300 (przelot) | 10.83 | 65.0 | 130 | 195 |
| 1800 | 15.0 | 90.0 | 180 | 270 |
| 2100 (max) | 17.5 | 105.0 | 210 | 315 |

### 3.2 Źródła (każde budowane jako sygnał okresowy w długości pętli)
1. **Impulsy wydechowe (blow-down)** przy otwarciu zaworu wydechowego (~130° po GMP): szybkie narastanie (7° OWK, min. 0,45 ms) + zanik skalowany kątem (40° OWK) + ostry „crack” 0,25 ms. Amplituda ∝ przepływ(obciążenie, rpm). → **Układ wydechowy**: rezonanse rury 104/212/330 Hz, korpus tłumika 58 Hz, dołek TL 520 Hz, dolnoprzepustowy tłumik ~1,1 kHz.
2. **Turbulencja spalin**: szum pasmowy modulowany obwiednią impulsów (oddech „chuff”), nie stały syk.
3. **Spalanie → blok silnika**: ostre narastanie ciśnienia („klekot” diesla, silniejszy na jałowym i przy małym obciążeniu) pobudza 8 modów strukturalnych bloku (190 Hz … 4,6 kHz, Q 4–14).
4. **Moment gazowy → „dron” strukturalny** (niskie częstotliwości przez poduszki silnika) — główny składnik w kabinie.
5. **Mechanika**: wycie kół zębatych rozrządu (rząd 38 i 76 wału), tykanie zaworów (4 zdarzenia/cylinder/cykl), kliknięcia wtryskiwaczy common-rail (tylko gdy jest wtrysk).
6. **Dolot**: szum dolotu skalowany rpm² i doładowaniem, modulowany suwami ssania.
7. **Hamulec silnikowy**: dekompresja tuż przed GMP — bardzo ostry impuls (0,12 ms) o dużej energii + chropowata turbulencja (env²) + lekkie nasycenie tanh → „szczekanie” / chrapliwy ryk. Warstwa zawiera tylko składniki hamulca; w runtime gra NA warstwie „off” (silnik bez wtrysku).

### 3.3 „Osobowość” silnika (spójna w całym zestawie)
Stałe ziarno `ENGINE_SEED`: odchyłki amplitudy cylindrów (σ 8%), wyprzedzenia (σ 1,2°), szerokości impulsu (σ 8%), opóźnienia przednich/tylnych 3 cylindrów (kolektor twin-scroll), klekotu (σ 18%). Te same we wszystkich pętlach → crossfade nie zmienia „charakteru” silnika. Do tego losowość zdarzenie-po-zdarzeniu (amplituda 3–9%, faza 0,25–0,75°, szerokość 6%) i periodyczne „pływanie” obrotów (governor hunting, do 5,5° na jałowym).

### 3.4 Bezszwowe pętle (dowód konstrukcyjny)
- Długość pętli = **całkowita liczba cykli 720°** (≈4 s): `n_cycles = round(4·rpm/120)`, `n_samples = round(n_cycles·120/rpm·48000)`; dokładne rpm pętli zapisane w manifeście (błąd < 0,002%).
- Wszystkie pobudzenia są okresowe (zdarzenia zawijane modulo długość, szum generowany na długości pętli, LFO o całkowitej liczbie okresów).
- Każdy filtr przyczynowy liczony jako odpowiedź ustalona na sygnał powtarzany (`dsp.periodic_sosfilt`: 3× kafel, bierzemy ostatni okres) → szew jest matematycznie ciągły.
- Próbka 0 każdej pętli = **60° przed GMP zapłonu cylindra 1** (cicha część cyklu; ta sama faza we wszystkich klipach → runtime może je wyrównać fazowo).

### 3.5 Perspektywy
- `ext` — na zewnątrz, kilka metrów od ciągnika: wydech + blok (klekot) + mechanika + dolot.
- `cab` — wnętrze: wydech przez przegrody (LP 330/650 Hz), dudnienie kabiny 40 Hz (+4 dB), mod panelu 128 Hz, dron strukturalny, klekot przez ścianę grodziową (LP 650 Hz, półka −14 dB > 1,5 kHz), ślad chropowatości wydechu (pasmo 450–2400 Hz).
- Prerender zamiast filtrów w runtime: zero kosztu DSP na telefonie, a filtr „kabinowy” może być dowolnie złożony.

## 4. Warstwy — stan

| Warstwa | Plik(i) | Sterowanie w runtime | Stan |
|---|---|---|---|
| Spalanie / wydech / blok (rpm × obciążenie) | `engine_{ext,cab}_{off,mid,on}_{0600..2100}.wav` — 16 rpm × 3 obciążenia (0 / 0,4 / 1,0) × 2 perspektywy = 96 | rpm, load | **wygenerowane + runtime** |
| Hamulec silnikowy | `ebrake_{ext,cab}_{0900..2100}.wav` — 13 × 2 | rpm, engineBrake | **wygenerowane + runtime** |
| Gwizd turbo | `turbo_whistle_loop.wav` (3,2 kHz przy pitch 1) | turboBoost → pitch 0,6–1,45, głośność ∝ boost^1,5 × (0,35+0,65·throttle) | **wygenerowane + runtime** |
| Zdmuchnięcie przy odpuszczeniu gazu (wastegate/recyrkulacja) | `turbo_liftoff.wav` | detektor: spadek gazu > 0,5 przy boost > 0,35 | **wygenerowane + runtime** |
| Zwolnienie hamulca roboczego | `air_brake_release.wav` | zdarzenie z modelu hamulców | wygenerowane (wywołanie: TODO model pneumatyki) |
| Hamulec postojowy (zał.) | `parking_brake_set.wav` | zdarzenie | wygenerowane |
| Przedmuch osuszacza | `air_dryer_purge.wav` | ciśnienie zbiornika osiąga próg regulatora | wygenerowane |
| Zmiana biegu (cylinder AMT „pft”) | `gearshift_air.wav` | zdarzenie skrzyni | wygenerowane |
| Wycie skrzyni / retardera | `gear_whine_loop.wav` (1 kHz przy pitch 1) | prędkość wału wyjściowego / moment retardera | wygenerowana baza; retarder: osobna warstwa + szum oleju — TODO |
| Opony × nawierzchnia | `road_roll_loop.wav` | prędkość (pitch 0,75–1,35, głośność ∝ v^1,6) | wygenerowane (sucho/asfalt); mokro, kostka, szuter — TODO |
| Wiatr | `wind_loop.wav` | prędkość (∝ v^2,2) | wygenerowane |
| Kompresor powietrza | — | obroty, stan regulatora | TODO (pulsujący tłokowy, ~rpm·przełożenie) |
| Rozruch / wyłączenie | — | stan silnika | TODO (one-shoty; `EngineAudio` już płynnie wycisza pętle między 380 a 80 rpm) |

## 5. Runtime (`game/Assets/_Project/Audio/`)
- `IEngineAudioState` — interfejs: `Rpm, Load, Throttle, EngineBrake, TurboBoost`. Alternatywnie push: `EngineAudio.SetInput(in EngineAudioInput)`.
- `EngineSoundBank` (ScriptableObject) — siatka klipów + `clipRpmExact` + `clipCycles` z `manifest.json`.
- `EngineLayerGrid` — pula AudioSource’ów (6 na siatkę silnika, 3 na hamulec). Co klatkę: 4 komórki sąsiadujące (rpm × obciążenie), **prawo crossfade hybrydowe** `g = c·lin + (1−c)·equal-power`, `c = 0,9`; `pitch = rpm / rpm_pętli`; narastanie/zanik głosu 30 ms; nowy głos startuje **wyrównany fazowo do wału** względem najgłośniejszego (+ losowa całkowita liczba cykli) → sąsiednie pętle sumują się koherentnie, bez filtrowania grzebieniowego. Kradzież najcichszego głosu przy wyczerpaniu puli.
- `EngineAudio` (MonoBehaviour) — wygładzanie (τ: rpm 35 ms, load 50 ms, hamulec 80 ms, boost 50 ms), blend kabina/zewnątrz (equal-power, `InteriorBlend` z systemu kamer), turbo, lift-off, wyciszanie przy gaśnięciu.
- `EngineAudioDebugState` — suwaki w inspektorze + auto-sweep rpm do odsłuchu bez fizyki.
- **Zero GC na klatkę**: stałe tablice, brak LINQ/closure/string w `Update`/`Tick`. Alokacje tylko w `Awake` (tworzenie AudioSource’ów).
- Kompilacja sprawdzona Roslynem Unity (`Editor/Data/DotNetSdkRoslyn/csc.dll`, referencje `UnityEngine.CoreModule/AudioModule` 6000.3.28f1, netstandard 2.1) — 0 błędów; ostrzeżenia tylko CS0649 dla `[SerializeField]` (normalne poza Unity). **Nie testowane w edytorze ani na telefonie.**
- `tools/audio/runtime_sim.py` to wierne lustro algorytmu (te same stałe, ten sam LCG) — na nim renderowane jest demo i testy crossfade. Zmiana w jednym = zmiana w drugim.

### Integracja w grze (Etap 2, ADR 0009) — zrobione
- `Editor/Audio/VehicleAudioImporter.cs` (menu Kamion/Audio/Import vehicle audio, batch `Game.Editor.Audio.VehicleAudioImporter.ImportBatch`, `scripts/build-lab.ps1`): czyta `manifest.json`, kopiuje WAV do `Assets/_Project/Audio/Generated/Clips` (gitignored), import ADPCM (pętle: Compressed In Memory; one-shoty: Decompress On Load), tworzy 4 `EngineSoundBank` + `VehicleAudioLibrary` w `Resources/VehicleAudio`. Build importuje sam, `build-android.ps1` generuje WAV, gdy ich brak (`render_all.py --no-previews`, podglądy OGG w repo nietknięte).
- `Gameplay/TruckAudioController.cs`: `IEngineAudioState` z modelu (rpm, `Engine.LastLoad`, zapotrzebowanie gazu, `EngineBrakeState`, `Boost`); blend kabina/zewnątrz z trybu kamery (0,15 s); one-shoty ze zdarzeń modelu: zwolnienie hamulca po przytrzymaniu, hamulec postojowy zał./zwol., przedmuch osuszacza przy odcięciu regulatora, start zmiany biegu AMT; pętle opon i wiatru od prędkości.
- Sprawdzone: w scenie DrivingLab na biegu jałowym grają 2 głosy silnika (test PlayMode); APK: „Sounds” 13,1 MB. **Nie odsłuchane** (agent nie słyszy; telefon zablokowany).

### Import do Unity (historia — wykonane w Etapie 2)
1. `cd tools/audio && uv run python render_all.py` → `art-source/audio/generated/` (≈47 MB WAV, gitignored).
2. Skopiować WAV do `game/Assets/_Project/Audio/Clips/` (lub dodać Editor-importer czytający `manifest.json` i tworzący 4 `EngineSoundBank`).
3. Ustawienia importu klipów silnika: **Load Type = Compressed In Memory, Compression = ADPCM**, Preload, sample rate 48 kHz (opcja: override 44,1 kHz dla Low).
4. Banki `cab` / `ebrake_cab`: `spatialBlend = 0`; `ext`: `1`.

## 6. Budżet mobilny (Helio G99 / Samsung A16, 3,57 GiB RAM — `docs/DEVICE_MATRIX.md`)

| Zasób | Budżet | Stan / uzasadnienie |
|---|---|---|
| Głosy silnika (ustalony stan) | 4 silnik + 2 hamulec + 1 turbo | demo: maks. **6** jednocześnie aktywnych głosów silnik+hamulec (wliczając wygaszane) |
| Głosy silnika (przejście kamery kabina↔zewn.) | ≤ 12 przez ~0,1 s | obie siatki aktywne tylko w trakcie blendu |
| Pojazd łącznie (silnik, pneumatyka, opony, wiatr, kierunkowskaz) | ≤ 14 real voices | |
| Cała gra | Real Voices 32, Virtual 64 (Project Settings → Audio, decyzja lidera) | |
| CPU audio | cel < 3% jednego rdzenia A76 dla warstwy pojazdu | `UNVERIFIED` — zmierzyć Profilerem (Audio → DSP CPU) na A16. ADPCM dekoduje się tanio; resampling pitch jest natywny |
| RAM banków silnika | ADPCM: ext ≈ 5,3 MB + cab ≈ 5,3 MB + hamulec 2 × 1,4 MB ≈ **13 MB** | 9,21 M próbek/perspektywę silnika + 2,50 M hamulca (manifest). Plan B dla Low: Vorbis CompressedInMemory (~5× mniej RAM, więcej CPU) albo siatka co 200 rpm (−50%) |
| Latencja | DSP buffer „Best Latency” niewymagany; „Good” wystarcza | silnik nie jest dźwiękiem UI |

## 7. Weryfikacja obiektywna („odsłuch przez analizę”)
Agent nie słyszy — jakość techniczną sprawdzają skrypty; **ocena brzmienia należy do właściciela**.

Komendy: `uv run python analyze.py` (kod wyjścia 1 przy błędzie), `uv run python render_demo.py`. Wyniki: `docs/reports/audio/analysis.json`, `demo_analysis.json`.

| Test | Kryterium | Wynik (122 pętle) |
|---|---|---|
| Brak przesterowania | peak < −0,5 dBFS | maks. **−3,0 dBFS** (wspólne wzmocnienie dla całego banku, zachowane relacje głośności) |
| Szew pętli (skok) | `|x[0]−x[−1]|` < 99,9 percentyl `|Δx|` wewnątrz | maks. stosunek **0,71** |
| Szew pętli (2. różnica) | jw. dla `Δ²x` | maks. **0,10** |
| Wysokość dźwięku | odstęp (NWD) 3 najsilniejszych prążków rzędów = rpm/20 | błąd **0,000%** we wszystkich 122 |
| Struktura rzędów | najsilniejszy prążek 15–300 Hz leży na rzędzie silnika; rzędy zapłonu ≥ 6 dB nad połówkowymi; połówkowe obecne (< 40 dB) | rzędy zapłonu nad połówkowymi: **15,9–24,5 dB** (zmienność cylindrów słyszalna, ale nie dominuje) |
| Pliki SFX | pętle: szew jw.; one-shoty: zero na brzegach; peak < −0,5 dBFS | wszystkie OK |
| Crossfade (sweep 600→2100 rpm w lustrze runtime) | odchyłka poziomu od interpolacji poziomów pętli | maks. **0,42 / 0,42 / 0,75 dB** (on / mid / off); przy prawie 50/50 było 1,9 dB „falowania” → strojenie `c = 0,9` |
| Kliknięcia w crossfadzie | maks. `|Δx|` sweepu / maks. `|Δx|` w źródłach | **0,83–0,90** (< 1 → brak skoków większych niż w samych pętlach) |
| Śledzenie f_zapłonu w demo | szczyt widma przy rpm/20 z telemetrii | mediana błędu **0,36%**, p90 **1,4%** (rozdzielczość 5,9 Hz + interpolacja paraboliczna) |
| Głośność demo | −16 LUFS (BS.1770, cel mobile z `docs/08`) | kabina **−16,0 LUFS** (peak −1,3 dBFS); zewn. **−17,5 LUFS** (ograniczone peakiem −1 dBFS) |

Obejrzane wykresy (PNG, ≤ 300 KB każdy) i co na nich widać:
- `engine_loop_spectra.png` — prążki dokładnie na czerwonych liniach harmonicznych zapłonu (30 / 65 / 105 Hz i wielokrotności); między nimi słabsze rzędy połówkowe; kabina wyraźnie stłumiona powyżej ~400 Hz.
- `engine_waveforms.png` — 12 impulsów na 2 cykle, równe odstępy 120°, różna wysokość impulsów cylindrów; na jałowym widoczne szpilki klekotu przy GMP; hamulec silnikowy: ostre piłokształtne „szczeknięcia”.
- `sfx_spectrograms.png` — gwizd turbo 3,2 kHz (+2. i 3. harmoniczna), syk hamulców opadający w jasności, opadający świst lift-off.
- `drive_demo_spectrogram.png`, `drive_demo_exterior_spectrogram.png` — harmoniczne podążają za krzywymi rpm/20 (cyjan) przez wszystkie fazy: jałowy, ruszanie, 3 zmiany biegów, przelot 1300, redukcja i hamulec silnikowy; gwizd turbo rośnie z doładowaniem i opada przy zmianach. Pionowe prążkowanie na jałowym na wykresie 0–10 kHz to mora renderowania (zdarzenia 30 Hz) — obwiednia HF pętli jałowej jest płaska (p99 tylko 2–4 dB nad medianą).
- `crossfade_sweep.png` — poziom w sweepie leży na punktach poziomów pętli, bez „garbów” między punktami siatki.

## 8. Plan miksu
- **Grupy miksera** (AudioMixer — zasób lidera): `Master → Vehicle {Engine, Turbo, Pneumatics, Drivetrain, Tyres, Wind} · World · UI · Radio`.
- **Kabina vs zewnątrz**: osobne banki (prerender), blend equal-power sterowany kamerą; snapshoty `Cab` / `Exterior` dla reszty grup (zewnętrzne źródła świata w kabinie: LP ~1,5 kHz −10 dB; deszcz o dach: tylko w kabinie).
- **Przestrzeń**: zewnętrzny silnik 3D z komory silnika (log rolloff 4–250 m, doppler 0 — rpm steruje pitch); później osobne źródło wydechu za kabiną (wymaga rozdzielenia banków ext na „engine” i „exhaust” — możliwe w generatorze, ×2 RAM).
- **Dwa profile wyjścia** (`docs/08` §2):
  - *Głośnik telefonu*: HPF ~150 Hz (głośnik i tak nie odtworzy 30–105 Hz), +3–4 dB w 200–800 Hz (harmoniczne 2–8 rzędu zapłonu niosą „ciężar” na małym głośniku), łagodna kompresja wielopasmowa, limiter −1 dBTP.
  - *Słuchawki*: pełne pasmo (fundamentalna 30–105 Hz i dudnienie kabiny 40 Hz zostają), mniejsza kompresja.
- **Głośność**: −16 LUFS integrated dla typowej jazdy (demo zmierzone), peak ≤ −1 dBFS.
- **Priorytety**: silnik priorytet 16, turbo 32, reszta pojazdu 64, świat ≥ 128.

## 9. Pliki w repo
- Generator: `tools/audio/` (`pyproject.toml`, `uv.lock`, Python 3.12) — `dsp.py`, `engine_synth.py`, `sfx_synth.py`, `render_all.py`, `analyze.py`, `runtime_sim.py`, `render_demo.py`.
- Odsłuch dla właściciela: `art-source/audio/demo/drive_demo.ogg` (kabina, 30 s), `drive_demo_exterior.ogg`, telemetria `drive_demo_telemetry.csv`.
- Podglądy (każda pętla ×2 pod rząd — szew powinien być niesłyszalny): `art-source/audio/previews/*.ogg`.
- Pełny bank WAV: `art-source/audio/generated/` (gitignored, odtwarzalny).
- Raporty: `docs/reports/audio/`.

## 10. Znane ograniczenia / ryzyka
- **Brzmienie nieocenione uchem** — liczby potwierdzają strukturę (rzędy, szwy, crossfade), nie „realizm”. Ryzyka do sprawdzenia w odsłuchu: zbyt „czysty”/syntetyczny ton przy stałych obrotach (powtarzalność co ~4 s), za mało klekotu albo za dużo, gwizd turbo zbyt tonalny.
- Brak referencji porównawczej z prawdziwej ciężarówki (docs/08 §3.1 przewiduje nagrania właściciela — gdyby powstały, porównam widma rzędów i balans pasm).
- Na głośniku telefonu fundamentalna jest niesłyszalna — konieczny profil miksu z §8 (nieprzetestowany).
- Runtime nie był uruchomiony w Unity; ustawienie `timeSamples` po `Play()` wymaga potwierdzenia w edytorze/na urządzeniu.
- Rozruch/wyłączenie, kompresor, retarder, warianty nawierzchni — TODO (§4).
