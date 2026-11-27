# ADR 0320 — obiekty charakterystyczne miasteczek: most kratownicowy na Narwi, pomnik króla w Knyszynie, Rynek w Tykocinie

Status: Proposed (agent landmarks-s24, 2026-11-21). Numer nadany przez lidera.
Powiązane: przegląd `artifacts/vqa-wave5` (pomnik = szara „butelka”, Rynek Tykocina = pusty trawnik, most = belka),
ADR 0067 (hero_bridge), 0227 (Rynek w Knyszynie), 0307 (B-16 / B-18 przy moście), 0318 (woda Narwi), 0316, D43 (referencje
tylko z otwartych źródeł), docs/06 (anti-slop).

## 1. Most DW671 na Narwi (ul. Puchalskiego, OSM w96942026, 194,8 m)

**Co stoi naprawdę** (Commons „Tykocin Most drogowy 01–09”, Zala, 2025-09-20, CC BY-SA 4.0; ortofoto GUGiK 2024 0,25 m):
cztery stalowe przęsła kratownicowe z jazdą dołem i parabolicznym pasem górnym (słupki i krzyżulce z prętów
przewiązanych, tężniki górne kratowe, tablice w skośne pasy na portalach), farba srebrnoszara; chodniki na wspornikach
na zewnątrz dźwigarów, niebieska belka krawędziowa i balustrada z niebieską ramą i jasnymi szczeblinami; filary
betonowe z izbicami. Na obu końcach krótkie przęsła belkowe.

**Decyzja.** Nowa reguła generatora `kind: truss_bridge` (`tools/worldgen/streetscape/truss_bridge.py`), nie asset
z Blendera: most musi iść dokładnie po wygenerowanej jezdni (niweleta, spadki, szerokość po D94), a geometria jest
w całości prętowa — liczy się ją ze stacji łańcucha tak samo jak pomost. Hak w `roads/build_world.py` zaraz po
`hero_bridge.apply`.

- **Zostaje bez zmian:** jezdnia, krawężniki, kapy, bariery SP, spód pomostu, kolizja drogi, korytarz trasy, woda
  (ADR 0318) i słupki B-16 „3,7 m” / B-18 „12 t” 15 m przed obiektem (ADR 0307; test pilnuje `limit_signs.placed`).
- **Znika:** generyczna balustrada na krawędzi kapy (`<chain>:parapet`) oraz filary i przyczółki „co 30 m z reguły”
  (łańcuch pomijany w `build_bridge_supports`).
- **Dochodzi:** na każde przęsło kratowe dwa dźwigary 0,30 m za krawędzią kapy (pas górny i dolny jako ciągłe skrzynki,
  słupki i krzyżulce Pratta jako pręty przewiązane: dwie półki + zygzak przewiązek, blachy węzłowe), tężniki górne
  tylko tam, gdzie zostaje skrajnia, zastrzały portalowe, tablice w pasy na skrajnych portalach, chodniki wspornikowe
  1,55 m z balustradą, filary na stykach przęseł (oczep, ściana, pale, izbica od strony napływu), przyczółki.
  LOD0 → warstwa `buildings`, LOD1 → `buildings_low` (pręty pełne, bez przewiązek, szczeblin i wsporników).
  Kolizja: pasy dolne + 1 m ponad nimi, filary, przyczółki; tężniki górne bez kolizji.

**Dane i ich status.**

| Wielkość | Wartość | Źródło / status |
|---|---|---|
| przęsła od południa | 15 (belka) + 51 + 39 + 38 + 37 + 15 (belka) m | ortofoto 2024, ±1 m (przesunięcie radialne pasów uwzględnione); suma 195 m = OSM 194,8 m |
| liczba pól | 12 (główne), 9 (pozostałe) | 12 policzone na zdjęciu 05; 9 = WORKING_VALUE (ta sama długość pola) |
| strzałka pasa górnego | 1 : 6,5 rozpiętości (7,8 m / ~5,8 m) | zdjęcie 05, WORKING_VALUE |
| układ krzyżulców | Pratt, opadające ku środkowi | zdjęcia 05 / 06, ESTIMATED |
| skrajnia pod tężnikami | ≥ 4,30 m nad jezdnią | B-16 „3,7 m” + 0,5 m zapasu znaku (zał. 1 do Dz.U. 2003 nr 220 poz. 2181, pkt 3.2.17 — przytoczone z pamięci, UNVERIFIED) + 0,1 m; WORKING_VALUE |
| przekroje prętów, chodnik, balustrada, filary | `truss_bridge.DEFAULTS` | proporcje ze zdjęć 02 / 04 / 09, WORKING_VALUE |
| strona napływu (izbice) | wschód | zdjęcia 04 / 06 robione od wschodu pokazują izbice; kierunek nurtu z BDOT nie sprawdzony — UNVERIFIED |
| kolory | `truss_steel`, `truss_rail_blue`, `truss_picket` | zdjęcia 02 / 05 / 09, WORKING_VALUE (zdjęcie to nie pomiar albedo) |

