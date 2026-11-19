# ADR 0301 — Audyt pasów na trasie autopilota (Białystok, DK8): pasy z ortofoto jako generowane overrides, szerokość z BDOT nie poniżej standardu

Status: Proposed (agent `lanes-audit-s24`, gałąź `lanes-audit-s24`), 2026-11-19. Scalić po zakończeniu agenta DK19
(zmiany globalne generatora). Powiązane: ADR 0075 (fidelity), 0077 (`center_offset`), 0095 (`lane_edges`), 0203 / 0206 /
0208 (kafle `bialystok-maczka` / `-kleeberga` / `-knyszynska`), 0233 (`lanes_follow_width`), 0275 (przejścia na szwach).

## Kontekst
Właściciel po przejeździe autopilotem `bialystok-industrial-c → maczka → kleeberga → knyszynska` (DK8 Andersa / Maczka /
Kleeberga, Szosa Ełcka / Knyszyńska): „źle idą pasy, za wąskie jezdnie”. Dotąd pasy w `maczka` / `kleeberga` /
`knyszynska` brały się z reguł (`lanes` OSM × szerokość z BDOT10k przycięta do PTB2022 § 17), bez pomiaru; w
`industrial-c` są ręczne `lane_edges` (ADR 0095).

## Pomiar (narzędzie `tools/worldgen/qa/lane_width_audit.py`)
Przekrój prostopadły do trasy co 50 m (174 stacje), ortofoto GUGiK WMS HighResolution 0,08 m (komórki 128 m dociągnięte
`--fetch`, manifest z URL/sha256/licencją) wobec generatora w pamięci (`fidelity/gen.py`); farba = wąskie piki jasności w
≥ 20 % z 25 wierszy ±6 m (łapie przerywane P-1, odrzuca dachy aut i krawężniki). Pasy na zdjęciu — tylko ze stacji, gdzie
łańcuch linii jest czytelny (`ortho_lane_fit.station_layout`); paski z naniesionymi liniami: `artifacts/lanes-audit-s24/
{before,after}/strips_*.jpg` (każda liczba niżej obejrzana na pasku).

| miejsce (krawędź) | OSM lanes / BDOT | generator przed | ortofoto 0,08 m | generator po |
|---|---|---|---|---|
| Maczka E, 3 pasy (w249740773, w257357743, w707029850/54) | 3 / 10,5 m | 3 × 3,25 m, linie krawędziowe 10,0 m, oś jezdni 1,4–1,9 m za daleko w lewo (ku pasowi dzielącemu) | pasy 3,62–3,75 m (prawy do krawężnika 3,9 m), jezdnia 11,8 m | `lane_edges` z pomiaru, `center_offset` −1,37…−1,89 m |
| Maczka, 2 pasy (w257358866) | 2 / 7,0 m | 2 × 3,25 m | 3,59 / 3,74 m, jezdnia 8,47 m | z pomiaru |
| Kleeberga, 2 pasy (w301702369, w249740778) | 2 / 7,5 m | 2 × 3,25 m | 3,57–3,73 / 3,65–3,70 m, obok kreskowany pas dzielący P-21 | z pomiaru, oś −0,6…−0,8 m |
| Kleeberga / Maczka 3 pasy (w257355878/79, w693614875, w76073115) | 3 / 7,0–11,5 m | 3 × 3,33–3,50 m, oś przesunięta | 3,50–3,95 m, oś −0,55…−1,92 m | z pomiaru |
| Szosa Knyszyńska / Ełcka (dwukierunkowa, G) | 2 / 6,0 m | 2 × 3,00 m = 6,5 m | linie krawędziowe 6,3–6,5 m od siebie + utwardzone pobocza | bez zmian (reguła potwierdzona) |

Zbiorczo (`qa/lane_audit_compare.py`, stacje z czytelnym łańcuchem linii; błąd linii = odległość granicy pasa z ortofoto
od najbliższej linii generatora; „po” = generator w pamięci po wszystkich zmianach, ten sam kod co `build_world`,
`artifacts/lanes-audit-s24/after2/`):

