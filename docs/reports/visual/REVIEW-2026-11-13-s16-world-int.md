# REVIEW 2026-11-13 s16 — integracja świata s16 (0141..0146, Mistral r4–r6), niezależna ocena D51

Krytyk: visual-critic (Opus). Materiał: `artifacts/world-int-s16/pairs/Low-clear|Low-overcast/` (42/42 pary, render `64628d9f38`),
pełna rozdzielczość `artifacts/world-int-s16/sbs/renders/`, porównania kamer kontrolnych `artifacts/world-int-s16/cmp/` (11).
Baseline: `artifacts/sbs-poses-r2/after/pairs` (main `565c317d0e`), `artifacts/putry-andersa/after4/pairs` (gałąź 0146).
Kryterium: D51 (układ jezdni, pasy, węzły, wiadukty, oznakowanie, charakterystyczne obiekty, położenie i proporcje; niebo/trawa/tekstury później) + `docs/06` §2.
Ocena zrobiona przed przeczytaniem `docs/reports/WORLD-INTEGRATION-2026-11-13-s16.md`. Wszystko z edytora (Low) — zrzutów z telefonu brak.

Klasyfikacja: R = kierowca znający miejsce je rozpozna (układ i kotwice zgodne, braki drugorzędne);
P = układ ok, ale brak/zła kotwica kadru albo element sprzeczny ze zdjęciem; N = układ nie ten.

## Werdykt: FAIL dla pełnego pakietu zdjęcie|render (bramka 3); G3-B warunkowo

| | R | P | N |
|---|---|---|---|
| G3-A (22) | 5 | 15 | 2 |
| G3-B (20) | 13 | 6 | 1 |
| **Razem (42)** | **18** | **21** | **3** |

Priorytetowe 5: 494288 R, 482392 R, 320326 R, 275528 R, **297817 P** (lider: R) — 4/5, nie 5/5. Samoocena lidera obejmowała 5 kadrów; pozostałych 37 nikt nie ocenił.

Integracja jest netto lepsza od main (10 awansów, w tym 810896 N→R), ale wnosi nowe, widoczne regresje (turkusowe szklane stożki,
kikuty barier, odsłonięte żółte filary w kolejnych kadrach). G3-B (trasa Andersa/DK8) jest blisko pakietu dla właściciela; G3-A nie —
połowa kadrów pod wiaduktem traci kotwicę pierwszego planu (wyspa żwirowa, zielona tablica ulicy, podpora, bariera), a dwa kadry `cm*`
pokazują plac/parking zamiast ulicy.

## Kadry G3-A

