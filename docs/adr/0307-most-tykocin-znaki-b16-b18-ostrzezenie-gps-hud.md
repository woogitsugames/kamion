# ADR 0307 — most DW671 na Narwi w Tykocinie: znaki B-16 / B-18 w świecie, ostrzeżenie o limicie w GPS i HUD (D91)

Status: Proposed (agent bridge-warn-s24, 2026-11-19). Numer nadany przez lidera.
Powiązane: D91 (trasa zostaje przez most, gra ostrzega), ADR 0303 (znalezisko: limit mostu; `maxaxleload=10` nieaktualne),
0302 (podróże GPS przez kafle, `RelaxTruckLimits`), 0164 / 0150 (limity ciężarówki w grafie KRTG v2), 0279 (znaki z OSM,
B-18 z wartością), 0283 (HUD: rząd kafli ostrzeżeń), D43 (zdjęcia tylko z otwartych źródeł).

## 1. Co pokazują zdjęcia (stan znaków)
Most: OSM w96942026 (`bridge=yes`, `maxheight=3.7` od 2017-01-23, `maxweight:hgv=12 ton` od 2026-08-22), w grafie kafla
`tykocin` krawędź `w96942026:1123400724-1123401506`, 194,8 m, EPSG:2180 (751871,2 600508,6) → (751883,1 600314,1).

| Źródło | Data | Co widać |
|---|---|---|
| Mapillary 462178938209236, 934907033961350, 182213347108443 (sekw. `alo0ggn3…`, autor grobin) | 2020-06-23 | wjazd **południowy** (od miasta, jazda na północ): na jednym słupku po prawej **B-16 „3,7 m”** nad **B-33 „40”**; dalej A-32 (oszronienie) z tabliczką przy portalu kratownicy. Brak B-18 / B-19. |
| Mapillary 206576431107020, 775602599816523, 3960288177424526 (sekw. `t99tgzly…`, grobin) | 2020-09-20 | wjazd **północny** (od Knyszyna, jazda na południe): **B-16 „3,7 m”** po prawej, ok. 15–20 m przed kratownicą (odległość szacowana z kadru). Brak B-18 / B-19. |
| Wikimedia Commons „Tykocin Most drogowy 08.jpg” (autor Zala; seria 01–09) | 2025-09-20 | wjazd południowy: **B-16 „3,7 m”** nad **B-33 „40”**, A-32 + tabliczka „Narew”, tablice w skośne pasy na portalach. Brak B-18 / B-19. |

Licencje: Mapillary CC BY-SA 4.0 (Graph API v4, `tools/refs/mapillary_fetch.py`, manifest z autorem / ID / sha256 w
`Data/raw/mapillary/tykocin-bridge/manifest.jsonl`); Commons CC BY-SA 4.0 (`Data/raw/refs/tykocin-bridge-commons/LICENSES.json`).
Zdjęcia są wyłącznie referencją, poza gitem i buildem. Wycinki: `artifacts/bridge-warn-s24/refs/sheet1.jpg`, `commons_sheet.jpg`.

Zasięg źródeł (2026-11-19): Mapillary w bbox mostu ma sekwencje 2010-11-19 (5 zdjęć) i 2019-07-03 … 2020-09-20, nic nowszego;
Panoramax (`api.panoramax.xyz/api/search`, bbox mostu) — 0 zdjęć; Commons — najnowsze zdjęcia mostu z 2025-09-20.

**Wnioski.**
- **B-16 „3,7 m” — potwierdzony przy obu wjazdach** (2020 i 2025). Zgodny z OSM `maxheight=3.7`.
- **B-18 „12 t” — niepotwierdzony.** Nie ma go na żadnym zdjęciu, ale tag `maxweight:hgv=12` pochodzi z 2026-08-22, czyli jest
  o 11 miesięcy nowszy od najnowszego zdjęcia. Wartość 12 t = **WORKING_VALUE z OSM**. Uwaga: `maxweight:hgv` w OSM opisuje
  limit masy dla ciężarówek — w terenie może to być B-18 albo B-5 z tabliczką; do sprawdzenia zdjęciem po 08.2026.
- **B-19 (nacisk osi) — brak** na zdjęciach i w OSM dla mostu.
- **DK65, `maxaxleload=10` (ADR 0303).** Zdjęć po 13.03.2021 (uchylenie Dz.U. 2017 poz. 878) nie ma: Mapillary przy rondzie
  DK65 w Knyszynie (jedyne miejsce w grafach korytarza, gdzie krawędź 10 t styka się z krawędzią bez limitu) kończy się na
  2020-09-20. Na 4 obejrzanych klatkach wylotów DK65 z tego skrzyżowania (2020-06-23: 307618994191688, 227037455858388;
  2020-09-20: 4051264164960522, 497139681404601) znaku B-19 nie widać. To nie dowodzi stanu dzisiejszego — **nadal
  UNVERIFIED**, wniosek ADR 0303 (dane nieaktualne) bez zmian.