| kafel | stacje przed / po | błąd linii mediana | p90 | błąd szer. pasa trasy (mediana) |
|---|---|---|---|---|
| `bialystok-maczka` | 19 / 24 | 0,50 → 0,10 m | 1,52 → 0,60 m | −0,32 → +0,10 m |
| `bialystok-kleeberga` | 27 / 28 | 0,60 → 0,25 m | 1,75 → 1,88 m (krawędzie bez fitu przy wylotach) | −0,10 → +0,12 m |
| `bialystok-knyszynska` | 14 / 15 | 0,40 → 0,40 m | 1,70 → 1,70 m | +0,05 → +0,02 m |
| `bialystok-industrial-c` | 16 | 0,25 m (ręczne `lane_edges` ADR 0095, bez zmian) | 0,72 m | 0,00 m |

## Przyczyny
1. **BDOT10k zaniża szerokość jezdni jednokierunkowych DK8** (10,5 m przy 11,8 m; 7,0–7,5 m przy 8,3–8,5 m), a
   `network.edge_section` brał ją (przyciętą w dół do wartości „trudnych warunków” 3,25 m) zamiast standardu 3,50 m.
2. **Oś OSM nie jest osią jezdni**: na Maczka/Kleeberga linia OSM biegnie 0,5–1,9 m od środka jezdni w stronę pasa
   dzielącego (rysowana wzdłuż linii pasów, jak w ADR 0095). Bez `center_offset` cała jezdnia z pasami wchodziła na pas
   dzielący, a trasa (środek pasa generatora) leżała na prawdziwej linii pasa — „pasy idą źle”.
3. **Górny limit szerokości pasa** `std + 0,25` był niższy niż dopuszcza § 17 ust. 1 dla Z / L / D (3,50 m).
4. Liczba pasów OSM na trasie zgodna z ortofoto tam, gdzie pomiar jest pewny; odcinki 3 → 2 → 3 pod wiaduktami to
   prawdziwe zjazdy / wjazdy (obok łącznica bez linii), nie błąd OSM. Linie przerywane na zdjęciu przy wylotach — patrz
   „Otwarte”.

## Decyzja
1. **Reguła szerokości (`standards.py`, `network.edge_section`)** — PTB2022 (Dz.U. 2022 poz. 1518) § 17 ust. 1, tekst
   ponownie przeczytany 2026-11-19 (`api.sejm.gov.pl/eli/acts/DU/2022/1518/text.html`): GP „standardowo 3,50 m, w trudnych
   warunkach 3,25 m”; Z / L / D „dopuszcza się … 3,50 m”; S „dopuszcza się 3,75 m”. `LANE_WIDTH_MAX` = S 3,75, Z/L/D 3,50,
   A/GP/G = std + 0,25 (WORKING_VALUE, jak dotąd). `bdot_lane_floor(cls, oneway)`: na **jednokierunkowych A / S / GP** BDOT
   może pas poszerzyć, ale nie zwęzić poniżej standardu klasy (pomiar wyżej); wszędzie indziej podłoga = wartość „trudnych
   warunków” (dwukierunkowa G Szosa Knyszyńska: BDOT 6,0 m zgadza się z liniami krawędziowymi 6,3–6,5 m — pierwsza wersja
   z podłogą 3,50 m dla G pogorszyła ją do 7,5 m i została cofnięta).
