# Brief: nowy region „z grubsza” (D63/D64) — Białystok w stronę Knyszyna

Agent: world-builder/geo-worldgen (Opus lub Fable), n = ring-region-0203, ADR 0203. Najpierw: docs/owner/S20-AGENT-PREAMBLE.md, docs/05, docs/11 (D63), tools/worldgen/regions.py + Data/Regions/bialystok-dojlidy (wzór najmłodszego regionu, ADR 0179), research na gałęzi origin/research/cloud2-next-region-ring (R9: dostępność danych; przegląd docs/reports/REVIEW-2026-11-14-s20-cloud2-r9.md — wysokości z LoD1, BDOT10k i LoD1/LoD2 powiatu 2002 sprawdzone na GUGiK; NIE pobierać Drzewa3D 45,8 GB).

Cel (wersja przejezdna, D63): jeden kafel/region przylegający do obecnych (wybierz odcinek obwodnicy S8/DK8 lub DK19 z węzłem, ~3–5 km trasy, uzasadnij w ADR), zdefiniowany jako nowy region w regions.py + Data/Regions/<id>/ (region.yaml, overrides.yaml minimalne), ingest danych (OSM, NMT, ortofoto, BDOT/LoD1) przez istniejące skrypty, build_region → build_world → import-region → scena gry dla regionu, trasa startowa (export-route), kamery kontrolne (8–12 z drogi), visual-qa Low/High, pytest/EditMode. Bez szlifu punktów — tylko usunięcie błędów krytycznych (dziury w terenie, zawieszone mosty/budynki, brak kolizji, crash). Raport: czas buildu, pamięć WORLD_MEMORY Low/High, draws/tris na kamerach, lista największych braków do szlifu (do backlogu). APK + krótki przejazd A16 robi lider.

## AKTUALIZACJA D64 (ważniejsza niż powyższy wybór odcinka)
Kolejność: (1) rozbudowa Białegostoku w stronę wylotu na Knyszyn, (2) droga do Knyszyna, (3) Knyszyn. Pierwszy agent (0203): ustal z OSM trasę ciężarówki Białystok → Knyszyn (wypisz drogi i węzły, długość), zaplanuj podział na kafle/regiony (od obecnych regionów C/Dojlidy do granicy miasta, korytarz, Knyszyn), zapisz plan w ADR 0203, a potem zbuduj z grubsza PIERWSZY kafel Białegostoku na tej trasie (przylegający do istniejących regionów, jeśli to możliwe), przejezdny. Kolejne kafle = kolejni agenci.

## AKTUALIZACJA 2 (właściciel): zwykła droga, nie ekspresówka; budowa ekspresówki przy Knyszynie
Trasa Białystok → Knyszyn = istniejąca zwykła droga (krajowa/wojewódzka), nie droga ekspresowa. W rejonie Knyszyna trwa budowa ekspresówki: sprawdź OSM (`highway=construction`, `construction=*`, `proposed`, objazdy, daty edycji), datę ortofoto i NMT względem robót; odtwarzaj stan bieżący przejezdny, plac budowy uproszczony (WORKING_VALUE), a rozbieżności źródeł wypisz w ADR jako pytania do właściciela.

## Zdjęcia właściciela z Knyszyna
`docs/owner/OWNER-PHOTOS-KNYSZYN.md` (pliki w research/_incoming/owner-knyszyn-photos-2026-11-14, bez EXIF/GPS; prywatność — patrz plik). Strefa budowy z żółtym oznakowaniem tymczasowym jest na kadrach 20260728_*.