Żaden piksel zdjęć nie trafia do repo ani buildu; brak tekstur, napisów i herbów.

## 2. Pomnik na Rynku w Knyszynie (Zygmunt August)

Zdjęcia właściciela 1 i 8 (`Data/raw/refs/owner-knyszyn-2026-11-15`, poza gitem): ciemny brąz, szeroki płaszcz
opadający z ramion, mała głowa w koronie, szary granitowy cokół; osobny blok z zegarem słonecznym przed figurą.
Dotychczasowy model (ADR 0227): sześcioboczna bryła 2,34 m w materiale `steel_painted` — za mała, za wąska, plastikowa.

**Decyzja.** `knyszyn_park_props_0227._king` buduje figurę toczoną (`streetscape/monument_kit.py`: przekroje
superelipsy per pierścień) 16-boczną w LOD0 / 8-boczną w LOD1: wysokość ~3,2 m na cokole 1,05 m (z porównania z ludźmi
i cokołem na zdjęciu 1; WORKING_VALUE), 1,25 × 1,05 m u dołu, zwężenie ku ramionom, szyja, głowa, obręcz i zęby korony,
wałek kołnierza, dwie krawędzie rozchylonego płaszcza, łańcuch. Materiały `monument_bronze` (patyna) i
`monument_granite`. Pozycja, oś, blok zegara i kolizja jak w ADR 0227 (kolizja podniesiona do nowej wysokości).
To stylizowana sylwetka, nie skan ani kopia rzeźby; status w QA zostaje `PROXY_NOT_APPROVED` do oceny krytyka.

## 3. Rynek w Tykocinie (Plac Stefana Czarnieckiego)

**Dane.** Ortofoto GUGiK 2024: po rewitalizacji plac to brukowana płyta z pomnikiem, obejście wokół dwóch trawników,
**bez drzew** — dlatego drzew nie dodano (zadanie mówiło „drzewa”; dane mówią, że ich tam nie ma). OSM (pbf 2026-11-08)
ma tylko pieszą pętlę w99624671; brak węzłów pomnika, ławek, latarni i drzew. Pomnik: Commons „Tykocin pomnik Stefana
Czarnieckiego 01 / 05 / 08” (CC BY-SA 4.0), „…, 1762 01” (CC BY-SA 3.0 pl), „Mglisty poranek na placu Czarnieckiego…”
(CC BY 4.0) — manifest `Data/raw/refs/tykocin-rynek-commons/manifest.jsonl`.

**Decyzja.**
- Trzy `paved_area` w `Data/Regions/tykocin/overrides.yaml`: płyta, obejście wschodnie i zachodnie
  z otworami na trawniki; obrysy z ortofoto, ±1 m (ESTIMATED). Materiał `yard_paving` — generator nie ma zestawu
  kostki kamiennej (`paved.py` mapuje sett → yard_paving).
- `streetscape/tykocin_rynek_0320.py`: pomnik (trzy stopnie, kute ogrodzenie, cokół prosty, cokół „wazowy” toczony
  o przekroju zaokrąglonego kwadratu, figura w długim płaszczu z buławą w wyciągniętej prawej ręce, piaskowiec +
  złocona buława), wysokość ~7,5 m (WORKING_VALUE, szacunek względem ogrodzenia i domów), zwrot na południe
  (ESTIMATED z oświetlenia na zdjęciach południowych); na trawniku wschodnim kwadratowy basen w kamiennej obudowie,
  ośmioboczna rabata i długa niska rama (kształty z ortofoto, przeznaczenie ESTIMATED); 10 ławek w miejscach ciemnych
  podłużnych znaków wzdłuż południowej krawędzi (ESTIMATED).