| Kadr | D51 | main→s16 | Trafione | Błędne (priorytet, pozycja w kadrze) |
|---|---|---|---|---|
| 1259231 | P | P→P | pomost, czerwona kapa, przyczółek po prawej | **P1** brak dużej podpory na pierwszym planie (zdjęcie x 0,1–0,25), w s16 tylko skrawek przy x 0; **P1** brak bariery W na pierwszym planie (zdjęcie y 0,75–0,95 przez cały kadr) |
| 1398898 | R | P→**R** | doszła podpora x 0,3 i bariera po lewej; łuk jezdni | P2 podpora kwadratowa, na zdjęciu okrągła; P2 zielona tablica ulicy x 0,35 (na zdjęciu niewidoczna) |
| 1406533 | P | P→P | droga na rampie, bariery | P1 brak bliskiej dwuramiennej latarni z lewej (zdjęcie x 0,15); zdjęcie pod słońce — mało kotwic |
| 149248 | P | P→P | wiadukt z lewej, łuk w prawo | **P1** wyspa żwirowa (zdjęcie dół, x 0–0,6) renderuje się jako ciemny asfalt; P1 zielona tablica ulicy na pierwszym planie x 0,28 — na zdjęciu jej tam nie ma |
| 177786 | P | P→P (lepiej) | wieżowiec x 0,8 trafiony; zniknął fałszywy niebieski nakaz z pierwszego planu | **P1** brak podpory z czerwonym pasem (zdjęcie x 0,15–0,35, dominanta kadru); P1 brak bariery i żwiru na pierwszym planie |
| 178689 | R | P→**R** | podpora z lewej, wieżowiec; zniknął niebieski znak ze środka | P2 brak bariery na pierwszym planie; P2 żwir → asfalt |
| 201270 | P | P→P (lepiej) | podpora x 0,35–0,5, bariera po skosie jak na zdjęciu | **P1** zielona tablica ulicy: zdjęcie pierwszy plan x 0,1–0,25 duża, render x 0,6 mała daleko (stacja/poza); P2 bariera rozmyta (tekstura); żwir → asfalt |
| 223210 | P | P→P | droga ekspresowa, bariery | P2 latarnia dwuramienna x 0,22 vs zdjęcie x 0,37; kadr generyczny |
| 2818555 | P | P→P | wiadukt z lewej | P1 brak zielonej tablicy (zdjęcie x 0,55) i wyspy żwirowej; P2 brak dwuramiennej latarni x 0,85 |
| 2948595 | P | P→P | 2 pasy, podwójne bariery, latarnie w pasie dzielącym | P2 czerwone kapy po lewej (na zdjęciu niewidoczne); brak kotwicy odróżniającej to miejsce |
| 303305 | P | P→P | prosta, bariery | **P1** sylwetka bloków na horyzoncie z lewej (zdjęcie x 0,12–0,2) zastąpiona ścianą lasu |
| 309664 | P | P→P (lepiej) | usunięty gigantyczny słup ze środka kadru z main | P2 latarnia x 0,25 vs 0,38; zdjęcie pod słońce |
| 320215 | P | P→P | prosta, bariery, latarnie | **P1** bloki na horyzoncie (x 0,15–0,25) → las (jak 303305); P2 nowy słup tuż przy kamerze (lewa krawędź, y 0–0,55) |
| 320326 | R | P→**R** | D-3 x 0,36 (zdjęcie 0,36), D-6 x 0,64 (0,65), kostka, krawężnik, żwir — największy zysk integracji | P2 podpory kwadratowe vs okrągłe; P2 zielone plamy trawy z twardą krawędzią na żwirze (x 0,25–0,7, y 0,85) |
| 3970163 | P | P→P | wiadukt, podpory | P1 zielona tablica ulicy: zdjęcie x 0,5 pierwszy plan, render x 0,62 daleko; P2 kikut bariery x 0,6 (overcast) |
| 454716 | P | P→P | prosta, bariery | P1 horyzont z lewej: bloki i topole → las |
| 482392 | R | R→R | pomost z kapą, podpory z czerwonym pasem, **doszedł znak F x 0,92** | **P1 regresja**: bariera W po prawej to krótki kikut zaczynający się w powietrzu (x 0,85–1,0, y 0,73–0,82), na zdjęciu biegnie po skosie od x 0,4; **P1** masywna podpora/ściana na lewej krawędzi (x 0–0,08, y 0,4–0,78), na zdjęciu jej nie ma; P2 jasna spodnia strona pomostu (zdjęcie: głęboki cień); P2 pas żółtych kropek na trawie y 0,75; P2 białe plamy na jezdni x 0,85–1,0 y 0,85–0,95; P2 hala w tle biała bez kolorowej elewacji |
| 500263 | R | P→**R** | znak F na słupku, bariera na pierwszym planie, podpory | P2 znak x 0,62 vs 0,78 na zdjęciu |
| 504348 | P | P→P | wiadukt, łuk w prawo | **P1** zielona tablica ulicy: zdjęcie lewa krawędź pierwszy plan, render x 0,55 daleko; żwir → asfalt |
| 751431 | P | P→P | ściana oporowa z kapą i poręczą | **P1** ściana to gładka szara płyta — na zdjęciu duże wielokątne panele z fugami (jedyna kotwica kadru); P2 brak żółtego znaku x 0,87; bariera za nisko |
| cm109685822 | **N** | N→N | — | **P0** zdjęcie: ulica z chodnikiem z kostki, trawnik, przeszklony biurowiec po prawej; render: rozległy plac z kostki/parking. Poza albo świat |
| cm92458760 | **N** | N→N | — | **P0** zdjęcie: skrzyżowanie z przejściem, rondo z kwietnikiem, kominy EC, znaki, wiadukt z lewej; render: plac i magazyny, brak kominów, znaków, ronda |

