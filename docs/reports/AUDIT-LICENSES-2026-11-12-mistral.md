# AUDIT LICENSES — 2026-11-12 (mistral)

Audyt rejestru licencji `docs/LICENSES.md` na gałęzi `mistral/14-licenses`, baza: `main` @ `4536a36f`. Zakres zmian: tylko `docs/LICENSES.md` oraz ten raport. Żadnej licencji nie zgadywano — każdy wpis ma wskazane, udokumentowane pochodzenie.

Wejście: sekcja 3 raportu `docs/reports/AUDIT-DOCS-2026-11-12-mistral.md` z gałęzi `mistral/3-docs-consistency` (lista zasobów śledzonych w git bez wpisu w rejestrze).

## 1. Zasoby bez wpisu — ustalone pochodzenie

### 1.1 `art-source/truck/brand/bielik.svg`, `art-source/truck/brand/narew.svg`

- **Pochodzenie: wygenerowane kodem repo** — `tools/blender/truck/make_logos.py` (czysty stdlib; SVG bez fontów: litery z kresek geometrycznych, znak z wielokątów; `<title>` w każdym SVG: „original, fictional").
- Dowody: commit `4ce63ae0` („make_logos.py: TRAKT / BIELIK / NAREW marks as font-free SVG"); `docs/plan/TRACK-A.md` §5 („Pliki: `art-source/truck/brand/{trakt,bielik,narew}.svg` (generator `tools/blender/truck/make_logos.py` …)"); użycie jako wejście: `tools/blender/truck/exterior/geom.py` (`load_svg_mark`) oraz `tools/blender/truck/interior/build_interior.py --badge bielik|narew`.
- **Licencja: project licence** (własne, fikcyjne znaki marek; nie pochodzą z żadnego zewnętrznego źródła).
- **Zmiana w rejestrze:** nowy wiersz `truck-brand-marks-a2`. `trakt.svg` pozostaje we wzmianince wiersza `truck-exterior-a6` (bez duplikatu).

### 1.2 `art-source/truck/exterior/door_interface.json`

- **Pochodzenie: wygenerowany kodem repo** — `tools/blender/truck/exterior/body.py`, funkcja `door_interface()` (pole `"generator": "tools/blender/truck/exterior/body.py (door_interface)"` zapisane w samym pliku). Zawartość: dane `WORKING_VALUE` (layout drzwi, stopni, szyby — klasa pojazdu, do potwierdzenia zdjęciami właściciela).
- Dowody: `git log --follow` (pierwsze wprowadzenie m.in. w `cfe0dd60`, `e5b0394c`); czytany przez `tools/blender/truck/exterior/build.py:185` i `tools/blender/truck/interior/build_interior.py` (`DOOR_IF_PATH`).
- **Licencja: project licence.**
- **Zmiana w rejestrze:** dopisano do kolumny „Użycie" istniejącego wiersza `truck-exterior-a6`, obok `glass_interface.json` — analogicznie, bo oba pliki interfejsów są zapisywane przez generator exterior (`a6_export.py (glass_interface)`, `body.py (door_interface)`).

### 1.3 `art-source/truck/exterior/qa/*.py` (9 skryptów)

- **Pochodzenie: kod projektu** — jednorazowe skrypty QA rundy ADR 0115 (audyt szwów atlasu, siatek kół, plandeki, retencji brudu), wprowadzane commitami `wip(truck): …` (m.in. `e5ede77e`, `31cdcbd3`, `aaa896e6`). Uruchamiane ręcznie jako `blender -b --python <skrypt>`, tylko do odczytu geometrii; wyniki trafiają do ignorowanego `_Generated`, bez zmian produkcyjnych.
- **Licencja: project licence.**
- **Zmiana w rejestrze:** nowy wiersz `truck-exterior-qa-0115`.

## 2. DO USTALENIA PRZEZ WŁAŚCICIELA

**Brak.** Wszystkie zasoby z listy wejściowej mają jednoznacznie ustalone pochodzenie własne (kod repo), więc żaden wpis nie wymagał decyzji właściciela ani zgadywania licencji.

## 3. Kontrole formatu rejestru

- BOM na początku `docs/LICENSES.md`: **brak** (plik zaczyna się od `#`).
- Duplikaty ID w wierszach tabel: **brak**.
- Zmienione pliki w tej gałęzi: `docs/LICENSES.md` (1 wiersz zmodyfikowany, 2 wiersze dodane) oraz `docs/reports/AUDIT-LICENSES-2026-11-12-mistral.md` (ten raport).
