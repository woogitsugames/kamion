# Tor A4 — zewnętrze ciężarówki TRAKT (koncepcja B), wersja do oceny

**Co to jest:** pełne zewnętrze naszego ciągnika 4×2 w docelowym stylu: sylwetka B (aerodynamiczna, szyba pochylona 19°), marka **TRAKT** (decyzja właściciela 2026-11-09; rejestry znaków towarowych jeszcze niesprawdzone). Model jest w całości generowany kodem (`tools/blender/truck/exterior/`), w skali 1:1, z wymiarami z `art-source/truck/dims.json`. Wnętrze widoczne przez szyby to proste bryły zastępcze — pełne wnętrze robi równolegle zadanie A5.

Rendery: Blender Cycles 1600×900, dwa oświetlenia:
- **pochmurno** — rozproszone niebo + słaby, bardzo miękki „słońce”, pełne odbicia światła (jak dobre zdjęcie w szary dzień),
- **jak URP** — płaskie światło otoczenia + jedno słońce, **bez odbić rozproszonych**, jedno odbicie lustrzane: tak mniej więcej zobaczy to telefon (Unity URP bez GI).

Tło: prosty plac logistyczny zbudowany w skrypcie (płyty betonowe z fugami, hale z bramami, linia lasu, maszty). **Nie pobierałem żadnego HDRI** — nie ma nowych zasobów do `docs/LICENSES.md`. Napisy na tablicy i oponach: font Inter (OFL, plik już w repo).

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

Pozostałe: `przod_white_urp.jpg`, `bok_white_urp.jpg`, `34tyl_white_urp.jpg`, `zbl_reflektor_dark_overcast.jpg`.

## Wygląd marki TRAKT na przodzie
Znak TRAKT to litera T, której nóżka jest drogą w perspektywie. Przód jest zbudowany z tego samego pomysłu, żeby nie był „przyklejonym logo”:
- **grill w kształcie T** — szeroka górna belka i „droga” rozszerzająca się w dół, ciągnięta dalej w zderzaku jako ciemny wlot powietrza aż do tablicy;
- **reflektory w narożnikach pod belką T**, z wewnętrzną krawędzią równoległą do krawędzi „drogi”;
- **podpis świetlny (światła dzienne LED)**: w każdym reflektorze poziomy pasek (belka T) + ukośna linia (krawędź drogi) — razem z grillem cały przód czyta się jako T. Pod spodem 5 modułów LED drogowych, 2 soczewki projektorowe, pomarańczowy kierunkowskaz;
- emblemat T (z pliku `art-source/truck/brand/trakt.svg`) — jedyny chrom na ciężarówce; napis TRAKT ciemnym chromem nad grillem.
Nie kopiuje żadnego producenta: brak ukośnej belki, gwiazdy, lwa, gryfa, rombu, sześciokąta czy pionowych lamp w kształcie L.

## Lusterka: klasyczne (wybór domyślny) i kamery (wariant)
| klasyczne | kamery |
|---|---|
| ![](34przod_white_overcast.jpg) | ![](34przod_white_overcast_kamery.jpg) |
| ![](przod_white_overcast.jpg) | ![](przod_white_overcast_kamery.jpg) |

Domyślnie **klasyczne**: główne (kl. II) + szerokokątne (kl. IV) na ramieniu, krawężnikowe (kl. V) po prawej, przednie (kl. VI) nad prawym narożnikiem. Powody: (1) to dalej większość ciężarówek na polskich parkingach, (2) gracz cofający z naczepą patrzy w lusterko jak w prawdziwe — działa to samo co w kabinie A5 (tam też są klasyczne), (3) kamery wymagają ekranów na słupkach A we wnętrzu, których A5 nie ma. Wariant z kamerami jest w generatorze (`--mirrors camera`), lusterko kl. VI zostaje w obu.

## Inżynieria i ergonomia (skrót, szczegóły w `docs/reports/visual/truck-A3/`)
- **Nadkole i błotnik w narożniku kabiny** zamiast „pudełka nad kołem”: zderzak, narożniki z nadkolem, stopnie i boczne osłony to jedna osłona **na ramie**; kabina siedzi na niej z linią uchylania na 1,22 m. Test uchylania o 50° — kabina przechodzi nad zderzakiem.
- **Stopnie**: trzy, za kołem, po skosie do przodu (0,45 / 0,79 / 1,10 m), aluminiowa blacha ryflowana + nosek; uchwyty: wpuszczony w panelu za drzwiami (mieści się w 2,55 m) + na słupku A wewnątrz. Najwyższy stopień ma 0,59 m szerokości, nie całą szerokość drzwi — bo koło jest pod drzwiami (patrz ustalenie nr 1 w raporcie A3).
- **Szczeliny**: drzwi (zgodne z otworem wnętrza A5: tył −0,28 m, szyba 2,17–2,94 m), klapa serwisowa przodu, linia uchylania, łączenie dachu, panele tylnej ściany.
- **Widoczność**: słupek A lewy 8°, prawy 3,5°; ziemia na wprost od ~5 m przed zderzakiem (tabela i mapa w A3).
- Szerokość nadwozia 2,548 m (limit 2,55), wysokość 3,98 m (limit 4,00).

