# Bramka 3 — Referencyjna próbka jakości (raport końcowy)

Data raportu: 2026-11-13 (s19) · Autor: build-qa · Decyzja: **D57** (`docs/11_DECYZJE_WLASCICIELA.md`, s16, 2026-11-13)
APK pomiaru: `artifacts/apk/kamion-0.1.0-3ffbf13881.apk`, 217,3 MB, SHA256 `110760f57a269f051489728ae07ab2989b25852dd20f00d5303ea3318b900b7c` (plik `.sha256` obok), build czysty (`apkDirty=false`) · Unity 6000.3.28f1
Telefon: Samsung Galaxy A16 (SM-A165F, MT6789 / Mali-G57 MC2, Android 16, serial RFGL34SJYDZ) · profil **Low 30 FPS** (D49)
Definicja bramki: `docs/03_ETAPY_I_BRAMKI.md` (Etap 3). Szkic z danymi historycznymi (10.11): `docs/reports/GATE-3-draft.md`.

## Werdykt: ZALICZONA (D57, decyzja właściciela)

Właściciel rozpoznał miejsca w pakiecie 12 par zdjęcie | render i zaakceptował kierunek (D57: „PASS — właściciel rozpoznaje miejsca”).
Kryterium bramki ustawione wcześniej przez właściciela: **rozpoznawalność trasy > dopracowanie materiałów** (D51). Kolor nieba,
odcień trawy, tekstury i drobne zużycie nie blokują bramki 3 i są dopracowywane po niej (lista niżej).
Poprawki 0161–0163 zostały zaliczone przez właściciela jako dopracowanie, nie warunek bramki.

## Kryteria z `docs/03` (Etap 3) i stan

| Kryterium | Stan | Dowód |
|---|---|---|
| Side-by-side ze zdjęciami miejsca w tych samych ujęciach | ✅ (z odstępstwem) | pakiet 12 par `artifacts/owner-package-s16/01-275528.jpg … 12-339463.jpg`. Odstępstwo: referencje to otwarte zdjęcia (Mapillary/Commons/KartaView, D43), nie zdjęcia właściciela — właściciel ocenił pakiet i przyjął (D57) |
| Checklista `docs/06` §5 | ⚠️ częściowo (patrz niżej) | krytyk 42 par: FAIL pełnego zestawu, PASS pakietu 12 par; kontrole automatyczne nieodświeżone dla `3ffbf13881` |
| Zmierzony koszt na Samsungu A | ✅ Low (D49: A16 oficjalnie Low) | `artifacts/gate3/20261113-081528/RFGL34SJYDZ/gate3-result.json`, `artifacts/gate3/20261113-085052/RFGL34SJYDZ/gate3-result.json` |
| Oszacowany zapas dla High | ⚠️ tylko starsze buildy | S24+ High na końcowym APK nie zmierzony (HANDOVER „KONIEC S16”); dane S24+ z 10.11 w szkicu |
| Akceptacja kierunku artystycznego przez właściciela | ✅ | D57 |

## Liczby z telefonu (A16 Low 30 FPS, zestaw 40 t na autopilocie 30 km/h, okno od 25 s)

Źródło: `gate3-result.json` (pola `frameTime`, `gpuMs`, `cpuMainMs`, `pssMb`, `thermalStatus`, `cameras`). Oba przebiegi `valid=true`,
APK czysty. Ostrzeżenie w pliku: HEAD repo w chwili pomiaru (`4cfe9cfb7f` / `ff9777e2db`) różny od commita APK — mierzony jest APK `3ffbf13881`, nie HEAD.

