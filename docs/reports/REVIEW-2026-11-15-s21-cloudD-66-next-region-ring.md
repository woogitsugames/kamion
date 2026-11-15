# Przegląd PR #66 — R9 next-region-ring (dane dla następnego regionu), po FIX — s21 cloud D, 2026-11-15

**Werdykt: SCAL z erratą.** Wszystkie 4 punkty FIX z przeglądu s20 (`REVIEW-2026-11-14-s20-cloud2-r9.md` §6) są wykonane:
- **F1:** User-Agent jest ogólny, 0 trafień „kamion” w skryptach.
- **F2:** klasy niższe i budynki wpisane jako ESTIMATED z pomiaru recenzenta, 1:1 z §4.
- **F3:** Commons dla 24 z 24 punktów; L03/L19/L23 odtworzyłem dziś co do sztuki.
- **F4:** opis PR spójny z README.

**11 z 11 obejrzanych kadrów ma opis zgodny z obrazem.** Errata dotyczy:
- zdjęć w gicie (9,7 MB);
- jednego kadru niezwiązanego z drogą (PX33, wnętrze kawiarni);
- rozbieżności PX30 z R2-083 (#62), którą trzeba odnotować.

- Gałąź `origin/research/cloud2-next-region-ring` @ `a6bc9922a`. Commity FIX: `1dff923fd`, `2ff367b91`, `c58117deb`, `a6bc9922a`. Baza `81c9baee7`, 612 commitów za `origin/main`.
- `git diff --stat origin/main...`: 106 plików (+154 508 linii), wszystkie w `research/cloud2/next-region-ring/` ✓.
- Manifest: 401 wierszy (było 371), id R9-001…371 bez zmian, nowe od R9-372. Wewnętrzny `REVIEW.md` po FIX: PASS z uwagami P2.

## 1. Punkty FIX (s20 §6) i kryteria R9
| Pkt | Wymóg | Wynik | Dowód recenzenta |
|---|---|---|---|
| F1 (P1) | UA bez nazwy projektu w 7 skryptach + notatka w `sources.md` | **TAK** | `grep -rni kamion fetch.py tools/` daje 0. UA `research-fetch/1.0` / `research-fetch/1.0 (generic)` w `fetch.py`, `audit.py`, `audit_fix.py`, `commons_landmarks.py`, `gugik_skorowidze.py`. Notatka „Poprawki 2026-11-15” jest w `sources.md` |
| F2 (P1) | klasy < primary i budynki (Overpass albo pomiar recenzenta jako ESTIMATED) | **TAK (ESTIMATED)** | R9-394…400: secondary 148,0 / tertiary 252,1 / unclassified 189,5 / residential 948,3 / living_street 133,8 / service 912,8 / track 864,1 km. R9-401: 83 505 budynków. Wszystko zgodne z s20 §4. Metoda opisana. Overpass ponowiony, mirror zwracał 504 (uczciwie zgłoszone) |
| F3 (P1) | Commons 24/24 z obsługą `error`/429, ≥ 1 plik na L03/L19/L23 z licencją | **TAK** | §3: L03 = 82, L19 = 10, L23 = 363, identycznie jak w manifeście. 5 plików (CM01–CM05) obejrzanych, licencje CC0 / CC BY-SA 4.0. **Mój pierwszy strzał dla L03 dostał odpowiedź z `error` (429)**, co potwierdza, że stare zera były artefaktem |
| F4 (P2) | opis PR: 3 punkty bez kadru | **TAK** | opis PR i README §7: L03, L19, L23 |
| — | OSM, GUGiK, zdjęcia, punkty do bramki, raport planistyczny | **TAK** | bez zmian względem s20 (wtedy TAK), plus §4a i §6 |
| — | zdjęć nie commitować | **NIE** | `.gitignore`: `!files/jpg1600/`, `!files/commons/`. 39 + 5 plików, 9,7 MB. PX31 to duplikat PX26 (oznaczony) |
| — | tylko własny katalog | **TAK** | — |

## 2. Obejrzane obrazy (11, każdy osobno ≤ 960 px)
| Kadr | Licencja | Ocena opisu |
|---|---|---|
| CM01 `20240501_124520 … Choroszcz` (R9-389) | CC0, Rakoon | ✓ zdjęcie przez szybę z odbiciami, wysoka trawa, ogrodzenie z jasnych paneli, hale (jedna z niebieskim pasem), brzozy, ścieżka czerwonawa (poprawione w FIX). Bramownic poboru opłat **nie widać** ✓ |
| CM02 `20250520_152809` (R9-390) | CC0 | ✓ bramownica kratowa z pomostem, zielona tablica „…CZAS OCZEKIWANIA / PRZEJŚCIA GRANICZNE / Bobrowniki / Kuźnica / Kukuryki” z polami czasu, bariery, roboty ziemne z koparką (marka na maszynie, nieprzenoszona do opisu) |
| CM03 most DK65 k. Dzikich (R9-391) | CC BY-SA 4.0, Athantor | ✓ rzeka, trawiaste brzegi, kratowy most kolejowy w głębi. Mostów S19 brak |
| CM04 `20200508_145754` (R9-392) | CC BY-SA 4.0, Rakoon | ✓ asfalt z linią przerywaną, krawężnik, wyspa z otoczakami i trawą, łukowa jezdnia z balustradami na innym poziomie, mała zielona tablica, biało-czerwone tablice; portalu tunelu nie widać |
| CM05 `20200805_130930` (R9-393) | CC0 | ✓ **czerwona asfaltowa DDR** z osią i piktogramami przy rondzie al. Niepodległości, chodnik z kostki, wyspa z krzewami i żwirem, bloki 5–6 kondygnacji |
| PX21 2d6cc10e (R9-329) | CC-BY-SA-4.0, stanton | ✓ niebieski łuk stalowy z wieszakami nad jezdniami, trawiasta skarpa z ogrodzeniem, latarnie |
| PX24 d5b3de31 (R9-332) | CC-BY-SA-4.0 | ✓ kładka belkowa z pochylnią, wysokie przezroczyste ekrany na zielonych słupach z odbiciem budynku, pylon stacji paliw (marki w opisie brak ✓) |
| PX30 25d2b4ca (R9-338) | CC-BY-SA-4.0 | ✓ obiekt z barierą z poręczą, czerwonawa nawierzchnia chodnika technicznego, wysięgnik kratowy z tablicą „← Dziesięcin…”, D-2 przekreślony (koniec drogi z pierwszeństwem) |
| PX33 4d84fb34 (R9-341) | CC-BY-SA-4.0, mapcomplete | ✓ wnętrze kawiarni. Opis uczciwy („brak obiektów drogowych”), ale kadr nie wnosi nic do R9, a leży w repo (errata E2) |
| KV05 (R9-346) | CC BY-SA 4.0 (KartaView) | ✓ jeden pas z poboczem, niebieska tablica ze schematem ronda, znakiem ostrzegawczym i zakazem ciężarówek, bramownica z tablicą VMS w głębi, pomarańczowy baner (marka, nieodtwarzana) |
| KV06 (R9-347) | CC BY-SA 4.0 | ✓ jednojezdniowa z podwójną ciągłą, brązowy ekran z poziomych żłobkowanych paneli, siatka na ukośnych słupach, las, pod słońce |

Zgodność **11/11**. W s20 obejrzano 11 innych kadrów (PX02, 05, 08, 14, 17, 18, 20, 26, 29, KV03, KV04), wszystkie zgodne. Razem 22 z 43 kadrów pakietu przeszły przegląd lidera.

## 3. Liczby sprawdzone u źródła (6 nowych + 8 wierszy F2)
- **Commons geosearch** (r = 1 km, `gslimit=500`, 2026-11-15): L19 = **10** ✓, L23 = **363** ✓, L03 = **82** ✓ (za drugim podejściem, bo pierwsze zwróciło `error`).
- **GUGiK HEAD:** `LOD1/2024/20/2002.zip` ma Content-Length **23 868 560** ✓ (R9-215). Last-Modified to 26.03.2025; manifest podaje rozmiar, nie datę.
- **UA:** grep 0 trafień „kamion”, 6 miejsc z `research-fetch/1.0` ✓.
- **F2:** 8 wierszy R9-394…401 zgodnych z tabelą s20 §4 (wartości i metoda). Status ESTIMATED jest poprawny, bo źródło jest jedno.

SOURCED / ESTIMATED: manifest ma ESTIMATED 254, SOURCED 144, UNVERIFIED 1, WORKING_VALUE 2. Nie znalazłem liczby bez statusu.

## 4. Wnioski dla gry i planu regionu (plik, liczba)
| Temat | Wniosek | Działanie |
|---|---|---|
| Nazwa i zakres (s20) | „Ring S8” nie istnieje. S8 kończy się na węźle Białystok Zachód, dalej jest DK8 trunk | `docs/03` i HANDOVER: „obrzeża: S8 Choroszcz–Białystok Zachód, S19, Trasa Generalska, DK8/19 N” |
| Paczka GUGiK | powiat **2002**: BDOT10k 90,3 MB, LoD1 2024 23,9 MB (HEAD ✓), LoD2 34,1 MB. **Nie pobierać** Drzewa3D (45,8 GB) | geo-worldgen: `Data/SourceManifests/gugik-*-2002.json` na wzór 2061 |
| Wysokości budynków | OSM `height` 0,3 %, `building:levels` 22,9 % z 83 505 (ESTIMATED) | LoD1 2024 jako źródło H, tak jak w C i Dojlidach (`tools/worldgen/buildings.py`) |
| Drogi niższe | `width` ≈ 0 %. `lanes`: secondary 97 %, tertiary 44 %, residential 5 % | szerokości z `standards.py`, oświetlenie z `highway=street_lamp` |
| **DDR poza C i Dojlidami** | CM05: **czerwona** asfaltowa DDR przy al. Niepodległości (DW669, L23) | ADR 0188 ogranicza czerwień do 11 way w C. W następnym regionie kolor DDR weryfikować per odcinek (ortofoto/kadr), bez domyślnej szarości z Dojlid |
| Tablice graniczne | CM02: bramownica z czasem oczekiwania na przejściach (Bobrowniki / Kuźnica / Kukuryki) przy S8 | kandydat na obiekt rozpoznawalny bramki regionu (VMS jako tekstura statyczna, jak `tysiaclecia-its-vms-gantry`) |
| **Rozbieżność z R2 (#62)** | PX30 (2019, Maczka W): „**←** Dziesięcin…” na wysięgniku. R2-083 (KartaView 2021): „Dziesięciny **↗**” (białe pole) na bramownicy | P2: to raczej dwie różne tablice albo zmiana 2019→2021. Przed override w regionie `bialystok-maczka` sprawdzić ortofoto i kadr ≥ 2024 |
| Kamery kontrolne | azymut API PX17–19 odbiega o ponad 50° (s20) | brać kurs z toru |

## 5. Errata (przy scaleniu, nie blokuje)
1. **E1 (proces, decyzja lidera):** zdjęcia w gicie (`files/jpg1600/` 39 plików, `files/commons/` 5 plików, 9,7 MB), wbrew CLOUD2-PROMPT. Do wyboru `git rm -r --cached` obu katalogów (oryginały pobiera `fetch.py`) albo świadoma akceptacja.
2. **E2:** PX33 (wnętrze kawiarni, MapComplete) należy usunąć z `files/jpg1600/` i oznaczyć w manifeście „odrzucony — nie dotyczy drogi”. Nie ma powodu trzymać w repo zdjęcia wnętrza lokalu.
3. **E3:** README §6 lub wiersz R9-338: dopisać „por. R2-083 (#62): w 2021 ta sama relacja ze strzałką ↗, do weryfikacji”.
4. **E4 (z s20 §7, bez zmian):** `overpass/*.json` (2,6 MB). Lider może przenieść je do `files/` przy scaleniu, jeśli `build_manifest.py` dostanie ścieżkę.

## 6. Dla lidera
- **Scalić PR #66.** FIX jest kompletny. E1 i E2 rozstrzygnąć przy scaleniu (E2 to `git rm` jednego pliku i zmiana statusu R9-341).
- Plan regionu: wnioski z sekcji 4 (nazwa, paczka GUGiK 2002, kolor DDR per odcinek, VMS graniczny). Mapillary (token lidera) dla L03, L19 i L23 nadal potrzebne.
