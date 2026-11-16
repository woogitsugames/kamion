# 03 — Etapy i bramki jakości

> **D73 / ADR 0260 (15.11.2026): platformą główną jest Windows (PC).** Bramki i budżety pod PC: ADR 0266.
> Telefon (Android, potem iOS) = wersja późniejsza i lżejsza. Wymagania mobilne z poprzedniej wersji tego
> dokumentu **nie są skasowane** — są oznaczone „🔒 zabezpieczenie mobilne (odroczone, D73)” i nadal obowiązują
> jako granica, której nie wolno bez ADR przekroczyć w danych wspólnych (np. < 2 M tris High), ale nie blokują bramek.

Zasady:
- Etapy są sekwencyjne, ale **tor artystyczny ciężarówki (A) biegnie równolegle** z torem jazdy (F) od Etapu 1.
- **Build jest prawdą:** dowodem bramki jest **build Windows Standalone x64 (player, nie edytor)** uruchomiony
  na maszynie pomiarowej oraz liczby z narzędzia `scripts/pc-metrics.ps1` (§ „Pomiar na PC”). Edytor kłamie o wydajności.
- Bramka = raport po polsku dla właściciela (`docs/reports/GATE-N.md`): co zrobione, **liczby z playera Windows**
  (klasa sprzętu, rozdzielczość, tier, p50/p95/p99, pamięć RAM/VRAM, czas ładowania), zrzuty/nagrania **z playera**,
  znane braki, decyzje do podjęcia.
- Nie przeskakujesz bramki, żeby wygenerować więcej treści. Jeśli wynik nie spełnia celu: profiluj, zawęź, popraw.
- Po każdej bramce: tag w git, aktualizacja `docs/STATUS.md` i `docs/ROADMAP.md`.
- Terminy: nie podawaj sztywnych dat. Mierz i raportuj koszt (np. godziny pracy agentów na km drogi) od Etapu 4.
- Bramki już zaliczone na telefonie (Gate 3 — D57, A16 Low) **pozostają zaliczone**; na PC wymagają tylko pomiaru
  kontrolnego (brak regresji), nie powtórnej akceptacji kierunku artystycznego.

---

## Klasy sprzętu PC i budżety — **wszystko `WORKING_VALUE`** (D74, ADR 0266)

Referencyjny PC **nie jest ustalony** (pytanie do właściciela). Maszyna dewelopera (RTX 5070) **nie jest referencją**,
ale wg **D76** mierzy klasy „min” i „zalecany” **emulacją** (metoda zastępcza): 1920×1080 pełny ekran, tier Low / High,
limit 30 / 60 FPS, VSync wyłączony (`tools/pcperf/budgets/pc-machines.json`, ADR 0266 „Uzupełnienie s23 (D76)”). Taki
pomiar **zalicza bramkę z adnotacją „EMULACJA (D76)”**; inna konfiguracja na tej maszynie i klasa „wysoki” = wynik
informacyjny. **Przed publiczną obietnicą wymagań sprzętowych** obowiązuje pomiar na prawdziwym słabszym sprzęcie
(iGPU HD 630 / GTX 660 dla „min”, GTX 1660 dla „zalecany”) — emulacja nie odtwarza przepustowości słabszego GPU/CPU/RAM.

Klasy **min** i **zalecany** = wymagania sprzętowe właściciela z **D74** (wzorowane na kartach Steam ETS2/ATS; Windows 10
64-bit). Modele sprzętu to klasa wymagań, nie wyniki benchmarków. Klasa **wysoki** = propozycja ADR 0266 spoza D74.
Progi FPS, RAM/VRAM procesu i dysk to propozycja lidera (SCS nie publikuje FPS) — do potwierdzenia przy pierwszym pomiarze.

