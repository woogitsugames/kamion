# ADR 0075: Obiektywna miara zgodności dróg z OSM i ortofoto (fidelity)

Status: przyjęty (geo-worldgen), 2026-11-10. Powiązane: ADR 0074 (spójność nawierzchni, naprawy generatora), ADR 0066
(otwarte źródła referencji), ADR 0002 (zakaz Google).

## Kontekst
Właściciel: „drogi itp. mają być dosłownie takie same [jak na OpenStreetMap], żeby ktoś, kto tam mieszka, wiedział
jak jechać”. Na telefonie widział lewy pas ze strzałką „na wprost” wjeżdżający w wysepkę z trawą
(`artifacts/owner/bugs/2026-11-10-lane-into-island.webp`). Dotąd kontrola zgodności była wzrokowa (nakładki Blendera)
plus jedna metryka osi na 7 odcinkach (`docs/DATA_QA.md` §5). Brakowało liczb per odcinek i per skrzyżowanie oraz
testu, który nie pozwoli się pogorszyć.

## Decyzja
1. Pakiet `tools/worldgen/fidelity/` (Python, deterministyczny, jedna komenda):
   `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region <id> [--fetch] [--no-tile]`.
   Czyta generator w pamięci (`roads.pipeline.build` + `roads.markings.build_markings`, przechwycone wywołania strzałek
   i linii poprzecznych), więc każda rozbieżność wskazuje funkcję generatora.
2. Źródła prawdy:
   - **OSM**: ten sam wycinek Geofabrik co graf (snapshot 261108 = 2026-11-08, pobrany 2026-11-09; świeży — bez nowego
     pobierania). Wszystkie tagi dróg (także `placement`, `width:lanes`, `change:lanes`, których graf nie czyta),
     `landuse=grass`, ronda, węzły sygnalizacji/przejść. ODbL, atrybucja „© OpenStreetMap contributors”.
   - **Ortofoto GUGiK**: arkusz 0,25 m (2024-05-27) dla całego kafla + komórki WMS HighResolution 128 m @ 0,08 m/px
     wzdłuż trasy startowej i wokół obu rond (49 komórek, `Data/raw/refs/gugik-ortho-hr/`, manifest z SHA256 i URL).
     Rejestracja WMS vs arkusz: przesunięcie ≤ 0,25 m (1 px arkusza) na 3 komórkach testowych. Data nalotu mozaiki
     WMS: `UNVERIFIED` (zdjęcia wiosenne, inne niż arkusz 2024-05-27).
   - **BDOT10k**: szerokość jezdni `SZEROKOSCNAWIERZCHNI` (już w grafie, `src: bdot10k`); BDOT nie ma poligonów jezdni,
     więc krawędzie mierzymy na ortofoto.
   - **Mapillary**: tylko lista zdjęć do ręcznej weryfikacji strzałek (CC BY-SA, referencja, nie dane).
3. Metryki (szczegóły i progi WORKING_VALUE w docstringach `metrics.py` / `imaging.py`):
   (a) oś: odległość osi wygenerowanej od drogi OSM co 1 m, p50/p95/max per krawędź i dla trasy;
   (b) krawędzie: profil prostopadły co 2 m (trasa, 0,08 m/px) i co 4 m (reszta kafla, 0,25 m/px), kolor asfaltu
   uczony z wnętrza wygenerowanej jezdni (k-means w Lab, stały start), krawędź = początek ≥ 0,6 m ciągłego „nie-asfaltu”;
   boki przylegające do innej jezdni i stacje pod pomostem są pomijane (zliczane); IoU masek jezdni w oknach
   skrzyżowań w pasie 4 m wokół wygenerowanej jezdni, bez placów/chodników z danych;
   (c) pasy: `lanes`, `lanes:forward/backward`, `turn:lanes*` vs przekrój generatora; tagi ignorowane przez generator;
   pasy policzone na ortofoto (linie malowane między wykrytymi krawędziami, moda z odcinków 24 m);
   (d) rozdzielenia: wysepki/pasy dzielące generatora (domknięcie 7 m minus jezdnia) — udział asfaltu pod nimi na ortofoto
   (≥ 60 % = „wysepki nie ma na ortofoto”), oraz wysepki z ortofoto leżące na wygenerowanej jezdni;
   (e) ronda: promień (dopasowanie okręgu), pasy, wloty/wyloty OSM vs ramiona generatora;
   (f) strzałki P-8 i linie P-14/P-13: farba na ortofoto w miejscu strzałki (±12 m wzdłuż pasa) i pasmo poprzeczne;
   (g) połączenia: każda droga przejezdna OSM w kaflu jest w grafie; stopień węzłów trasy OSM vs ramiona;
   plus test „pas w wysepkę”: z końca każdego ramienia na wprost 20 m po pasie; trafienie w rozdzielenie ≤ 12 m
   i porównanie z ortofoto (wysepka generatora na prawdziwej jezdni = błąd generatora).
4. Wyniki: `Data/Regions/<id>/generated/fidelity_qa.json` (w gicie, z SHA256 wejść i modułów `roads/*.py`),
   `artifacts/fidelity-r9/overlays/*.jpg` (≤ 960 px), `artifacts/fidelity-r9/DIFFS.md` (rozbieżność → przyczyna →
   moduł/funkcja).
5. Test `tests/gis/test_road_fidelity.py` (ratchet): cele właściciela dla trasy startowej — oś p95 ≤ 1,0 m, krawędź
   p95 ≤ 0,75 m, liczba pasów zgodna w 100 % zweryfikowanych odcinków, 0 wysepek nieobecnych na ortofoto. Cele jeszcze
   niespełnione są `xfail(strict=True)` (zacznie przechodzić → test każe zaostrzyć), a stan bieżący jest zapisany jako
   linia bazowa, której nie wolno pogorszyć. Test sprawdza też, że raport nie jest przeterminowany (SHA256 wejść).

## Konsekwencje
- Zgodność jest liczbą per odcinek i per skrzyżowanie; agent ADR 0074 naprawia generator i widzi efekt w ratchecie.
- Klasyfikator ortofoto ma znane słabości (cienie drzew, chodniki w kolorze asfaltu, parkingi przy jezdni, auta na
  krawędzi): wyniki krawędzi to rozkład, nie pomiar geodezyjny; każda nakładka jest oglądana przez człowieka/agenta.
- Komórki WMS i arkusz są tylko referencją pomiarową (docs/05 §3), nigdy teksturą.
