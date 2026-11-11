# S10 A — ADR0086 tint gamma

- Bootstrap: gałąź gpt-tint-gamma z main4f7da66c; przeczytano kontrakt S10, HANDOVER s9, zasady, visual-qa. Zakres: kontrakt liniowego _Tint i kalibracja importera; bez zmian geometrii/światła/roślinności.
- NASTĘPNY KROK: `git lfs checkout` oraz kopie lokalnych cache i produktów Fab; potem import/render baseline przed zmianą kodu.

- Krok2: skopiowano Data/raw/derived+cc0, CC0/_raw, megascans, Unity _Generated/Library, material PNG caches i zdjęcia; rawfab/gugik/osm/refs/mapillary = junction tylko do odczytu. Bez zmian źródeł main. NASTĘPNY KROK: `uv run --project tools/worldgen python tools/worldgen/roads/build_world.py --region bialystok-industrial-c`; baseline wymaga świeżego importu, cache main nie jest dowodem.

- Krok3: GPU readback kopii rzeczywistego WorldPBR (zmieniony tylko zwrot fragmentu) potwierdził kontrakt Color: raw0.08 ->0.007194, raw0.5->0.214041; zapis gamma(linear) daje dokładnie0.08/0.5, takżeHDR1.5/2.5. SetColor i SetVector identycznie. Dowód tint-probe.json, UnityLinear/D3D12. NASTĘPNY KROK: po ukończeniu before-build import-region + cztery baseline Low/High clear/overcast (bez zmian importera).