- **Latarni nie dodano**: na ortofoto 0,25 m nie da się ich odróżnić od donic — UNVERIFIED, potrzebne zdjęcie z ziemi
  z pozycjami (Mapillary / właściciel).

## 4. Otwarte

1. Ukośna krata ciemniejszych pasów bruku na płycie Rynku (widoczna na ortofoto i zdjęciu „Mglisty poranek…”) —
   wymaga zestawu kostki kamiennej; dziś jednolita kostka betonowa.
2. Latarnie i donice Rynku w Tykocinie — brak danych o pozycjach.
3. Liczba pól krótkich przęseł, układ krzyżulców i strona izbic mostu — do potwierdzenia zdjęciem z boku każdego
   przęsła.
4. Materiały mostu i pomników są jednolite (kolor + chropowatość); zacieki rdzy, nity i spękania kamienia wymagają
   własnych zestawów tekstur.

## 5. Liczby (build_world + render kontrolny High / clear, Win64, 2026-11-21)

| Obiekt | LOD0 (tris) | LOD1 (tris) | Uwagi |
|---|---|---|---|
| most kratownicowy (`truss_bridges`) | 26 154 | 5 302 | 4 przęsła kratowe, 5 filarów, 2 przyczółki; usunięte 92 tris generycznej balustrady + filary z reguły |
| Rynek w Tykocinie (`tykocin_rynek_0320`) | 2 870 | 1 562 | pomnik, ogrodzenie, 10 ławek, basen, rabata, rama; 120 tris kolizji |
| król w Knyszynie (figura + cokół + zegar) | 682 | 196 | było 180 / 180 |

Kamery mostu, przed (`artifacts/vqa-wave5/tykocin-bridges/stats.txt`, worktree win-build) → po (`artifacts/landmarks-s24/r2-bridge/stats.txt`);
szacunek edytora przed batchingiem SRP, inne worktree i stan main, więc różnica zawiera też cudze zmiany:
`tyk_narew_on_deck` 1 116 523 → 1 170 767 tris, draws 571 → 604; `tyk_narew_side` 1 011 482 → 1 124 176, draws 390 → 443;
`tyk_narew_eye_ab` 1 119 672 → 1 173 652, draws 616 → 648. Nowe materiały: 4 (most) + 4 (pomniki) w LOD0;
LOD1 pomników używa materiałów już obecnych w kaflu. Pomiaru FPS w playerze nie robiono (bramka = build, CLAUDE.md pkt 2).

Rundy render → SBS → poprawka: 2 (r1: czerwona farba z `viaduct_concrete` na filarach i chodniku → `truss_concrete`;
bruk `park_flush` przebijany przez teren → zwykły `paved_area`; korona króla zbyt „kolczasta”, szyja za cienka →
szersza głowa, niska korona). Arkusze: `artifacts/landmarks-s24/sbs/r2-*.jpg`.

## Dopisek (tykocin-plaza-s24, 2026-11-27): pomnik Czarnieckiego jako hero asset, ławki i mała architektura Rynku

Powód: `artifacts/critic-s24-wave11/CRITIC.md` pkt 10 — „posąg niskopoligonowy, gładki cokół bez zacieków; ławki
identyczne, ustawione równo” (kadr `look-tykocin-plaza-cab-0325`). Zamyka §4.4 dla pomnika w Tykocinie i częściowo §4.2
(donice); latarnie nadal otwarte.

### Rozbieżność z treścią zadania
Zadanie mówiło o „patynie brązu”. Pomnik Czarnieckiego w Tykocinie jest **z piaskowca** (1762; wszystkie zdjęcia Commons
z `Data/raw/refs/tykocin-rynek-commons`), z metalu są tylko złocona buława i ciemnozielony karwasz na prawym
przedramieniu. Zrobiono więc wietrzenie kamienia (ciemna skorupa we wnękach i pod gzymsami, zacieki, porosty, jaśniejszy
odnowiony cokół), a patyna (ścieżka `_BRONZE_PATINA` z ADR 0331) trafiła tylko na karwasz i rękawicę. Zasada „nie
zmyślaj” ma pierwszeństwo przed opisem zadania.

