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
