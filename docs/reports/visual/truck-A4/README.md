# Tor A4 — zewnętrze ciężarówki TRAKT (koncepcja B), runda 3 (po recenzji R2)

**Co to jest:** pełne zewnętrze naszego ciągnika 4×2 w docelowym stylu: sylwetka B (aerodynamiczna, szyba pochylona 19°), marka **TRAKT** (decyzja właściciela 2026-11-09; rejestry znaków towarowych jeszcze niesprawdzone). Model jest w całości generowany kodem (`tools/blender/truck/exterior/`), w skali 1:1, z wymiarami z `art-source/truck/dims.json`. Wnętrze widoczne przez szyby to proste bryły zastępcze — pełne wnętrze jest osobnym zadaniem (A6, tapicerka koniak).

**Runda 3** odpowiada na recenzję `docs/reports/visual/REVIEW-2026-11-09-r2.md`, punkty #2 (drzwi, stopnie, nadkole), #3 (przód z lat 2020.) i #11 (zużycie i materiały). Szczegóły w sekcji „Runda 3 — zmiany” i w tabeli przed/po. Oceny nie wystawiam sam — kolejny przegląd robi `visual-critic`.

Rendery: Blender Cycles 1600×900, 160 próbek, dwa oświetlenia:
- **pochmurno** — rozproszone niebo + słaby, bardzo miękki „słońce”, pełne odbicia światła (jak dobre zdjęcie w szary dzień),
- **jak URP** — płaskie światło otoczenia + jedno słońce, **bez odbić rozproszonych**, jedno odbicie lustrzane: tak mniej więcej zobaczy to telefon (Unity URP bez GI). To nadal emulacja w Cycles, nie prawdziwy kadr URP.

Tło: prosty plac logistyczny zbudowany w skrypcie. **Nie pobierałem żadnego HDRI** ani tekstur — nie ma nowych zasobów do `docs/LICENSES.md`. Obrazy w `Data/photos/` to **referencje AI, nie zdjęcia** — użyte tylko do nastroju i proporcji (stopnie za kołem, kabina w kolorze nadwozia do dołu, soczewka lampy z grubością), nie jako wzór kształtu.

## Najważniejsze kadry

| | biel flotowa | zieleń butelkowa (ciemna) |
|---|---|---|
| 3/4 przód, pochmurno | ![](34przod_white_overcast.jpg) | ![](34przod_dark_overcast.jpg) |
| 3/4 przód, jak URP | ![](34przod_white_urp.jpg) | ![](34przod_dark_urp.jpg) |
| przód | ![](przod_white_overcast.jpg) | ![](przod_dark_overcast.jpg) |
| bok lewy | ![](bok_white_overcast.jpg) | ![](bok_dark_overcast.jpg) |
| 3/4 tył (prawa strona) | ![](34tyl_white_overcast.jpg) | ![](34tyl_dark_overcast.jpg) |

Zbliżenia (biel, pochmurno / jak URP):

| reflektor | nadkole i stopnie | tył kabiny, siodło, przewody | koła tylne, błotnik |
|---|---|---|---|
| ![](zbl_reflektor_white_overcast.jpg) | ![](zbl_stopnie_white_overcast.jpg) | ![](zbl_tyl_white_overcast.jpg) | ![](zbl_kolo_white_overcast.jpg) |
| ![](zbl_reflektor_white_urp.jpg) | ![](zbl_stopnie_white_urp.jpg) | ![](zbl_tyl_white_urp.jpg) | ![](zbl_kolo_white_urp.jpg) |

Z punktu oczu kierowcy (lusterka ustawione na oko): `oko_przod_white_overcast.jpg`, `oko_lewo_white_overcast.jpg`, `oko_prawo_white_overcast.jpg`; mapa widoczności `widocznosc_mapa.png` + `widocznosc.json`.
Pozostałe: `przod_white_urp.jpg`, `bok_white_urp.jpg`, `34tyl_white_urp.jpg`, `zbl_reflektor_dark_overcast.jpg`, wariant z kamerami `*_kamery.jpg`.

## Runda 3 — przed / po

Obrazy „przed” (runda 2, zmniejszone do 960 px) są w `przed_r3/`.