### Decyzja
1. **Hero asset z Blendera** (skill `blender-hero-asset`): `tools/blender/world/landmarks/make_czarniecki.py` →
   `art-source/world/landmarks/tykocin_czarniecki/{tykocin_czarniecki.npz, _meta.json}` z `dims.json` (wymiary i źródła,
   wszystko `WORKING_VALUE`). Wynik w zwykłym gicie (npz ~0,34 MB, nie LFS — budowa świata nie może zależeć od LFS);
   test pilnuje, że sha256 generatora i `dims.json` w `_meta.json` zgadza się z repo.
   - high poly: postać złożona z zamkniętych brył (toczony żupan i delia z fałdami, kończyny, części głowy, wałki
     futra, hełm u stopy) i **zespolona remeshem wokselowym 6 mm** w jeden „wykuty” blok (775 k trójkątów); loki
     futra i pasma brody jako przemieszczenie na zespolonej powierzchni. Głowa (4,5 mm, 74 k) i cztery kartusze gzymsu
     (9 mm, 94 k) to osobne bloki z własnym budżetem;
   - low poly: decymacja kwadrykowa do budżetu (sylwetka zostaje, płaskie tkaniny dostają mało trójkątów);
   - architektura (platforma, stopnie, cokół prosty, cokół „wazowy” z wgłębionymi polami inskrypcyjnymi, gzyms) jako
     jawne siatki ciągnięte po profilu wokół kwadratu, twarde krawędzie tam, gdzie profil je ma;
   - **wypiek do `COLOR_0` względem high poly** (promienie BVH): AO, brud we wnękach (AO krótkiego zasięgu), osłonięcie
     od deszczu, zacieki pod każdym gzymsem, porosty od północy, wilgoć u podstawy, jaśniejszy odnowiony cokół. Shader
     bez zmian: ścieżka `facade_tint` (ADR 0348: `albedo *= 2 * rgb`). Zero zmian w C# i shaderach;
   - nowy zestaw modulacyjny `sandstone_weathered_tint` (`sets_plaza.py`: ziarno, uławicenie, wżery, łuszczenie, cienkie
     zacieki wzdłuż v; kafel 1,6 m) — niesie to, co mniejsze od dłoni; duże plamy są w wierzchołkach.
2. **Poza** odczytana z Commons 01 / 08 / „1762 01”: prawa ręka wyciągnięta w przód–bok mniej więcej poziomo z buławą
   trzymaną pionowo (na zdjęciu z dołu wygląda na uniesioną — perspektywa), głowa zwrócona ku buławie, lewa dłoń na
   rękojeści szabli, żupan do połowy łydki z pasem i pętlicami, delia podbita futrem odrzucona na prawe ramię, długa
   rozdwojona broda, głowa odkryta (ADR 0320 miał czapkę — na zdjęciach jej nie ma), hełm przy lewej stopie.
   Kartusze na czterech ścianach gzymsu (dwa widać na zdjęciach, dwa ESTIMATED). Bez napisów i herbów.
3. **`tykocin_rynek_0320.py`** wstawia asset (LOD0 → `buildings`, LOD1 → `buildings_low`) i dokłada to, co cienkie lub
   stoi obok: ogrodzenie na platformie (słupki narożne, dwie poprzeczki, płaskie szczeble z grotami), cztery puste
   tablice na froncie, cztery kamienne słupki z łańcuchem, 8 donic z begoniami wokół pomnika (ESTIMATED ze zdjęć).
4. **Ławki i donice**: 10 ciemnych znaków z ortofoto (tożsamość ESTIMATED) = 6 ławek + 4 skrzynie z kwiatami (na
   zdjęciu we mgle wzdłuż krawędzi stoją skrzynie). Ławki z żeliwnymi bokami w **3 wariantach**: z podłokietnikami
   1,8 m, prosta 1,5 m (4 szersze deski), bez oparcia 1,8 m. Każda obrócona o 2–9° w losową stronę i przesunięta do
   ±0,25 m w poprzek / ±0,3 m wzdłuż rzędu (ziarno = indeks znaku, więc wynik jest powtarzalny). Zużycie w `COLOR_0`:
   własny ton każdej deski (od świeżej bejcy do wyszarzałej), wymieniona jasna deska, wytarta przednia krawędź
   siedziska, ciemne czoła desek, ugięcie środkowych desek, w ~1/5 ławek z oparciem brak jednej deski.
   Materiały: `wood_planks_bench` (zestaw `wood_siding`), `planter_flowers` (zestaw `hedge_foliage`, kolor kwiatów /
   liści per wierzchołek), żeliwo = `fence_anthracite`. Kosze na śmieci pominięte (nie ma ich na żadnym zdjęciu).
