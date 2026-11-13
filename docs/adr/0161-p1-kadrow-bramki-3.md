# ADR 0161 — P1 kadrów bramki 3 (Putry, EC, wyjazd Kwadrat): świat + pozy

Status: Proposed (agent p1-0161, s16–s17, gałąź `p1-0161`), 2026-11-13. Do scalenia przez lidera; gałąź wyszła
z `origin/main` ff9777e2d (przed ADR 0164) — scalenie trywialne poza plikami `generated/` (przebudować świat po scaleniu).

## Kontekst
Recenzja s16b (`docs/reports/visual/REVIEW-2026-11-13-s16-world-int.md`, D51/D57: bramka 3 = rozpoznawalność) zostawiła
listę P1 w kadrach G3-A/G3-B: brak strzałek P-8 na łączniku do Ronda Putry (339463, 4312632), D-1 + A-7 w złym miejscu
(4312632), portal p40 zasłaniający kadr, brak sygnalizatorów na pierścieniu (182011), klomb i azyl przy wjeździe EC
(cm92458760), wyjazd Kwadrat za wąski i brukowany zamiast trawnika z chodnikiem (cm109685822), kapa mostowa jak bieżnia
(494288), głowice filarów jak jasny kołnierz (P2). Horyzont/drzewa = ADR 0163, budynki = ADR 0167 — poza zakresem.

## Decyzje (wszystkie jako `authored_overrides` w `Data/Regions/bialystok-industrial-c/overrides.yaml`, WORKING_VALUE)
| Problem | Zmiana | Źródło |
|---|---|---|
| P-8 na łączniku (339463, 4312632) | 11 strzałek `putry-link-p8-*` (L/R) | ortofoto GUGiK 0,25 m, Mapillary 339463/4312632 |
| D-1 + A-7 (4312632) | D-1 w pozycji z ortofoto, obrót 295°, A-7 pod spodem; tekstura zestawu | Mapillary 4312632 |
| portal p40 zasłania kadr | przesunięty 31 m (distance 86, `columns_en`) | ortofoto (fundamenty) |
| sygnalizatory na pierścieniu (182011) | `kind: gate3_signal` (nowy w `gate3_landmarks.py`) + wyspa `putry-ring-s-nose-island` | Mapillary 182011 |
| azyl i klomb przy EC (cm924) | `ec-access-plantings` (berberys) + brukowany azyl | Commons cm92458760, ortofoto |
| wyjazd Kwadrat (cm109) | `kwadrat-exit-carriageway-width`: 4,0 m przy szlabanie → 7,7 m za klinem, pas ruchu `lane_edges [0.25, 3.75]` od krawędzi lewej; `kwadrat-exit-verge-lawn` (`kind: unpaved_area`, nowy w `paved.py`) + `kwadrat-exit-footway` | ortofoto hr_cm109.png |
| kapa mostowa (494288) | `bridge_cap_red` x0,62 (ten sam odcień) w `build_world.py` | Mapillary 494288 (sRGB kapa/asfalt w cieniu ekranu) |
| głowice filarów (P2) | `hero_bridge.py`: głowica `pier_yellow` zamiast `bridge_concrete` (+2 linie) | CC0 7204_May_2021 |

Pozy 7 kadrów (`sbs_authored_overrides.json`, `tools/choice.json` → `finalize.py`): cm92458760, cm109685822, 962702,
1259231, 482392, 4312632, 182011 — wybrane z arkuszy sond r1/r2 (`artifacts/p1-0161/r1|r2/sheet-*.jpg`), pewność C.

## Zmiany w kodzie współdzielonym (konflikt z furn-0162 — minimalne)
- `furniture.py` `clear_carriageway`: +2 linie — słup postawiony autorsko na wyspie z krawężnikiem (wyspa leży na
  obrysie jezdni) nie jest odsuwany z jezdni (`pl.on_authored_island`).
- `hero_bridge.py`: kolor głowicy filaru (1 wywołanie `_prism`).
- `network.py` (s17): `lane_edges` razem z profilem szerokości (`width: [[t, w], ...]`) zachowuje najszerszą szerokość
  profilu (wcześniej `sec.width` spadało do ostatniej krawędzi pasa, 3,75 m).
- `paved.py`: `kind: unpaved_area` (trawnik wycina wszystkie źródła danych poza autorskimi; niewycinający nic = stale).

