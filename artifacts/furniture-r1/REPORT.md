# Strumień I — ADR 0102 — gotowe do recenzji lidera (R2)

Gałąź: `gpt-furniture-r1`; SHA zweryfikowanego kodu: `b087967ceafd5a1222c1f7e880bab2ab36c49ef5`; baza: `9e6e9fde`.

- Osadzanie na osi stopy z zachowaniem poziomu kolizji; 20 lokalnych korekt lamp do 1,05 m. Relief QA: 147→107, max 1,087→0,411 m.
- Rodziny starych lamp, dopasowane obejmy, hatch, skany CC0 z brudem/korozją i neutralnymi naklejkami; szary tył znaków; U-prototyp; schodkowe ogrodzenia.
- Gate3Audit, korytarz 40 m: 223 podpory; floating 4→0, sunk 0→0 (`audit-before.json`, `audit-after.json`, `final-metrics.json`).
- GIS: **379 passed, 1 xfailed**, 649,86 s; EditMode: **226/226**, 0 failed, 0 skipped (`pytest-after.log`, `editmode.xml`).
- Low, 8 ujęć trasy: draws delta max **0**, tris delta konserwatywnie **≤+1,183%** z błędem zaokrąglenia SceneStats (`frame-budget*.json`); CPU estimate, GPU/telefon UNVERIFIED.
- Pamięć siatek Low 111,3→112,3 MB; High 239,7→240,7 MB. Low betonowej lampy 105→91 tris, stalowej 53→53; sloty istniejących modeli bez wzrostu.
- 806 prymitywów dróg/mostów/barier/krawężników/kolizji/oznakowania identycznych bajtowo (`protected-geometry.json`); w generacji 0 `fallback=True`.
- PNG przed/po: `before/{Low,High}-{overcast,clear}/`, `after/{Low,High}-{overcast,clear}/` — po 36; obejrzano 8 arkuszy `compare/`. `after-r1/` jest odrzuconą rundą.
- Samokrytyka: `docs/reports/visual/REVIEW-2026-11-11-s10-0102-self.md`; ADR: `docs/adr/0102-street-furniture-r1.md`; logi Unity: `unity-logs/`.
- Otwarte: niezależna recenzja/telefon lidera; dokładne przypisanie rodzin do ulic, zmienna metaliczność rdzy, różnorodność papieru, ciężka podmurówka na skarpach. U: 0 instancji w danych regionu.
- Przewidywane konflikty: addytywne `materials.py`, `export.py`, props GLB/metadata, generated QA/manifest, `LICENSES.md`; po integracji regeneracja produktów.
- Dla lidera: `git merge gpt-furniture-r1`, następnie `uv run --project tools/worldgen python tools/worldgen/roads/build_world.py --region bialystok-industrial-c` i `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` po sprawdzeniu PHONE_RUN.
- Artefakty skopiowane do głównego `artifacts/furniture-r1/`; gałąź pozostawiona do integracji, bez scalania ani pushu main przez autora.