5. LOD1 kamienia, drewna i kwiatów **zachowuje własny materiał z `COLOR_0`** (3 dodatkowe wywołania w warstwie low
   jednego kafla), żeby pomnik nie zmieniał barwy przy przełączeniu LOD; reszta LOD1 jak dotąd na materiałach kafla.
6. Kamery kontrolne `czarniecki_figure_0320b`, `czarniecki_34_0320b`, `czarniecki_pedestal_0320b`,
   `plaza_furniture_0320b` (authored, przeżywają regenerację).

### Budżet i uzasadnienie

| Pozycja | ADR 0320 | Teraz | Uwagi |
|---|---|---|---|
| asset pomnika LOD0 | — | 26 476 | figura 10 500, głowa 2 600, kartusze 1 300, architektura 11 240 + 448 (kostka platformy), buława 420 |
| asset pomnika LOD1 | — | 1 914 | figura 540, głowa 110, kartusze 96, architektura 1 064, buława 120 |
| cały Rynek (`tykocin_rynek_0320`) LOD0 | 2 870 | 35 446 | + ogrodzenie, łańcuchy i żeliwo ławek 3 036, deski ławek i skrzyń 2 592, kwiaty 3 072 |
| cały Rynek LOD1 | 1 562 | 3 164 | 9 % LOD0 |
| materiały | 4 | +3 (`monument_sandstone_aged`, `wood_planks_bench`, `planter_flowers`) | `monument_sandstone` (ADR 0320) nieużywany |
| tekstury | — | +1 zestaw 1024² (`sandstone_weathered_tint`) | reszta to zestawy już w buildzie |

Dlaczego tyle: pomnik jest jedynym obiektem charakterystycznym Rynku i celem kadru z kabiny; 26,5 k to tyle, co most
kratownicowy z tego samego ADR (26 154) i ok. 0,8 % budżetu klatki knyszyn-w (3,17 M p95, ADR 0327). LOD0 jest tylko
w warstwie `buildings` (blisko); z daleka zostaje 1,9 k. Architektura ma gęstą siatkę (11 k) celowo — zacieki i plamy
żyją w wierzchołkach, więc krok siatki 8,5 cm jest rozdzielczością wietrzenia; tańsza wersja wymagałaby własnej
tekstury 2K dla jednego obiektu. Testy: `tests/gis/test_truss_bridge_0320.py` (asset ≤ 27 k / LOD1 ≤ 2 k, Rynek ≤ 36 k,
LOD1 ≤ 10 % LOD0, kolory wierzchołków w obu LOD, warianty i obrót ławek). **FPS w playerze nie mierzony.**

### Pętla wizualna
Look-dev Blender (Cycles, LOD0 z wypieczonym kolorem) r1–r4, `artifacts/tykocin-plaza-s24/lookdev/`: r1 futro jak
„stos naleśników”, ręka za krótka, kartusze jak kraby → r2 próba ważonej decymacji zniszczyła korpus (odrzucona) →
r3 głowa jako osobny blok, nieregularne loki, kartusz z ramą → r4 broda wyłożona na pierś.

Unity (High / clear, Win64; kafel `tykocin` przebudowany w prywatnej kopii derived worktree, `build_world` exit 0,
630 s): przed `artifacts/tykocin-plaza-s24/vqa-before/` (import stanu main), po `vqa-after1/` → `vqa-r2/` → `vqa-after/`.
r1: skrzynie jasne jak surowa sosna, kwiaty jak złożone kartki w paski (kępki za duże, UV zdegenerowane), tablice
za duże i białe, kamień oliwkowy → r2: drewno ×0,6, tablice −30 %, kamień jaśniejszy i mniej zielony → r3: futro
ciemniejsze od żupana (jak na „1762 01”), masa kwiatów zielona z drobnymi kępkami kwiatów. Arkusze zdjęcie | przed | po:
`artifacts/tykocin-plaza-s24/sbs/`.

**Znalezisko przy okazji:** figura z ADR 0320 stała **tyłem do DW671** — kadr `czarniecki_figure_0320b` „przed” (z
południa) pokazuje plecy i pelerynę, choć `MONUMENT_FORWARD` mówił „południe” (bryły toczone miały przód po stronie −y).
Nowy asset ma przód = +y w swoim układzie i w kadrze z południa widać twarz, pętlice i buławę po lewej jak na Commons 01.
Sam zwrot pomnika (południe) pozostaje ESTIMATED.