| Odcinek | Wynik | mean FPS | p50 / p95 / p99 / max [ms] | klatki > 33 / > 50 ms | GPU p50 / p95 / p99 [ms] | CPU main p50 / p95 / p99 [ms] | PSS [MB] | bateria start→koniec [°C], thermal | kamery |
|---|---|---|---|---|---|---|---|---|---|
| G3-A (s 12–450 m, 436,7 m) — `artifacts/gate3/20261113-081528/RFGL34SJYDZ/` | budżet OK | 29,87 | 33,33 / 33,45 / 33,63 / 83,4 | 202 / 9 (z 1878) | 31,78 / 34,15 / 35,89 | 20,87 / 29,02 / 40,13 | 880,2 | 27,4 → 27,5, 0 | 57/57 CAPTURED |
| G3-B (s 1232–1718 m, 485,9 m) — `artifacts/gate3/20261113-085052/RFGL34SJYDZ/` | budżet OK | 29,89 | 33,33 / 33,45 / 33,59 / 116,8 | 226 / 9 (z 2126) | 31,41 / 34,02 / 36,03 | 20,49 / 28,37 / 40,68 | 894,5 | 28,7 → 28,6, 0 | 46/46 CAPTURED |

Budżet WORKING_VALUE Low z `docs/PERFORMANCE_BUDGETS.md` (zapisany w `gate3-result.json`): p95 ≤ 34,0 ms, p99 ≤ 40 ms, PSS ≤ 1000 MB — wszystkie trzy `true` w obu przebiegach.

Uwagi do liczb:
- p50 = 33,3 ms to cap 30 FPS; p95 nie pokazuje zapasu. **GPU p95 (34,0–34,2 ms) jest powyżej budżetu klatki 33,3 ms** — GPU A16 nie ma zapasu na Low (ADR 0177: „GPU stoi ~1 ms pod budżetem 33,3 ms”, p90 ≈ budżet).
- CPU wątku głównego p99 40,1 / 40,7 ms (czas CPU, nie klatki).
- Klatki > 40 ms (`uv run --project tools/perf python tools/perf/p99_spikes.py --summary 20261113-081528 20261113-085052`, okno od 25 s):
  **G3-A 14 z 1844, G3-B 14 z 2079** (ranga 1 % = 18 / 20).
- Duplikaty klatek kamer: 0 (`duplicateFrames: []`), `gameLacks: []`, `driveLog.suspiciousLines: 0`.
- Obejrzany zrzut z telefonu (przykład): `artifacts/gate3/20261113-085052/RFGL34SJYDZ/cam/g3b_eye_s1482.png` — bramownica Andersa z tablicami, ekrany akustyczne, mur z bloczków, bariera W, hala po prawej; obraz kompletny, bez czarnych pól.

### Regresja p99 po bramce i ADR 0177
Po zaliczeniu (s17, APK `3a60019ff1`) p99 wzrósł do klifu 50 ms przy tym samym p95 — źródła:
`artifacts/gate3/20261113-153533/RFGL34SJYDZ/gate3-result.json` (G3-A: p95 33,46, **p99 49,96**, > 50 ms: 12, PSS 899,8, `valid=true`) i
`artifacts/gate3/20261113-163012/RFGL34SJYDZ/gate3-result.json` (G3-B: p95 33,48, **p99 49,92**, > 50 ms: 14, PSS 926,2, `valid=true`);
klatki > 40 ms: **23 i 22** (`p99_spikes.py`, jak wyżej). Przebiegi `20261113-142719` i `-150244` (`a7010f7757`) mają `valid=false` (APK -dirty) i nie są dowodem.

Diagnoza i poprawka: **ADR 0177** (`docs/adr/0177-perf-p99-pso-refresh.md`, scalone w s18): p99 jest metryką-klifem (1–2 klatki zmieniają werdykt);
przyczyny: odpytywanie sensorów/PSS przez `DiagnosticsSampler` na wątku głównym co 2 s oraz nieaktualne kolekcje PSO po zmianach świata.
Wynik z ADR (A16 Low, APK `c5887f4fbb`, nowe PSO + telemetria w tle): klatki > 40 ms G3-A 1 / 10, G3-B 2 / 12; p99 33,50–33,60 ms
(dowody `artifacts/perf-p99-0177/{s17-probe,trace,ab}`). **Na main nie ma jeszcze świeżych kolekcji PSO** — procedura
`pwsh tools/perf/pso-refresh.ps1 -BeforeApk <czysty APK>` jest w kolejce integracji lidera po jednej regeneracji świata (HANDOVER „STOP S18”).

