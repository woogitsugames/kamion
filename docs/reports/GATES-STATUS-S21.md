# Stan bramek i Definition of Done — sesja 21 (2026-11-15)

Autor: agent F10 chmury D (tylko dokument, bez zmian kodu, bez Unity i bez telefonu). Baza: `origin/main` `c2b9b702a`.
Poprzednia wersja: `docs/reports/GATES-STATUS-S20.md` (baza `6dc816c`, 14.11 21:45). Ten plik **nie powtarza** szczegółów, które się nie
zmieniły (kryteria `docs/03`, tabele 0.x/1.x/2.x/A.x/4.x, komendy, tabela spójności R1–R32) — odsyła do sekcji S20. Dopisuje wszystko z s20 po
`6dc816c` i z s21 do `c2b9b702a`.

Źródła: `docs/reports/GATE-3.md:131-136` (A16 `af2570fccd`), `GATE-3.md:109-129` (pomiary s20), `docs/reports/GATE12-PHONE-2026-11-14-A16.md`,
`docs/reports/VERIFY-2026-11-15-axleloads-tuning-0201b.md`, `docs/11_DECYZJE_WLASCICIELA.md:87-108` (D63–D68), `HANDOVER.md` (blok s20 linie 1–172,
blok „SESJA 21” linie 173–190, na `c2b9b702a`), `game/ProjectSettings/EditorBuildSettings.asset`, `game/Assets/_Project/Editor/Build/BuildCommands.cs`,
`git log origin/main --first-parent --merges f48317146..c2b9b702a`, GitHub REST `pulls?state=open|closed`.

Zasada: każda liczba ma plik:linia albo sha. Liczby przepisane, nie mierzone przez autora. `artifacts/` jest poza gitem (`.gitignore:31`) —
autor ich nie widział; jeśli liczby nie ma w gicie, wpisane jest „brak w repo”.
Legenda: **SPEŁNIONE** · **CZĘŚCIOWO** · **NIESPEŁNIONE** · **NIEZMIERZONE**.

## Podsumowanie (zmiany względem S20 wytłuszczone)