| | **Min** | **Zalecany** | **Wysoki** |
|---|---|---|---|
| GPU (D74 / `WORKING_VALUE`) | NVIDIA GTX 660 / AMD RX 460 / Intel HD 630 (2 GB VRAM) | NVIDIA GTX 1660 / AMD RX 590 (≥ 6 GB VRAM) | dyskretny GPU wyższej klasy bieżącej generacji, ≥ 12 GB VRAM |
| CPU (D74 / `WORKING_VALUE`) | Intel Core i5-6400 / AMD Ryzen 3 1200 | Intel Core i5-9600 / AMD Ryzen 5 3600 | ≥ 8 rdzeni, bieżąca generacja |
| RAM systemu (D74 / `WORKING_VALUE`) | 8 GB | 12 GB | 32 GB |
| Dysk (gra bazowa ≤ 25 GB, D74) | SSD (HDD nie wspierany — do decyzji) | SSD | NVMe SSD |
| Rozdzielczość pomiaru | 1920×1080 | 1920×1080 | 2560×1440 |
| FPS docelowy (limit) | 30 | 60 | 60 (bez limitu jako informacja) |
| Tier URP (`QualityProfile`) | Low | High | Ultra |
| Czas klatki p50 | ≤ 33,3 ms | ≤ 16,7 ms | ≤ 16,7 ms |
| Czas klatki p95 | ≤ 36,0 ms | ≤ 18,5 ms | ≤ 18,5 ms |
| Czas klatki p99 | ≤ 50,0 ms | ≤ 25,0 ms | ≤ 25,0 ms |
| Klatki > 2× budżetu (66,7 / 33,3 / 33,3 ms) | ≤ 0,5 % | ≤ 0,5 % | ≤ 0,5 % |
| Klatki > 100 ms (przycięcia) po rozgrzewce | 0 | 0 | 0 |
| Pamięć procesu (prywatna, szczyt) | ≤ 4 GB | ≤ 7 GB | ≤ 10 GB |
| VRAM dedykowany procesu (szczyt) | ≤ 1,75 GB | ≤ 5 GB | ≤ 10 GB |
| Czas ładowania regionu (LoadScene → pierwsza klatka sceny) | ≤ 30 s | ≤ 20 s | ≤ 15 s |
| Draw calls (licznik „Draw Calls Count”, p95) | ≤ 2 000 | ≤ 4 000 | ≤ 6 000 |
| Trójkąty w klatce (p95) | ≤ 2 M | ≤ 6 M | ≤ 12 M |
| Kolekcje GC w oknie pomiaru (90 s) | ≤ 2 | ≤ 2 | ≤ 2 |

Te same liczby jako dane (jedno źródło prawdy dla parsera): `tools/pcperf/budgets/pc-budgets.json`.
Zmiana budżetu = zmiana tego pliku + wiersza w tabeli + wpis w ADR 0266 (lub nowy ADR), po decyzji właściciela.
**Ryzyko (D74):** Intel HD 630 przy obecnym świecie — pomiar tieru Low na iGPU konieczny, zanim klasa „min” zostanie
obiecana. Liczby z maszyny deweloperskiej (ADR 0261: RTX 5070, High, 1600×900, 360–445 fps głównie na postoju) są
informacyjne i nie zastępują pomiaru klas min/zalecany (ani emulacji D76 w warunkach klasy, ani prawdziwego sprzętu).

**🔒 Zabezpieczenie mobilne (odroczone, D73, zostaje):** budżety z `docs/PERFORMANCE_BUDGETS.md` (A16 Low/Medium 30 FPS,
p95 ≤ 34 ms, p99 ≤ 40 ms, PSS ≤ 1,0–1,2 GB; S24+ High 60 FPS; świat: draw calls 250/350/800/1000, **trójkąty
350 k / 550 k / 1,5 M / 2 M (Low/Medium/High/Ultra)**, tekstury 64–384 MB; ADR 0221: stretch High < 2 M). Dane
wspólne (regiony, ciężarówka) nie mogą ich przekroczyć bez ADR — PC dokłada treść **tierami** (High/Ultra), nie
przez puchnięcie danych bazowych.

## Pomiar na PC (narzędzie, ADR 0266)

- W playerze: `PcFrameMetricsRecorder` (`game/Assets/_Project/Telemetry/`) — włącza się tylko argumentem
  `-metrics <katalog>`; bufor prealokowany, zero GC w pętli, zapis na końcu: `frames.csv` (czas klatki, CPU/GPU
  z `FrameTimingManager`, draw calls/batches/trójkąty), `memory.csv` (pamięć Unity co 0,5 s, licznik GC), `run.json`
  (sprzęt z `SystemInfo`, build, tier, rozdzielczość, czas ładowania regionu, percentyle z gry do kontroli krzyżowej).
- Skrypt: `pwsh scripts/pc-metrics.ps1 -Exe artifacts/win/kamion-<ver>-<sha>[-regions]/Kamion.exe -Scene knyszyn-w -Tier High -Fps 60 -Width 1920 -Height 1080
  -DurationSeconds 90 -Class zalecany` → `artifacts/pc/<maszyna>/<ts>/` (+ `process.csv` z pamięcią procesu i VRAM
  z liczników Windows, `pc-report.json` / `pc-report.md`).
