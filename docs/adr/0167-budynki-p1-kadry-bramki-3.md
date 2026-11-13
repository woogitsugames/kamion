# ADR 0167 — P1 budynków w kadrach bramki 3 (cm92458760, cm109685822, wieżowiec przy Kwadracie)

Status: PROPOSED na gałęzi `bldg-0167` (2026-11-13, s17); nie scalone. Liczby w „Walidacja” są zmierzone na świecie
tej gałęzi; ocena `visual-critic` jeszcze wymagana (subagent nie uruchamia subagentów).
Źródło: `docs/reports/visual/REVIEW-2026-11-13-s16b-final.md` (P1 cm92458760: „bezokienny biały prostopadłościan
x 0,1–0,3”, „budynek EC szary zamiast niebieskiego”; P1 cm109685822: „budynek z prawej beżowy 3-kondygnacyjny vs
niebieski biurowiec”), `artifacts/live/p1-0161.md` („Budynki (lider)”). Kryterium: D51 (rozpoznawalność miejsca).

## 1. Ustalenia (dane, nie domysły)

Narzędzia: `artifacts/bldg-0167/tools/map.py` (ortofoto GUGiK 2024-05-27 0,25 m + obrysy + stożek kamery SBS),
`crop.py`. Zdjęcia tylko jako referencja (Commons: Rakoon cm92458760 2020-07-11 CC BY 3.0, cm109685822 2021-09-04
CC0; Mapillary richlv 177786140912399 / 178689077481862 2020-08-15 CC BY-SA 4.0).

| Obiekt | Rekord | Było | Zdjęcie / ortofoto |
|---|---|---|---|
| „biały prostopadłościan” cm924 | `osm:way/591365138`, 34 m², building=service, brak BDOT/LoD1 → wysokość domyślna 6,0 m | biała bezokienna bryła 6 m | półzagłębiona komora: ~1,6 m jasnoszarej ściany z kratkami + ciemna płyta dachu ~0,45 m (ściana 8,0 m = 960 px, ściana 170 px, płyta 50 px) |
| niebieski budynek EC | `bdot:2BE4B431-CA0E-…`, „siedziba firmy”, LoD1 2024 4,45 m, 1 kond. | szary tynk, ciemne okna pasmowe | jasnoniebieski tynk, rząd białych okien dwudzielnych co ~3 m na ścianie NE, ciemniejszy niebieski człon od ulicy |
| akumulator ciepła EC | `osm:way/279896715`, building=industrial, okrąg 21,8 m, brak BDOT/LoD1 → 6,0 m | dysk 6 m (niewidoczny) | zbiornik ~39 m: górna krawędź 310 ±15 px nad linią oka przy f = 1142 px i 148 m → 40 ±2 m nad okiem; kontrola: przesunięcie dachu na ortofoto ~15 m wobec ~14,5 m dla wieżowca 41,81 m (LoD1). Jasny płaszcz, niebieski pas ~9 m pod koroną |
| pawilon z prawej cm109 | `bdot:ffe33067-…`, „obiekt handlowo-usługowy”, 8,57 m, 2 kond. | beżowy tynk, okna punktowe | niebiesko-szara okładzina, witryny na całym parterze od drogi (NW), rząd małych okien piętra, ciemna attyka |
| wieżowiec (177786 / 178689) | `bdot:2BE4B431-CA0F-…`, 41,81 m, 11 kond. | jasnoszary | bladożółty tynk (zdjęcia + elewacja widoczna na ortofoto) |

Wysokość budynku w kadrze cm109 była poprawna (2 kondygnacje wg BDOT, 8,57 m LoD1) — „3-kondygnacyjny” w recenzji
to odczyt rytmu okien generatora; po zmianie parter to witryny, piętro to jeden rząd okien.

## 2. Decyzja

1. `tools/worldgen/streetscape/buildings_mesh.py` `load()`: nowy klucz override'u budynku `height_m` (2 linie) —
   autorska wysokość dla obiektów bez rekordu LoD1/BDOT; rekord `buildings.geojson` nie jest przepisywany.