## Szczegóły, które są w modelu
Szyba wklejana na płasko z czarnym rantem, wycieraczki i dysze spryskiwacza, kratka podszybia, klapka serwisowa, sygnały dźwiękowe za wlotem w zderzaku, stopnie do mycia szyby w narożnikach zderzaka, tablica PL 520×114 mm (rejestracja fikcyjna), lampy przeciwmgłowe/doświetlające, boczne kierunkowskazy i lampy obrysowe (białe przód, czerwone tył, pomarańczowe boczne), właz dachowy, deflektory boczne z gumową krawędzią, listwa dachu, lampa robocza, tylna ściana z panelem przyłączy (czerwone i żółte złącza pneumatyczne, gniazda elektryczne ISO 7638 / 15-pin) i spiralami na wieszaku, kładka z blachy ryflowanej z drabinką i uchwytem, siodło z płytą, smarem, rowkami, zamkiem i dźwignią, rama z rzędami śrub, oś przednia z resorami parabolicznymi, amortyzatorami, drążkami i tarczami hamulcowymi, oś tylna z mostem, 4 miechami i wahaczami, aluminiowy zbiornik paliwa z opaskami i przetłoczeniami, zbiornik AdBlue z niebieskim korkiem, skrzynka oczyszczania spalin z perforowaną osłoną i wylotem, skrzynka akumulatorów, zbiorniki powietrza, błotniki tylne z chlapaczami, lampy tylne, tylna tablica.
**Koła**: kute aluminium 22.5×9.00, 10 śrub, przód ET +120 mm (tarcza na zewnątrz, kołpak piasty), tył bliźniaki skręcone tarczami (zewnętrzne koło pokazuje głęboką czaszę i piastę osi). **Opony** 315/80 R22.5: własny bieżnik (przód: 4 zygzakowate rowki + nacięcia; tył: bloki z rowkami poprzecznymi), napisy na boku bez marki (rozmiar, indeks nośności 156/150L, TUBELESS RADIAL, STEER/DRIVE, M+S, symbol 3PMSF, REGROOVABLE, fikcyjny znak homologacji E20 i kod DOT).

## Materiały i budżet
- **Lakier** z warstwą bezbarwną (lekka „skórka pomarańczy”), dwa malowania: biel flotowa i ciemna zieleń butelkowa; **czarne tworzywa** matowe z mikroziarnem (nie smoła); chrom tylko na emblemacie; subtelny kurz drogowy rosnący ku dołowi i w zagłębieniach (zadbana flota, nie wrak).
- **Trójkąty LOD0 zewnętrza: 99 776** (cel High ≤ ~100 tys. ✔; bez wnętrza i brył zastępczych). Podział: koła 37,8 tys., kabina 28,8 tys., rama i osprzęt 19,8 tys., osłona dolna 9,8 tys., lusterka 3,7 tys. (`stats.json`).
- **Plan LOD** (zmierzony uproszczeniem automatycznym): LOD1 ≈ 43 tys. (45%), LOD2 ≈ 14,5 tys. (15%). Ostateczne LOD-y w A6: najpierw usunięcie niewidocznych ścian (wewnętrzna skóra kabiny, wnętrza kół bliźniaczych), potem uproszczenie.
- **Sloty materiałów w grze: 6** — LAKIER (9,2 tys. tr.), TWORZYWA/RAMA/GUMA/TABLICA (37,9 tys.), METAL (27,1 tys.), SZKŁO (2,5 tys.), ŚWIATŁA (6,2 tys., emisja sterowana z gry), OPONY (16,8 tys.). W Blenderze materiałów jest więcej, każdy ma przypisany slot (`game_slot`); scalenie w atlasy w A6.
- **UV**: każda część ma warstwę `UVMap` (rzut pudełkowy w skali świata, 1 = 1 m — gotowe pod tekstury kafelkowane); opony i felgi mają UV toczone (u = obwód, v = profil), tablice — UV płaskie. Pakowanie atlasów i wypalanie normalnych to A6.

## Pętla wizualna — co poprawiłem (przed → po)
Każdą rundę renderowałem i oglądałem; poprawki wynikają z tego, co było widać (albo z pomiaru).

**Względem A2 (uwagi krytyka z REVIEW-2026-11-09):**
1. Kabina „wisiała” nad kołem jak pudełko → **nadkole wycięte w narożniku osłony**, z obrzeżem i nadkolem wewnętrznym; kabina siedzi na osłonie z linią uchylania.
2. Ostre narożniki → narożniki zaokrąglone R 0,32–0,46 m (rosnące ku górze).
3. Mały, generyczny grill i dwie wąskie lampy, pusty przód → grill T + „droga” w zderzaku, duże reflektory z podpisem LED marki.
4. Brak lusterka kl. V/VI → są (i zostają przy wariancie z kamerami).
5. Stopnie 0,35 m przy drzwiach 1,15 m → trzy stopnie z blachą ryflowaną, najwyższy 0,59 m; pełna szerokość drzwi niemożliwa przy obecnym położeniu oczu/drzwi (ustalenie dla lidera).
6. Koła jako czarne dyski → felgi aluminiowe z czaszą, nakrętkami i piastami, opony z bieżnikiem i napisami.

