# STATUS axis-driveway-s24 (szew osi / czarny pas poprzeczny dk65-goniadzka + zjazd jako biala smuga i "patyki" w lusterku, knyszyn-w)

- Worktree `agent-aa4d26eb3e436ffcb`, galaz `worktree-agent-aa4d26eb3e436ffcb`. Nie scalac (lider).
- Srodowisko: Library skopiowana z win-build (Win64, 17,5 GB); `Data/raw/{gugik,osm,refs,mapillary,fab,cc0}` = junction do
  main; `Data/raw/derived` = prawdziwy katalog: prywatne kopie `knyszyn-w` i `cache`, reszta kafli = junction (odpinac
  `cmd /c rmdir`). Python: SAC blokuje nowy venv -> `artifacts/axis-driveway-s24/uvshim.ps1` (funkcja `uv` wolajaca
  interpreter agent-a492e5af856a32ed3, PYTHONPATH na ten worktree).
- [krok 0] Kamery QA w miejscu zjazdu (spawn buildu #10, route_s 90): `artifacts/axis-driveway-s24/drv_cameras.json`
  (-Gate3). build_all.py (PBR sets) w toku.
- NASTEPNY KROK: `. artifacts/axis-driveway-s24/uvshim.ps1; & scripts/import-region.ps1 -Region knyszyn-w -BuildTarget Win64`
  potem visual-qa przed + `KAMION_QA_DIAG=colorby:material`.
- [krok 1] Import Win64 + VQA "przed" (`artifacts/axis-driveway-s24/before`, 8 kamer, obraz krytyka odtworzony 1:1) i diag
  `colorby:material` (`diag-before-material`): (a) pionowy odcinek i falisty pas = `M_decal_seal` (szew osi DOKLADNIE w osi,
  przedluza kreske P-1; dwa polowkowe pekniecia poprzeczne konczace sie na nim); (b) zjazd = `M_yard_paving` (verge overlay
  `plots._verge_overlay` + apron) zawinięty w rowie, "patyki" = `M_verge_tufts` (verge_flora, karty trawy/ziol rowu) stojace
  NA zjezdzie. Poprawka (a) w decals.py (commit c82222636), testy 0323 14/14.
- NASTEPNY KROK: build_world knyszyn-w z KAMION_DBG_DRIVE_AT (diagnoza rowu pod zjazdem), potem poprawka (b).