## Kadry G3-B

| Kadr | D51 | main→s16 | Trafione | Błędne |
|---|---|---|---|---|
| 150280 | R | R→R | kominy EC, czerwone budynki z prawej, latarnie | P2 brak okrągłego znaku po lewej na pierwszym planie |
| 1528935 | P | P→P | wyspa z kreskowaniem, niebieska hala z lewej | **P1** brak dużych drzew liściastych po prawej (zdjęcie x 0,65–1,0), w renderze rzadkie młode; P1 brak A-7 (zdjęcie x 0,6) |
| 1801374 | P | P→P (**regresja**) | ekran z prawej (ciemny dół + szkło), łuk | **P1 regresja**: turkusowy półprzezroczysty szklany stożek (x 0,27–0,3, y 0,3–0,6; drugi za ekranem x 0,9) — iglak z materiałem ekranu albo zły impostor; brak na main. P1 brak dwuramiennej latarni po prawej (zdjęcie x 0,68) |
| 182011 | P | P→P (**regresja**) | ekran z prawej, domy za ekranem | **P1** brak sygnalizatorów na wysięgnikach (zdjęcie x 0,35–0,6), kotwica skrzyżowania; **P1 regresja**: dwa turkusowe stożki x 0,2 i x 0,34; P2 render pokazuje szeroki trawnik i chodnik z lewej, zdjęcie wąską jezdnię |
| 209622 | R | R→R | mur z czerwoną opaską, przęsło na filarach | **P1** filary żółte (x 0,65–0,8), oświetlone, bez cienia pod płytą — nadal; P1 mur gładki; P2 brak młodych drzewek |
| 2279538 | R | R→R | blok z lewej, portal daleko na osi, latarnie | P2 U-3a po prawej (na zdjęciu w cieniu, nie do potwierdzenia) |
| 275528 | R | R→R | portal z dwiema tablicami na belce, rozstaw słupów, 3 pasy | **P1** brak obu A-30 z tabliczką (zdjęcie x 0,22 i 0,82) — nadal; P2 sosna na lewej krawędzi |
| 297817 | **P** | P/R→P | kominy EC x 0,74–0,76, nowa dwuramienna latarnia z lewej, czerwona droga rowerowa z prawej | **P1** brak dwóch dużych drzew liściastych z lewej (zdjęcie x 0–0,35, y 0,5–0,8), przez co niebieska hala i biały magazyn zajmują lewą 1/3 kadru, czego na zdjęciu nie widać; **P1 regresja**: kikut bariery W bez początku (x 0,78–0,9, y 0,78–0,83); P2 portal na osi (x 0,45–0,57), na zdjęciu tylko mały niebieski znak |
| 326454 | R | R→R | ekrany z obu stron, biurowiec z prawej | P1 słupki ekranu miętowe, wypełnienie jak siatka (zdjęcie: ciemne słupki, szkło) |
| 3281350 | R | P→**R** | portal z lewej, doszła dwuramienna latarnia na osi (zdjęcie x 0,48) | P2 dwie tablice na portalu vs jedna na zdjęciu; P2 nos pasa dzielącego zamiast prostej |
| 339463 | **N** | N→N | wiadukt z lewej, ekran | **P0** układ: zdjęcie — jezdnia prosto ze strzałkami na nawierzchni i zielonymi drogowskazami (x 0,45–0,55), ekran wzdłuż prawej krawędzi; render — wolnostojący ekran w środku kadru, chodnik z kostki, jezdnia w lewej połowie. P1 żółte filary |
| 3678296 | R | R→R | ekran z prawej, drzewa po obu stronach, latarnie w pasie dzielącym | — |
| 381800 | R | R→R | U-3a x 0,7 (zdjęcie 0,72), portal daleko, latarnie | — |
| 4312632 | P | P→P | wiadukt z ekranem w poprzek | **P1** portal z dużą zieloną tablicą po prawej (x 0,8–1,0), na zdjęciu go nie ma; P1 brak D-1 na pierwszym planie (x 0,32); **P1** żółte filary (odsłonięte w s16, na main zakryte czarną ścianą) |
| 468026 | R | R→R | wiadukt z ekranem, portal po prawej | **P1** żółte filary (odsłonięte w s16); P2 brak drzew i żółtego rombu |
| 494288 | R | P→R | łuk w lewo, ekran po prawej, latarnie dwuramienne w pasie dzielącym, czerwona kapa | **P1** bariera mostowa = bariera W z prześwitem, kapa czyta się jak bieżnia (prawa 1/3, y 0,75–0,95); **P1** ekran: raster siatki, słupki miętowe; P2 pagórek na horyzoncie x 0,55–0,7. Identyczne z after4 — żadna poprawka z REVIEW-0146 nie weszła |
| 810525 | R | P→R | opaska nad murem, słupki ciemne | **P1** mur blokowy = płaska płyta bez fug |
| 810896 | R | N→**R** | obie jezdnie na jednym poziomie, bariera na słupkach przez pierwszy plan (kikut z after4 zamknięty), ekran daleko, latarnia i sygnalizator z prawej | P2 jasny klin czoła wypełnienia przy lewej krawędzi (x 0–0,1, y 0,5); P2 białe słupki bariery x 0,22 i 0,39 innym materiałem; P2 karty liści widoczne; ekran nadal jak siatka |
| 837235 | R | R→R | U-3a z prawej, portal daleko, blok z lewej | — |
| 962702 | P | P→P | ogrodzenie/ekran z lewej, latarnia x 0,6 | **P1** brak bariery W wzdłuż lewej krawędzi jezdni (zdjęcie y 0,85–0,92); P2 brak flag na latarni (kotwica) |