| | przed (R2) | po (runda 3) |
|---|---|---|
| 3/4 przód | ![](przed_r3/34przod_white_overcast.jpg) | ![](34przod_white_overcast.jpg) |
| przód | ![](przed_r3/przod_white_overcast.jpg) | ![](przod_white_overcast.jpg) |
| bok | ![](przed_r3/bok_white_overcast.jpg) | ![](bok_white_overcast.jpg) |
| nadkole i stopnie | ![](przed_r3/zbl_stopnie_white_overcast.jpg) | ![](zbl_stopnie_white_overcast.jpg) |
| reflektor | ![](przed_r3/zbl_reflektor_white_overcast.jpg) | ![](zbl_reflektor_white_overcast.jpg) |
| tył kabiny, siodło | ![](przed_r3/zbl_tyl_white_overcast.jpg) | ![](zbl_tyl_white_overcast.jpg) |
| koła tylne | ![](przed_r3/zbl_kolo_white_overcast.jpg) | ![](zbl_kolo_white_overcast.jpg) |
| ciemne malowanie | ![](przed_r3/34przod_dark_overcast.jpg) | ![](34przod_dark_overcast.jpg) |
| lusterko z fotela | ![](przed_r3/oko_lewo.jpg) | ![](oko_lewo_white_overcast.jpg) |
| mapa widoczności | ![](przed_r3/widocznosc_mapa.png) | ![](widocznosc_mapa.png) |

## Runda 3 — zmiany (changelog)

**#2 Drzwi, stopnie, nadkole (P0).** Punkt oczu **bez zmian** (−0,55; 0,45; 2,50).
- Otwór drzwi przesunięty do tyłu: tylna linia drzwi **y −0,60 m** (było −0,28). Przednia linia: pionowo na **y 0,80 m** do z 1,90, potem skosem do słupka A (na wysokości 2,14) i wzdłuż słupka. Przed drzwiami zostaje **stały panel narożny w kolorze nadwozia**.
- **Dolny tylny róg drzwi schodzi** poniżej linii uchylania (do z 0,98 m) za nadkolem jako fartuch drzwi; jego przednia krawędź idzie po łuku nadkola. Fartuch zasłania przód najwyższego stopnia.
- **Stopnie za przednim kołem** we wnęce w kolorze nadwozia (bez czarnych skrzynek): 3 stopnie, górne krawędzie 0,46 / 0,80 / 1,11 m, **szerokości 0,42 / 0,485 / 0,60 m**, głębokość 0,21 m, blacha ryflowana z ciemnym noskiem. Dolne stopnie ogranicza łuk nadkola; żeby się zmieściły, osłona stopni sięga 0,19 m za tylną ścianę kabiny (do y −1,14), a zbiornik paliwa, skrzynka oczyszczania spalin i akumulatory przesunęły się o 0,08–0,14 m do tyłu.
- Szyba boczna: tylna krawędź y −0,49 m (zgodnie z otworem −0,56 + 0,07 jak dotąd we wnętrzu). Uchwyt wpuszczony przeniesiony do stałego panelu za drzwiami (y −0,83…−0,74).
- **Plik dla wnętrza:** `art-source/truck/exterior/door_interface.json` — linie drzwi, otwór (DOOR_Y0 = −0,56, DOOR_Y1 = 0,76 przy podłodze / 1,14 na linii okna), szyba, fartuch, stopnie. Zapisuje go każde uruchomienie generatora. Karta drzwi we wnętrzu musi się do niego dopasować (zadanie dla agenta wnętrza).
- Mapa widoczności powtórzona: słupek A lewy nadal 8°, prawy 3,5°, ziemia na wprost od 4,96 m przed zderzakiem (bez zmian), róg pasażera 9,19 m (było 9,05).

