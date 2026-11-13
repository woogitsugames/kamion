# dojlidy-vis-0179 (ADR 0179, poprawki wizualne Dojlidy/Krywlany) — STATUS
- Stan: START przerwany na polecenie lidera (limit 5 h 93 %, Fable tyg. 95 %). Gałąź = main 110c756fe + ten plik. ŻADNYCH zmian w kodzie/danych, build_world i Unity NIE uruchomione.
- Przeczytane: AGENT-RULES, REVIEW-2026-11-13-s17-0174 (1R/4P/2N), ADR 0174 (kamery foto: P11-094 i P11-129 azymut UNVERIFIED).
## Plan (kolejność)
1. P0 kamery: `Data/Regions/bialystok-dojlidy/control_cameras_photo.authored.json` — P11-094 (Rosti po lewej; azymut z namiaru na budynek Rosti w buildings.geojson + przesunięcie px), P11-001 (pozycja na DDR przy bramie Kontri, nie za ogrodzeniem). Metadane: `research/mistral/p11-dojlidy-photos/` + errata `REVIEW-NOTE.md`.
2. P0 landmarki: `Data/Regions/bialystok-dojlidy/landmarks_d51.authored.json` — hala Kontri (Kuronia 3) i Bravilor: obrys/wysokość z LoD1/BDOT (`research/mistral/p12-dojlidy-landmarks/`), kolor/typologia ze zdjęć P11 v2 (`research/_incoming/mistral-p11-dojlidy-photos-v2/`); bez logo/marek.
3. P1 parking P11-063: jawny override (bez aut; krzewy + słupki biało-czerwone z łańcuchem).
4. P1 latarnie dwuramienne „Y” na Kuronii/Dywizjonu 303 (biblioteka regionu `Data/raw/derived/bialystok-dojlidy/props`).
5. P1 decale śladów opon tylko na skrzyżowaniach/wjazdach — NAJPIERW sprawdzić, czy reguła generatora dotyczy regionu C; jeśli tak: tylko region ≠ C albo opis do decyzji lidera.
6. P1 łąka lotniska (wysoka trawa/nieużytek + linia lasu na horyzoncie), płyta lotniska (dylatacje, niepowtarzalne przebarwienia).
7. P2 opcjonalnie: brama szpitala P11-129 (mur, słupy, STOP, B-33 „20”).
8. Weryfikacja: build_world dojlidy (slot heavy) → import do sceny dojlidy (slot unity, brak PHONE_RUN) → kamery Low overcast + SBS vs zdjęcia → EditMode → pytest tests/gis (region C bez różnic) → ADR `docs/adr/0179-*.md` → kopie do main `artifacts/dojlidy-vis-0179/`.
## NASTĘPNY KROK (komenda)
`cd C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dojlidy-vis-0179; Get-Content Data/Regions/bialystok-dojlidy/control_cameras_photo.authored.json, Data/Regions/bialystok-dojlidy/landmarks_d51.authored.json, research/mistral/p11-dojlidy-photos/REVIEW-NOTE.md` — potem edycja kamer P11-094/P11-001 (krok 1).
