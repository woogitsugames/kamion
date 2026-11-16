# STATUS ci-gis-s23 (D20) — PR #148
- CI gis: selektywny `git lfs pull --include $LFS_GIS` (55 obiektów, ~17,9 MB) + cache `.git/lfs/objects`; KAMION_LFS_REQUIRED -> wskaźnik = fail.
- Lokalnie pełne tests/gis z prawdziwymi plikami + strict: 1784 passed, 49 skipped (wszystkie Data/raw/derived), 2 xfailed, 0 failed (856 s).
- NASTĘPNY KROK: `gh api repos/woogitsugames/kamion/commits/$(git rev-parse HEAD)/check-runs` — job gis zielony -> lider scala PR #148.
