# BACKLOG S21 — jeden backlog otwartych punktów

- **Data:** 2026-11-14. **Baza:** `origin/main` @ `6dc816c` („docs: cloud3 prompts (X1/X2/Y1/Y2)”).
- **Zakres źródeł:** wszystkie recenzje `docs/reports/REVIEW-*.md` z sesji s15–s20 (53 pliki); sekcje „Otwarte/Open/Konsekwencje” wszystkich `docs/adr/*.md` (wyciąg lidera s21); follow-upy s19–s20 z `HANDOVER.md` (wyciąg lidera s21). Recenzje czytane sekcjami: werdykt, P0/P1/P2, otwarte, follow-up, „fakty dla agentów”; tabele liczb pominięte.
- **Wierszy:** 37. Dokument tylko porządkuje istniejące ustalenia — nic tu nie jest nowym pomiarem.

## Legenda

- **Źródła (skróty):** `R:<tag>:<linie>` = `docs/reports/REVIEW-2026-11-1x-<tag>.md` (np. `R:s20-0183:12` = `docs/reports/REVIEW-2026-11-14-s20-0183.md:12`); `A:<nnnn>:<linie>` = `docs/adr/<nnnn>-*.md`; `H:<linie>` = `HANDOVER.md` na `6dc816c`; `G:<n>` = `docs/reports/GATE-<n>.md`. Linie sprawdzone `grep -n`/`awk NR` na bazie.
- **Priorytet:** P0/P1/P2 dosłownie z recenzji/ADR. `*` = recenzja/ADR nie nadaje priorytetu — nadany przez autora backlogu (wpływ na bramkę → P1, reszta P2). `↑` = źródła różnią się, wzięty najwyższy.
- **Status:** `otwarte` — brak dowodu zamknięcia; `w toku (gałąź)` — gałąź na `origin` albo zlecenie w HANDOVER; `prawdopodobnie zamknięte (dowód)` — późniejsza recenzja/ADR/HANDOVER/commit na `origin/main` mówi, że naprawione; `do weryfikacji` — późniejsze źródło sugeruje zmianę, ale bez jednoznacznego zamknięcia.
- **Wielkość:** S ≤ ½ dnia agenta, M ≈ 1 agent-sesja, L > 1 sesji / wiele agentów (szacunek autora backlogu, `WORKING_VALUE`).
- **Obszary:** świat C (region `bialystok-industrial-c`), Dojlidy (region `bialystok-dojlidy`), ciężarówka (model/oświetlenie zestawu), fizyka, rendering (oświetlenie, niebo, shadery, noc), audio, UI (HUD, nawigacja), perf (telefon, pomiary, GC), research (źródła, paczki Mistral/GPT, licencje).

## Backlog