- Parser: `uv run --no-project python tools/pcperf/pc_metrics.py <katalog> --budget tools/pcperf/budgets/pc-budgets.json
  --class zalecany` (exit 0 = w budżecie, 1 = poza budżetem, 2 = pomiar nieważny/brak danych).
- Pomiar jest **nieważny**, gdy: build edytorowy, < 600 klatek po rozgrzewce, okno playera nie miało fokusu
  (`run.json: focusLost > 0`), VSync włączony przy pomiarze „bez limitu”, albo inna gra/renderowanie na tej samej maszynie.
- Raport zawsze podaje: maszynę pomiarową (CPU/GPU/RAM z `run.json`), czy jest referencyjna, klasę budżetu, tier,
  rozdzielczość, limit FPS, VSync, długość okna i rozgrzewkę.
- **Rodzaj pomiaru (D76):** parser porównuje `run.json` (GPU z `SystemInfo`, ekran, tier, limit FPS, VSync) z
  `tools/pcperf/budgets/pc-machines.json` i wpisuje `measurement_kind`: `reference` (prawdziwy sprzęt klasy — lista
  dziś pusta), `emulation` (RTX 5070 w warunkach klasy min/zalecany: 1920×1080 pełny ekran, Low/High, 30/60 FPS, VSync 0)
  albo `informational` (z powodem). Bramkę zalicza `gate_eligible: true` = werdykt PASS i `reference` albo `emulation`;
  raport emulacji ma adnotację „EMULACJA (D76) — nie zastępuje pomiaru na sprzęcie klasy X przed obietnicą wymagań”.
  Komendy: `pwsh scripts/pc-metrics.ps1 -Exe <exe> -Scene knyszyn-w -Tier Low -Fps 30 -VSync 0 -Width 1920 -Height 1080 -Class min`
  oraz to samo z `-Tier High -Fps 60 -Class zalecany`. Przed publiczną obietnicą wymagań — pomiar na prawdziwym sprzęcie
  klasy (wpis `reference` w `pc-machines.json`).

---

## Etap 0 — Fundament
**Zakres:** audyt, manifest i instalacja (`docs/02`), repo + LFS + `.gitignore`, struktura z `docs/10`, projekt Unity 6.3 URP, asmdef-y, **build Windows Standalone x64** (`Game.Editor.Build.BuildCommands.BuildWindowsPlayer`, `scripts/build-windows.ps1` — ADR 0261: batchmode `-executeMethod`, poprawny exit code, log, SHA256 artefaktu), `scripts/doctor.ps1`, scena `Boot` z ekranem diagnostycznym (wersja, API grafiki, GPU, RAM, FPS), **harness visual QA** (render kamer do PNG w edytorze + zrzut z playera), `scripts/pc-metrics.ps1`, konfiguracja MCP i Superpowers, ADR 0001–0005, `CLAUDE.md` uzupełniony o komendy.
🔒 Zabezpieczenie mobilne (odroczone, D73): ustawienia Android (ARM64, IL2CPP, Vulkan, target API zgodny z wymogiem Google Play), `scripts/build-android.ps1` + `-Install` (adb), zrzut z telefonu `adb exec-out screencap` — zrobione i utrzymywane, nie blokują bramki.
**Bramka:** player Windows uruchomiony z czystego klonu jedną komendą, `Player.log` bez wyjątków, pusta scena Boot: zmierzone FPS/czas klatki narzędziem `pc-metrics`; PNG z harnessu obejrzany; `doctor` zielony. Build Android nadal się kompiluje (nie mierzony).

## Etap 1 — Laboratorium jazdy: ciągnik (tor F)
**Zakres:** graybox ciągnika o **prawdziwych wymiarach i masach** (dokumentacja parametrów w `docs/VEHICLE_REFERENCE_DATA.md` ze źródłami), solver z `docs/04` warstwy 1–4, telemetria CSV + overlay debug, plac testowy (płaski asfalt, okręgi o znanym promieniu (np. 25 m i 50 m), ósemka, podjazd 6% i 12%, krawężnik 8–15 cm, koleiny, różne nawierzchnie), sterowanie przez warstwę wejścia (klawiatura/pad; kierownica — ADR 0263; 🔒 dotyk + gyro v0 dla telefonu), kamera kabiny v0.
**Bramka:** testy z `docs/04` §6 dla ciągnika solo zielone w tolerancjach; brak dryfu na postoju, brak oscylacji, krawężnik nie teleportuje; 3 przejazdy 0–80 km/h powtarzalne ±3%; **wszystko w playerze Windows** (fizyka w stałym kroku — wynik nie może zależeć od FPS: przejazdy przy limicie 30 i 60 FPS dają te same liczby w tolerancji). 🔒 Telefon: pomiar kontrolny przy powrocie do wersji mobilnej.

