# sigplate-0193
- c5950cb47+ADR: głowica S-1 przebudowana, kamera P11-094 przesunięta o 10 m, testy 43/43, before-C wyrenderowane (artifacts/sigplate-0193/before-C-sheet.jpg).
- W TLE: artifacts/sigplate-0193/run.ps1 (build_world C+dojlidy -> import -> after-C/after-D); status: run.status
- b4ed01d93 + 5ba20690b: zacommitowano przebudowane street_props.glb/props_meta.json, oczyszczono generated/settings, scalono origin/main (props.py/materials.py czysto; props_meta/street_props tymczasowo z main do przebudowy w build_world C).
- a77a1f96f + sheet.py: naprawiono sortowanie głębi w sheet.py (per-pixel Z-buffer 2x SSAA), zregenerowano after-heads.png (zweryfikowano wizualnie wszystkie 5 wariantów: czysty tył, zero artefaktów 3/4), pytest tests/gis/test_signal_head_0193.py = 17 passed.
- W TLE: artifacts/sigplate-0193/run2.ps1 (heavy: build_world C+dojlidy + build_all -> unity: import Low,High + after-C2/D2 Low,High); status: run2.status.
- after-C2 / after-D2 Low+High + gate3_signal + sbs2/*.jpg wyrenderowane i obejrzane (czysta czarna tarcza od tyłu, frontowa obwódka, D-6 ~13 m zgodny z P11-094; WORLD_MEMORY bez zmian: C Low 123.0 / High 265.9 MB, Dojlidy Low 98.2 / High 213.5 MB).
- Testy po scaleniu z origin/main (e82773fd4): EditMode 581 total / 580 passed / 0 failed / 1 skipped; pytest tests/gis 1168 passed / 1 failed (`test_dojbld_0185.py::test_fence_mesh_mips_do_not_preserve_coverage` — niezwiązany revert z main e668a9588) / 2 xfailed; ukierunkowane (0193/0174/0179/fidelity) 35 passed / 1 xfailed.
- ADR `docs/adr/0193-sygnalizator-tarcza-i-kamera-d6.md` zaktualizowany (PROPOSED, tabela Low/High A/B, WORLD_MEMORY, testy, ścieżki JPG/SBS).
- NASTĘPNY KROK: KONIEC — gotowe do weryfikacji/scalenia przez lidera na gałęzi `sigplate-0193`.