### świat C (12)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-001 | świat C | Wymiary znaków pionowych (romb/kwadrat, B-20, folia typ 2, U-4a, tabliczki T) + regeneracja i visual QA kamer znaków | R:s15-mistral-r3:68-70; R:s16-mistral-r4:11,72 | P2* | otwarte (wymiary scalone #24 — R:s16-mistral-r4:11; U-4a/tabliczki T i QA bez dowodu) | S |
| B-002 | świat C | `p21_hatch` 0,24/0,39 i 0,60/0,98 m — decyzja właściciela, potem zdjąć xfail | R:s15-mistral-r3:71-73 | P2* | otwarte (P-11 i łącznice scalone #25 — R:s16-mistral-r4:12) | S |
| B-003 | świat C | Zdublowane zapory edge-west — poprawka w C# `WorldEdgeBuilder.ReadExits`; zdjęcie xfail wolnych końców barier po regeneracji | R:s16-mistral-r5:90-91 | P2* | otwarte | S |
| B-004 | świat C | Walidator świata: „drzewa w jezdni” (53) sprawdzić na kamerach | R:s16-mistral-r6:115 | P2* | otwarte | S |
| B-005 | świat C | D51 „ulice domów wyraźnie gęściej zielone” niespełnione na Low/A16; korony „parasol na gołym pniu” zamiast lipy/klonu | R:s16-codex-0154:10,40-41,59 | P1* | otwarte | M |
| B-006 | świat C | Tablice Putry: ujednolicić epokę (2024+): bramownica A — jedna tablica 3-wierszowa z „675 Centrum”, bez wysięgnika B; portal N/C — dodać mały środkowy panel „↑ 675 Centrum”, jeśli brak | R:s16-gptpro-g2-g3:76; R:s16-research-pack-02:209-211; R:s17-mistral-r8-p7:7-8,16 | P1* | otwarte (brak dowodu wykonania) | S |
| B-007 | świat C | Kamery kontrolne: wysokość kadrów Panoramax (~1,3–1,5 m) vs oko kierowcy ~2,5 m; kadry 2019 tylko do geometrii; nowe kadry P1B-007/020/019/027/018/010/003 | R:s16-research-pack-02:203-206; R:s17-mistral-r8-p1b:49-61 | P2* | otwarte | S |
| B-008 | świat C | Sygnalizacja i meble wg P9/M50: `signal_pole` 4,3 m, wysięgnik ≥ 5,50 m, żerdź 12,0 m, hydrant 0,65 m, szafki, stojak U 0,80×0,80, słupki biało-czerwone ~1 m (WORKING_VALUE/proxy) | R:s16-research-pack-02:214-221; R:s17-mistral-r8-p6p8p9p5:77,177 | P2* | otwarte (część mogła wejść w 0162/0193 — brak dowodu w recenzjach) | M |
| B-009 | świat C | Graf: skrajnia domyślna 4,50/5,00 m (brak B-16 pod Putry/Wolnej Ukrainy/Żołnierzy Wyklętych/S8), reguła sprzeczności tagów, e-TOLL, korekta G10 „B-20 = STOP” | R:s16-research-pack-02:223-227; R:s17-mistral-r8-p6p8p9p5:52 | P2* | otwarte | S |
| B-010 | świat C | Zieleń Al. Tysiąclecia po przebudowie: młode palikowane drzewa (~5/100 m), horyzont = niski pas drzew + słupy WN, zadrzewiona skarpa N od bloków; Andersa — mieszanka klonów (nie aleja) | R:s16-research-pack-02:229-234; R:s17-mistral-r8-p10:55-59 | P2* | otwarte (las/horyzont częściowo w 0170/0187 — patrz wiersze lasu) | M |
| B-011 | świat C | Budynki: dachy skośne domów z OSM `roof:shape`/reguł; drewniane domy podlaskie tylko `authored_overrides`; kolory bloków OWT Białostoczek (ESTIMATED); nie używać kolumn P3/M53 kondygnacje/kolor_srgb | R:s16-research-pack-02:236-241; R:s17-mistral-r8-p3:3,23-38 | P2* | otwarte | L |
| B-012 | świat C | Oznakowanie poziome wg zał. 2: P-3a/P-5/P-6 kreska 4,00/przerwa 2,00, linia 0,12; P-3b 1,00/1,00; P-12 0,50; P-13 0,50×0,70; P-14 0,75×0,50 | R:s17-mistral-r8-p6p8p9p5:122,158-160 | P2* | otwarte (porównać z generatorem) | S |

### Dojlidy (3)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-013 | Dojlidy | Kafle K01/K04 i bramy firm (node OSM) — szerokości/promienie ESTIMATED (G03 8,0 … G14 7,0 m); konflikty dojazdu KAN (Mickiewicza maxweight=8) i BIAFORM (rondo Meyera hgv=no) — zlecenia nie przez te odcinki bez decyzji | R:s16-research-pack-02:196-201; R:s17-mistral-r8-p6p8p9p5:29 | P2* | otwarte | M |
| B-014 | Dojlidy | Hangar Aeroklubu (L10) ~360 m poza kaflem 0166 w `landmarks_d51.authored.json` → tło albo usunąć | R:s17-mistral-r8-p11-p12:99,125 | P2* | otwarte (brak dowodu) | S |
| B-015 | Dojlidy | Wyposażenie: latarnie dwuramienne (Y), wiaty stare/nowe UNVERIFIED, progi z A-11a; kamery kontrolne P11-001/063/094/056/129 (nie P11-084/091/092/064) | R:s17-mistral-r8-p11-p12:103-111 | P2* | otwarte | M |

### ciężarówka (1)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-016 | ciężarówka | Zgodność modelu z tabelą wymagań P4/M44: ciągnik bez konturu R104/tablic wyróżniających/R58/R73, z odblaskami bocznymi i obrysowymi; naczepa — kontur R104 z tyłu, tablice R70, odblaski trójkątne, RUPD/R73; lusterka R46 (pola widzenia kl. II/IV/V/VI); tablica 520×114 R10 | R:s16-research-pack-02:243-249; R:s17-mistral-r8-p4:65-94 | P1* | otwarte (brak audytu modelu względem tabeli w recenzjach) | M |

### fizyka (3)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-017 | fizyka | Decyzja właściciela: `maxLaunchGear` 4 vs 2 i `clutchMaxTorque` 4000 Nm (źródła nie rozstrzygają) | R:s15-mistral-r3:74-75 | P2* | otwarte | S |
| B-018 | fizyka | `reverse_dock_s_maneuver_comb` kończy złożeniem na odboju (91,2–91,6°); `reverse_grade6pct_comb` cofa ~8,2 km/h przy celu 4 km/h | R:s16-mistral-r5:92-93 | P2* | otwarte | M |
| B-019 | fizyka | F1: tolerancja miękkiego ogranicznika przegubu (0,6–3,3° nadmiaru) albo sztywniejszy stop; F2: wstrzykiwanie energii przy wywrotce (275 km/h w powietrzu) | R:s16-mistral-r6:108-109 | P1* | otwarte (przyczyna F2 niepotwierdzona) | M |

### audio (2)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-020 | audio | Test oktawy `comb_estimate`, który pada na starym kodzie bez WAV | R:s15-mistral-r3:67 | P2* | prawdopodobnie zamknięte (#30 M26 SCAL, legacy 17/17 FAIL — R:s16-mistral-r5:15) | S |
| B-021 | audio | Brak wolnych nagrań retardera, hamulca silnikowego, osuszacza, AMT, R6 13 l (3 negatywy) → syntezować/ElevenLabs; wzorzec przerwy momentu AMT z B8R (0,75–1,0 s, −13…−16 dB) | R:s16-gptpro-zips:60-66; R:s16-research-pack-02:289; R:s17-mistral-r8-p6p8p9p5:98,185 | P2* | otwarte | M |

### UI (6)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-022 | UI | HUD: telemetria dev i overlay diagnostyki nadal alokują przy zmianie treści (etykiety jazdy już 0 GC) | R:s15-mistral-r3:76-79; R:s16-mistral-r4:15,76-77 | P2* | otwarte (HUD jazdy zamknięty #22 M23 — R:s16-mistral-r4:15) | S |
| B-023 | UI | Regeneracja `bialystok-industrial-c_route.bytes` (KRTG v2, osie M28, flagi M27) + visual QA paska pasów i linii trasy na telefonie | R:s16-mistral-r4:69-71; R:s16-mistral-r5:84-87 | P2* | otwarte (brak dowodu regeneracji w recenzjach) | S |
| B-024 | UI | Planer C# liczy koszt z `GeomLength`, nie `length_m` (różnica do 5,64 m/krawędź) | R:s16-mistral-r5:88-89 | P2* | otwarte | S |
| B-025 | UI | `hgv=destination` nie zwalnia krawędzi startowej; `hgv:conditional` nieobsługiwane (0 w regionie C) | R:s16-mistral-r4:78-79 | P2* | otwarte (dotyczy kolejnych regionów) | S |
| B-026 | UI | Nawigacja: `HasExit` liczy wszystkie wyloty ronda; `RouteTracker.Update` ETA O(n) co klatkę (koszt na telefonie niezmierzony); 6 komunikatów głosowych na manewr do oceny na ucho; brak raportu NAV-RUNNER | R:s16-mistral-r6:110-114 | P2* | otwarte | M |
| B-027 | UI | Przystanki: 52 węzły OSM ↔ kody GTFS (nazwy/numery słupków) | R:s16-research-pack-02:220 | P2* | otwarte | S |

### perf (4)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-028 | perf | Testy `ZeroGc_*` nawigacji mierzą `GC.GetAllocatedBytesForCurrentThread()` (w edytorze 0) — przepisać na `Recorder("GC.Alloc")` | R:s16-mistral-r4:74-75; R:s16-mistral-r5:98 | P2* | otwarte | S |
| B-029 | perf | Rozszerzyć testy `Recorder("GC.Alloc")` na fizykę, audio i kamerę w PlayMode (audyt GC M32 niezweryfikowany pomiarem) | R:s16-mistral-r5:96-97 | P2* | otwarte | M |
| B-030 | perf | Pomiar A16 po 0153 (LOD aut): GPU p50/p95/p99 trasy ADR 0136 r2, pop aut 16/42,5 m, kolor atlasu po ASTC, PSS/hitching | R:s16-codex-0153:58-62 | P2* | otwarte (brak osobnego pomiaru w recenzjach) | S |
| B-031 | perf | Pomiar A16 po 0155: shadow pass i migotanie w ruchu przy wiadukcie | R:s16-codex-0155:62 | P2* | otwarte | S |

### research (6)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-032 | research | `docs/LICENSES.md`: CC BY-SA wycinków Mapillary/Panoramax/KartaView tylko jako referencja; ujednolicić licencję KartaView (CC BY vs CC BY-SA) | R:s16-gptpro-g2-g3:78; R:s17-mistral-r8-p10:46 | P2* | otwarte | S |
| B-033 | research | Źródła: GRRF-56-3 (inny dostęp), limity z art. 20 PoRD, obecna podstawa dla końców barier (GDDKiA); Dz.U. 2021 poz. 438 a zał. 2 | R:s16-mistral-r5:94-95; R:s16-mistral-r4:73 | P2* | otwarte | S |
| B-034 | research | M30 (r5) nadal bez PR | R:s16-mistral-r6:119 | P2* | otwarte (brak wzmianki w późniejszych recenzjach) | S |
| B-035 | research | PR #41 (M44) przed scaleniem: CMS zamiast kl. II/IV (R46 Rev.6), pełna lista zmian 2026/891 | R:s17-mistral-r8-p4:96-120 | P2* | otwarte | S |
| B-036 | research | Luki zdjęć referencyjnych: Batorego 0, Brzeska/Buska 0, Maczka zima 0, rondo Bieżeństwa z poziomu kierowcy 0, 9 ulic osiedla 0, lato 9 ulic osiedla 0, stan 2025–2026 bramownicy A/portalu N, tablice S19 — sesja zdjęciowa właściciela | R:s16-research-pack-02:282-295; R:s17-mistral-r8-p1b:37-47,68; R:s17-mistral-r8-p10:49-53; R:s17-mistral-r8-p7:9,11 | P2* | otwarte | M |
| B-037 | research | M51 `crowns.geojson` odbite lustrzanie N–S w kaflach 1024 m; filtr r ≤ 6,5 m wycina drzewostany — nie używać bez korekty | R:s17-mistral-r8-p10:7-9,38-41,56 | P1* | do weryfikacji (patrz recenzja M51-FIX-2 s20) | S |