## Etap 2 — Naczepa, pneumatyka, pełny układ napędowy (tor F)
**Zakres:** naczepa firankowa (pusta / 24 t ładunku), siodło jako stabilny constraint, hamulce pneumatyczne ciągnik+naczepa z opóźnieniem, ABS, retarder, hamulec silnikowy, AMT 12-biegowa + tryb manual, sprzęgło, zawieszenie kabiny, cofanie z kamerą naczepy.
**Bramka:** pełny pakiet walidacyjny `docs/04` §6 (pusty i 40 t), jackknife możliwy przy błędzie kierowcy, brak eksplozji solvera, golden telemetry w `tests/golden/`; **feel test właściciela na PC** (klawiatura/pad, a gdy gotowe — kierownica z FFB, D56) (ruszanie pod górę z 40 t, hamowanie awaryjne, rondo, cofanie pod rampę) z listą uwag i ich realizacją. 🔒 Feel test na telefonie (dotyk) — przy wersji mobilnej.

## Tor A (równolegle od Etapu 1) — Ciężarówka premium
Szczegóły w `docs/07`. Kroki z mini-bramkami do akceptacji właściciela:
A1 brief + referencje + wymiary → A2 **3 koncepcje sylwetki** (rendery kontrolne) → wybór właściciela → A3 blockout w skali z kabiną i pozycją oczu kierowcy → A4 high-poly zewnętrze → A5 kabina high → A6 low-poly + UV + bake + materiały → A7 LOD + kolizje + import + rendery w Unity i w playerze Windows → A8 naczepa.
**Bramka toru A (przed Etapem 5):** checklista `docs/07` §6 zaliczona, zrzuty z playera Windows (tier High i Ultra), budżet trójkątów/draw calli/pamięci spełniony dla klasy „zalecany” (`WORKING_VALUE`). 🔒 Zabezpieczenie mobilne: LOD-y i budżet profilu Medium (Samsung A) nadal spełnione (LOD dla telefonu nie może zniknąć).

## Etap 3 — Referencyjna próbka jakości (bramka anty-slop)
**Zakres:** 300–500 m prawdziwej ulicy ze strefy przemysłowej (ręcznie dopracowane, ale już z danych GUGiK/OSM), fragment finalnej kabiny, kalibrowane oświetlenie dzienne, asfalt i oznakowanie poziome, pobocze, krawężniki, latarnie, 2–3 budynki hero + bryły z LoD2, roślinność, niebo; lusterka.
**Bramka:** porównanie side-by-side z **zdjęciami właściciela z tego miejsca** w tych samych ujęciach; checklista `docs/06` §5 zaliczona; **akceptacja kierunku artystycznego przez właściciela**. Bez tego nie skalujemy mapy.
Stan: **zaliczona 13.11.2026 na telefonie (D57, A16 Low)**. Na PC: pomiar kontrolny klasy „zalecany” + pakiet par zdjęcie|render z playera Windows (tier High), żeby sprawdzić, że wyższy tier nie wprowadza slopu (`docs/06`).

## Etap 4 — Pipeline świata na 2×2 km
**Zakres:** `tools/worldgen` (Python) + importer Unity (`docs/05`): ingest z manifestem → graf dróg → przekroje i skrzyżowania → teren z NMT → budynki LoD1/LoD2 + fasady → roślinność (BDOT10k + modele drzew GUGiK) → oznakowanie z tagów → kolizje osobno → chunki → Addressables. Raport QA danych.
**Bramka:** regeneracja 2×2 km jedną komendą, ręczne poprawki przeżywają reimport, zestaw przejeżdża całość bez wpadnięcia pod teren, zero dziur w kolizjach, odchyłka osi drogi od źródła w zadanej tolerancji, raport `low_confidence`; **czas ładowania regionu w playerze Windows zmierzony** (`run.json: regionLoad`) i w budżecie klasy.

