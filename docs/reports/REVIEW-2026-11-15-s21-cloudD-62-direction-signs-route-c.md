# Przegląd PR #62 — R2 direction-signs-route-c (tablice kierunkowe E-* na trasie C) — s21 cloud D, 2026-11-15

**Werdykt: SCAL z erratą.** Mocne strony pakietu:
- **12 z 12 obrazów, które obejrzałem, ma opis zgodny z obrazem.** R2 poprawnie opisuje m.in. tył bramownicy nad przeciwną jezdnią (R2-010), w odróżnieniu od #42.
- Wszystkie 9 liczb sprawdzonych u źródła się zgadza (azymuty Panoramax, heading KartaView, tagi OSM).
- Cel „≥ 20 kadrów + Andersa” z bloku „Dokończenie” jest spełniony: 27 kadrów, 19 tablic/zespołów.

Braki:
- **Wymiary tablic** (wymóg R2) są UNVERIFIED. Częściowo zastępuje je R1 (sekcja 4 niżej).
- Kierunek SE Andersy oraz kierunek S Al. Tysiąclecia nie są obejrzane.
- **Zdjęcia są w gicie** (6,4 MB), wbrew zasadzie CLOUD2 „zdjęć nie commituj”.

Żadna z tych rzeczy nie podważa danych. Erratę opisuje sekcja 5.

- Gałąź `origin/research/cloud2-direction-signs-route-c` @ `b73baa177`. Baza `81c9baee7` jest 612 commitów za `origin/main`. `git diff --stat origin/main...` pokazuje 45 plików, wszystkie w `research/cloud2/direction-signs-route-c/` ✓.
- Manifest ma 83 wiersze: 27 kadrów, 19 tablic, 33 linie OSM `destination*` i 4 fakty OSM. Wewnętrzny `REVIEW.md` daje PASS z uwagami P2. Wcześniej lider tego PR nie przeglądał.

## 1. Kompletność (CLOUD2-PROMPT R2 + „Dokończenie”)
| Wymóg | Wynik | Dowód |
|---|---|---|
| Lokalizacje (OSM + zdjęcia) | **TAK** | Overpass z zapisanym zapytaniem i datą 2026-11-14T17:10Z. `traffic_sign=PL:E-*`: 0, `man_made=gantry`: 1. Pozycje = pozycje kadrów (uczciwie: „tablica przed kadrem”) |
| Treść i układ | **TAK** | 19 tablic/zespołów: Maczka → Putry (2019), Andersa NW (2021), Maczka W za Putry (2021), E-15/E-14 na wylocie N |
| Wymiary | **NIE** (UNVERIFIED) | brak pomiaru i normatywu. W `REVIEW.md` P2-1 odsyła do R1 |
| Sposób montażu | **TAK** | bramownice kratowe (2 słupy + rygiel), słupki, konstrukcja nad poboczem (R2-073) |
| Kamery kontrolne | **TAK** | `control_cameras_wgs84.json` (42 + 24 kamery, pyproj z origin `region.yaml`). Filtr „widzi lico” dla nowych tablic |
| ≥ 20 obejrzanych kadrów, ul. gen. Andersa | **TAK** | 12 Panoramax + 15 KartaView. Arkusze stykowe nie są liczone |
| Al. Tysiąclecia kier. S, rondo Bieżeństwa, Andersa SE | **NIE** | luki 1–3 w README, zgłoszone wprost |
| Samokontrola 20 % z obejrzeniem | **TAK** | seed 20261114: 12/57, 11 PASS / 1 FAIL. Seed 20261115: 6/26, 5 PASS / 1 FIX. W każdym wierszu obrazowym zapis „ponownie obejrzano …” |
| Licencje, Google, marki | **TAK** | Panoramax i KartaView CC BY-SA 4.0. Brak Google/Bing. Napisy firmowe oznaczone „nie odtwarzamy” |
| UA generyczny | **TAK** | `research-client/1.0` (`fetch.py`) |
| Zdjęć nie commitować | **NIE** | `files/kv_*.jpg` (15 × 1280 px) i `files/jpg1600/` (12 + `INDEX.csv`), razem 6,4 MB. `.gitignore` wyklucza tylko `files/pmx*.jpg` |
| Tylko własny katalog | **TAK** | diff jak wyżej |

