# STATUS farfield-blocks-cli — s24

- Naprawiono własność budynków far-field (bbox wszystkich zarejestrowanych kafli + ≥400 m od tras, raw i po kompresji), dachy Low/High oraz palety materiałów.
- Runtime rezerwuje sektory od Register, niezależnie od Ready/Unloading; dodano testy EditMode. Review innego agenta wykonany; audyt źródłowy/maski poprawione po uwagach.
- Dotychczas: pytest 83 PASS/1 SKIP (brak raw cache), runner .NET 35/35 PASS. Trwa końcowa walidacja po dodaniu testu bufora i normalizacji hashy. Unity i build_world nieuruchamiane.
- NASTĘPNY KROK: `.venv/Scripts/python.exe -m pytest tests/gis/test_far_field_streaming.py tests/gis/test_far_field.py tests/gis/test_far_field_boundary.py tests/gis/test_far_field_industrial_facade.py tests/gis/test_far_field_lod1.py tests/gis/test_far_field_terrain_source_0227.py -q`