2. `tools/worldgen/streetscape/materials.py`: jeden nowy materiał `plaster_blue` (albedo 0,09/0,19/0,31 odczytane z
   cm92458760 względem białych ram okien; WORKING_VALUE). Bez wariantu `__far_*` — tylko dla autorskich frontonów.
3. `tools/worldgen/streetscape/frontage.py`: nowy opcjonalny klucz frontonu `glass_lod1` — materiał szyb tylko w LOD1
   (runda 2). Tier Low rysuje wyłącznie LOD1; LOD1 chunków 6_6 i 6_7 nie ma prymitywu szkła, więc szyby autorskich
   frontonów idą tam materiałem ramy (`hall_flashing`) zamiast dokładać prymityw. LOD0 bez zmian (szkło).
4. `Data/Regions/bialystok-industrial-c/overrides.yaml` — 8 authored_overrides (przeżywają reimport):
   `g3a-ec-kiosk-height` (2,0 m, płyta dachu), `g3a-ec-blue-office` (fronton `plaster_blue`, 11 okien na NE),
   `g3a-ec-heat-accumulator` (39 m, płaszcz `plaster_grey`, niebieski pas 28,5–30,5 m dookoła),
   `g3a-kwadrat-blue-pavilion` (ściana `hall_plinth` — łupkowy szary; runda 1 z `plaster_blue` czytała się jako
   królewski błękit i dokładała prymityw w 6_6; witryny NW, pas okien piętra), `g3a-office-tower-colour`
   (`plaster_beige`, wariant dalekiej elewacji istnieje), `g3a-ec-round-tanks` i `-2` (okrągłe zbiorniki: gładki
   płaszcz `plaster_light` zamiast ceglanego „biurowca” z oknami; kolor WORKING_VALUE), `g3a-fuel-station-kiosk-height`
   (3,4 m z cienia na ortofoto; poniżej 5 m i 60 m² generuje się jako budynek gospodarczy).
5. Bez marek: panel z logo na zbiorniku i szyldy nie są odtwarzane.

Odrzucone: ciemniejszy drugi odcień niebieskiego dla członu od ulicy (`hall_wall_accent_blue` jest zastrzeżony dla
okładzin hal — `frontage.plan` odrzuca `hall_wall_*`; inny materiał = +1 draw na chunk i LOD); grafitowy biurowiec
kadru 326454015490067 (`bdot:2BE4B431-C34C-…`, render jasny, zdjęcie ciemne) — wymaga ciemnego materiału z wariantem
dalekiej elewacji albo frontonu (+2 draw w chunku 2_4): otwarte.

## 3. Walidacja

Świat rundy 2 (`build_world` 615 s, exit 0; import 574 s, exit 0), gałąź `bldg-0167`. Dowody (poza gitem):
`artifacts/bldg-0167/` w katalogu głównym — `pairs/Low-clear|Low-overcast` (42 + 42 pary SBS),
`before-after-cm924-cm109.jpg`, `before-after-tower.jpg`, `r2/budget.txt`, `r2/stats-Low-clear.txt`, `tools/`.

**Budżet, tier Low, 48 kamer kontrolnych, baza `artifacts/world-int-s16b/stats-Low-clear.txt`** (`tools/budget2.py`):

| Wielkość | Wynik |
|---|---|
| draws świata (renderery + rzucające cień) | +0 w 36 kamerach, +1 w 4, +2 w 8 (g3a-eye-s0262, g3a-rondo-bie-approach, photo-biezenstwa-ground, kwadrat-park-gate, stretch-02…05: +1 renderer, +1 cień) |
| draws instancjonowane (rekwizyty + drzewa) | −5…+3 (25 kamer +0) — nie z tej zmiany: rozkład instancji różni się między buildami |
| draws razem | −3 (kwadrat-park-gate) … +4 (cab-mirror-front); 23 kamery +0 |
| trójkąty | −0,83 % (cab-grain) … +0,95 % (stretch-01); cel ≤ +2 % spełniony |

