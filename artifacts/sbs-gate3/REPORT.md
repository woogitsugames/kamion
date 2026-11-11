# Stream J / ADR 0103 — REPORT (pending Unity evidence)
Wynik: PARTIAL — narzędzia gotowe, 0/40 rzeczywistych par wyrenderowanych; PHONE_RUN aktywny (właściciel potwierdził test).
Gałąź: gpt-sbs-gate3; implementacja fbafacf3; baza main 9e6e9fde; końcowy sha: git rev-parse HEAD.
40 unikalnych zdjęć Mapillary z autorami/licencją CC BY-SA 4.0/URL/SHA256, 20 przy każdym G3; żadne piksele nie trafiają do buildu.
Kamery: Data/Regions/bialystok-industrial-c/sbs_cameras.json; korekty: sbs_authored_overrides.json; metadane: sbs_references.json.
GPS -> EPSG:2180, korekta zbieżności południków, biliniowy NMT, seat=file; FOV z prostowania wg 40 modeli obiektywu; oko/horyzont nadal WORKING_VALUE.
Kod: tools/refs/sbs_gate3.py; wrapper scripts/sbs-gate3.ps1 (blokada przed KAŻDYM Unity; aspekty 4:3/16:9; Low/High x clear/overcast).
Arkusze: grid/horyzont/atrybucja/histogram; metrics.json: jasność, histogram, estymata niebo/asfalt, hashe; jawne maski polygonalne dostępne.
GIS baseline: uv run --project tools/worldgen python -m pytest tests/gis -q -> 370 passed, 1 xfailed (643.04 s), pytest-baseline.log.
Testy SBS: ta sama komenda z tests/gis/test_sbs_gate3.py -> 9 passed; tests/refs -> 51 passed; parser PowerShell i py_compile OK.
Dowody źródeł: contact-G3-A.jpg, contact-G3-B.jpg (obejrzane); coverage.json. Rendery/PNG par/statystyki Low/EditMode: PENDING.
Pokrycie: G3-A s=340.426–436.716 m, max odsunięcie 28.235 m; G3-B s=0–485.862 m, max 33.732 m. Brak zdjęć pierwszych ~300 m G3-A.
Ograniczenia: dystorsje prostowane wg metadanych SfM; dokładność modelu/roll niezweryfikowana; część zdjęć o zachodzie; kalibracja po renderach, niezależna recenzja i zdjęcia właściciela nadal wymagane.
Budżet: brak zmian runtime/świata/shaderów; przyrost kosztu z kodu gry 0 z konstrukcji, brak nowych pomiarów GPU i stats (UNVERIFIED).
ADR docs/adr/0103-gate3-side-by-side.md; każda licencja docs/refs/sbs-gate3-attribution.md (linki w LICENSES i REFERENCES).
Przewidywane konflikty: wyłącznie addytywne końce docs/LICENSES.md i docs/REFERENCES.md; nie dotykano innych strumieni/kamer.
Następny krok po zwolnieniu blokady: pwsh scripts/sbs-gate3.ps1 -EditMode (aktualny proces już czeka; nie uruchamiać drugiego).
Lider: po renderach kalibracja authored_overrides -> prepare -> render -> visual review; następnie git merge gpt-sbs-gate3, bez automatycznego PASS bramki.
Nie scalano/pushowano main ani gałęzi; artefakty kopiowane do głównego artifacts/sbs-gate3 bez commitu na main.