### Otwarte
- Ocena `visual-critic` (subagent nie tworzy subagentów — do zlecenia przez lidera); pomiar FPS w playerze.
- Inskrypcje pól cokołu (na zdjęciach czytelne jako poziome wiersze) i herb kartusza pominięte — bez liternictwa w świecie.
- Latarnie Rynku: na zdjęciach stoją stylizowane dwuramienne latarnie, w grze zostały słupy uliczne z reguły dróg
  (pozycji latarni nie ma w danych; ADR 0320 §4.2 bez zmian).
- Twarz z bliska jest uproszczona (2,6 k trójkątów na głowę); z ziemi (≥ 8 m, głowa 7 m nad brukiem) czyta się broda,
  wąsy, łuk brwiowy i łysina. Bez mapy normalnych — całe wietrzenie jest w wierzchołkach i w zestawie kafelkowym.
- Pozycje donic i podział 6 ławek / 4 skrzynie są ESTIMATED; zdjęcie właściciela z Rynku rozstrzygnie.


## Dopisek plaza-barn-fix-s24 (2026-11-27, worktree `agent-a8bad7a40407c997e`): skrzynie, kwiaty, cokół i ławki Rynku (krytyka s24 dzień 27, pkt 1)

**Uwagi krytyka:** skrzynie z kwiatami za duże (1,6–2 m na kadrze, w kodzie 1,1–1,25 m + nawis kwiatów) zamiast ok.
0,8–1,0 m; kwiaty blade, szaro-fioletowe (zdjęcie: karminowa begonia, pierścień 8–10 skrzyń przy ogrodzeniu); cokół za
czysty (brak patyny, inskrypcji); ławki identyczne.

**Decyzja (`tykocin_rynek_0320.py`, `make_czarniecki.py`, `materials.py`):**
1. Skrzynie przy pomniku: **10 sztuk** w pierścieniu `RING_M = 2,80 m` od osi (3 z przodu, 3 z tyłu, po 2 na bokach),
   między krawędzią platformy (2,45 m) a linią łańcucha (3,1 m); `MONUMENT_BOX` 0,91 × 0,40 × 0,32 m + kopuła kwiatów 0,25 m.
   Skrzynie na krawędzi placu (`EDGE_BOX`) 0,97 × 0,42 × 0,34 m. Rozrzut ±4 cm i ±4° (ustawiane ręcznie). Mniejsze skrzynie
   mają po 2 szersze deski na bok (było 3). Układ ESTIMATED (Commons 01 / 08, mglisty poranek), wymiary WORKING_VALUE.
2. Kwiaty: kopuła wystaje 3 cm ponad krawędź i 12 % poza nią (było: brzeg 2 cm pod krawędzią); udział kwiatów 74 %
   wierzchołków masy / 88 % kępek dla begonii (było 14 % / 72 % — masa czytała się jako zielona z fioletem); podstawa kępki
   to przyciemniony własny kolor (wcześniej mieszanie czerwieni z zielenią dawało szaro-fiolet). `planter_flowers`
   0,25 / 0,08 / 0,15 → **0,30 / 0,07 / 0,12**: begonia ≈ 0,48 / 0,008 / 0,036 linear, liść ≈ 0,03 / 0,067 / 0,018.
3. Cokół (asset przebudowany Blenderem 4.2.16, `generator_sha256` w meta): odnowiony blok i stopnie mniej „czyste”
   (redukcja skorupy 0,45 → 0,72, rozjaśnienie 1,24 → 1,13), zacieki spod pasa bez redukcji (×1,15), ciemniejszy nalot
   w dolnej części: 0,8 m od górnego stopnia w górę bloku, stopnie i cokół platformy (bryzgi, glony). **Pole inskrypcji:**
   gładkie pole z wypukłą ramką (1,20 × 0,72 m, listwa 5,5 cm, 1,8 cm przed licem) na froncie bloku — tekstu nie dodano,
   bo brak czytelnego źródła (bez zmyślonego liternictwa). LOD0 26 476 → **26 516** (+40 trójkątów ramy), LOD1 bez zmian.
