# ADR 0160 — G3-A: P0 układu kadrów i kotwice pierwszego planu (pozy, tablice, znaki)
Status: Proposed (agent g3a-0160, s16, gałąź `g3a-0160`), 2026-11-13. Gałąź zawiera main + `barriers-0159` @ 43d879f4b
(ADR 0159) i świat przebudowany z obu zmian (regen2); do scalenia przez lidera po 0159 albo razem z nią.

## Kontekst
Recenzja `docs/reports/visual/REVIEW-2026-11-13-s16-world-int.md` (D51): G3-A 5 R / 15 P / 2 N. P0: `cm109685822`,
`cm92458760` (G3-A) i `339463` (G3-B) pokazują inny układ niż zdjęcie. P1: brak kotwic pierwszego planu pod wiaduktem
Bieżeństwa (zielone tablice, wyspy żwirowe, podpory, bariery), brak A-30 (275528), sygnalizatorów (182011), D-1 (4312632),
A-7 (1528935). Pytanie: winna jest poza kamery czy świat?

## Metoda (dowody, bez zgadywania)
1. **Widok z góry świata vs ortofoto GUGiK vs OSM** (`artifacts/g3a-0160/tools/glbtop.py`): rasteryzacja chunków GLB
   (lod0, kolor wg materiału) obok wycinka ortofoto 0,25 m i grafu dróg, z ostrosłupem kamery (`probes/gt_*.png`).
2. **Sondy póz** (`probes.py`, `plan_r1..r3.py`, `render.ps1`): kandydaci w jednym przebiegu Unity (Low, overcast),
   arkusze zdjęcie | sondy (`probes/r*/sheet-*.jpg`). Wybór po kotwicach zapisanych w `choice.json`.
3. **Resekcja**: (a) cm92458760 — dwa kominy EC (OSM 628899553/4) na x 0,773 i 0,947 zdjęcia, 11,1° rozstawu przy hfov 70;
   (b) seria richlv 2020-08-15 pod wiaduktem — heading z punktu zbiegu pomostu (oś 298,6°, poprawka na pochylenie 18–22°),
   pozycja z podpór (`resect.py`, `resect2.py`; wieloznaczne, więc rozstrzygane sondami).
4. Zapis: `sbs_authored_overrides.json` (east/north_delta, heading_delta, eye, horizon, hfov) → wpisy `sbs_cameras.json`
   i `sbs_references.json` liczone tym samym wzorem co `sbs_gate3.prepare()` (`finalize.py`; sonda == produkcja < 2 mm,
   `verify_all()` bez rozbieżności). Wszystko WORKING_VALUE, nie pomiar w terenie.

