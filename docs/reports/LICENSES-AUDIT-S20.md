# Audyt licencji i atrybucji — sesja 20 (X1, 2026-11-14)

Gałąź `docs/licenses-audit-s20`, baza: `main` @ `f2d50b6a9`. Zakres: tylko dokumenty (`docs/LICENSES.md`, ten raport, `docs/owner/ATTRIBUTION-SCREEN-DRAFT.md`). Kodu, danych ani zasobów nie zmieniano. Każde twierdzenie ma wskazany plik:linia albo URL obecny w repo; czego nie da się potwierdzić z repo, ma znacznik `UNVERIFIED`.

## 0. Inwentarz (krok 1)

### 0.1 Metoda
- `git ls-files` + `grep -rIl -i "licen[cs]e\|CC BY\|CC0\|ODbL\|attribution\|atrybucj"` po `research/**`, `art-source/**`, `Data/SourceManifests/**`, `game/Assets/**`, `tools/**`, `docs/adr/*.md`.
- Odczyt kolumn `licencja` / `licencja_url` / `zrodlo` wszystkich `research/**/manifest.csv`, `asset_manifest.csv`, `download_list.csv` (34 pliki CSV; część z separatorem `;`).
- Audyt maszynowy `uv run --project tools/licenses python tools/licenses/audit.py` (reguła zasobu: `tools/licenses/audit.py:1-25`) i testy `uv run --project tools/licenses pytest tools/licenses/tests -q`.
- Starsze gałęzie: `origin/mistral/14-licenses` (`a2466051b`) i `origin/mistral/31-licenses-audit` (`55457999b`) — porównane z `main` (`git diff HEAD origin/<gałąź>`).

### 0.2 Wynik audytu maszynowego na `main` (przed tą gałęzią)
| Miara | Wartość |
|---|---|
| zasoby śledzone (obraz/audio/model/font, bez `generated`) | 2603 (audio 132, model 16, obraz 2454, font 1) |
| pokryte wpisem w `docs/LICENSES.md` | 2425 |
| **bez wpisu** | **178** |
| podejrzane (Fab/Google w nazwie/treści) | 0 |
| `pytest tools/licenses/tests` | **1 failed, 8 passed** — `test_all_tracked_assets_covered_in_licenses_md` (`tools/licenses/tests/test_audit.py:85-91`, twardy fail od integracji r5) |

Zasoby bez wpisu (178): `research/gptpro/3-s8-signs/files/*.jpg` 145, `research/g7-street-greenery/files/*` 12, `research/gptpro/2-next-regions/files/G2-A0*.jpg` 9, `research/g5-street-furniture/files/*` 7, `game/Assets/_Project/Rendering/Resources/Night/T_Night*.png` 4, `research/g10-truck-restrictions/files/G10-S01_…png` 1.

### 0.3 Starsze gałęzie audytu licencji
- `mistral/14-licenses` (`a2466051b`): wiersze `truck-brand-marks-a2`, `truck-exterior-qa-0115`, `door_interface.json` i raport `AUDIT-LICENSES-2026-11-12-mistral.md` — **już w `main`** (`docs/LICENSES.md:144-148`, raport w `docs/reports/`). Nic do przeniesienia.
- `mistral/31-licenses-audit` (`55457999b`): `tools/licenses/*` i sekcja „Audyt śledzonych zasobów — M31” — **już w `main`** w wersji nowszej (lider poprawił w integracji r5: twardy fail zamiast `xfail`, test zbyt szerokich wzorców `*photo*`; `git diff HEAD origin/mistral/31-licenses-audit -- tools/licenses/tests/test_audit.py`). Gałąź jest starsza niż `main` (brak wierszy `audio-elevenlabs-sfx-v3-regen04`, `world-vehicle-lod-atlas`, sekcji ADR 0162). Nic do przeniesienia.
- Twierdzenia raportu `AUDIT-LICENSES-2026-11-12-mistral.md` sprawdzone: `make_logos.py` i SVG istnieją (`art-source/truck/brand/{bielik,narew,trakt}.svg`), wiersze w rejestrze są (`docs/LICENSES.md:144-148`) — **potwierdzone**.
- Twierdzenia `FAB-PATCH-LICENSE-2026-11-10.md` dotyczące publicznego repo: repo `woogitsugames/kamion` jest **publiczne** (`gh api repos/woogitsugames/kamion` → `"visibility": "public"`, 2026-11-14) — wniosek „nic z Fab w gicie” pozostaje kluczowy. Uwaga: `docs/11_DECYZJE_WLASCICIELA.md:17` (D11) nadal mówi „Prywatne GitHub” — rozbieżność do decyzji właściciela (§3, R-P1-5).

### 0.4 Źródła znalezione w repo (podsumowanie; szczegóły w tabeli zbiorczej `docs/LICENSES.md`)
- **Dane geograficzne do buildu:** OSM (Geofabrik), GUGiK NMT / ortofoto / BDOT10k / LoD1 2024 / LoD2 2017 — dla **dwóch** regionów: `bialystok-industrial-c` (w rejestrze) i `bialystok-dojlidy` (manifesty `Data/SourceManifests/*dojlidy*` — **brak w rejestrze**).
- **Referencje (nie do buildu):** Mapillary, KartaView, Panoramax, Wikimedia Commons, Openverse/Flickr, GUGiK WMS/WCS, ArcGIS Miasta Białystok, dokumenty BIP/ZDM/BKM/GDDKiA, akty Dz.U./ELI/ISAP, regulaminy EKG ONZ i EUR-Lex, Freesound/OpenGameArt/BBC RemArc (audio), katalogi producentów i prasa (tylko fakty), zdjęcia wklejone przez właściciela (tylko obserwacje).
- **Zasoby w buildzie:** Poly Haven (CC0), Fab/Megascans (Fab Standard, lokalnie poza gitem), ElevenLabs SFX (plan płatny), synteza własna, Inter (OFL), DejaVu Sans Bold (rasteryzowany), Unity + pakiety (glTFast Apache 2.0, URP Unity Companion License, pozostałe `UNVERIFIED`), własne generatory.
- **Nieużyte mimo wzmianek:** BDL (Bank Danych o Lasach), IMGW — 0 wystąpień poza instrukcją dla Mistrala (`docs/owner/MISTRAL-TASKS-10.md:204`); ambientCG — dopuszczony, nieużyty (`docs/LICENSES.md:82`); Suno — tylko zakaz w `CLAUDE.md`.

### 0.5 Stan po tej gałęzi
`docs/LICENSES.md`: tabela zbiorcza 40 źródeł (`docs/LICENSES.md:382`), nowe sekcje: region Dojlidy (:431), pakiety research śledzone w repo (:447), tekstury nocy (:461), silnik i pakiety Unity (:467), uwagi spójności (:473). Audyt maszynowy: **2603/2603 pokryte, 0 bez wpisu, 0 podejrzanych**; `pytest tools/licenses/tests` **9 passed**; `tests/gis/test_cc0_scans.py`, `test_fab_not_tracked.py`, `test_fab_atlas.py` — zielone (2026-11-14).
