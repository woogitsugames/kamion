# Rondo Knyszyn (DK65 × DW671) — pomiar na ortofoto GUGiK (ADR 0274)

Narzędzie: `tools/worldgen/qa/roundabout_ortho.py` (ortofoto GUGiK WMS `PZGIK/ORTO/WMS/StandardResolution`, warstwa
`Raster`, EPSG:2180; data arkusza z usługi `SkorowidzeWgAktualnosci`; klient `osm-research-client/1.0`). W gicie są
wyłącznie liczby — żaden piksel ortofotomapy nie jest zapisywany (licencja źródła: `docs/LICENSES.md`, wiersze
`gugik-orto-*`).

```
uv run --project tools/worldgen python tools/worldgen/qa/roundabout_ortho.py probe knyszyn 1426801304 docs/reports/roundabout-0274/knyszyn_ortho_probe.json
```

## Wynik (2026-11-16): ronda nie ma na ortofoto

| | wartość | skąd |
|---|---|---|
| arkusz w środku pierścienia (EPSG:2180 760623,71 / 611996,27) | N-34-106-B-b-1-4, **2025-05-27**, piksel 0,1 m | skorowidz 2025; skorowidz 2026 — brak arkusza; 2024: 2024-05-27, 0,25 m |
| asfalt w kole r < 2,5 m wokół środka | **100 %** (`centre_disc_asphalt_share` 1,0) | na rondzie stałaby tam wyspa |
| asfalt na okręgu osi pierścienia (r 8,79 m) | 91 % | |
| `roundabout_visible` | **false** | zdjęcie pokazuje zwykłe skrzyżowanie czterowlotowe sprzed przebudowy |

Wniosek: promieni krawężnika, szerokości wlotów ani długości wysepek ronda **nie da się zmierzyć** na ortofoto GUGiK
(stan na 16.11.2026). OSM też ich nie daje: pierścień way 1426801304 v1 (2025-09-03) był `highway=proposed`, v2
(2026-01-05, changeset 176857414) ma `source=Yanosik` — ślady GPS, same osie, bez krawężników i wysepek. Zdjęcia
właściciela 9–11 (dron) są tylko lokalnie u lidera (`Data/raw/refs/owner-knyszyn-2026-11-15/`), w chmurze ich nie ma.
Dlatego wartości ronda w `Data/Regions/knyszyn/overrides.yaml` zostają **WORKING_VALUE / ESTIMATED** (`confidence: low`,
pole `verify`), a test `test_knyszyn_overrides_and_probe_are_consistent` przypomni o pomiarze, gdy sonda zobaczy rondo.

## Co zmierzone (stan sprzed budowy; tylko jako tło)

Szerokość asfaltu ramion co 5 m wzdłuż osi z grafu, od węzła rozdziału na zewnątrz (`arm_carriageways` w JSON):

| ramię (way) | mediana | uwagi |
|---|---|---|
| DK65 N (232511646) | 7,8 m (7,4–8,0; 9,3–9,4 m w odległości 10–15 m) | zgodne z override `dk65-carriageway-width` (asfalt 7,3–7,6 m + linie); poszerzenie 9,3 m = dawny pas do skrętu |
| DK65 S (286990127) | 5,9 m — **odczyt nieważny** | wschodni pas ma nową, ciemniejszą nakładkę; klasyfikator bierze za asfalt tylko jaśniejszą część |
| DW671 E (1464342641), W (1478765548) | 3 i 2 stacje | krawędzie grafu 21 i 12,6 m — za krótkie na medianę |

## Ta sama miara dla wygenerowanego ronda

`measure_mask()` czyta dowolny raster „asfalt / nie-asfalt”. Test `test_generated_kerbs_read_back_with_the_orthophoto_ruler`
rasteryzuje obrys generatora (0,1 m/px) i odczytuje tym samym kodem promień zewnętrzny pierścienia (±0,3 m), 8 łuków
wyokrąglających i 4 wysepki — po pojawieniu się nowego ortofoto to samo polecenie `probe` da liczby do porównania 1:1.
Dokładność: krawędź asfaltu ±0,3 m, promień łuku z dopasowania okręgu do widocznej z środka części krawężnika —
rząd ±50 % przy łukach 6–8 m (krótki łuk; test dopuszcza 0,5×–2×), długość wysepki ±0,5 m.

## Porównanie obrysu: ADR 0218 → ADR 0274 (dane z gita, test `test_knyszyn_outline_is_tighter_than_adr_0218`)

| | ADR 0218 (domknięcie 6 m wokół śladów OSM) | ADR 0274 (projektowane pasy + promienie) |
|---|---|---|
| szerokość wlotu 2 m za krawężnikiem pierścienia (W, S, E, N) | 13,1 / 11,8 / 12,9 / 13,4 m | 10,9 / 11,0 / 11,5 / 11,4 m |
| to samo 5 m i 8 m dalej | 11,1 / 9,9 / 11,1 / 10,9 → 9,6 / 8,3 / 10,4 / 8,4 m (lejek) | 10,6–11,2 → 9,6–11,2 m (równoległe; DK65 z wysepką) |
| asfalt w pasie 3 m za krawężnikiem pierścienia | 165,5 m² | 141,3 m² (−15 %) |
| wysepki (od krawędzi pierścienia) | S ~8 m, N ~7 m | S 0,6–29,2 m, N 0,6–20,2 m, W 0,6–16,3 m, E 0,6–5,1 m (każda przecięta przejściem; za przejściem E zostaje < 3 m² — asfalt) |
