# sigplate-0193
- c5950cb47+ADR: głowica S-1 przebudowana, kamera P11-094 przesunięta o 10 m, testy 43/43, before-C wyrenderowane (artifacts/sigplate-0193/before-C-sheet.jpg).
- W TLE: artifacts/sigplate-0193/run.ps1 (build_world C+dojlidy -> import -> after-C/after-D); status: run.status
- b4ed01d93 + 5ba20690b: zacommitowano przebudowane street_props.glb/props_meta.json, oczyszczono generated/settings, scalono origin/main (props.py/materials.py czysto; props_meta/street_props tymczasowo z main do przebudowy w build_world C).
- a77a1f96f + sheet.py: naprawiono sortowanie głębi w sheet.py (per-pixel Z-buffer 2x SSAA), zregenerowano after-heads.png (zweryfikowano wizualnie wszystkie 5 wariantów: czysty tył, zero artefaktów 3/4), pytest tests/gis/test_signal_head_0193.py = 17 passed.
- NASTĘPNY KROK: przebudowa światów bialystok-industrial-c i bialystok-dojlidy w slocie heavy (build_world.py), potem import Low,High i render after-C2 / after-D2 w slocie unity.