## 2. Obejrzane obrazy (12, każdy osobno ≤ 960 px, 2 wycinki)
| Kadr (wiersz) | Licencja | Ocena opisu |
|---|---|---|
| kv 0211 (R2-058/073) | CC BY-SA 4.0 (KartaView) | ✓ E-1 nad wjazdem do wykopu: „19 Kuźnica PL BY / 65 Ełk / Warszawa”, białe „Centrum” w lewo, żółte „676 Krynki” w prawo, zielony oczep muru. Drobiazg: okrągły znak zakazu ciężarówek jest w **dolnej, środkowej części schematu**, a nie „na prawym ramieniu” (errata E2) |
| kv 0253 (R2-060/075) | jw. | ✓ bramownica kratowa: „↑ 19 Kuźnica / 65 Ełk” oraz „Os. Białostoczek / Centrum handlowe ↗”, małe tablice z „i” po obu stronach |
| kv 0258 (R2-061/076) | jw. | ✓ wjazd na estakadę, pole wyłączone, żółty słupek z C-9 (obok), E-1 schemat ronda na słupkach, „70” po obu stronach |
| kv 0303 (R2-066/079) | jw. | ✓ bramownica z jedną tablicą przeddrogowskazu w lewej części rygla: Warszawa/Ełk prosto, odgałęzienie w prawo Augustów/Kuźnica z polem żółtym i białym |
| kv 0306 (R2-067/080) | jw. | ✓ 2 tablice nad pasami, B-23 nad C-5 po obu stronach, żółte tablice, biała tablica na 2 słupkach |
| kv 0313 (R2-068/081) + wycinek | jw. | ✓ E-1 za przezroczystym ekranem na zielonych słupach. Na wycinku „8 E67 Warsza…/65 Ełk”, żółte pole i białe „Centrum” z ciemnym skreśleniem (czytelność graniczna, opis ostrożny ✓) |
| kv 0338 (R2-069/082) + wycinek | jw. | ✓ „8 E67 Warszawa / 65 Ełk” prosto, odgałęzienie do białego „Dziesięciny”. Po lewej słup z kamerą, w tle tył bramownicy nad przeciwną jezdnią |
| kv 0342 (R2-070/083) | jw. | ✓ dwie tablice na bramownicy (szczegół czytelny tylko w wycinku, nie sprawdzałem), po lewej tył bramownicy |
| pmx e11bd6e4 (R2-001/013/019) | CC-BY-SA-4.0 (API dziś) ✓ | ✓ E-1 na bramownicy: „Bobrowniki/Lublin” i „Augustów/Kuźnica”, żółty pas u dołu, żółta tablica objazdu, 3 tablice E-22 na 2 słupkach (brązowa „16 km Uzdrowisko Supraśl”). Zielone tło wygląda na turkusowe z powodu przebarwienia kamery 2019 |
| pmx 9f85aac8 (R2-005/016) | ✓ | ✓ 3 tablice pod estakadą, środkowa dwupolowa, prawa mała z żółtym polem. A-7 i roboty drogowe widoczne |
| pmx 6ded8ec0 (R2-008/017) | ✓ | ✓ E-15 „8 19 / E 67” po obu stronach, B-26 nad „70”, tył bramownicy po lewej, C-9 na wysepce |
| pmx 5f92573a (R2-011/018) | ✓ | ✓ E-14 na 2 słupkach, za daleko, by odczytać. Tło na kadrze wygląda na niebieskie, co R2 słusznie zostawia jako UNVERIFIED (P7-004 z 2024 pokazuje tę tablicę jako zieloną) |

## 3. Liczby sprawdzone u źródła (9)
- **Panoramax API** (`search?ids=`): e11bd6e4 ma `view:azimuth` 98, 2019-08-15T15:31:54Z, (23,14483; 53,15949); 6ded8ec0 ma 56; 9f85aac8 ma 98, przy czym w manifeście R2-005 `kierunek_deg` = 98 ✓. Rozbieżność azymutu API i kursu toru w R2-008…012 jest w manifeście opisana ✓.
- **OSM API 0.6:** node 11877183092 = `man_made=gantry` (53,1676547; 23,1479321) ✓. Way 173956079: `destination=Augustów Kuźnica;Centrum`, `destination:ref=8;19` ✓. Way 23982185: `Lublin;Bobrowniki PL/BY`, `19;65`, Maczka ✓.
- **KartaView API** (sekw. 3686129, strona 2): 1326673405 ma (53,145363; 23,18471), heading 299,71, 2021-06-23 10:33:23, ind. 211 ✓. 1326673573 ma heading 301,65, ind. 253 ✓.
- **sha256:** `kv_3686129_0211.jpg` = `b0336392…10c19c7`, zgodny z kolumną `sha256` R2-058. `jpg1600/pmx_e11bd6e4.jpg` zgodny z `INDEX.csv` ✓.

SOURCED / ESTIMATED: treści tablic mają status SOURCED (obraz). Kurs toru i odległość od ronda są oznaczone ESTIMATED, a wymiary, tło E-14 i stan 2026 UNVERIFIED. Nie znalazłem liczby bez statusu.