## lane_blind_end na wyjeździe Kwadrat (rozstrzygnięte)
b4: poszerzenie do 7,7 m samym profilem szerokości dawało układ jednopasowy z szerokości maksymalnej — przy szlabanie
(4,0 m) środek pasa był 1,85 m na prawo od osi jezdni i pas z placu wchodził w krawężnik: road consistency 66, na trasie
`lane_blind_end` 2 (main: 65 / 1). Poprawka: pas mierzony od lewej krawędzi (`lane_edges [0.25, 3.75]`) — przy szlabanie
wyśrodkowany jak wygenerowany, za klinem trzyma się lewej strony, a 3,95 m od krawężnika to pas parkowania z ortofoto.
b5: road consistency **65**, na trasie `lane_blind_end` **1** (bez regresji wobec main).
`test_ratchet_lanes` znów 25/25 zweryfikowanych (pas z `lane_edges` = prawda z ortofoto, ADR 0095);
`test_region_gate_cannot_be_driven_round` (szlaban depot) zielony — szlaban stoi w części 4,0 m.

## Weryfikacja
- Świat b5 (= b6 po zmianie samego `reason`): road consistency 65, `lane_blind_end` na trasie 1 (jak main).
- Import Low 122,3 MB / High 264,8 MB (`WORLD_MEMORY`), 64 chunki; ImpostorTrimBake 18 impostorów; EditMode 493/493.
- pytest `tests/gis`: PYTEST_FILL. Po drodze `test_measured_sections_have_evidence` wymagał ścieżki `xsec/` w
  `reason` — dowody (wycinki ortofoto `hr_cm109*.png`) skopiowane do `artifacts/p1-0161/xsec/`.
- Budżet Low (48 kamer kontrolnych, `visual-qa -Tier Low -Lighting clear`) wobec `artifacts/world-int-s16/after`:
  draws −252 … +6 (instancing z main), trójkąty −1,47 … +2,73 %, wyjątek `stretch-05-docks` +7,51 % (instancje
  188→220, +20 k trójkątów instancjonowanych; kamera poza strefą zmian 0161, przyczyna UNVERIFIED — prawdop. różnica
  main/trim impostorów; baseline ma trójkąty z dokładnością 1 k). `artifacts/p1-0161/final/budget-low.txt`.
- SBS Low overcast + clear: 42 pary x 2 (`artifacts/p1-0161/pairs/`). Obejrzane 9 kadrów P1: 339463 (P-8 widoczne,
  portal nie zasłania), 4312632 (D-1 + A-7 na miejscu; P-8 poza kadrem przy tej pozie), 182011 (sygnalizatory na
  pierścieniu), cm109685822 (trawnik + chodnik + jezdnia za klinem), cm92458760 (berberys + azyl — azyl wychodzi
  w kadrze zbyt duży i bez przejścia, poza pewnością pozy C), 494288 (kapa ciemniejsza, nie „bieżnia”), 962702,
  1259231, 482392 (filary/głowice). Ocena `visual-critic` — do zlecenia przez lidera (subagent nie tworzy subagentów).

## Epoka zdjęć (przegląd paczek badawczych 02, §5 „0161”)
Kadry 182011 (2019), 4312632 / 962702 / 1259231 / 482392 (2020) i cm92458760 (2020) są sprzed portalu C (2021) i
przebudowy Al. Tysiąclecia (2021/22). Sprawdzone: każda zmiana świata w tym ADR ma położenie z ortofoto GUGiK
(portal p40 — `hr_gantry.png`, sygnalizator — `hr_182a.png` z cieniem wysięgnika, P-8 / D-1, klomb, wyjazd Kwadrat),
zdjęcie służy tylko do rozpoznania obiektu; nic nie zostało przesunięte pod zdjęcie wbrew ortofoto. Oznakowanie
i zieleń w tych kadrach porównywać z G3 2024 / P10, nie z 2019–2020. Kadry Panoramax P1-NNN (az. w `manifest.csv`,
kamera ~1,3–1,5 m ESTIMATED) — nowe kamery kontrolne poza zakresem 0161 (otwarte, do lidera).

## Konsekwencje
- Pozy pewność C: przy nowych zdjęciach właściciela (D-list, brama Kwadrat) do ponownej resekcji.
- Szerokość wyjazdu Kwadrat przy bramie (realnie szersza) czeka na zdjęcia bramy (D-list poz. 1).
- Dla 0163: poligon drzew BDOT `bdot:2BE4B432-6BC0…` zasłania bloki w 303305/320215/454716; dla 0162: latarnia 1801374,
  znaki cm924 (F-10, D-6, tablica ulicy); dla 0167: biały budynek cm924 za wysoki, EC szary zamiast niebieskiego.