## Przyczyny P0
| Kadr | Przyczyna | Dowód | Poprawka |
|---|---|---|---|
| 339463 (G3-B) | **poza** | punkt SfM Mapillary na chodniku przy przystanku, 8,1 m od osi trunk_link w173956083, po drugiej stronie ekranu | prawy pas trunk_link (1,5 m od osi, 92 m od węzła 2840742310), heading = styczna, eye 1,5; B |
| cm92458760 | **poza** | geotag Commons w pełnych sekundach (53°09'10", 23°10'06"), ok. 150 m od miejsca; rozstaw kominów 11,1° pasuje tylko na skrzyżowaniu Bitwy Białostockiej / wjazd EC (tablica ulicy na zdjęciu) | E 542 N -750, heading 134 (siatka), hfov 70, eye 1,5 (okno pojazdu); B; kadr kontekstowy 57,5 m od trasy G3-A |
| cm109685822 | **poza + świat** | heading 40° (zgadnięty) zamiast ~34°, punkt 13 m od jezdni w środku parkingu; po korekcie układ zgodny, ale świat ma plac `yard_behaton` w miejscu trawnika i chodnika | zachodni chodnik gałęzi w194536287, heading 34, hfov 70, eye 1,6; C do poprawki świata |

3/3 P0 to błąd pozy, 1/3 dodatkowo świat. Żaden P0 nie wymaga przebudowy dróg.

## Kotwice pierwszego planu
| Kotwica (kadr) | W danych? | Dlaczego nie było w kadrze | Działanie |
|---|---|---|---|
| podpora z czerwonym pasem 177786 | tak (kolumna 570,1/-717,5) | poza (heading 313 zamiast 321, kamera 5 m obok) | poza: podpora x 0,2–0,3 (zdjęcie 0,15–0,35), wieżowiec x 0,83 (0,82) |
| bariera W + podpora 1259231 | tak / tak | poza (heading 235 → 250, eye 1,7 → 0,9) | bariera na pierwszym planie; podpora nadal poza lewą krawędzią — C |
| tablica nazwy ronda 201270 / 3970163 / 2818555 / 149248 | tak (override north) | poza (heading SfM +9…+15° w całej serii richlv) **i** dane: punkt ADR 0125 czytany z błędnych póz | heading z VP pomostu, eye 0,9; tablica +6,2 m E (556,4/-699,4) z trzech klatek (rozrzut ≤ 1,2 m) |
| bliska tablica z lewej 504348 | tak (override east 567,1/-704,2) | poza: kamera produkcyjna miała tę tablicę na osi kadru (na zdjęciu jej tam nie ma) | sonda r4: kamera 3,5 m od tablicy wschodniej w azymucie 250, heading z VP pomostu; tablica x 0–0,16 (zdjęcie 0–0,15); B |
| wyspy żwirowe 149248 / 2818555 / 504348 / 3970163 / 201270 | tak (`island_gravel`, ADR 0144) | poza: kamera stała na jezdni pierścienia (eye 1,7) | po korekcie jasny żwir na pierwszym planie; materiał bez zmian |
| A-30 ×2 275528 | tak (`andersa-gantry-warning-*`) | dane: 9 m przed portalem i 8,6 m w bok = poza kadrem 90° | `at_en` z kadru czołowego (portal 15,2 m, zgodność ze światem 0,1 m): E -262,18 N -215,59 i E -255,26 N -205,84 |
| sygnalizatory na wysięgnikach 182011 | tak (`signal_mast` n1847044961, n4075461271) | poza (J1); sondy r3 pod wiaduktem nie trafiły | nierozwiązane, C |
| D-1 4312632 | **nie** (reguła stawia D-1 tylko przy skrzyżowaniach z niższą klasą) | brak danych + poza | poza B (trunk_link, heading styczna -63, eye 0,9); nowy `gate3_sign` andersa-link-median-d1 |
| A-7 1528935 | **nie** (brak OSM give_way na włączeniu łącznicy) | brak danych + poza (kamera po stronie Andersa za klinem) | poza B (pas łącznicy w268473388); nowy `gate3_sign` andersa-slip-merge-a7; face A-7 w `gate3_landmarks.py` |

## Zmiany
- `sbs_authored_overrides.json` (+ `sbs_cameras.json`, `sbs_references.json`): 339463, cm92458760, cm109685822, 2818555,
  3970163, 201270, 504348, 149248, 177786, 1259231, 1528935, 4312632.
- `overrides.yaml`: biezenstwa-street-name-north (+6,2 m E), andersa-gantry-warning-left/right (`at_en`), nowe
  andersa-slip-merge-a7 i andersa-link-median-d1.
- `tools/worldgen/streetscape/gate3_landmarks.py`: face A-7 (trójkąt ostrzem w dół, bok 0,9 m = `SIGN_SIZE["triangle"]`).
- `tests/gis/test_sbs_gate3.py`: 339463 poza J1; cm92458760 kadr kontekstowy 40–80 m od trasy. `tests/gis/test_sbs_*.py`: 91 passed.
- Render par na świecie **regen1** (tablica north już przesunięta; A-30 `at_en`, A-7, D-1 jeszcze niezbudowane —
  przerwane przy 72 % limitu). Tylko Low-overcast, preflight pominięty świadomie. `test_gate3_landmarks::test_every_gate3_sign_is_placed`
  przejdzie dopiero po przebudowie świata z bieżącym `overrides.yaml`.

## Ocena 22 par G3-A (przed → po)
Samoocena agenta (nie krytyk), Low-overcast; przed = render world-int s16, po = `artifacts/g3a-0160/pairs/`.
Kadry bez zmiany pozy oceniono jak w recenzji s16.

| Kadr | przed | po | uzasadnienie |
|---|---|---|---|
| cm92458760 | N | **P** | kominy x 0,77/0,94, słup, wiadukt z lewej, przejście; brak klombu, niebieskich budynków EC, zbiornika, znaków |
| cm109685822 | N | **P** | droga w prawo, hala z czerwonym pasem, budynek z prawej; plac z kostki zamiast trawnika i chodnika (świat) |
| 201270 | P | **R** | tablica nazwy z lewej na pierwszym planie, bariera, żwir, pomost |
| 3970163 | P | **R** | tablica x 0,5 jak na zdjęciu, żwir, krawężnik |
| 2818555 | P | **R** | tablica x 0,55 (zdjęcie 0,56), żwir |
| 149248 | P | **R** | fałszywa bliska tablica zniknęła, żwir, pomost |
| 177786 | P | **R** | dominująca podpora z czerwonym pasem, wieżowiec; P2 brak bariery na pierwszym planie |
| 504348 | P | **R** | (regen2 + sonda r4) bliska tablica nazwy na lewej krawędzi, pomost, żwir, łuk w prawo; P2 pomost dalej niż na zdjęciu |
| 1259231 | P | P | bariera W na pierwszym planie; podpora poza kadrem |
| 1398898, 178689, 320326, 482392, 500263 | R | R | bez zmian |
| 1406533, 223210, 2948595, 303305, 309664, 320215, 454716, 751431 | P | P | bez zmian (horyzont bloków, latarnie, ściana oporowa — poza zakresem) |
| **Razem G3-A (22)** | **5 R / 15 P / 2 N** | **11 R / 11 P / 0 N** | regen1: 10 R / 12 P; regen2 bez regresji, +504348 |

G3-B: 339463 N → P (ekran z prawej, wiadukt z lewej, portal na osi; brak strzałek na jezdni i drzew w pasie dzielącym);
1528935 i 4312632 nowe pozy B, znaki A-7/D-1 do obejrzenia po przebudowie.

## Do zrobienia w świecie (dla 0159 / lidera)
- cm109685822: `yard_behaton` Kwadrat Park obejmuje pas trawnika i chodnik wzdłuż zachodniej krawędzi gałęzi w194536287
  (E ~595–605, N -600…-640); budynek po prawej to granatowy 2-kond. z przeszklonym parterem (render: beżowy 3-kond.).
- cm92458760: klomb na wyspie przy wjeździe do EC, niebieskie budynki EC, zbiornik, D-6 i tablica „ul. Bitwy Białostockiej”.
- 339463: strzałki kierunkowe na trunk_link przed skrzyżowaniem, drzewa w pasie dzielącym.
- 4312632: pod pomostem czarne płyty zamiast podpór i prześwitu (ekrany/ściany — 0159).
- Pozy C do dalszej kalibracji: 1259231, 182011.
- 149248: tablica nazwy ronda ok. 3x za duża względem zdjęcia (kamera za blisko tablicy wschodniej albo na zdjęciu widać
  tylko tablicę północną) — do rozstrzygnięcia przy następnej kalibracji serii richlv.
- 4312632: D-1 stoi w miejscu ze zdjęcia (x 0,33), ale tarcza widoczna niemal z boku (zdjęcie: ok. 45°) — obrót tarczy
  przy pasie dzielącym do sprawdzenia (`travel_bearing_deg` 312,8 z osi łącznika).

## Walidacja (regen2, 2026-11-13)
Drzewo: main @ ede13f874 + `barriers-0159` @ 43d879f4b + ta gałąź; `build_world` 767 s, road consistency 65 (jak 0159),
import 64 chunki Low+High, `sbs_pairs.py preflight` OK. Pary: `scripts/sbs-low-pairs.ps1` Low overcast + clear, 42 kadry,
przed = `artifacts/world-int-s16/sbs`; kopie <= 960 px: `artifacts/g3a-0160/pairs-final/` (repo główne). 504348 w parach =
render sondy r4 e35a (ta sama poza co produkcja, różnica < 2 mm, `finalize.py` + `verify_all()` bez rozbieżności).

| Sprawdzenie | Wynik |
|---|---|
| A-30 ×2 (275528) w kadrze | tak: x 0,17 i 0,82 (zdjęcie 0,22 i 0,82), wysokość jak na zdjęciu |
| A-7 (1528935) w kadrze | tak: x 0,54 (zdjęcie 0,61), żółty trójkąt z czerwonym obrzeżem ostrzem w dół |
| D-1 (4312632) w kadrze | tak: x 0,33 (zdjęcie 0,33); tarcza prawie z boku — Open |
| `test_gate3_landmarks.py` | 13 passed (w tym `test_every_gate3_sign_is_placed`) |
| `tests/gis/test_sbs_*.py` po 504348 | 91 passed |
| `tests/gis` całość | PYTEST_GIS |
| EditMode | 467 / 467 passed |
| Budżet Low-clear, kamery kontrolne vs main (world-int-s16) | max +2 draws (route-putry-approach), max +1,0 % tris (route-putry-entry-signs); vs 0159 after3: +3 draws, +0,3 % tris |

Samoocena agenta, nie `visual-critic`. G3-B: 339463 P (bez zmian względem regen1), 275528 A-30 obecne, 1528935 i
4312632 P (znaki są, układ jezdni / roślinność odbiegają).

## Open
- Ocena niezależna (`visual-critic`) 22 + 1 par z `pairs-final/`.
- Pozy C: 1259231 (podpora poza lewą krawędzią), 182011 (sygnalizatory na wysięgnikach — w świecie, poza kadrem).
- 149248: tablica ok. 3x za duża; 4312632: obrót tarczy D-1; cm109685822 plac `yard_behaton` zamiast trawnika
  i chodnika; cm92458760 klomb / budynki EC (lista „Do zrobienia w świecie”).

## Konsekwencje
- Seria richlv ma systematyczny błąd SfM heading +8…+15°; eye 0,9 jak w ADR 0143.
- Kotwice obecne w świecie, ale poza kadrem, nie wymagały przebudowy (podpora 177786, sygnalizatory 182011, żwir).
- Nowe znaki są danymi (`kind: gate3_sign`) i przeżywają reimport.
