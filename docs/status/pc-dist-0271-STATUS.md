# STATUS — pc-dist-0271 (H9, ADR 0271, chmura H r2)

Gałąź `pc-dist-0271` (z origin/main). Zakres: dokumenty + skrypty dystrybucji PC (bez ProjectSettings, Packages, asmdef, BuildCommands.cs, build-windows.ps1).

- [2026-11-15] Start: przeczytane CLAUDE.md, AGENT-RULES, HANDOVER s22, D73/D74, ADR 0261, build-windows.ps1, BuildCommands.BuildWindows, LICENSES.md, LICENSES-AUDIT-S20, docs/10. Fakty: wyjście `artifacts/win/kamion-<ver>-<sha>[-low][-regions][-dev]/Kamion.exe` (+ `Kamion.exe.sha256`, `build.json`, `Kamion-okno.cmd`, `Kamion-knyszyn.cmd`, `Kamion.content.json`/`.top.txt`/`.variants.txt`); `*_DoNotShip` usuwane przez skrypt; backend Standalone = Mono (brak wpisu w `scriptingBackend`); companyName `woogitsugames`, productName `Kamion`; splash Unity włączony.
  NASTĘPNY KROK: research źródeł (itch.io, Steam, Unity docs) → `docs/12_DYSTRYBUCJA_PC.md`.