2. **Pasy z ortofoto jako generowane overrides**: `tools/worldgen/qa/ortho_lane_fit.py --region A --region B …` (wszystkie
   kafle trasy naraz — krawędź przechodząca przez szew ma ten sam identyfikator w obu kaflach i dostaje ten sam wpis) →
   `Data/Regions/<id>/overrides.ortho_lanes.json` (w gicie; `pipeline.GENERATED_OVERRIDES`, ładowane przed
   `overrides.yaml`, więc wpis autorski dla tej samej krawędzi wygrywa; krawędzie już ułożone ręcznie są pomijane).
   Stacje co 10 m po trasie, ≥ 20 m od końców krawędzi; tylko jednokierunkowe `motorway…tertiary` z ≥ 2 pasami.
   Wpis = `lane_edges` (ADR 0095), `width`, `center_offset` (ADR 0077), `edge_lines`; powstaje tylko, gdy ≥ 3 stacje,
   modalna liczba pasów ≥ 60 % stacji, MAD granic ≤ 0,25 m (zewnętrznych ≤ 0,40 m), żaden pas trunk/primary < 2,9 m.
   Strona otwarta (łącznica / strefa włączania bez linii) — brakujące granice od strony zamkniętej z szerokością pasa z
   pomiaru i liczbą pasów OSM. Wszystkie progi WORKING_VALUE. Plik jest generowany — nie edytować; reimport = ponowne
   uruchomienie narzędzia. Ten sam przekrój mierzy też **przeciwną jezdnię** dwujezdniowej (way antyrównoległy 5–16 m od
   punktu trasy), żeby obie jezdnie odsunęły się od pasa dzielącego razem; wpis odrzucany, gdy |środek − oś OSM| > 2,5 m
   albo pas > 4,2 m. Wynik: 19 wpisów (`maczka` 14, `kleeberga` 6, krawędź szwu w249740774 w obu), raport
   `artifacts/lanes-audit-s24/fit/fit_report.json` (odrzucone krawędzie z powodem).
3. `seam_taper._load_overrides` (nominalny przekrój sąsiada) i `build_world` (sha wejść w manifeście) czytają też plik
   generowany.
4. `route_start.json` czterech kafli przeliczone (`scripts/export-route.py`) — trasa idzie środkiem zmierzonego pasa.
5. Testy `tests/gis/test_lanes_audit_0301.py` (18): reguła BDOT na rzeczywistych parach (lanes, BDOT) z trasy, limity
   § 17, `station_layout` na zmierzonych przekrojach (3 pasy, 2 pasy, P-21 obok, pas do krawężnika), kolejność ładowania,
   jezdnia Maczka 3 pasy po przebudowie sieci (pasy 3,4–4,0 m, oś −1,0…−2,2 m), schemat pliku.

## Konsekwencje
- Przebudowa kafli: `bialystok-maczka`, `bialystok-kleeberga` (nowe pasy i osie), `bialystok-industrial-c` (krawędź
  w257367422 / trasa), `bialystok-knyszynska` (reguła BDOT dla łącznic trunk_link, trasa) — `build_world` + import.
  Reguła BDOT działa globalnie: każdy kafel z jednokierunkową GP i BDOT < 3,50 m/pas dostaje szersze pasy przy
  najbliższej przebudowie (lista dla lidera: kafle z `trunk`/`motorway` jednokierunkowymi — `grep '"trunk"'`).
- Narzędzie fitu działa tylko na trasie startowej (tam są stacje); reszta sieci zostaje przy regułach.

## Otwarte
- Kreskowany pas dzielący P-21 Kleeberga (3 m asfaltu między jezdniami) nie jest generowany — dziś zieleń/krawężnik.
- Krawędzie odrzucone przez fit (zbyt mało stacji / niespójna liczba pasów przy wylotach): w173990799 (wiadukt),
  w606396479, w668340288, w76073122 (tunel pod rondem), w242987870 / w301702368 / w261104557 (wyloty z pasami do skrętu
  — potrzebny profil wzdłuż krawędzi, nie jedna stała), w306609228.
- Szosa Knyszyńska: linie krawędziowe P-7 widoczne na ortofoto nie są malowane (klasa G bez override `edge_lines`).
- Łącznice jednopasowe (`lanes=1`): BDOT 7,0 m → 5,5 m (górny limit reguły) przy ~4,9 m na ortofoto (w242989867,
  `knyszynska`) — fit obejmuje tylko ≥ 2 pasy; do osobnego pomiaru.
- Strona jezdni otwarta na łącznicę / strefę włączania: brakujący pas dołożony z szerokością zmierzonego pasa (bez linii
  krawędziowej po tej stronie) — prawdziwa linia P-7 przy krawężniku bywa niewykryta (prawy pas do krawężnika 3,9 m).
- Recenzja `visual-critic` renderów przed/po: do zlecenia przez lidera (agent nie tworzy subagentów).
- Linie przerywane w miejscu zwężeń/poszerzeń (P-1e / P-6) nie są osobno weryfikowane.
