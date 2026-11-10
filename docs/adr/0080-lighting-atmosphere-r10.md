# ADR 0080: Oświetlenie i atmosfera świata r10 — pokład chmur, mgiełka przy ziemi, overcast kierunkowy, krzywa kontrastu do decyzji właściciela

Status: przyjęty — **decyzja właściciela 2026-11-10: wariant 3 „głęboki” dla overcast** (toe 0,9 / p 0,4 / pivot 0,6,
−0,2 EV), wdrożony w `LP_Overcast.asset` i `LightingPreset.CreateOvercast()`; clear bez zmian, mokro wyłączone
(rendering-perf, 2026-11-10). Liczby z renderów edytora (kamery kontrolne WorldC, 2340×1080);
**koszt na telefonie UNVERIFIED** (zakaz adb w tym zadaniu).

## Kontekst
Overcast w r9 wyglądał „mlecznie”: płaska kopuła nieba, brak ciemnych tonów, jednolite trawniki. Pomiar
`scripts/light-metrics.py` (luma Rec.709 na sRGB, %, średnia z kamer świata; kabina/ciężarówka pominięte):

| zestaw | p10 | p50 | p90 | sky_top | sky_hor | sky_sigma | trawa sat | trawa sigma |
|---|---|---|---|---|---|---|---|---|
| zdjęcia overcast, otwarte źródła (132 szt., pomiar poprzedniego agenta, STATUS.md) | 16,5 | 50,4 | – | – | – | – | 34,8 | 4,4 |
| zdjęcia, powtórny skan `Data/raw/refs` (106 kandydatów; zawiera też kafle orto, co zawyża p10) | 19,7 | 52,3 | 93,1 | 88,5 | 77,0 | 8,3 | 33,3 | 3,8 |
| main przed r10, High overcast (19 kamer) | 36,2 | 52,1 | 90,5 | 90,3 | 83,1 | 5,6 | 23,5 | 2,0 |

## Decyzje
1. **Pokład chmur w `Kamion/Sky`** (tekstura szumu; 2 / 3 / 5 próbek na piksel nieba wg `cloudQuality` 0/1/2 = Low /
   Medium i High / Ultra; `cloudsOff`, `rq_clouds=-1` = płaska kopuła). `cloudContrast` 0,21 (0,30 → 0,26 → 0,21: zdjęcia
   pełnego zachmurzenia w Białymstoku są prawie bez struktury, a ciemne plamy przy krzywej kontrastu wyglądały burzowo).
2. **Mgiełka przy ziemi** (`KamionAtmosphere.hlsl`): ekstynkcja `beta (1 + a exp(-(y - y0)/H))` całkowana analitycznie,
   głębokość optyczna per wierzchołek, jeden `exp` + `lerp` per piksel (jak dotychczasowy MixFog). Overcast: a = 1,6,
   H = 60 m. Wyłącznik: `groundHazeOff` / `rq_haze=0`.
3. **Overcast kierunkowy + przeciek słońca** (`overcastDirectional` 0,6, `overcastSunLeak` 0,05): miękki gradient jasności
   nieba i ledwie widoczne cienie zamiast zupełnie bezkierunkowego światła.
4. **Krzywa kontrastu („toe”)** `c' = g c (c + (1 - s) p) / (c + p)` (`LookGrading.Toe`): na tierach z post-processingiem
   wkomponowana w krzywą master LUT-u (bez dodatkowego kosztu), na Low liczona w shaderze (`KamionTone`, jedno dzielenie
   wektorowe per piksel). Overcast: wariant 3 (decyzja właściciela), pozostałe presety `lookToe = 0`.
5. **Mokra nawierzchnia** jako parametr (`wetness`, `rq_wet`), domyślnie 0. **Nie przeszła samokontroli** (patrz „Otwarte”).
6. **Zróżnicowanie trawników** (`grassVariation`): kępy ciemniejszej trawy i wypalone płaty z mapy makro; siła wypalenia
   zmniejszona w rundzie 2 (0,75 → 0,5).
7. **SSAO tylko Ultra**: osobny renderer `Mobile_Renderer_SSAO.asset` (generowany przez `SsaoRendererSetup.EnsureBatch`);
   Low/Medium/High zostają na rendererze bez dodatkowych przebiegów. WORKING_VALUE, niemierzone na flagowcu.

## Warianty krzywej dla overcast (przedstawione właścicielowi; wybrany: 3)
High overcast, 6 kamer świata, `artifacts/light-r10/owner/metrics.json`. Cel lidera: p10 ≤ 28.