4. Ławki: dwie bejce `BENCH_STAINS` — ciemny orzech i cieplejszy kasztan (×1,32 / 1,02 / 0,78), kolejność
   `BENCH_STAIN_OF = (0, 1, 1, 0, 1, 0)`: nigdy trzy jednakowe obok siebie. WORKING_VALUE.

**Budżet (zmierzony):** Rynek LOD0 35 446 → **35 678** (limit testu 36 000), LOD1 3 164 → 3 284; kwiaty 3 072 → 3 584,
deski 2 592 → 2 272. Unity (edytor Win64, High / clear, `stats.txt`): `czarniecki-pedestal-0320b` `drawsEst` 293 → **293**,
`trisExact` +232; `plaza-furniture-0320b` 370 → **370**; `look-tykocin-czarniecki` 307 → **307**; `look-tykocin-plaza-photo-0325`
317 → **317**. Materiały +0.

**Pętla wizualna:** look-dev cokołu `artifacts/plaza-barn-fix-s24/lookdev/`; Unity przed (kod HEAD 0e9424aaa, kafel
przebudowany w prywatnej kopii derived) / po: `artifacts/plaza-barn-fix-s24/vqa-{before,after}/tykocin/`, arkusze
przed|po `sbs/tykocin-*.jpg`, `sbs/czarn-side.jpg`. Okiem: pierścień małych skrzyń z czerwonymi kopułami przy ogrodzeniu
jak na Commons 01; petunie na krawędzi placu nasycone (fiolet / róż); rama pola inskrypcji czytelna z kadru cokołu.
**Otwarte:** nalot cokołu jest umiarkowany (z kadru 10 m czyta się głównie zacieki i ciemniejszy dół) — ocena
`visual-critic` do zlecenia przez lidera; ławki — różnica bejc widoczna z bliska, z kabiny słabo.

## Dopisek codex-monument-face-s24 — twarz, fałdy i buława

W punkcie 1 przeglądu `critic-s24-day27` twarz zlewała się w jedną plamę. Zdjęcia Commons „1762 01” i „01”
pokazują odkryte czoło, cofniętą linię włosów, wydatny nos, wąsy i rozdwojoną brodę. Hełm leży przy stopie.
Detale odtworzono z tych zdjęć i z ujęcia „08”. Proporcje rzeźbionych detali są `WORKING_VALUE`.

- Powierzchnię twarzy ukształtowano ciągłym profilem z zagłębieniami oczodołów i nozdrzy. Wąsy zwężają się przy
  policzkach, a dwa pasma brody układają się na piersi na różnej wysokości. Remesh głowy ma krok 3,6 mm.
- Żupan i delia mają fałdy o różnej szerokości i głębokości. Ich grzbiety i węższe zagłębienia zbiegają się ku
  punktom podparcia tkaniny. Buława ma czytelniejszy trzonek i płytką bruzdę na łączeniu głowicy, widoczną na zdjęciu.
- Na karwaszu i rękawicy zapisano w `COLOR_0` wypiek AO oraz maski z krzywizny high poly. Ujemna krzywizna,
  krótkie AO i pionowe ślady spływu wzmacniają zieleń w zagłębieniach. Wypukłe, odsłonięte krawędzie dostają
  jaśniejszy ton zgodnie z ADR 0331. W piaskowcu mocniej zaznaczono rysy twarzy i pas osadu u podstawy gruszki.
- Na północnej ścianie cokołu zmniejszono liczbę kolumn siatki LOD0 z 15 do 9 w powierzchniach prostych.
  Cztery dodatkowe kolumny profilu pola na gruszce i próbki na narożach zachowują położenie. Zysk w budżecie
  pokrywa gęstszą głowę i buławę.

| Pomiar | Przed | Po |
|---|---:|---:|
| Rynek LOD0 | 35 678 | 35 832 |
| Rynek LOD1 | 3 284 | 3 284 |
| Pomnik LOD0 | 26 516 | 26 670 |
| Pomnik LOD1 | 1 914 | 1 914 |
| Głowa LOD0 | 2 600 | 3 798 |
| Buława LOD0 | 420 | 504 |
| Cokół i platforma LOD0 | 11 728 | 10 600 |

Dane pochodzą z metadanych NPZ i z `tykocin_rynek_0320.build` uruchomionego na obydwu wersjach assetu.
Do limitu Rynku pozostało 168 trójkątów LOD0.
