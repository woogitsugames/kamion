# sigplate-0193
- c5950cb47+ADR: głowica S-1 przebudowana, kamera P11-094 przesunięta o 10 m, testy 43/43, before-C wyrenderowane (artifacts/sigplate-0193/before-C-sheet.jpg).
- W TLE: artifacts/sigplate-0193/run.ps1 (build_world C+dojlidy -> import -> after-C/after-D); status: run.status
- b4ed01d93 + 5ba20690b: zacommitowano przebudowane street_props.glb/props_meta.json, oczyszczono generated/settings, scalono origin/main (props.py/materials.py czysto; props_meta/street_props tymczasowo z main do przebudowy w build_world C).
- NASTĘPNY KROK: poprawa sortowania głębi w artifacts/sigplate-0193/sheet.py, regeneracja after-heads.png i pytest tests/gis/test_signal_head_0193.py -q.