| wariant | parametry (`rq_look`, `rq_ev`) | p10 | p50 | p90 | sky_top | trawa sat |
|---|---|---|---|---|---|---|
| 0 obecny | bez krzywej (`rq_look=0`) | 40,4 | 57,2 | 91,3 | 88,3 | 22,8 |
| 1 łagodny | toe 0,8 / p 0,30 / pivot 0,50 (`rq_look=3`) | 32,4 | 52,7 | 92,9 | 89,0 | 31,6 |
| 2 fotograficzny | toe 0,9 / p 0,40 / pivot 0,60 (`rq_look=4`) | 29,0 | 49,5 | 91,1 | 87,7 | 34,9 |
| 3 głęboki | jak 2 i −0,2 EV (`rq_look=4,rq_ev=-0.2`) | 26,2 | 45,1 | 87,3 | 85,6 | 35,4 |
| 2 na Low (toe w shaderze) | `rq_look=4` | 27,2 | 48,6 | 86,7 | 85,6 | 34,7 |

Odrzucone w sweepie (`artifacts/light-r10/sweep/`): stare B/C (toe 0,5 i 0,7 z małym p: p10 37 / 35) oraz samo obniżenie
ekspozycji (C −0,67 EV: p10 27,3, ale p50 43 i niebo szarzeje do 81 / 68 — niezgodne ze zdjęciami).

Rekomendacja agenta była „2” (p50 i niebo bliżej zdjęć); właściciel wybrał **3** — cel p10 ≤ 28 spełniony.
Reszty różnicy do zdjęć (p10 17–20) nie należy dociągać krzywą: wynika z braku okluzji i ciemnych obiektów w scenie.

## Stan końcowy po wdrożeniu wariantu 3
`artifacts/light-r10/final/{Low-overcast,High-overcast,High-clear}` (po 30 kamer), `final/metrics.json`.

| zestaw | kamery | p10 | p50 | p90 | sky_top | sky_hor | sky_sigma | trawa sat | trawa sigma |
|---|---|---|---|---|---|---|---|---|---|
| High overcast | 6 (jak w tabeli wariantów) | 26,1 | 45,1 | 87,3 | 85,6 | 77,7 | 7,7 | 35,5 | – |
| Low overcast | 6 | 24,4 | 44,3 | 83,0 | 82,6 | 71,5 | 5,9 | 35,4 | – |
| High overcast | 19 (wszystkie kamery świata) | 24,3 | 41,5 | 82,4 | 82,0 | 74,5 | 7,3 | 36,3 | 2,2 |
| Low overcast | 19 | 23,2 | 40,3 | 78,4 | 80,0 | 69,3 | 5,2 | 37,2 | 2,1 |
| High clear | 19 | 30,0 | 49,6 | 68,0 | 61,6 | 63,1 | 5,5 | 28,6 | 2,4 |
| main przed r10, High overcast | 19 | 36,2 | 52,1 | 90,5 | 90,3 | 83,1 | 5,6 | 23,5 | 2,0 |

Uwaga: p50 overcast (41,5 / 40,3 na 19 kamerach) jest ok. 10 pkt poniżej zdjęć (50–52) i niebo na Low schodzi do 80 / 69 —
to świadomy koszt wariantu 3.

## Kabina pod krzywą (uzupełnienie ADR 0044)
Krzywa świata ściągała wnętrze prawie do czerni (wzmocnienie toe przy 0 dąży do g (1 − s) = 0,16; pas deski w cab-dash:
66,5 % pikseli < 3 %). W widoku z kabiny powierzchnie wnętrza (`Kamion/Cab Interior`) i zegary (`Kamion/Cab Display`)
zapisują **przeciwobraz krzywej** (`KamionCabToeInverse`, postać zamknięta, jeden `sqrt` per piksel wnętrza), więc po LUT-cie
(High) albo `KamionTone` (Low) wnętrze ma wyświetlanie z ADR 0044 — jak telefon lokalnie podnoszący wnętrze pod światło.
Świat za szybą dostaje pełną krzywą. Siła: `CabInteriorLighting.toeCompensation` = 1 (WORKING_VALUE), A/B `rq_cabtoe=0..1`.
Odniesienie pomiaru kabiny (`CabMeterEv`) liczone bez biasu −0,2 EV, żeby lowsun/dusk nie zmieniły liftu.
Presety bez toe (clear): wektor zerowy = tożsamość.

Pas deski (dolne 22 % kadru), luma %, `artifacts/light-r10/cab/`:

| kamera | High ov. bez krzywej (r10) p10 / p50 | High ov. wariant 3 przed p10 / p50 / czarne < 3 % | High ov. po p10 / p50 / czarne | Low ov. po p10 / p50 / czarne |
|---|---|---|---|---|
| cab-dash | 4,7 / 8,6 | 2,0 / 2,4 / 66,5 % | 2,7 / 7,8 / 10,1 % | 3,1 / 8,2 / 8,6 % |
| cab-driver | 7,1 / 19,2 | 2,0 / 7,4 / 20,6 % | 5,9 / 16,8 / 1,8 % | 6,2 / 16,4 / 1,4 % |
| cab-gate | 7,0 / 25,1 | 2,0 / 11,8 / 14,8 % | 5,9 / 22,8 / 1,7 % | 5,9 / 22,8 / 1,4 % |
| cab-left | 11,0 / 31,3 | 3,1 / 17,3 / 7,9 % | 9,4 / 21,7 / 0,9 % | 9,8 / 18,3 / 0,8 % |
| cab-right | 8,2 / 13,6 | 2,4 / 3,9 / 29,3 % | 6,6 / 12,9 / 1,6 % | 7,5 / 12,2 / 1,7 % |

High clear: kamery cab-* identyczne z `rq_cabtoe=0` i bez (np. cab-dash 4,7 / 8,9, cab-gate 5,5 / 29,6) — brak zmiany, brak przepalenia.
Plansza: `artifacts/light-r10/cab/sheet-High.jpg`. Pas deski obejmuje też fragment świata za szybą (stąd niższe p50 w cab-left).

## Samokrytyka wg docs/06
- Wariant 0 nadal mleczny — bez krzywej overcast nie jest gotowy.
- Warianty 2 i 3 mocno przyciemniały wnętrze kabiny (`owner/montage/warianty_cab-driver.jpg`) — naprawione kompensacją
  w widoku z kabiny (sekcja wyżej). Z zewnątrz wnętrze kabiny dostaje pełną krzywą (ciemna szyba — zgodne z ADR 0044 r5).
- Wariant 3: zenit nieba na High miejscami ciemnoszary i plamisty (`final/sheet-High-overcast.jpg`), słupki A w kabinie
  prawie czarne, ciemne auta to bryły bez detalu.
- Ciemne lakiery aut gubią detal w 2/3 (auta = ADR 0078, inny agent).
- Chmury: struktura liczbowo blisko zdjęć (sigma 6,9–7,7 vs 8,3), ale kafel szumu daje miejscami ostre, ciemne plamy;
  ruch chmur oceniony tylko na klatkach nieruchomych.
- Trawniki: sigma 1,9–2,3 vs 3,8–4,4 na zdjęciach — wciąż zbyt jednolite.
- Mokro: FAIL. Asfalt w bliskim polu robi się jaśniejszy i gładki jak plastik, oznakowanie się zlewa
  (`owner/montage/mokro.jpg`); kostka prawie się nie zmienia. Nie włączać.

## Koszt
- Edytor (Low, 4 kamery, 60 klatek, `-TimeFrames`): włączone / wyłączone w granicach szumu pomiaru (identyczne ustawienia
  różnią się między przebiegami: stretch-01 wyłączone 8,1 i 7,8 ms, włączone 6,6 / 7,3 / 7,7 ms) — **brak wniosku**.
- Zmiana na piksel na Low: niebo +2 próbki tekstury (tylko piksele nieba), mgła bez zmiany liczby `exp`, toe +1 dzielenie
  wektorowe (liczone także przy `s = 0` — do wycięcia, jeśli pomiar pokaże koszt).
- Draw calle i trójkąty bez zmian (stats.txt przed/po identyczne dla tych samych kamer).
- **Pomiar na Samsungu A wymagany przed bramką**: `pwsh scripts/build-android.ps1 -Install -Run -Tier Low`, potem
  `device-metrics.ps1` A/B z `-e rq_clouds -1 -e rq_haze 0 -e rq_look 0`. `docs/PERFORMANCE_BUDGETS.md` bez zmian do pomiaru.

## Otwarte
Pomiar na telefonie (koszt nieba / toe / `sqrt` w kabinie na Low; wygląd kabiny na wyświetlaczu telefonu); mokra
nawierzchnia; SSAO Ultra na flagowcu; trawniki; siła `toeCompensation` do oceny właściciela w ruchu.
Testy: `LookToeTests` (toe, odwrotność = postać zamknięta shadera, preset = wariant 3, `FogTau`); EditMode 174/180 —
6 porażek to wskaźniki LFS zamiast FBX ciężarówki w worktree (niezwiązane ze zmianą).
