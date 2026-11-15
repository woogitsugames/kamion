# 0221 — Budżet trójkątów dróg: P-23 i obrzeża placów bez wierzchołków, które nie niosą kształtu

Status: PROPOSED (gałąź `budget-fix-s21`, baza `main` `64ff11ee4`). Data: 2026-11-15. Dotyczy: ADR 0188 (DDR), 0033 (ściany terenu),
docs/06 §6 (hipoteza High ≤ 1,5–2 mln trójkątów w kadrze).

## Kontekst
Po scaleniu ADR 0188 (drogi dla rowerów) region C przekroczył budżet: kamera `stretch_04` 2 022 535 trójkątów High
(`mesh_budget.frame_estimate`; limit testów 2 000 000), `route_onramp_andersa_above` 1 993 338. Wzrosła tylko kategoria `roads`
(+28 835 w klinie `stretch_04`): `markings` +21 489, `paved` +6 983. Pomiar (tally źródeł, `KAMION_SRC_TALLY`):
1. **P-23** (symbol roweru na DDR): 44 szt. w regionie × 479 trójkątów. Obrys kół budował `Point.buffer(1.0, 32)` — 128-kąt na
   każdy z 4 okręgów kół; liczba trójkątów ≈ liczba wierzchołków obrysu (249 + 227). 21 tys. z 27,8 tys. przyrostu `markings`.
2. **Obrzeża i skarpy nawierzchni utwardzonych** (`paved._edges`): próbkowanie krawędzi co 2 m „żeby szły po gruncie”, 6 trójkątów
   na próbkę (obrzeże) — 75 814 trójkątów w klinie `stretch_04`, z czego 94 % to segmenty 2 m na prostych krawędziach nad
   wygładzonym gruntem (σ 3 m). ADR 0188 dołożył tu obrzeża DDR (5,1 km tras).
Stan sprzed 0188 (1 993 321) też nie miał zapasu, więc samo cofnięcie przyrostu nie wystarcza.

## Decyzja
- `cycleways.P23_WHEEL_QUAD_SEGS = 8`: koła P-23 jako 32-kąty. Błąd cięciwy ≤ 3,5 mm na długiej osi (1,43 m) dużego symbolu, pole
  farby w granicach 1 % (test). 479 → 183 (mały) / 483 → 187 (duży) trójkątów na symbol. Liczba symboli bez zmian (44).
- `paved._edge_keep`: z próbek krawędzi co 2 m zostają tylko te, które niosą kształt — Douglas–Peucker z tolerancją
  `EDGE_TOL_XY_M` 2 mm w planie i `EDGE_TOL_Z_M` 5 mm w wysokości (WORKING_VALUE; obrzeże wystaje 30 mm, skarpa sięga 300 mm).
  Zawsze zostają: wierzchołki, w których zmienia się stan „budowane / pominięte przy jezdni lub przy sąsiednim pasie DDR”, oraz
  gęste sąsiedztwo każdego narożnika (normalna w narożniku to dwusieczna; bez sąsiadów obrzeże zwężałoby się na całym boku, a
  skarpa skręcała — pierwsza wersja r2 dała przez to nowy punkt w `terrain_walls_qa`, r3 wraca do 3).
- `build_world._src_tally`: diagnostyka, tylko z `KAMION_SRC_TALLY=<plik.json>` — trójkąty warstw drogowych per chunk i
  `warstwa|materiał|klasa źródła`. Bez wpływu na wynik.
Nie zmieniono: limitu w testach, estymatora, funkcji ADR 0188, powierzchni placów, znaków poziomych na jezdni.

## Budżet (frame_estimate regionu C, trójkąty High / Low)
| kamera | przed (80345541c) | po |
|---|---|---|
| stretch_04 | 2 022 535 / 974 570 | 1 986 314 / 938 349 |
| route_onramp_andersa_above | 1 993 338 / 869 437 | 1 966 981 / 843 080 |
| route_onramp_andersa | 1 884 422 / 858 146 | 1 852 645 / 826 369 |
| fire_station_above | 1 777 872 / 741 511 | 1 755 524 / 719 163 |
W klinie `stretch_04`: P-23 16 286 → 6 291 (34 symbole), `paved|curb_concrete|edge` 75 814 → 55 056. Draw calle i materiały bez zmian
(te same siatki chunków). Pomiaru na telefonie nie było (zmiana tylko zmniejsza geometrię).

## Walidacja
- `tests/gis/test_budget_0221.py` (symbol P-23, `_edge_keep`: prosta, spadek, garb 2 cm, łuk R 5 m, granice pominięć, pierścień,
  plac 60 × 30 m, zapas budżetu regionu C ≤ 1,99 mln).
- Rendery przed/po (High, Low; `stretch_04`, `route_onramp_andersa`, `route_onramp_andersa_above`, zbliżenia `p23_close`, `p23_top`):
  `artifacts/budget-fix-s21/{before,after}-{High,Low}/`.
- `terrain_walls_qa`: 3 punkty jak przed zmianą.

## Otwarte
- Zmiana `paved._edges` dotyczy każdego regionu z nawierzchniami utwardzonymi, P-23 — C i Dojlidy (45 szt.). Pozostałe regiony
  dostaną lżejsze obrzeża przy następnej regeneracji; nie jest ona wymagana (stare paczki są poprawne, tylko cięższe).
- Zapas `stretch_04` to 13,7 tys. trójkątów. Kolejne dźwignie tej samej klasy (zmierzone w klinie): linie stanowisk na placach
  `marking_yard` 12,5 tys. (próbki co 2 m), krawężniki jezdni 131 tys. (stacje co 2 m także na prostych).
- Tolerancje 2 mm / 5 mm to WORKING_VALUE, ocenione na renderach edytora, nie na telefonie.
