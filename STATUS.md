# STATUS seams-p3-s24 (ADR 0304)

- qa.seams przed (main 11e22c1ff, 1. przebieg assign_sides): 16 FAIL, na trasie 10 (8 referencji rozstawu + 2 pobocza DK8).
- Przyczyna pobocza DK8 (kleeberga|knyszynska w261104557, C|Maczka w257367422): qa porównywało 1. przebieg assign_sides;
  generator meshuje 2. przebieg (trims). W 2. przebiegu oba kafle budują to samo -> qa.seams domyślnie 2. przebieg (`--pass1` stary).
- Referencje: ortofoto 0,1 m (qa/seam_line_ortho.py): knyszynska|dk65-01 6,40-6,45 m (gen 5,6), Knyszyn 6,75-6,8 m (gen 7,1)
  -> referencje miały rację; override width 6.7 (Szosa Knyszyńska, 2 kafle) + dk65-edge-line-spacing-0304 = 6.8 (4 kafle).
- qa.seams po: 7 FAIL, na trasie 0 (artifacts/seams-p3-s24/seams_after1.md). pytest 0304/0212/0220/0208: 55 passed.
- NASTĘPNY KROK: przebudowa prywatna 6 kafli: pwsh -File artifacts/seams-p3-s24/rebuild.ps1 ; potem import Win64 + visual-qa.
- 07:3x: docstring qa.seams + ADR 0304 draft w 7d221a2ec (wypchnięte). Library skopiowana z win-build (robocopy exit 1 = OK).
  Przebudowa prywatna 6 kafli w toku (artifacts/seams-p3-s24/rebuild.status); snapshot „przed” derived knyszynska + knyszyn-w
  w artifacts/seams-p3-s24/before-derived/.
- NASTĘPNY KROK: po `DONE` w rebuild.status: import Win64 + visual-qa (-Cameras seam_*, dk65_seam_east_out) po/przed.
- 07:5x: przebudowane knyszyn-w, dk65-monki-01, bialystok-knyszynska (exit 0); render przed/po wystartowany (artifacts/seams-p3-s24/vqa.status).
- 08:2x: import exit 2 = brak SM_CabInterior_LOD0.fbx w worktree; skopiowane z main, rendery wystartowane ponownie.
- 09:3x: 6/6 kafli przebudowane (exit 0), rendery przed/po gotowe (vqa/{before,after}); pytest tests/gis w toku (pytest.status).
- 10:4x: pytest gis 2510 passed / 5 failed -> poprawiony test_edge_lines_0205 (6.7); 4 pozostałe = świeżość katalogu / route_links /
  manifest C (do odświeżenia przez lidera po przebudowie w main). ADR 0304 uzupełniony. KONIEC zadania — raport do lidera.