**#3 Przód z lat 2020. (P0).**
- **Jeden grill w kształcie T** zamiast trzech pól identycznych listew: grafitowa ramka wokół całego T, w belce T **dwie grube listwy w kolorze nadwozia** z zaokrąglonym noskiem, w „drodze” **trzy cienkie grafitowe listwy** o profilu żaluzji, głębiej i z rosnącym odstępem, za wszystkim **drobny plaster miodu** (komórka 22 mm). Trzy różne grubości, głębokości i przekroje.
- Zderzak: „droga” z grilla przedłużona jako **wlot z grubszym plastrem miodu** (34 mm) w grafitowej ramce, bez listew; dolny wlot też plaster miodu, bez listew.
- **Reflektory**: smuklejsze (0,23 m wysokości), **soczewka z grubością** (dwie powierzchnie z odbiciem Fresnela) w czarnej uszczelce, czarna maska w środku, **dwa moduły projektorowe w odbłyśnikach z głębokością** (czasza, pierścień z ciemnego chromu, ciemna soczewka), **cienka listwa LED świateł drogowych w czarnej masce** zamiast 5 „kostek”, pomarańczowy kierunkowskaz na dole. Podpis świateł dziennych (pozioma belka + ukośna krawędź „drogi” = połowa znaku T) jest teraz **wewnątrz soczewki**, a nie na krawędzi obudowy.
- **Usunięty „dziób” nad szybą**: profil czoła nad szybą jest gładki (wysunięta warga na z 3,00–3,13 dawała ciemny cień jak spoiler z lat 90.). Przy okazji zastępcza półka wnętrza nie przebija już narożnika dachu.
- **Koniec ciemnego „cokołu”**: zderzak, narożniki, panel przed nadkolem i skrzynka stopni są w kolorze nadwozia powyżej linii **0,67 m**; ciemne zostają tylko dolny zderzak z wlotem, obrzeże nadkola (~65 mm), wnętrze nadkola i pas pod najniższym stopniem.
- Napis TRAKT: ciemny satynowy metal na bieli, **satynowe srebro na ciemnej zieleni** (R2 #9: znikał).

**#11 Zużycie i materiały (P1).**
- Lakier: **film drogowy** na dolnych ~0,6 m, **zacieki** pionowe na bokach, **natrysk z tylnych kół** na tylnej ścianie kabiny, brud w zagłębieniach (wnęka stopni, szczeliny). Tworzywa, rama i zbiornik też dostały film drogowy.
- **Felgi mniej lustrzane**: chropowatość 0,26 (było 0,17), toczone rowki, anizotropia po obwodzie, **pył hamulcowy** w czaszy i przy nakrętkach.
- **Siodło**: smar ciemnobrązowo-czarny, mokry połysk tam, gdzie gruby, matowa brązowa smuga tam, gdzie cienki, grudki (było płaskie jasnoszare).
- Stopnie: brud z butów w rowkach blachy ryflowanej.
- **Przedni chlapacz** za kołem (guma z żebrami, obejma) i **szczotka przeciwrozbryzgowa** wewnątrz krawędzi nadkola.
- **Lusterka ustawione na punkt oczu**: normalna szkła = dwusieczna kierunku do oka i wymaganego pola widzenia (kl. II do tyłu wzdłuż naczepy, kl. IV szerzej i niżej, kl. V w dół przy kole). Z fotela szkło jest widoczne całe zamiast „na krawędź” (rozmiar kątowy w `widocznosc.json`).

**Inne:** linia lasu w tle bez „piły” (R2 #11 w tle), wsporniki uchylania kabiny cofnięte o 2 cm, żeby nie przebijały wlotu w zderzaku.

**Pętla wizualna rundy 3** (każdą rundę oglądałem w zmniejszeniu do 800 px i w wycinkach):
1. R3.1: nowe drzwi/stopnie, nowy grill i lampy → nad szybą pojawił się **ciemny pas** jak osłona przeciwsłoneczna. Strzał promieniem pokazał, że to zastępcza półka wnętrza wystająca przez nowe, cofnięte czoło → półka zmniejszona.
2. R3.2: ciemny „łezkowaty” kształt w narożniku dachu (ta sama półka w zaokrągleniu) → półka węższa; **wsporniki uchylania przebijały plaster miodu** w zderzaku → płytsza kieszeń + wsporniki cofnięte; siodło za jasne (odbicie nieba w smarze) → ciemniejszy i bardziej matowy cienki smar; natrysk na tylnej ścianie niewidoczny → mocniejszy; **103,6 tys. trójkątów** → listwy grilla na płaskiej części czoła z 2 podziałami, lżejsze moduły lamp, szyba, wewnętrzne felgi: **99,7 tys.**
3. R3.3: sprawdzenie w obu malowaniach i w „jak URP” — wynik w kadrach powyżej.

## Wygląd marki TRAKT na przodzie
Znak TRAKT to litera T, której nóżka jest drogą w perspektywie. Na przodzie ten pomysł żyje w **ramce grilla** (obrys T: szeroka belka i „droga” rozszerzająca się w dół, przedłużona w zderzaku) i w **świetle dziennym** (w każdej lampie belka + ukośna krawędź drogi). Emblemat T (z `art-source/truck/brand/trakt.svg`) siedzi na listwach belki; to jedyny chrom na ciężarówce.
Nie kopiuje żadnego producenta: brak ukośnej belki, gwiazdy, lwa, gryfa, rombu, sześciokąta, pionowych lamp w kształcie L ani poziomych „schodków” listew.

## Lusterka: klasyczne (wybór domyślny) i kamery (wariant)
| klasyczne | kamery |
|---|---|
| ![](34przod_white_overcast.jpg) | ![](34przod_white_overcast_kamery.jpg) |
| ![](przod_white_overcast.jpg) | ![](przod_white_overcast_kamery.jpg) |

Domyślnie **klasyczne**: główne (kl. II) + szerokokątne (kl. IV) na ramieniu, krawężnikowe (kl. V) po prawej, przednie (kl. VI) nad prawym narożnikiem. Wariant z kamerami jest w generatorze (`--mirrors camera`), lusterko kl. VI zostaje w obu.

## Inżynieria i ergonomia (skrót)
- **Drzwi i stopnie**: patrz runda 3 powyżej i `door_interface.json`. Koło przednie jest pod przednią połową drzwi, stopnie za kołem, fartuch drzwi nad najwyższym stopniem.
- **Nadkole w narożniku osłony** zamiast „pudełka nad kołem”: zderzak, narożniki z nadkolem i skrzynki stopni to jedna osłona **na ramie**; kabina siedzi na niej z linią uchylania na 1,22 m. Oś uchylania y 1,42 m.
- **Szczeliny**: drzwi (z fartuchem), klapa serwisowa przodu, linia uchylania, łączenie dachu, panele tylnej ściany, linia zderzaka 0,67 m.
- **Widoczność**: słupek A lewy 8°, prawy 3,5°; ziemia na wprost od ~5 m przed zderzakiem.
- Szerokość nadwozia **2,548 m** (limit 2,55), wysokość **3,98 m** (limit 4,00), długość 6,06 m (`wymiary.json`).

## Materiały i budżet
- **Lakier** z warstwą bezbarwną (lekka „skórka pomarańczy”), biel flotowa i ciemna zieleń butelkowa, z warstwą brudu drogowego (wyżej). **Czarne tworzywa** matowe z mikroziarnem; **grafit** (ramki grilla i „drogi”, cienkie listwy) — satynowy lakier z drobnym metalicznym pyłkiem, nie chrom; **plaster miodu** jako tekstura generowana w skrypcie (bez plików z zewnątrz).
- **Trójkąty LOD0 zewnętrza: 99 710** (cel High ≤ ~100 tys. ✔). Podział: koła 37,2 tys., kabina 28,6 tys., rama i osprzęt 19,8 tys., osłona dolna 10,5 tys., lusterka 3,7 tys. (`stats.json`).
- **Plan LOD** (uproszczenie automatyczne): LOD1 ≈ 43,0 tys. (45%), LOD2 ≈ 14,3 tys. (15%). Ostateczne LOD-y w A6.
- **Sloty materiałów w grze: 6** — LAKIER (12,0 tys. tr.), TWORZYWA/RAMA/GUMA/TABLICA (36,2 tys.), METAL (26,7 tys.), SZKŁO (2,0 tys.), ŚWIATŁA (6,1 tys.), OPONY (16,8 tys.). Nowe materiały renderowe (`trim_graphite`, `grille_honey*`, `brush`, `wordmark`) mają przypisany slot (`game_slot`).
- **UV**: rzut pudełkowy w skali świata (1 = 1 m), opony i felgi toczone, tablice płaskie. Pakowanie atlasów, wypalanie normalnych i gęstość tekseli — A6.

## Znane braki (świadomie)
- Wnętrze przez szyby to bryły zastępcze; wnętrze A6 nie ma jeszcze nowego otworu drzwi (dane w `door_interface.json`).
- Dwa dolne stopnie mają 0,42 i 0,485 m, nie 0,55–0,6 m: ogranicza je łuk nadkola przy obecnym rozstawie (koło na y 0, ściana kabiny −0,95). Najwyższy ma 0,60 m.
- Krawędzie osłony dolnej bez fazowania (wróci przy retopologii A6); szczeliny paneli to paski geometrii — w A6 pójdą do mapy normalnych. Brud jest proceduralny; maski zużycia do wypalenia w A6.
- Nadal **brak kadru URP i z telefonu** (checklista `docs/06` §5 pkt 2) i prawdziwych zdjęć do porównania (pkt 3). Bez nich nie może być PASS.
- Brak bryły silnika i chłodnicy w teście uchylania (R2 #10) — poza zakresem tej rundy.

## Czego potrzebuję od Ciebie
1. Zdjęcie prawdziwej ciężarówki z miarką: środek koła przedniego → tylna krawędź drzwi, szerokości stopni, wysokość progu. Potwierdzi lub poprawi wartości z `door_interface.json` (teraz WORKING_VALUE).
2. Ocena nowego przodu (grill T z ramką, listwy w kolorze nadwozia, plaster miodu, lampy) — od `visual-critic` i od Ciebie.

## Jak odtworzyć
```
blender -b --factory-startup --python tools/blender/truck/exterior/build.py -- --mode a4 --out docs/reports/visual/truck-A4 --mirrors camera --tag _kamery --samples 160 --views 34przod,przod
blender -b --factory-startup --python tools/blender/truck/exterior/build.py -- --mode a4 --out docs/reports/visual/truck-A4 --lights overcast --liveries dark --samples 160 --views 34przod,bok,przod,34tyl,zbl_reflektor
blender -b --factory-startup --python tools/blender/truck/exterior/build.py -- --mode a4 --out docs/reports/visual/truck-A4 --lights urp --liveries dark --samples 160 --views 34przod
blender -b --factory-startup --python tools/blender/truck/exterior/build.py -- --mode a4 --out docs/reports/visual/truck-A4 --lights overcast,urp --liveries white --samples 160 --views 34przod,bok,przod,34tyl,zbl_reflektor,zbl_stopnie,zbl_tyl,zbl_kolo --vis
```
Kolejność ma znaczenie: ostatnie uruchomienie (lusterka klasyczne) zapisuje `stats.json`, `wymiary.json`, `widocznosc*.json/png` i `oko_*.jpg`. Każde uruchomienie zapisuje też `art-source/truck/exterior/door_interface.json`. Tekstury (bieżnik, napisy na oponach, tablica, blacha ryflowana, plaster miodu) generują się same do `art-source/truck/exterior/textures/` (poza gitem). `--blend <plik>` zapisuje scenę do podglądu (poza gitem).

---

<details><summary>Historia: rundy A4 przed recenzją R2</summary>

**Względem A2 (uwagi krytyka z REVIEW-2026-11-09):** nadkole wycięte w narożniku osłony z linią uchylania; narożniki zaokrąglone R 0,32–0,46 m; grill T + „droga” w zderzaku; lusterka kl. V/VI; stopnie z blachą ryflowaną; felgi aluminiowe i opony z bieżnikiem i napisami.

**Rundy A4 (1–15):** szerokość 2,554 → 2,548 m (deflektory); materiał ścian kieszeni z bryły tnącej; zderzak z ciemnym dołem; napis TRAKT czytelny i nie lustrzany; jeden grill w kształcie T; deflektory boczne dopasowane do dachu; okno boczne przezroczyste (wykryte w mapie widoczności); słupek A 17,5° → 8°; deska zastępcza nie przebija narożnika; szyba jako cienkie szkło; UV tablic; klin pod zderzakiem (artefakt fazowania); budżet 132 → 99,8 tys.; las jako ciągła linia.
</details>
