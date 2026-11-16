# STATUS — import-pbr-stale-s23 (D43)
- Krok 1: freshness PBR przeniesiony do `build_all.py --check/--list-outputs` (pomija pliki nieprodukowane: asphalt_detail_photo bez zdjęcia, scan-only bez skanów); import-region.ps1 woła check (exit 0/3). pytest 6/6.
- NASTĘPNY KROK: `pwsh scripts/import-region.ps1 -Region knyszyn` (lider; oczekiwane: „PBR Medium: … skipped”, bez build_all).