## Kamery kontrolne (cmp)
- `route-putry-approach`, `route-putry-entry-signs`: zdublowany ekran naziemny zniknął (zysk), mur z opaską; **cały rząd żółtych walców** pod przęsłem — P1, najbardziej rażący błąd materiałowy trasy.
- `g3a-eye-s0262`: doszły linie napowietrzne — zysk; plac sterylnie czysty (D51 — później).
- `putry-above`: geometria węzła spójna; **P2** prostopadłościany skyline wiszące nad horyzontem (y 0,57, x 0,33–0,62) — z oka kierowcy niewidoczne, z góry wyglądają jak błąd.
- `dk8-dk19-exit`, `edge-west`: bez zmian; za zaporą nadal widać koniec świata.

## Regresje vs main (`sbs-poses-r2`) / after4
| Kadr | Regresja | P |
|---|---|---|
| 1801374, 182011 | turkusowe półprzezroczyste stożki (nowy obiekt/materiał) | P1 |
| 482392 | bariera skrócona do kikuta w powietrzu; masywna podpora na lewej krawędzi | P1 |
| 297817 | kikut bariery W po prawej | P1 |
| 468026, 4312632 | odsłonięte żółte filary (zysk geometryczny, ale wada materiału wychodzi na wierzch) | P1 |
| 320215 | słup tuż przy kamerze na lewej krawędzi | P2 |

Awanse: 1398898, 178689, 320326, 500263, 3281350, 494288, 810525, 209622, 275528, **810896 (N→R)**; poprawa w obrębie P: 177786, 201270, 309664.

## Czerwone flagi docs/06
Sterylny beton i asfalt, jasne spody pomostów bez AO (wszystkie kadry pod wiaduktem), płaskie płyty zamiast murów blokowych/paneli,
miętowe słupki ekranów, żółte filary, turkusowe stożki, kikuty barier — całość wygląda jak gra mobilna z 2016. Wg D51 materiały nie blokują
bramki, ale żółte filary, stożki i kikuty to nie tekstura do dopracowania, tylko obiekty, które kierowca odbiera jako błąd — i one psują rozpoznawalność.