### Otwarta decyzja właściciela: metryka „≤ 12 klatek > 40 ms na przejazd”
Propozycja z ADR 0177 (WORKING_VALUE dla A16 Low): raportować obok p99 liczbę klatek > 40 ms w oknie przejazdu G3, próg **≤ 12**.
Konsekwencja do świadomej decyzji: **przebiegi, na których zaliczono bramkę (D57), mają 14 i 14 — byłyby tuż nad progiem**;
s17 23 / 22 — odrzucone; po 0177 1–12 — przechodzą. Próg nie zmienia D57 (decyzja zapadła na budżecie p95/p99/PSS), ale od jego przyjęcia
każdy kolejny pomiar bramki 3 będzie raportował tę liczbę.

## Kamery kontrolne i porównanie ze zdjęciami (`docs/06` §5)

| Punkt checklisty | Stan | Dowód |
|---|---|---|
| 1. Zestaw kamer kontrolnych | PASS | 57 kamer G3-A i 46 G3-B (oko kierowcy co 50 m, ¾ zestawu, ronda z góry, kabina) × światło domyślne/overcast, wszystkie CAPTURED na A16 |
| 2. Render z edytora i zrzut z telefonu | PASS dla kamer kontrolnych; **brak zrzutów A16 dla 42 póz par zdjęciowych** | telefon: `artifacts/gate3/20261113-0{81528,85052}/RFGL34SJYDZ/cam/*.png`; edytor: `artifacts/world-int-s16b/pairs/` |
| 3. Side-by-side z referencją | PASS (pakiet 12) | `artifacts/owner-package-s16/` |
| 4. Przegląd `visual-critic` (inny agent) | pełny zestaw 42 par **FAIL**, pakiet 12 par **PASS warunkowy** | `docs/reports/visual/REVIEW-2026-11-13-s16b-final.md`: **27 R / 15 P / 0 N** (G3-A 12/10/0, G3-B 15/5/0; poprzednio 18/21/3) |
| 5. Kontrole automatyczne | **nieodświeżone** dla `3ffbf13881` | ostatni raport `artifacts/gate3/evidence/gate3-evidence.md` z 10.11 (repo `119b2c2151`, FAIL: albedo, normalne/UV, obiekty vs teren) — do powtórzenia po integracji s19 |
| 6. Wynik | bramka ZALICZONA decyzją D57 przy D51; punkty 2 i 5 do domknięcia jako dług techniczny | — |

R = kierowca znający miejsce rozpozna; P = układ dobry, brak lub zła kotwica; N = inny układ.

## Rozmiary
- APK `3ffbf13881`: 217,3 MB (`gate3-result.json` → `apk.sizeMB`).
- Draw calls / trójkąty na A16: nie mierzone z telefonu w tym przebiegu (zmiany budżetu są mierzone w edytorze per ADR, np. 0159: Low draws +0, tris ≤ +1,3 %).

## Znane braki (otwarte zadania po bramce, stan s19)

| ADR | Zakres | Gałąź / stan |
|---|---|---|
| 0170 | horyzont: drzewostan lasu, korony przy kamerze (czarna skrzynka p07_b), tuja/świerk | `horizon-0170` — domykanie faili pytest + ADR, nie scalone |
| 0172 | P1 pakietu: sygnalizator 182011 wg ortofoto 2024 (decyzja właściciela 13.11), znaki cm924 | `p1b-0172` — r4, nie scalone |
| 0179 | Dojlidy (nowy region, D60) — poprawki wizualne | `dojlidy-vis-0179` — iteracja 2 po SBS; region ≠ C, scalany osobno |
| 0180 | wieżowiec: kolumna okien na szczycie, pasma okien | **scalone** `6a2318d67` (r2); P2 w ADR „Otwarte”; świat jeszcze nie przebudowany |
| 0184 | LOD1: pasek `FAR_PLAIN_V` nachodzi na płytę balkonową (białe łaty NW) | `atlas-0184` (od `tower-0180`) — scalany po 0180 |

Pozostałe z krytyka s16b (P1, poza powyższymi): podpora 1259231, ściana 482392, bariera 962702 po złej stronie kamery, D-1 obrócony (4312632),
latarnia dwuramienna 1801374 / 1406533; P2: filary, stożki świerków. Materiały wg D51 („gra mobilna z 2016”: sterylny beton, jasne spody pomostów, płaskie światło) — po bramce.