Cel „draws +0” **nie jest spełniony w 12 kamerach** (max +2 po stronie świata). Liczba prymitywów budynków w LOD1
się nie zmieniła (`chunk_6_6.low.glb` 22 → 22, `chunk_6_7.low.glb` 20 → 20; zamiany 1:1 `plaster_light__far_ribbon` →
`plaster_beige__far_ribbon` i `plaster_white` → `plaster_blue`). Zmieniły się obwiednie prymitywów w 6_7:
`plaster_grey` sięga teraz 176 m n.p.m. (było 152; zbiornik 39 m), `plaster_blue` obejmuje 118 × 88 m (zastąpiony
`plaster_white` obejmował 24 × 23 m). Przypuszczalna przyczyna +1 renderer / +1 cień: prymityw wcześniej odcinany
przez frustum jest teraz widoczny (zbiornik rzeczywiście stoi w kadrze) — UNVERIFIED, nie rozbijane na poziomie
rendererów Unity. Runda 1 dawała do +7 (2 nowe prymitywy LOD1), runda 2 je usunęła.

**Kadry** (Low-clear, przed = `world-int-s16b/pairs`, po = runda 2). Względem bazy zmieniły się tylko cm92458760
(11,6 % pikseli połowy renderu) i cm109685822 (4,3 %); pozostałe 40 par ≤ 2,3 % (szum drzew/impostorów).

- cm92458760: biały bezokienny prostopadłościan zniknął (niska komora z ciemną płytą dachu); budynek EC niebieski z
  rzędem okien; zbiornik akumulatora 39 m z niebieskim pasem stoi w kadrze. Uwaga recenzji 0161 („biały
  prostopadłościan w x 0,33–0,45”) — zamknięta. Różnice pozostałe: ramy okien ciemne (zdjęcie: białe), brak panelu z
  logo (celowo), zbiornik w kadrze dalej w prawo niż na zdjęciu (poza kadru — zakres 0160/0161).
- cm109685822: elewacja od drogi (NW) łupkowoszara z pasem witryn i rzędem okien piętra zamiast beżowej z oknami
  punktowymi. **Częściowo**: ściana szczytowa w słońcu nadal czyta się jako jasna, ciepłoszara (ten sam `hall_plinth`,
  oświetlony), a całość jest szara, nie niebieska szklana jak na zdjęciu.
- 177786140912399 / 178689077481862 (wieżowiec): zmiana na `plaster_beige` **praktycznie niewidoczna** (0,2 % pikseli);
  render dalej jasnoszary, zdjęcie: żółta ściana szczytowa, biały front. Niezamknięte.

**Testy**: TESTY_PLACEHOLDER

`build_world`: road consistency 65 (na trasie 1 `lane_blind_end`), ściany terenu > 0,15 m: 4 (max 0,345 m) — bez
zmian względem rundy 1 tej gałęzi. Telefon: nie mierzone (zmiana ≤ +2 draws / < 1 % trójkątów na Low).
Ocena `visual-critic`: do wykonania przez lidera.

## 4. Otwarte

- Biurowiec kadru 326454 (jak wyżej).
- Wieżowiec: żółty szczyt wymaga nasyconego materiału z wariantem dalekiej elewacji (+draw w 6_6) albo frontonu
  z osobnym materiałem szczytu.
- Pawilon cm109: niebieski odcień szkła / okładziny (obecnie neutralny szary), ściana szczytowa.
- +1 renderer / +1 cień w 12 kamerach Low: potwierdzić przyczynę na poziomie rendererów (lub przyjąć jak D62).
- Ramy okien frontonu są ciemne (jeden materiał ram w `frontage`); na zdjęciu białe.
- Wysokość zbiornika 39 m i kiosku 2,0 m: WORKING_VALUE (zdjęcie + ortofoto) do sesji zdjęciowej właściciela.
- Pozy kadrów (cm924 B, cm109 C) nie były ruszane — położenie brył w kadrze zależy od nich (zakres 0160/0161).