## Lista poprawek (kolejność)
1. **P0** `cm109685822`, `cm92458760`, `339463`: ustalić, czy winna poza (SfM/kompas), czy świat. Nie wchodzą do pakietu właściciela jako N bez wyjaśnienia; skrzyżowanie z rondem i kominami (cm92458) to kotwica G3-A.
2. **P0 (proces)** APK Low na A16 + zrzuty kadrów 494288/482392/320326/297817/275528 — bez telefonu bramka 3 nie jest zamknięta (CLAUDE.md zasada 2).
3. P1 turkusowe stożki (1801374, 182011): znaleźć obiekt (prawdopodobnie iglak/impostor z materiałem szkła ekranu) i naprawić.
4. P1 żółte filary → szary beton albedo ok. 0,45 + przyciemnienie pod pomostem (209622, 468026, 4312632, 339463, route-putry-*).
5. P1 kikuty barier: bariera zaczyna się w gruncie, nie w powietrzu (482392, 297817, 3970163).
6. P1 kotwice pierwszego planu G3-A: zielone tablice ulic na właściwych stacjach (201270, 504348, 3970163, 2818555; fałszywa w 149248), wyspy żwirowe zamiast asfaltu (149248, 2818555, 504348, 3970163), podpory i bariery W na pierwszym planie (1259231, 177786; ściana na lewej krawędzi 482392).
7. P1 A-30 + tabliczka przy portalu 275528 (otwarte od REVIEW-0146).
8. P1 sylwetka bloków na horyzoncie zamiast ściany lasu (303305, 320215, 454716) i duże drzewa liściaste (297817 lewa, 1528935 prawa).
9. P1 sygnalizatory na wysięgnikach 182011; D-1 w 4312632, A-7 w 1528935; portal w 4312632 do weryfikacji.
10. P1 materiały z REVIEW-0146 (żaden nie wszedł): ekran bez rastra, słupki grafit; bariera mostowa DK8; mury z fugami/panelami (751431, 810525, 209622).
11. P2: wiszący skyline (putry-above), podpory okrągłe, flagi na latarni 962702, plamy trawy na żwirze 320326, białe słupki 810896, słup przy kamerze 320215.

## Oceny 1–10
| Kategoria | Ocena | Uwagi |
|---|---|---|
| Rozpoznawalność D51 — G3-B | 7 | 13/20 R; rdzeń trasy (DK8, Andersa, portale, U-3a) czyta się |
| Rozpoznawalność D51 — G3-A | 4 | 5/22 R; pod wiaduktem gubione kotwice pierwszego planu, 2 x N |
| Skala i proporcje | 6 | znaki/tablice/latarnie trafione; podpory kwadratowe; ściana za blisko kamery w 482392 |
| Światło i ekspozycja | 3 | jasne spody pomostów, brak AO (D51 — później) |
| Materiały | 3 | siatka zamiast szkła, mięta, żółć, płyty bez fug, turkusowe stożki |
| Zużycie i osadzenie | 3 | sterylnie; kikuty barier bez osadzenia |
| Powtarzalność | 6 | nie razi w tych kadrach |
| Polskie realia (znaki, bariery) | 6 | D-3/D-6/F/U-3a/tablice OK; brak A-30, D-1, A-7, sygnalizatorów; bariera W na moście |
| Artefakty | 5 | stożki, kikuty, wiszący skyline; bez z-fightingu i dziur |

Werdykt końcowy: **FAIL** dla pełnego pakietu 42 par. Integracja to krok naprzód (18 R; na main szacunkowo ok. 8 R), ale 21 P + 3 N to jeszcze nie
poziom kierowca rozpozna drogę dla G3-A. Właścicielowi można pokazać **wyselekcjonowany pakiet G3-B** (13 R) po poprawkach 3–5 i pomiarze na A16;
G3-A dopiero po poprawkach 1 i 6. Samoocena lidera 5/5 obejmowała tylko 5 kadrów i zawyża 297817.