**Rundy A4:**
1. Narożne deflektory wystawały → szerokość **2,554 m (ponad limit)** i czarne „uszy” przy słupkach → zmniejszone, potem usunięte (2,548 m).
2. Ściany kieszeni po cięciu (reflektory, grill) dziedziczyły lakier — białe ramki w lampach → przenoszenie materiału z bryły tnącej.
3. Zderzak jako pusta biała płyta → ciemny dół z tablicą i lampami, linia podziału, potem „droga” z grilla przedłużona w zderzaku.
4. Napis TRAKT niewidoczny (srebro na bieli), a z przodu **lustrzane odbicie napisu** → ciemny chrom i poprawiona kolejność liter.
5. Grill czytał się jak dwa osobne grille z białą belką → jeden ciągły grill w kształcie T, większe reflektory klinowe.
6. Deflektory boczne wystawały ponad ramiona dachu („rogi” z przodu) → dopasowane do zwężenia dachu.
7. **Okno boczne było nieprzezroczyste** (czarna ramka jako pełny panel) — wykryte w mapie widoczności (zasłonięte 36°–110° w lewo) → ramka jako pierścień.
8. Słupek A zasłaniał 17,5° → 8° (szersze zawinięcie szyby, węższy frit, szyba boczna dalej do przodu).
9. Cień „rury” przed reflektorem → zastępcza deska wnętrza przebijała narożnik kabiny (wykryte strzałem promienia z kamery) → zmniejszona.
10. Pusta, ciemna górna połowa reflektora → wewnętrzna ramka z ciemnego chromu i 5 modułów LED.
11. Szyba z cienkiej powierzchni działała jak soczewka i z kabiny dawała „bańkę” całkowitego odbicia → szkło cienkie (przezroczyste + odbicie zależne od kąta, symetryczne dla obu stron).
12. Tablice: pasek UE w środku tablicy, tylna nieczytelna → poprawne UV.
13. W rzutach z boku i z przodu **klin pod zderzakiem aż do ziemi** → artefakt fazowania na bryle po cięciu (wierzchołek w z = 0) → bez fazowania tej bryły; przy okazji −5 tys. trójkątów.
14. Budżet: 132 tys. → 99,8 tys. trójkątów (lżejsza siatka kabiny, felgi i koła wewnętrzne, spirale).
15. Tło: las z klocków → ciągła linia lasu.

## Znane braki (świadomie)
- Wnętrze przez szyby to bryły zastępcze (A5 je zastąpi) — z bliska widać „puste” fotele.
- Krawędzie osłony dolnej bez fazowania (wróci w A6 przy retopologii); szczeliny paneli to paski geometrii — w A6 pójdą do mapy normalnych.
- Kurz i brud są proceduralne i lekkie; prawdziwe maski zużycia (progi, stopnie, błotniki) w A6 przy wypalaniu.
- Brak zdjęć referencyjnych właściciela i porównania obok siebie (checklista `docs/06` §5 pkt 3) oraz zrzutów z telefonu (pkt 2) — model nie jest jeszcze w Unity (A7).
- Ocena `visual-critic` — do zlecenia przez lidera.

## Czego potrzebuję od Ciebie
1. Ocena kierunku przodu (grill T, podpis świateł) i obu malowań — czy biel + zieleń, czy inny ciemny kolor.
2. Lusterka: zostajemy przy klasycznych?
3. Zdjęcia z listy w `docs/plan/TRACK-A.md` §4, zwłaszcza okolica koła przedniego ze stopniami i widok z fotela — rozstrzygną położenie drzwi/stopni (raport A3, ustalenie 1).

## Jak odtworzyć
```
blender -b --factory-startup --python tools/blender/truck/exterior/build.py -- --mode a4 --out docs/reports/visual/truck-A4 --lights overcast,urp --liveries white --samples 160 --views 34przod,bok,przod,34tyl,zbl_reflektor,zbl_stopnie,zbl_tyl,zbl_kolo
blender -b --factory-startup --python tools/blender/truck/exterior/build.py -- --mode a4 --out docs/reports/visual/truck-A4 --lights overcast --liveries dark --samples 160 --views 34przod,bok,przod,34tyl,zbl_reflektor
blender -b --factory-startup --python tools/blender/truck/exterior/build.py -- --mode a4 --out docs/reports/visual/truck-A4 --lights urp --liveries dark --samples 160 --views 34przod
blender -b --factory-startup --python tools/blender/truck/exterior/build.py -- --mode a4 --out docs/reports/visual/truck-A4 --mirrors camera --tag _kamery --samples 160 --views 34przod,przod
```
`stats.json` i `wymiary.json` zapisuje każde uruchomienie — wersje w repo pochodzą z wariantu z lusterkami klasycznymi. Tekstury (bieżnik, napisy na oponach, tablica, blacha ryflowana) generują się same do `art-source/truck/exterior/textures/` (poza gitem). `--blend <plik>` zapisuje scenę do podglądu (poza gitem).