Proces / pomiar:
1. **Regresja p99 (ADR 0177)** — poprawka scalona, ale nowe kolekcje PSO i pomiar A16 dopiero po jednej regeneracji świata w s19.
2. **S24+ High/30 na końcowym APK nie zmierzony** (zapas High oszacowany tylko z buildów 10.11 — szkic).
3. Zrzuty A16 dla póz par zdjęciowych (punkt 2 checklisty) i świeże kontrole automatyczne (punkt 5).
4. Test „feelingu” na odcinku (lista w szkicu) — nie wypełniony; D57 obejmuje rozpoznawalność, nie jazdę.

## Pomiar kontrolny po integracji s19 (dla lidera)
Po regeneracji, PSO refresh i czystym APK (kolejność w HANDOVER „STOP S18”), z ręcznie założonym `artifacts/locks/PHONE_RUN`
(`gate3-run.ps1` sam go nie zakłada) i bez działającego Unity (Unity restartuje demona adb):
```
pwsh scripts/gate3-run.ps1 -Serial RFGL34SJYDZ -Tier Low -Fps 30 -SkipBuild -Apk artifacts/apk/kamion-0.1.0-<sha>.apk              # G3-A
pwsh scripts/gate3-run.ps1 -Serial RFGL34SJYDZ -Tier Low -Fps 30 -SkipBuild -Apk artifacts/apk/kamion-0.1.0-<sha>.apk -Segment B   # G3-B
uv run --project tools/perf python tools/perf/p99_spikes.py --summary <ts-A> <ts-B>                                              # klatki > 40 ms
```
Liczby dopisać tutaj jako „pomiar kontrolny s19” obok D57 (nie zastępują przebiegów zaliczenia).

## Pomiar kontrolny s20 (2026-11-14, A16 RFGL34SJYDZ, Low/30, APK kamion-0.1.0-77cfd94bf8, czyste drzewo)
Po integracji s20 (0170, 0172, 0181, 0184, 0191+0192, regeneracja C, PSO odświeżone).
| odcinek | FPS | p50/p95/p99/max ms | > 50 ms | GPU p50/p95/p99 ms | CPU main p50/p99 ms | PSS MB | kamery | budżet |
|---|---|---|---|---|---|---|---|---|
| G3-A | 29,99 | 33,33 / 33,46 / 33,57 / 50,2 | 2 | 32,1 / 34,5 / 35,7 | 21,6 / 31,1 | 917,5 | 57/57 | OK |
| G3-B | 29,95 | 33,33 / 33,45 / 33,62 / 50,1 | 6 | 31,3 / 34,3 / 37,1 | 21,9 / 33,5 | 877,8 | 46/46 | OK |
Dane: `artifacts/gate3/20261114-063715`, `artifacts/gate3/20261114-071223`. GPU p50 ~31–32 ms przy 33,3 ms klatki — mały zapas na Low. Przegląd wizualny zrzutów: `docs/reports/REVIEW-2026-11-14-s20-gate3-phone.md`.

### S24+ (RZCX60VE8ZY, właściciela) High/30, APK kamion-0.1.0-18e368be69-high (świat High), s20 2026-11-14
| odcinek | FPS | p95/p99/max ms | > 50 ms | GPU p50 ms | PSS MB | temp. °C | kamery |
|---|---|---|---|---|---|---|---|
| G3-A | 29,96 | 33,54 / 33,79 / 66,8 | 3 | 23,0 | 1670 | 27,9 | 56/57 |
| G3-B | 29,97 | 33,62 / 34,31 / 66,3 | 1 | 22,5 | 1644 | 34,5 | 46/46 |
Thermal 0. Budżet w skrypcie dla High = 60 FPS (p95 ≤ 17 ms) → „OVER” wynika z limitu 30 FPS; GPU p50 ~23 ms oznacza, że High/60 nie jest osiągalne bez optymalizacji. Bateria 94 → 60 % (dwa odcinki). Dane: `artifacts/gate3/20261114-074426`, `artifacts/gate3/20261114-081950`.