| Bramka | Werdykt w raporcie | Stan faktyczny wg dowodów (s21) | Główna blokada |
|---|---|---|---|
| Etap 0 | CZĘŚCIOWO (`GATE-0.md:5`) | bez zmian od S20 §1 — pomiar Boot A16 tylko na APK `-dirty` (`device/DEVICE-RUN-2026-11-09.md:7,14`) | aktualizacja `GATE-0.md` + pomiar Boot na czystym APK Low |
| Etap 1 | SZKIC (`GATE-1.md:6`) | CZĘŚCIOWO — 0–80 ×3 na A16 PASS na `77cfd94bf8` (`GATE12-PHONE…:15-17`); **po scaleniu #90 (0201b, `f9781a32b`) runner solo 0–80 14,055 s zamiast 13,580 s (+3,5 %) — na telefonie niezmierzone** (`VERIFY-…-0201b.md:13,22`) | ponowny `gate12-phone` na APK z 0201b; postój/okręgi na telefonie; werdykt właściciela |
| Etap 2 | SZKIC (`GATE-2.md:6`) | CZĘŚCIOWO — liczby telefonu z 14.11 (`GATE12-PHONE…:9-10`); **po 0201b 40 t 80→0 runner 41,200 m (było 41,020), pusty 0–80 21,137 s (dolna granica 20 s)** (`VERIFY-…-0201b.md:18-20,30`); feel test właściciela brak | feel test (B-075), ponowny pomiar telefonu po 0201b |
| Tor A | brak raportu | NIEZMIERZONE jako bramka (S20 §4); **w s20/s21: dane opony/nacisków R3 scalone (0201 `a31939ef5`, 0201b `f9781a32b`), marki usunięte z danych (#78 `cae0c95f5`); światła 0197 = PR #79 otwarty** | raport toru A, profil, akceptacja |
| Etap 3 | ZALICZONA D57 (`GATE-3.md:8`) | ZALICZONA, **utrzymana na A16 na czystym APK `af2570fccd`: G3-A i G3-B ważne, w budżecie** (`GATE-3.md:131-136`); **G3-B na `edb5524993` z S20 §5 pkt 1 zastąpiony pomiarem na `af2570fccd`**; checklista `docs/06` §5 pkt 2 i 5 nadal otwarte | **stan main po `af2570fcc` niezmierzony na telefonie; 2 FAIL budżetu trójkątów High (stretch_04 2 022 535 > 2 000 000, `HANDOVER.md:169-172`) — „bramki nie mierzyć na tym stanie” do czasu budget-fix 0221** |
| Etap 4 | brak raportu | NIEOTWARTA formalnie (S20 §6); **narzędzie fidelity dla każdego regionu = PR #95 qa-tools-0219 otwarty; szwy kafli = PR #106 seams-0224 otwarty** | `GATE-4.md`, regeneracja jedną komendą w gicie |
| **Korytarz DK65 w APK (D67)** | — | **NIE W BUILDZIE**: APK `af2570fccd` i main mają w build settings tylko Boot, DrivingLab, WorldC (§6) | PR #104 region-select-0229 (chmura E), budget-fix 0221, pomiar A16 |

---

## 1. Etap 3 — A16 na czystym APK `af2570fccd` (G3-A / G3-B)

Źródło liczb: `docs/reports/GATE-3.md:131-136` (commit `6624550e4` „docs: gate3 A16 G3-A/G3-B valid on clean APK af2570fccd”), zgodne z
`HANDOVER.md:148` (G3-A) i `HANDOVER.md:151` (G3-B). Telefon: A16 SM-A165F (RFGL34SJYDZ), Low/30.

| Segment | ważny | śr. FPS | p95 ms | p99 ms | max ms | > 50 ms | GPU p95 ms | PSS MB | kamery | dowód (poza gitem) | źródło |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G3-A | TAK | 30,0 | 33,46 | 33,55 | 49,97 | 0 | 34,65 | 930,5 | 57/57 | `artifacts/gate3/20261115-141511/RFGL34SJYDZ/` | `GATE-3.md:134` |
| G3-B | TAK | 29,94 | 33,46 | 33,61 | 83,29 | 3 | 34,39 | 933,8 | 46/46 | `artifacts/gate3/20261115-145242/RFGL34SJYDZ/` | `GATE-3.md:135` |

- Budżet (WORKING_VALUE p95 ≤ 34, p99 ≤ 40, PSS ≤ 1000 MB): oba segmenty OK (`GATE-3.md:136`).
- **Z czego jest APK:** `af2570fccd` = commit `af2570fccdfc30f32362937ab2e747db2c35d8f7` na main (15.11 14:11, „docs: s20 — cloud C prompt”).
  Zawiera scalenia 1–51 z tabeli §7 (ostatnie: research night-lamps `02d42a640`) i regenerację D+C `c8b5a588d`. `GATE-3.md:136` wymienia: Argon
  0193/0186/0194, 0208, 0212, fizyka #77, marki #78.
- **Czego APK NIE zawiera** (scalone po `af2570fcc`, niezmierzone na telefonie): M61-FIX (research), M67, 0213 (woda dk65-02/03), Argon 0188/0187/0189,
  0214 (dk65-06…11), regeneracja `80345541c` (regen4), #90 0201b (fizyka), 0216 (lato + LED Knyszyn), research R2/R4/R6/R9, recenzje 0225.
  Dla stanu `80345541c` HANDOVER zapisał 2 FAIL budżetu trójkątów High i „Bramki nie mierzyć na tym stanie bez tej poprawki” (`HANDOVER.md:169-172`).
- **Brak w repo** dla `af2570fccd`: GPU p50, CPU main, temperatura, klatki > 40 ms (metryka ADR 0177) — tabela `GATE-3.md:132-135` ich nie ma.
  Wcześniejszy pomiar na `f1cb07ee0c-dirty` (p95 33,5, p99 33,7, > 50 ms 7, PSS 920 MB, 57/57) jest nieważny jako APK `-dirty` (`HANDOVER.md:142`).
- **Pętla wizualna:** „Zrzuty kamer do obejrzenia (pętla wizualna) — w katalogach `cam/`” (`GATE-3.md:136`); recenzji zrzutów z `af2570fccd`
  w `docs/reports/` nie ma (ostatnia: `REVIEW-2026-11-14-s20-gate3-phone.md` na `77cfd94bf8`).

### Trend A16 Low/30 (wszystkie ważne pomiary G3 z gita)

| APK | data | G3-A p95 / p99 / PSS | G3-A GPU p95 | G3-B p95 / p99 / PSS | G3-B GPU p95 | źródło |
|---|---|---|---|---|---|---|
| `77cfd94bf8` | 14.11 | 33,46 / 33,57 / 917,5 | 34,5 | 33,45 / 33,62 / 877,8 | 34,3 | `GATE-3.md:113-114` |
| `edb5524993` | 14.11 | 33,43 / 33,56 / 900,8 | 34,4 | NIEZMIERZONY | — | `GATE-3.md:127-128` |
| `af2570fccd` | 15.11 | 33,46 / 33,55 / 930,5 | 34,65 | 33,46 / 33,61 / 933,8 | 34,39 | `GATE-3.md:134-135` |

Wniosek (z tabeli, bez nowego pomiaru): p95/p99 stabilne; **GPU p95 nadal > 33,3 ms klatki** (B-113); **PSS G3-B +56 MB** (877,8 → 933,8) względem
`77cfd94bf8`, 66 MB do limitu 1000 MB (WORKING_VALUE). Max G3-B 83,29 ms (3 klatki > 50 ms) — przy `77cfd94bf8` 50,1 ms (6 klatek).

## 2. Etapy 1–2 — A16 (`GATE12-PHONE-2026-11-14-A16.md`) i stan po 0201b

Pomiar telefonu (jedyny w repo): A16 RFGL34SJYDZ, Low/30, APK `kamion-0.1.0-77cfd94bf8.apk`, sha256 `33bb082a…`, `dirty: False`
(`GATE12-PHONE…:3`), katalog `artifacts/gate12/20261114-062841` (`:1`). Ciąg wersji w grze „77cfd94bf8-dirty” (`:9-13`) — wyjaśnienie w S20 §7.

| przebieg | FPS | p50/p95/p99 ms | PSS MB | krok fizyki p50/p99 µs | wynik | kluczowe liczby | źródło |
|---|---|---|---|---|---|---|---|
| s080_40t | 30,01 | 33,329 / 33,467 / 33,55 | 392,4 | 594,4 / 721,7 | PASS | 0–80 47,79 s, 80→0 40,72 m, MFDD 6,996, siodło ≤ 0,1675 mm | `GATE12-PHONE…:9` |
| s080_empty | 30,02 | 33,328 / 33,609 / 33,758 | 393,1 | 601,8 / 914,6 | PASS | 0–80 20,67 s, 80→0 39,67 m, MFDD 7,461 | `:10` |
| s080_solo_1 | 30,02 | 33,329 / 33,463 / 33,539 | 412,3 | 606,9 / 738,7 | PASS | 0–60 10,00 s, 0–80 13,66 s, 80→0 35,85 m, MFDD 7,442 | `:11` |
| s080_solo_2 | 30,02 | 33,325 / 33,599 / 33,81 | 390,1 | 626,5 / 989,5 | PASS | j.w. | `:12` |
| s080_solo_3 | 30,02 | 33,33 / 33,46 / 33,546 | 385,5 | 612,6 / 750,0 | PASS | j.w. | `:13` |

Powtarzalność 0–80 solo ×3: 13,66 / 13,66 / 13,66 s, odchyłka 0,00 % → PASS (`GATE12-PHONE…:15-17`).

**Zmiana w s21 — #90 axleloads-tuning-0201b scalony** (`f9781a32b`, 15.11): runner .NET, nie telefon (`VERIFY-…-0201b.md:13-22`):

| wariant | metryka | A16 (telefon, `77cfd94bf8`) | runner przed | runner po #90 | źródło |
|---|---|---|---|---|---|
| solo | 0–80 | 13,66 s | 13,580 s | 14,055 s (+3,5 %) | `VERIFY-…-0201b.md:13` |
| solo | 80→0 | 35,85 m | 35,774 m | 35,387 m | `:14` |
| 40 t | 0–80 | 47,79 s | 47,540 s | 47,575 s | `:17` |
| 40 t | 80→0 | 40,72 m | 41,020 m | 41,200 m | `:18` |

„Wartości ‚bramka A16’ … po #90 nie były mierzone na telefonie” (`VERIFY-…-0201b.md:20`). Cienkie zapasy po zmianie: `park_12pct_up_comb@empty`
4,97/5 mm, `kingpin_load_vs_static` 1,023/1,03, `downhill_7pct_full_lever@laden40` 70,60/71 km/h (`:31`). dotnet 277/277, runner 135/135 (`:9-10`),
EditMode 600/603 (2 znane FAIL `CarPaintMaterialTests.DepositionChannel_*`, `:23`).

**Stan bramek 1–2 w s21:** bez zmiany werdyktów (`GATE-1.md:6`, `GATE-2.md:6` = „SZKIC — czeka na telefon”); tabele S20 §2 (1.1–1.7) i §3 (2.1–2.5)
aktualne poza wierszami 1.1/1.5/2.1: liczby telefonu dotyczą fizyki **sprzed** 0201b — przed zaliczeniem trzeba je powtórzyć.

## 3. S24+ High/30

Jedyny pomiar w repo: s20, 14.11, APK `kamion-0.1.0-18e368be69-high.apk` (świat High) — `GATE-3.md:117-122`, `HANDOVER.md:64-65`.

| odcinek | FPS | p95/p99/max ms | > 50 ms | GPU p50 ms | PSS MB | temp. °C | kamery | źródło |
|---|---|---|---|---|---|---|---|---|
| G3-A | 29,96 | 33,54 / 33,79 / 66,8 | 3 | 23,0 | 1670 | 27,9 | 56/57 | `GATE-3.md:120` |
| G3-B | 29,97 | 33,62 / 34,31 / 66,3 | 1 | 22,5 | 1644 | 34,5 | 46/46 | `GATE-3.md:121` |

W s21 **brak nowego pomiaru S24+**: „S24+ niepodłączony” (`HANDOVER.md:151`), wcześniej „S24+ zniknął z adb (Unity zabija daemon)” (`HANDOVER.md:141`).
Pomiaru High bez limitu / `-Fps 60` nadal brak (S20 W2, R25). APK High dla `af2570fccd` w repo nie jest wymieniony — brak w repo.

## 4. Pozostałe bramki — co się zmieniło od S20

- **Etap 0:** bez zmian (S20 §1).
- **Tor A:** dane R3 w grze — `rollingRadius` 0,524 m obok `radius` 0,51 m (`game/Assets/_Project/Vehicle/Physics/Definitions/Data/tire_315_80_r22_5.tire.json:5-6`,
  ADR 0201, `a31939ef5`); naciski 73/27 % i strojenie AMT (ADR 0201b, `f9781a32b`); plik skrzyni przemianowany na `amt12_od_class.gearbox.json`
  (#77/#78). Światła ADR 0197 = PR #79 otwarty (wg `HANDOVER.md:136` „NIE: wymaga eksportu naczepy i renderów”). Brud naczepy: research M61-FIX scalony
  częściowo (#94, `5fe25e71b`; `HANDOVER.md:147`). Raportu toru A nadal brak.
- **Etap 4:** w s20/s21 doszło 21 regionów w `regions.py` (`HANDOVER.md:155`; kafle 0203–0214), etap wody (0210, 0213), PR otwarte: #95 qa-tools-0219
  (jeden parser id grafu → fidelity dla każdego regionu; `HANDOVER.md:140` — narzędzie fidelity działało tylko dla C), #106 seams-0224, #96 rail-0217,
  #102 rail-dk65-0223, #97 roundabout-0218, #98 dk65-k1-0220, #80 dk65-d65-data (ADR 0215), #101 treerows-0222, #93 putry-ring-0198b (ADR 0226), #82 piers-0198.
  Formalnie bramka nieotwarta (brak `GATE-4.md`).

## 5. Decyzje właściciela D63–D68 (`docs/11_DECYZJE_WLASCICIELA.md`)

| D | data | treść (skrót) | wpływ na bramki | źródło |
|---|---|---|---|---|
| D63 | 14.11 s20 | nowe regiony najpierw „z grubsza” (przejezdne, LoD1, bez dopracowania do bramki), szlif później; wersja z grubsza zmierzona na A16, bez błędów krytycznych | Etap 4/6: „z grubsza” ≠ bramka jakości; wymóg pomiaru A16 dla każdego regionu | `docs/11:87-88` |
| D64 | 14.11 s20 | kierunek: Białystok → droga do Knyszyna → Knyszyn; zwykła droga, nie ekspresówka; plac budowy jako uproszczona strefa (WORKING_VALUE); priorytet: wierność sieci drogowej | zakres Etapu 4 przesunięty na korytarz DK65 | `docs/11:90-93` |
| D65 | 15.11 | wariant A (Fasty, Dobrzyniewo Duże); rondo DK65×DW671; S19 Fasty otwarta; stara DK65 bez objazdu; Ełcka ~6,9 m; nowa jezdnia dk65-05 = plac budowy; lato; LED | dane korytarza | `docs/11:95-96` |
| D66 | 15.11 | Ełcka/Studzienna 6,6 m (zamiast 6,9 m z D65) | PR #80 do scalenia ze zmianą 6,9 → 6,6 (`HANDOVER.md:155`) | `docs/11:98-99` |
| D67 | 15.11 s21 | korytarz Białystok → DK65 → Knyszyn w następnym APK z wyborem regionu; limit APK ≤ 2 GB; docelowo regiony jako osobne paczki | §6; pomiar A16 (rozmiar APK, PSS, gate3 w C bez pogorszenia) | `docs/11:101-103` |
| D68 | 15.11 s21 | zmierzch 300°; lato także w C i Dojlidach (przebudowa po 0221, potem telefon); LED 4000 K (WORKING_VALUE) | **regeneracja C+D z latem zmieni wygląd kadrów bramki 3 → nowy pomiar G3 i recenzja zrzutów** (wniosek autora) | `docs/11:105-106` |

Decyzje S20 §8 W1–W10: **żadna nie została rozstrzygnięta w s20/s21** (D63–D68 ich nie dotyczą; W1 ostatnio wymieniona jako otwarta w bloku „STOP S19”, `HANDOVER.md:206`;
blok „SESJA 21” żadnej z nich nie rozstrzyga). Częściowo zmienia się kontekst: W9 (rozmiar świata w APK, D24 ≤ 110 MB) — D67 ustala ≤ 2 GB dla APK z korytarzem;
relacja D67 do D24 nieopisana w `docs/11` → do potwierdzenia przez lidera/właściciela.

## 6. Korytarz DK65 w APK — co jest w buildzie

| pozycja | stan | źródło |
|---|---|---|
| sceny w build settings (main `c2b9b702a`) | `Boot.unity`, `DrivingLab.unity`, `_Generated/World/bialystok-industrial-c/WorldC.unity` | `game/ProjectSettings/EditorBuildSettings.asset:9,12,15` |
| to samo na `af2570fcc` (APK G3 15.11) | identyczne 3 sceny | `git show af2570fcc:game/ProjectSettings/EditorBuildSettings.asset` |
| scena High | `WorldC_High.unity` dokładana tylko w buildzie High (flaga) | `game/Assets/_Project/Editor/Build/BuildCommands.cs:56-59` |
| `-noWorld` | usuwa sceny `_Generated/World/` (tylko pomiar) | `BuildCommands.cs:62-65` |
| regiony korytarza w main | dane i generator są (21 regionów, `HANDOVER.md:155`); sceny `_Generated` poza gitem (ADR 0011) | — |
| wybór regionu w buildzie | **PR #104 region-select-0229 otwarty** (head `f824f3b7a`; „wybór regionów w buildzie (-Regions) i w menu startowym”) | GitHub REST pulls |
| rozmiar | APK z samym C: 224 MB (`HANDOVER.md:179`, D67 `docs/11:102`); katalogi `_Generated` regionów 440–1250 MB (`HANDOVER.md:179`); limit ≤ 2 GB (D67, `HANDOVER.md:182`) | — |
| warunek przed buildem | budget-fix-s21 (ADR 0221) — D67: „Następny APK (po naprawie budżetu trójkątów C, ADR 0221)” | `docs/11:102` |

**Wniosek:** żaden APK zbudowany do `c2b9b702a` nie zawiera korytarza DK65 ani Knyszyna (z gita: build settings i brak scalonego #104). Paczki
regionów (F1 regionpacks-0234) i płynne kafle (F2 streaming-0235) — w toku, chmura D r2.

## 7. Scalenia na main od początku s20 (`f48317146`, 13.11 22:15) do `c2b9b702a`

Czas = data commita scalenia (`git log --first-parent --merges`). ADR/PR z tytułu commita lub z GitHub (`pulls?state=closed`, `merged_at`).
Poza listą (scalenie przez checkout katalogu, nie merge): M57-FIX #88 → `33e10d9bf`, M60-FIX #91 → `c10c872ab` (`HANDOVER.md:142,150`).

| # | sha | czas | scalenie | ADR | PR |
|---|---|---|---|---|---|
| 1 | `263847db7` | 13.11 22:33 | gates-s19 — GATE-3 passed (D57), GATE-1/2 drafts + phone measurement script | — | — |
| 2 | `703f852b8` | 13.11 22:40 | 0172 P1b — signal 182011 (ortofoto 2024), sign cluster cm924 (critic s20 SCAL warunkowo; generated = ours, … | 0172 | — |
| 3 | `a4d2a1782` | 13.11 22:46 | 0170 horizon forest stand, near crowns, thuja rows (critic s20 SCAL warunkowo; generated = ours, regen in i… | 0170 | — |
| 4 | `ea6fdf840` | 13.11 22:55 | 0195 autopilot straight 0-80-0 for gates 1/2 (runner 39/39, PlayMode 8/8; DrivingLab regenerated with 1300 … | 0195 | — |
| 5 | `caa352d5d` | 13.11 23:18 | Mistral M47-FIX-2 + M47-FIX-3 (P11 Dojlidy photos, sign codes per s20 review; errata: P11-131 punkt_opis st… | — | — |
| 6 | `7d4463285` | 13.11 23:18 | 0184 LOD1 FAR_PLAIN strip off balcony slab (Low LOD1 light patches removed; draws/tris +0; lead viewed hi_d… | 0184 | — |
| 7 | `b823e3c49` | 13.11 23:24 | 0181 lamp lens structure + plate illumination (r2 after critic s20: aliasing fixed, Low cups round, plate c… | 0181 | — |
| 8 | `1d72f829c` | 14.11 04:31 | 0191 lamp pools + 0192 night windows/sky/halo — integrated s20 (critic SCAL warunkowo; P1 fixed: Kwadrat Pa… | 0191, 0192 | — |
| 9 | `baae5f0e0` | 14.11 17:35 | 0190 tower P2 — gable frame, roof masts, downpipes off, SE bands brighter (critic SCAL warunkowo: phone sho… | 0190 | — |
| 10 | `1e5f38f47` | 14.11 17:38 | 0183 white-red chain bollards (r4: two-sided chain cards, maroon paint, P11-063 credit; critic r3b SCAL war… | 0183 | — |
| 11 | `a1f1615ee` | 14.11 17:44 | 0185 Dojlidy buildings P1 (critic SCAL warunkowo; overrides/materials = sum of blocks; fence mip change pen… | 0185 | — |
| 12 | `5eb18d59e` | 14.11 17:44 | 0196 Dojlidy plant, segment gates, runoff shuffle, runway (critic SCAL warunkowo; overrides = sum, building… | 0196 | — |
| 13 | `7add452b9` | 14.11 18:32 | Mistral M62 + M62-FIX hospital gate P11-129 (review s20: SCAL z erratą) | — | #53 |
| 14 | `2c6508d7c` | 14.11 18:36 | Mistral M51-FIX-2 greenery P10 (review s20: SCAL z erratą) | — | — |
| 15 | `cf2dc8c77` | 14.11 18:36 | Mistral M56 + M56-FIX Andersa viaducts (review s20: SCAL z erratą) | — | #54 |
| 16 | `15b0adc58` | 14.11 19:59 | research cloud2 truck-parameters (review s20) | — | #61 |
| 17 | `16aa865a7` | 14.11 19:59 | research cloud2 traffic-signs-catalog (review s20) | — | #67 |
| 18 | `c41794d02` | 14.11 19:59 | research cloud2 mobile-gpu-a16 (review s20) | — | #59 |
| 19 | `b8d03e932` | 14.11 20:13 | research cloud2 sky-weather-bialystok (review s20: SCAL z erratą) | — | #60 |
| 20 | `174626305` | 14.11 20:14 | research cloud2 street-trees (review s20: SCAL z erratą) | — | #63 |
| 21 | `7fa891786` | 14.11 20:24 | research cloud p15-dojlidy-details (review s20: SCAL z erratą) | — | #68 |
| 22 | `6885ef544` | 14.11 20:24 | research cloud p22-red-bike-paths (review s20: SCAL z erratą) | — | #70 |
| 23 | `d235743c5` | 14.11 20:24 | research cloud p23-traffic-signals (review s20: SCAL z erratą) | — | #69 |
| 24 | `5e4431818` | 14.11 20:31 | research cloud M60 dusk (review s20: SCAL z erratą; main M60 source over Mistral #57) | — | #71 |
| 25 | `0411de271` | 14.11 20:36 | research cloud M68 Krywlany forest (review s20: SCAL z erratą) | — | #72 |
| 26 | `f1dfef0af` | 14.11 22:47 | 0199 dusk/night calibration (twilight table, coral band removed, lamp fade, window shares, night floor; lea… | 0199 | — |
| 27 | `2f9eb2a4d` | 14.11 22:59 | docs/brand-sweep-s20 (cloud session X/Y, docs only) | — | #73 |
| 28 | `dd8532992` | 14.11 22:59 | docs/gates-status-s20 (cloud session X/Y, docs only) | — | #74 |
| 29 | `0e2352a16` | 14.11 22:59 | docs/backlog-s21 (cloud session X/Y, docs only) | — | #75 |
| 30 | `2045dfe81` | 14.11 22:59 | docs/licenses-audit-s20 (cloud session X/Y, docs only) | — | #76 |
| 31 | `6031883c7` | 14.11 23:13 | 0200 tower NW bands, roof masts, SE annex (lead reviewed photo115626 SBS; open: ochre plaster colour) | 0200 | — |
| 32 | `e4bd4f95c` | 14.11 23:17 | 0202 Dojlidy U-12b chain fence + runway 27L/axis/widths + airport fence (regen Dojlidy pending) | 0202 | — |
| 33 | `f6ba266e4` | 15.11 01:33 | 0205 DK65 corridor tile dk65-01 rough (drivable 632 m; edge lines + 6.0 m; lead reviewed top-vs-ortho) | 0205 | — |
| 34 | `67eea261c` | 15.11 01:55 | 0203 (regions.py = sum of entries) | 0203 | — |
| 35 | `c8afe5a7a` | 15.11 02:00 | 0204 (regions.py = sum) | 0204 | — |
| 36 | `8205aa15d` | 15.11 03:27 | 0207 (regions.py = sum) | 0207 | — |
| 37 | `4320d3b6a` | 15.11 05:35 | 0206 (regions.py = sum) | 0206 | — |
| 38 | `d4914ba6e` | 15.11 07:20 | 0209 Knyszyn west tile knyszyn-w (DK65 exit to Mońki, drivable 1989 m; seams ±0.1 m) | 0209 | — |
| 39 | `e243e3e86` | 15.11 07:31 | 0210 water stage (rivers/ponds opt-in; Supraśl+Biała under DK65 bridge in dk65-02; C/Dojlidy unchanged; lea… | 0210 | — |
| 40 | `8fbe0b972` | 15.11 09:53 | 0212 knyszyn edges + DK65 edge lines + monki/tykocin tiles | 0212 | — |
| 41 | `134298d01` | 15.11 12:10 | 0208 bialystok-knyszynska tile + maczka deck wall | 0208 | — |
| 42 | `fa857b11b` | 15.11 12:11 | Argon sigplate-0193 (review SCAL) | 0193 | — |
| 43 | `dd4bdd42d` | 15.11 12:11 | Argon dojgreen-0186 (review SCAL); generated D from branch, regen pending | 0186 | — |
| 44 | `5d64bcd92` | 15.11 12:11 | Argon stains-0194 (review SCAL); generated from branch, regen pending | 0194 | — |
| 45 | `a31939ef5` | 15.11 12:12 | cloud A truckdata-0201 (PR verified: dotnet green) | 0201 | #77 |
| 46 | `cae0c95f5` | 15.11 12:12 | cloud A brand-fixes-s21 (PR verified: dotnet green) | — | #78 |
| 47 | `71e035504` | 15.11 13:58 | research/dk65-knyszyn-refs (review SCAL with errata) | — | #83 |
| 48 | `6445c71f9` | 15.11 13:58 | research/gate3-spots-s21 (review SCAL with errata) | — | #81 |
| 49 | `d1ae61f43` | 15.11 13:58 | research/krywlany-airfield-s21 (review SCAL with errata) | — | #84 |
| 50 | `1d41dde14` | 15.11 13:58 | research/plant-gates-s21 (review SCAL with errata) | — | #86 |
| 51 | `02d42a640` | 15.11 13:58 | research/night-lamps-s21 (review SCAL with errata) | — | #87 |
| 52 | `5fe25e71b` | 15.11 14:38 | M61-FIX p18 trailer soiling (PR #94, partial: criteria not fully met, honest gaps) | — | #94 |
| 53 | `24def362a` | 15.11 15:38 | research/rooftop-gsm-s21 M67 (review r2 SCAL) | — | #89 |
| 54 | `2ff133e21` | 15.11 16:20 | 0213 water dk65-02/03 reeds, banks, colour | 0213 | — |
| 55 | `5a5ee9166` | 15.11 16:25 | Argon ddr-0188 (overrides union; generated from branch, regen pending) | 0188 | — |
| 56 | `33ee4f985` | 15.11 16:26 | Argon forest-0187 (vegetation dedupe keeps 0186 authored priority + 0187 floor exemption; overrides union) | 0187 | — |
| 57 | `35aecd6f1` | 15.11 16:26 | Argon hospgate-0189 (fences: deck keepout 0208 + gate cut 0189) | 0189 | — |
| 58 | `8a99d4302` | 15.11 16:49 | 0214 DK65 tiles 06-11 (K1 cross-section, S19 construction sites) | 0214 | — |
| 59 | `f9781a32b` | 15.11 18:10 | #90 axleloads-tuning-0201b (verify-cloud-b SCAL: dotnet 277/277, runner 135/135) | 0201b | #90 |
| 60 | `5432820e3` | 15.11 18:28 | 0216 summer + white LED Knyszyn (EditMode 605/0 fail; sodium heads 0; lead viewed night A/B) | 0216 | — |
| 61 | `75c1e25f5` | 15.11 18:47 | research/cloud2-direction-signs-route-c (cloud D review s21: SCAL z erratą) | — | #62 |
| 62 | `b78ceca42` | 15.11 18:47 | research/cloud2-bialystok-building-typology (cloud D review s21: SCAL z erratą) | — | #64 |
| 63 | `629c4ffb9` | 15.11 18:47 | research/cloud2-pavements-kerbs (cloud D review s21: SCAL z erratą) | — | #65 |
| 64 | `5644c5c32` | 15.11 18:47 | research/cloud2-next-region-ring (cloud D review s21: SCAL z erratą) | — | #66 |
| 65 | `ace27ff70` | 15.11 18:47 | research/rooftop-gsm-s21 (cloud D review s21: SCAL z erratą) | — | #99 |
| 66 | `c2b9b702a` | 15.11 18:47 | reviews-0225 (cloud D review s21: SCAL z erratą) | 0225 | #105 |

Razem **66** commitów scalających. Statusy ADR bez zmian w treści plików ADR (np. `0187…md:2`, `0199…md:2`, `0201…md:2` nadal „PROPOSED”, „kandydat … nie scalone”, „Proposed …
Scalenie: lider”) — rozbieżność dokument vs historia gita (por. S20 R26).

## 8. Definition of Done — zmiany od S20 §7

| Element DoD | s20/s21 | Braki (dowód) |
|---|---|---|
| Kompiluje się na Androidzie | czysty APK `af2570fccd` (`GATE-3.md:131`); EditMode po 0216: 605/0 fail (`HANDOVER.md:184`) | brak APK po `af2570fcc` |
| testy zielone | pytest gis 1373/1375 po regen4 (`HANDOVER.md:169`); dotnet 277/277 (`VERIFY-…-0201b.md:9`) | **2 FAIL budżetu High** (`HANDOVER.md:170-171`); CI `gis` na main czerwone na 3 znanych testach (test_forest_0187, test_road_fidelity::test_report_not_stale, test_world_v31::test_frame_budget_with_forest_hlod — preambuła zadań chmury D r2) |
| budżet wydajności nie pogorszony | G3 A16 `af2570fccd` w budżecie (§1) | stan po `af2570fcc` niezmierzony; GPU p95 > 33,3 ms; PSS G3-B +56 MB vs `77cfd94bf8` |
| review innego agenta | recenzje Argon, chmur B/C/D (`docs/reports/REVIEW-2026-11-15-*`, `VERIFY-2026-11-15-*`) | nadal brak recenzji `GATE-1.md`/`GATE-2.md`/`GATE12-PHONE…` i zrzutów `af2570fccd` |
| docs/ADR | GATE-3 dopisany (`6624550e4`) | GATE-0/1/2 nieaktualne (S20 §7); statusy ADR scalonych w s20/s21 nadal „Proposed” (§7) |
| commit / tag | — | po bramce 3 nadal tylko tag `v0.0-gate0` (S20 §5 pkt 6) |

## 9. Komendy dla lidera (kolejność wg `HANDOVER.md:190` i D67/D68)

```
# po scaleniu budget-fix-s21 (0221) i regeneracji C+D z latem (D68): pytest budżetu
uv run --project tools/worldgen python -m pytest tests/gis -k "hero_bridge or frame_budget" -q
pwsh scripts/test.ps1 -Platform EditMode
pwsh scripts/build-android.ps1                                   # -> artifacts/apk/kamion-<ver>-<sha>.apk (czysty)
pwsh scripts/gate3-run.ps1 -Serial RFGL34SJYDZ -Tier Low -Fps 30 -SkipBuild -Apk artifacts/apk/kamion-0.1.0-<sha>.apk              # G3-A
pwsh scripts/gate3-run.ps1 -Serial RFGL34SJYDZ -Tier Low -Fps 30 -SkipBuild -Apk artifacts/apk/kamion-0.1.0-<sha>.apk -Segment B   # G3-B
uv run --project tools/perf python tools/perf/p99_spikes.py --summary 20261115-141511 20261115-145242 <ts-A> <ts-B>                # > 40 ms (W1)
& ./scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-0.1.0-<sha>.apk -UseExistingLock -Only @('s080_solo_1','s080_solo_2','s080_solo_3','s080_empty','s080_40t')  # po 0201b
pwsh scripts/device-metrics.ps1 -Serial RFGL34SJYDZ -Launch -DurationSeconds 90 -Tier Low -Fps 30
```
Parametry jak w S20 (`scripts/gate3-run.ps1:25-49`, `scripts/gate12-phone.ps1:33-45`; lista `-Only` tylko w formie `& … @(...)`). APK z korytarzem:
po scaleniu #104 — komenda z opisu PR #104 (`-Regions`), nie podaję jej tu, bo nie ma jej na main.
