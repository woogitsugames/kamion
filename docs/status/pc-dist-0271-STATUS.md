# STATUS — pc-dist-0271 (H9, ADR 0271, chmura H r2)

Gałąź `pc-dist-0271` (z origin/main). Zakres: dokumenty + skrypty dystrybucji PC (bez ProjectSettings, Packages, asmdef, BuildCommands.cs, build-windows.ps1).

- [2026-11-15] Start: przeczytane CLAUDE.md, AGENT-RULES, HANDOVER s22, D73/D74, ADR 0261, build-windows.ps1, BuildCommands.BuildWindows, LICENSES.md, LICENSES-AUDIT-S20, docs/10. Fakty: wyjście `artifacts/win/kamion-<ver>-<sha>[-low][-regions][-dev]/Kamion.exe` (+ `Kamion.exe.sha256`, `build.json`, `Kamion-okno.cmd`, `Kamion-knyszyn.cmd`, `Kamion.content.json`/`.top.txt`/`.variants.txt`); `*_DoNotShip` usuwane przez skrypt; backend Standalone = Mono (brak wpisu w `scriptingBackend`); companyName `woogitsugames`, productName `Kamion`; splash Unity włączony.
  NASTĘPNY KROK: research źródeł (itch.io, Steam, Unity docs) → `docs/12_DYSTRYBUCJA_PC.md`.
- [2026-11-15] Zrobione: `scripts/package-windows.py` + `tests/dist` (pytest **14 passed**), `scripts/collect-logs.ps1` (nieuruchomiony), `dist/windows/README.txt.in`, `dist/windows/kamion.iss` (nieskompilowany), CI job `dist-tests`, `docs/12_DYSTRYBUCJA_PC.md`, ADR 0271, wpis w LICENSES.md. Bloker: R-P0-2 (ODbL §4.6) — `--release` zwraca 3. Suno: brak w buildzie.
  NASTĘPNY KROK (lider, Windows): `uv run --no-project python scripts/package-windows.py artifacts/win/kamion-0.1.0-<sha>-regions --dry-run`, potem bez `--dry-run`; rozpakować, uruchomić `Zbierz-logi.cmd`.
