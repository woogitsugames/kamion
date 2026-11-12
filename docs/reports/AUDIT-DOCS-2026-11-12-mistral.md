# AUDIT DOCS — 2026-11-12 (mistral)

Audyt spójności dokumentacji na gałęzi `mistral/3-docs-consistency`. Zakres zmian: tylko pliki `*.md` w `docs/` oraz ten raport i skrypt `tools/docs/adr_index.py`. Data audytu: 2026-11-12, baza: `main` @ `e0328ea4`.

## 1. ADR (`docs/adr/`)

Indeks wygenerowany automatycznie: **`docs/adr/README.md`** (tabela: numer, tytuł, status, data, link), skrypt **`tools/docs/adr_index.py`** (czysty Python, bez zależności; ponowne uruchomienie: `python3 tools/docs/adr_index.py` z katalogu głównego repo, sam drukuje też audyt; `--check` = tylko audyt).

Wyniki audytu (111 plików `NNNN-*.md`):

- **Duplikaty numerów:** brak.
- **Luki w numeracji (20):** 0026, 0027, 0028, 0030, 0031, 0032, 0034, 0035, 0036, 0037, 0040, 0053, 0054, 0055, 0057, 0090, 0123, 0127, 0128, 0129. Zakres faktyczny: 0001–0131.
- **ADR bez pola statusu (6):** `0099-road-surface-wear.md`, `0108-light-sky-exposure-post.md`, `0111-sbs-evidence-confidence.md`, `0116-landmarks-remiza.md`, `0119-landmarks-wiadukt-dk8.md`, `0121-background-horizon.md` (w indeksie oznaczone „⚠ brak statusu"). Uwaga: część ADR używa polskiego nagłówka „Stan:" zamiast „Status:" — skrypt uwzględnia oba.
- **Odwołania „ADR NNNN” do nieistniejących ADR (6 numerów, 10 miejsc w plikach .md/.py/.cs/.ps1):**
  - ADR 0032 — `tests/physics/test_scenario_strictness.py`
  - ADR 0090 — `docs/owner/GPT-TASK-02-S10.md`, `docs/reports/visual/REVIEW-2026-11-11-s10-gpt-0087-0090.md`, `artifacts/firestation-r10/STATUS.md` (ten ostatni jawnie mówi „bez nowego ADR0090”, więc to świadome odwołanie do nieistniejącego numeru)
  - ADR 0123 — `docs/owner/START-PROMPT-S11.md`
  - ADR 0127 — `docs/adr/0130-sbs-poses-g3b.md`
  - ADR 0134 — `docs/11_DECYZJE_WLASCICIELA.md` (D53), `docs/reports/REVIEW-2026-11-12-s12-0134-0135.md`
  - ADR 0135 — `docs/11_DECYZJE_WLASCICIELA.md` (D52), `docs/reports/REVIEW-2026-11-12-s12-0134-0135.md`

  Nie poprawiano treści odwołań (poza zakresem — to decyzja właściciela: albo dopisać ADR-y 0134/0135, albo skorygować odwołania).

## 2. Linki względne

Przeskanowano 239 plików: wszystkie `docs/**/*.md` oraz `HANDOVER.md` i `CLAUDE.md` (linki inline `[t](url)`, referencyjne `[r]: url` i `href="…"`; bez kotwic i URL-i zewnętrznych).

- **Zepute linki względne: 2**, oba celowe, nie są literówkami — wypisane, nie poprawiane:
  - `docs/LICENSES.md` → `ATTRIBUTION-mapillary.md` (plik generowany, pojawi się po pierwszym użyciu `--attribution`; opisane w tekście obok linku)
  - `docs/refs/sbs-priorities.md` → `../../artifacts/sbs-gate3/latest/index.html` (katalog `artifacts/` poza gitem)
- **Literówki ścieżek do poprawy: 0** (brak też near-missów typu wielkość liter).

## 3. Rejestr licencji `docs/LICENSES.md`

Zestawiono z zasobami śledzonymi w git: `git ls-files` dla `art-source/**` oraz `game/Assets/**/*.{png,jpg,tga,wav,ogg,mp3,fbx,glb,ttf,otf}` poza `_Generated` — **638 plików** (453 w `art-source/`, 185 w `game/Assets/`).

- **BOM na początku pliku:** brak (plik zaczyna się od `#`).
- **Duplikaty wpisów:** brak (żadne ID tabeli nie występuje dwa razy; duplikują się tylko wiersze separatorów `|---|`, co jest poprawne).
- **Brak spacji w oznaczeniach licencji (typu „CC BY-SA2.5”):** nie znaleziono wariantów bez spacji przy wersji licencji. Znaleziono i **poprawiono** 7 innych braków spacji (formatowanie): wiersz 166 (`only1k`, `+twig_alpha`, `verified2026-11-11`, `No7197`) oraz wiersz 242 (`sprawdzone2026-11-11`, `twig_alpha1kPNG`, `MD5API`, `modelu3D`).
- **Zasoby bez wpisu, które NIE wynikają jednoznacznie z kodu generatora — do decyzji właściciela (nie zgadywano licencji):**
  - `art-source/truck/brand/bielik.svg`, `art-source/truck/brand/narew.svg` — własne fikcyjne znaki marek, używane jako wejście przez `tools/blender/truck/make_logos.py` i `geom.py`; brak dedykowanego wpisu (jest tylko `trakt.svg` w wierszu `truck-exterior-a6`).
  - `art-source/truck/exterior/door_interface.json` — używany przez `tools/blender/truck/exterior/build.py`/`body.py`; brak wpisu (jest tylko `glass_interface.json`).
  - `art-source/truck/exterior/qa/*.py` (9 skryptów QA) — kod projektu, brak jawnego wpisu.
- **Uwagi (wynikają z kodu generatora, więc nie wymagają wpisu, ale warto doprecyzować rejestr):**
  - `game/Assets/_Project/Environment/Boot/T_Checker_1m.png` — generowany w kodzie przez `BootSceneBuilder.cs` (`CreateCheckerTexture`); brak osobnego wiersza.
  - 169 plików WAV w `game/Assets/_Project/Audio/Generated/Clips/**` — śledzone w gicie, mimo że wiersze audio (`audio-engine-r6-synth`, `audio-sfx-synth`, `audio-layers-synth`) mają „W gicie? generator tak; WAV nie”. Pochodzenie wynika jednoznacznie z generatorów `tools/audio/`, ale kolumna „W gicie?” jest niezgodna ze stanem faktycznym.
  - Wszystkie pozostałe zasoby (m.in. `art-source/world/vegetation/**`, `art-source/world/signs/**`, `art-source/truck/{exterior,interior,trailer}/export/**`, `art-source/world/materials/_renders/**`, `game/Assets/_Project/Rendering/**`) mają wpis lub wynikają wprost z wskazanego kodu generatora (`world-trees`, `world-forest-hlod`, `world-foliage-textures`, `world-sign-faces`, `world-ground-pbr-renders`, `truck-exterior-a6`, `truck-interior-a6`, `trailer-curtainsider-13-6`, `WorldTextureGenerator.cs`, `DrivingLabSceneBuilder.cs`).
- **Potencjalny duplikat treści (nie usunięty — sprzeczne informacje, decyzja właściciela):** w sekcji „Świat — otoczenie kafla C” dwa sąsiednie akapity (wiersze ~140 i ~142) oba zaczynają się od „Wszystkie zasoby poniżej są wygenerowane naszym kodem”, ale przeczą sobie co do użycia tekstur CC0 (jeden: „od ADR 0063 używane”, drugi: „nie użyto” z wyjątkami).

## 4. Pliki zmienione w tej gałęzi

- `docs/adr/README.md` — nowy, wygenerowany indeks ADR
- `tools/docs/adr_index.py` — nowy skrypt generatora/audytu
- `docs/LICENSES.md` — 7 poprawek formatowania (braki spacji)
- `docs/reports/AUDIT-DOCS-2026-11-12-mistral.md` — ten raport