## 2. Znaki w świecie
**Decyzja.** Reguła generatora, nie ręczne obiekty: `tools/worldgen/streetscape/limit_signs.py` (wołana w `stage.py` po
`osm_signs`). Dla każdego odcinka łańcucha na **obiekcie** (`bridge` / `tunnel`) z `maxheight` i / lub `maxweight:hgv`
(inaczej `maxweight`) w `roads.graph.json`: jeden słupek na kierunek jazdy, 15 m przed obiektem (WORKING_VALUE; zdjęcia:
ok. 15–20 m), po prawej, twarzą do ruchu; B-16 na górze, B-18 pod nim. Wartości czytane tymi samymi parserami co graf GPS
(`navgraph.build_route_graph.parse_length_m / parse_weight_t`) — znak, GPS i HUD mają jedno źródło.
- Nowa twarz parametryczna `B-16_<m>` (`signs.py::b16`, Z1 pkt 3.2.17: wartość z „m” między dwoma czarnymi trójkątami,
  przecinek dziesiętny); `B-18_<t>` istniał (ADR 0279). Własny schematyczny rysunek, bez cudzych grafik.
- Zakres celowo wąski: tylko obiekty. `maxweight` na zwykłej ulicy (Tykocin: 6 t / 12 t na 15 krawędziach grafu) to znaki przy
  skrzyżowaniach — osobna reguła, nie budowana tutaj. `maxaxleload` nie daje B-19 (jedyne wartości w korytarzu to nieaktualne 10 t).
- Różnica względem zdjęć: w terenie B-16 wisi na jednym słupku z B-33 „40” (wjazd południowy); u nas B-16 + B-18 mają własny
  słupek, a B-33 stawia istniejąca reguła prędkości. B-18 stoi mimo braku na zdjęciach (D91 + OSM, WORKING_VALUE).
- Kratownicy nad jezdnią świat nadal nie ma (ADR 0303) — fizycznie nic nie zatrzyma zestawu 4,0 m.

## 3. Ostrzeżenie w grze (bez blokowania)
**Dane.** Limity są już w grafie tras każdego kafla (KRTG v2, ADR 0164: `EdgeMaxHeightCm`, `EdgeMaxWeightC`,
`EdgeMaxAxleLoadC`, `EdgeMaxLengthCm` z OSM). Mechanizm jest ogólny — każda krawędź z limitem poniżej zestawu, w każdym kaflu.
**Decyzja.**
- `Core/Navigation/RouteRestriction.cs`: `TruckLimits` (zestaw: masa, nacisk, wysokość, długość; domyślnie stałe planera
  40 t / 11,5 t / 4,00 m / 16,47 m), `RouteRestriction` (odcinek z limitem: kilometraż trasy, punkt początku, wartości,
  które limity przekroczone), `RestrictionScout`:
  - `OnRoute` — pierwszy odcinek z limitem na trasie w zasięgu **500 m** (`WarnM`, D91) aż do jego końca;
  - `OnRoad` — bez trasy: droga pod ciężarówką śledzona w przód do 500 m, na skrzyżowaniach tylko „prosto” (≤ 40°,
    WORKING_VALUE); ostrzega też kierowcę, który jedzie bez GPS.
- Planer zapisuje odcinki z limitem w `RoutePath.Restr` (tylko plan z `RelaxTruckLimits` może przez nie przejść; legalność
  tras bez zmian), `NavTrip.Compose` przenosi je do trasy wielokaflowej (kilometraż i punkt w układzie bieżącego kafla).
- `NavigationService.Restriction` (aktualne ostrzeżenie; na trasie co klatkę, bez trasy co 0,25 s; zero alokacji) + log
  `[NAV] restriction ahead: …` / `on the restricted stretch`. Masa zestawu z modelu pojazdu (`VehicleModel.TotalMass`,
  `NavigationInstaller`); wysokość i długość nie mają jeszcze źródła w danych pojazdu — stałe planera (**WORKING_VALUE**).
- Widoki: pasek „Ograniczenie / za 450 m” ze znakami (3,7 m, 12 t) na minimapie HUD i na ekranie nawigacji w kabinie;
  znacznik-znak w miejscu początku odcinka na minimapie, pełnej mapie i ekranie kabiny; pełna mapa w opisie trasy:
  „ograniczenie: wysokość do 3,7 m, masa do 12 t”. Pokazywane są tylko limity, które zestaw przekracza.
- HUD (ADR 0283, rząd kafli — jedyny element HUD widoczny w widoku z kabiny): bursztynowe kafle „WYSOKOŚĆ 3,7 m”,
  „MASA 12 t” („OGRANICZENIE” dla nacisku / długości) zaraz po czerwonych; znikają za mostem.
- Teksty w tabelach `NavText` / `HudTexts` (PL). Nic nie jest blokowane ani przeplanowywane.

## Liczby (zmierzone 2026-11-19, `artifacts/bridge-warn-s24/`)
PLACEHOLDER_NUMBERS

## Konsekwencje / otwarte
- B-18 12 t na moście: WORKING_VALUE do zdjęcia po 08.2026 (i rodzaj znaku: B-18 czy B-5 + tabliczka).
- Kafel `tykocin` przebudowany z tej gałęzi do wspólnego `Data/raw/derived`; przebudowa z gałęzi bez `limit_signs.py`
  (np. kolejka regen-wave-2) usuwa znaki do czasu scalenia.
- Reguła znaków dotyczy obiektów; limity mas na ulicach (znaki przy skrzyżowaniach) i znaki uprzedzające z tabliczką
  odległości / F-5, F-6 przed ostatnim objazdem — osobne zadanie.
- Wysokość i długość zestawu z danych pojazdu (dziś stałe) — gdy pojawią się inne naczepy / ładunki.
- Komunikat głosowy (`NavVoice`) nie zapowiada ograniczenia.
