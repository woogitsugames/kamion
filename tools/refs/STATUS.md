# STATUS: otwarte źródła referencji (D43, ADR 0066), stan 2026-11-10

Gałąź: worktree-agent-ab1fb0a47d2f0a491 (nie scalona; integruje lider).

## Zrobione
- Kod: `tools/refs/{refs_common,open_sources,gugik_ortho,bialystok_open_data}.py`, testy `tests/refs/test_open_sources.py` (48 zielonych).
- ADR 0066, README `tools/refs`.
- Pobrane (poza gitem, `Data/raw/refs/<źródło>/`, junction `Data/raw` -> główny katalog): KartaView 79 zdjęć (pokrycie ujęć 13-55, 41/55), Panoramax 23 (17/55),
  GUGiK ortofoto 55 kadrów 160 m (WMS bywa zwraca białe kafle, klient ponawia), dane Miasta Białystok (ArcGIS Online, brak drzew/oświetlenia/znaków).
- Montaże: `artifacts/refs/<źródło>/` (w worktree; skopiować do głównego `artifacts/refs` przed usunięciem worktree).

## W toku / do zrobienia
1. Commons (`--source commons --categories`) działa w tle; Openverse zwracał 504 (API chwilowo niedostępne), ponowić:
   `uv run --project tools/refs python tools/refs/open_sources.py --source openverse --interval 1.5`
2. `docs/REFERENCES.md`: dopisać tabelę źródeł; `docs/LICENSES.md`: wpisy źródeł (KartaView/Panoramax/Commons/Openverse/GUGiK ortho/Miasto Białystok).
3. Skopiować artifacts/refs z worktree do głównego repo, odpiąć junctiony (`Data/raw`, `artifacts`?) przed usunięciem worktree.
4. Raport końcowy (<= 20 linii).

## Komendy
    uv run --project tools/refs pytest tests/refs -q
    uv run --project tools/refs python tools/refs/open_sources.py --source kartaview --radius 80
    uv run --project tools/refs python tools/refs/open_sources.py --source panoramax --radius 100
    uv run --project tools/refs python tools/refs/open_sources.py --source commons --radius 600 --categories
    uv run --project tools/refs python tools/refs/gugik_ortho.py --interval 1.5
    uv run --project tools/refs python tools/refs/bialystok_open_data.py --catalog

## Log
- 19:59 commons: geosearch+imageinfo gotowe (cache 163), pobrano 83 plików, potem stoi na 429/Retry-After z upload.wikimedia.org. Następny krok: gdy proces skończy
  (lub po ubiciu) ponowić tę samą komendę (cache + manifest wznawiają bez duplikatów), potem openverse (API zwracało 504).
- Openverse: 504 na każde zapytanie o 19:4x; ponowić `open_sources.py --source openverse --interval 1.5`.
- 20:03 incremental manifest (co 10 pobran), adopt istniejących plików; commons ubity i wznawiany.
- 20:15 STAN: manifesty: kartaview 79 (by-sa), panoramax 23 (by-sa), commons 74+ (cc0 53, by 11, by-sa 10; wznawiany w tle), gugik-ortho 55, bialystok-open-data 11 warstw, openverse 0 (proces w tle, API wróciło).
  Pokrycie ujęć ulicznych+Commons: 54/55 (brak tylko #2). Podsumowanie: `uv run --project tools/refs python tools/refs/summarize.py`.
  NASTĘPNY KROK: dokończyć commons/openverse (te same komendy z sekcji Komendy; wznawiają się), potem `summarize.py`, docs/REFERENCES.md (tabela źródeł),
  docs/LICENSES.md (wpisy źródeł), skopiować artifacts/refs z worktree do głównego artifacts/refs, odpiąć junctiony, raport <= 20 linii.

## Log 20:55 (przejecie sesji 5)
- Nowe: tools/refs/object_refs.py (obiekty kwadrat-park, fire-station, dusk-sodium), tools/refs/curation/<obj>.json (odrzucenia po przegladzie), matplotlib+shapely w pyproject.
- STRAZ POZARNA: OSM way/211035271 JRG nr 2, ul. Andersa, 53.157322, 23.156306 (miasto: Andersa 46, 53.157380, 23.155985). fire-station: 17 refs + 2 ortho + plan, INDEX.md gotowy.
- kwadrat-park: kartaview/panoramax 0 trafien (teren prywatny), commons-geo 5, commons-search w toku (429 z thumb bywa wolne).
- Commons ogolny: 140 plikow; openverse 1 (API wolne).
  NASTEPNY KROK: uv run --project tools/refs python tools/refs/object_refs.py --object kwadrat-park dusk-sodium  (wznawia z cache)
  potem: ... open_sources.py --source commons --radius 600 --categories --interval 1.5 ; ... --source openverse --interval 1.5 ; summarize.py ;
  object_refs.py --object fire-station kwadrat-park dusk-sodium --index-only ; docs/REFERENCES.md + docs/LICENSES.md ; pytest tests/refs -q

## Log 2026-11-10 (domkniecie, agent Fab/Patch)
- Commit 306fd3a: retry na bledy sieci, Retry-After <= 120 s, zapis manifestu co 3 pobrania. Dodane 2 testy klienta HTTP; `pytest tests/refs -q`: 50 zielonych.
- summarize.py: kartaview 79 (41/55), panoramax 23 (17/55), commons 134 (cc0 92, by 17, by-sa 25; 54/55), openverse 0, gugik-ortho 55, miasto 11 warstw. Bez obrazu tylko ujecie 2.
- ADR 0066 uzupelniony o stan koncowy; REFERENCES: dusk-sodium poprawione na 0 obrazow (bylo opisane jak gotowe).
- artifacts/refs skopiowane do glownego `artifacts/refs` (kwadrat-park, dusk-sodium, coverage).
- OTWARTE: openverse (504), dusk-sodium (0 obrazow), detale Kwadrat Parku UNVERIFIED.
  NASTEPNY KROK: uv run --project tools/refs python tools/refs/object_refs.py --object dusk-sodium ; uv run --project tools/refs python tools/refs/open_sources.py --source openverse --interval 1.5 ; uv run --project tools/refs python tools/refs/summarize.py