## 4. Wnioski dla gry (plik, liczba)
| Element | Gra dziś | R2 | Działanie |
|---|---|---|---|
| Bramownica Andersa przed rozwidleniem (`andersa-putry-approach-gantry`, `overrides.yaml` l. 371) | L: Warszawa/Ełk ↑↑; P: Augustów / Kuźnica PL BY / 675 Centrum ↗ (G3 2020/2024) | R2-080 (2021): ten sam układ, żółte pole i białe pole pod Augustów/Kuźnica | ✓ bez zmian. Niezależne potwierdzenie z 3. roku (2020, 2021, 2024) |
| E-1 przeddrogowskaz ~500 m przed Putry (R2-079, bramownica) | brak wpisu w `overrides.yaml`. Tablica E-1 może pochodzić z generatora (`streetscape_qa.json` → `route_checks` E-1 w j:n2629251371) | treść jak R2-079, montaż na bramownicy kratowej | **P2:** porównać kamerą `driver_andersa_to_putry` (8 m od R2-067). Jeśli generator stawia E-1 na słupkach, dodać override `sign_gantry` z treścią R2-079 (WORKING_VALUE stacja = kadr R2-066 + ~40 m, potwierdzić ortofoto) |
| E-1 na estakadzie ~240 m przed Putry (R2-081) | `andersa-putry-portal-p40`: 675 Centrum ← (G3 2024) | 2021: „Centrum” przekreślone | ✓ zostaje stan 2024. Stan 2021 był tymczasowy |
| Maczka W za Putry (R2-082/083) | region `bialystok-maczka`, brak override | Warszawa/Ełk ↑ + Dziesięciny ↗, 2 bramownice kratowe | P2 dla regionu Maczka: treść zgodna z OSM `destination` (Dziesięciny jest w `roads.graph.json`) |
| Wysokość wiersza tablicy (`tools/worldgen/streetscape/signs.py`, `overhead_board(row_m=0.62)`, WORKING_VALUE) | 0,62 m | R2: UNVERIFIED. **R1** (`research/cloud2/traffic-signs-catalog/README.md` §3.5): wiersz = 8 gr, d = 6 gr, największa grupa IX d = 420 mm | **P2, wniosek recenzenta (wyliczenie):** przy d ≤ 420 mm wiersz ≤ 8/6 × 420 = **560 mm**, więc 0,62 m wychodzi ok. 10 % ponad maksimum normy. Tabela 1.9 w R1 nie podaje grup dla E-*, dlatego grupa E-2 jest UNVERIFIED. Przy override z `size_m` z proporcji kadru (ADR 0162) zostaje proporcja kadru |
| Montaż E-1/E-2 | bramownice kratowe ✓ | wszystkie bramownice na trasie C są kratowe, szare (ocynk UNVERIFIED) | ✓. Dolna krawędź nad jezdnią ≥ 5,00 m (R1-246) jako test w `streetscape_qa` |
| E-15 „8 / 19 / E 67” na wylocie N (R2-017) | — | po obu stronach, na słupkach | kamery `route_putry_entry_signs` (62 m), `putry_above` (66 m): sprawdzić, czy E-15 stoją |

## 5. Errata (przy scaleniu albo w następnej paczce, nie blokuje)
1. **E1 (proces, decyzja lidera):** zdjęcia są w gicie (`files/kv_*.jpg` i `files/jpg1600/`, 6,4 MB), wbrew CLOUD2-PROMPT. Dwie drogi: (a) przy scaleniu `git rm -r --cached research/cloud2/direction-signs-route-c/files/kv_* research/cloud2/direction-signs-route-c/files/jpg1600` i do `.gitignore` dopisać `files/`, bo `fetch.py` i tak pobiera oryginały i sprawdza sha256; (b) świadomie przyjąć, bo `INDEX.csv` ma licencję, autora i sha256, a CC BY-SA wymaga atrybucji, która tam jest.
2. **E2:** R2-073 (i opis R2-058): „na prawym ramieniu znak zakazu ciężarówek” → „w dolnej, środkowej części schematu”.
3. **E3:** README, „Wymiary: UNVERIFIED” → dopisać odsyłacz do R1 §3.5 (proporcje gr, grupy liter) i §3.6 (dolna krawędź nad jezdnią ≥ 5,00 m, E poza obszarem zabudowanym ≥ 1,00 m).
4. **E4 (luki, następna paczka):** Andersa SE, sekwencja KartaView 2769366 (2019), Al. Tysiąclecia kier. S (Panoramax 989ab5f4), rondo Bieżeństwa. Odległość kadr → tablica zmierzyć na ortofoto GUGiK.

## 6. Dla lidera
- **Scalić PR #62** (diff tylko w katalogu pakietu, stara baza bez konfliktów). E1 rozstrzygnąć przy scaleniu.
- Do gry: dwa wnioski P2 z sekcji 4 (E-1 ~500 m przed Putry na bramownicy; `row_m` 0,62 vs ≤ 0,56 m z R1). Nie wymagają ADR, wystarczy override albo poprawka WORKING_VALUE z odnośnikiem do R1/R2.