## Etap 5 — Vertical slice: strefa przemysłowa + wylot (2–3 km)
**Zakres:** finalna ciężarówka i naczepa w grze, 2–3 km na poziomie Etapu 3, baza/magazyn z rampą, pętla jednego zlecenia, zapis/wznowienie (także po zabiciu procesu), nieliczny ruch AI (bezpieczne zachowania, priorytety, ronda), sygnalizacja świetlna, audio bazowe (`docs/08`), HUD (pod monitor, ADR 0265) + GPS z własnego grafu + nazwy ulic, menu i ustawienia jakości (tiery + rozdzielczość + VSync/limit FPS), dzień/zmierzch, deszcz (przyczepność + mokry asfalt), streaming + floating origin.
**Bramka:** właściciel przejeżdża slice 3× z rzędu bez soft-locka; **30 min jazdy w playerze Windows bez crasha**, z raportem `pc-metrics` (p50/p95/p99, klatki > progi, pamięć RAM/VRAM w czasie — brak trendu wzrostowego = brak wycieku, temperatura GPU jeśli dostępna z `nvidia-smi`, inaczej `UNVERIFIED`) dla klasy „zalecany” i „min” (gdy będzie sprzęt); raport wizualny z playera (dzień, zmierzch, deszcz, kabina noc); lista elementów nadal tymczasowych. **Pierwsza rzecz, którą wolno nazwać „grą”.** 🔒 30 min na Samsungu A z temperaturą — przy wersji mobilnej.

## Etap 6 — Cały Białystok 1:1
**Zakres:** dzielnica po dzielnicy (kolejność do ustalenia po analizie danych), każda przechodzi bramkę jakości jak Etap 3/4 (w skali). Narzędzia produkcyjne: generatory typologii zabudowy białostockiej (bloki z wielkiej płyty, kamienice, domy jednorodzinne, drewniane domy na Bojarach, hale, galerie handlowe), autoring obiektów charakterystycznych (Pałac Branickich, katedra, ratusz, Rynek Kościuszki, stadion, dworzec PKP — model własny na bazie danych i zdjęć właściciela), sygnalizacja i oznakowanie całej sieci, pełny ruch AI z autobusami miejskimi, piesi (prosto, później), HLOD/impostory.
**Bramka per dzielnica:** checklista jakości, koszt produkcji zmierzony (godz./km², godz./obiekt hero), brak regresji wydajności w `pc-metrics` (porównanie z poprzednim pomiarem tej samej trasy, ta sama maszyna pomiarowa), ciągłość sieci na granicach chunków i dzielnic. 🔒 Budżet danych mobilnych (tris/draw calls Low–Ultra) nadal spełniony.

## Etap 7 — Obrzeża + pierwsza trasa skrócona + test DLC
**Zakres:** miejscowości wokół Białegostoku 1:1, pierwszy odcinek trasy między miastami w skali skróconej (ADR skali po teście 2–3 wariantów współczynnika), strefy przejściowe miasto↔trasa, drugi region pack technicznie odrębny (dowód systemu DLC na PC: instalacja/usunięcie bez reinstalacji gry, granica regionów, zapis w usuniętym regionie → bezpieczny fallback).
**Bramka:** przejazd Białystok → miejscowość obok przez granicę paczek bez przycięcia (0 klatek > 100 ms na granicy w `pc-metrics`); testy DLC z `docs/10` zielone. Kanał dystrybucji paczek na PC — decyzja właściciela (pytania w `docs/10` §3a).

## Etap 8 — Polerowanie i testy zamknięte
Profile jakości per klasa PC (strojenie High/Ultra, rozdzielczości, skalowanie rozdzielczości), test 30 min na każdej dostępnej klasie, pełne wsparcie kierownic (FFB, pedały, skrzynia H — D56), crash reporting, lokalizacja PL/EN, onboarding sterowania, instalator/paczka dystrybucyjna Windows (zip `scripts/package-windows.py`, itch.io najpierw, Steam po decyzji właściciela — ADR 0271, `docs/12`; `--release` zablokowany do zamknięcia R-P0-2; bez publikacji bez zgody). 🔒 Android: AAB + Play Asset Delivery, testy wewnętrzne w Play Console — dopiero w wersji mobilnej.

## Etap 9+ — Podlasie → Polska → kraje DLC; wersja telefonowa; iOS
Rozszerzanie regionami tą samą procedurą. **Wersja telefonowa (Android) — lżejsza** (D73): osobne tiery/treść, bramki mobilne 🔒 z tego dokumentu i `docs/PERFORMANCE_BUDGETS.md` wracają jako obowiązujące. iOS: po wersji Android, jeśli pojawi się Mac (ewentualnie chmurowy).
