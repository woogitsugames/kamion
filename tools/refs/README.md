# tools/refs: referencje uliczne z Mapillary

Pobiera zdjęcia uliczne z Mapillary API v4 (CC BY-SA 4.0, decyzja D42, ADR 0065) jako REFERENCJĘ: wzór, dopasowanie
kadru, kalibracja koloru. Google Maps/Street View/Earth: zakaz. Zdjęcia surowe: `Data/raw/mapillary/<region>/` (poza gitem).

Token: zmienna środowiskowa `MAPILLARY_TOKEN`, a gdy jej brak linia `MAPILLARY_TOKEN=...` w `%USERPROFILE%\.kamion\secrets.env` (poza repo). Brak = komunikat z instrukcją dla właściciela. Token z mapillary.com/dashboard/developers.

Komendy (z korzenia repo):

    # cały region (bbox z Data/Regions/<id>/region.yaml, kafle <= 0,01 deg2), bez panoram, max 200
    uv run --project tools/refs python tools/refs/mapillary_fetch.py --region bialystok-industrial-c --max 200
    # najbliższe zdjęcia przy kamerach gate3 (promień 30 m, azymut +-40 deg), arkusze porównawcze
    uv run --project tools/refs python tools/refs/mapillary_fetch.py --region bialystok-industrial-c \
        --points Data/Regions/bialystok-industrial-c/gate3_cameras.json --radius 30 --contact-sheet
    # arkusze z istniejącego manifestu (bez tokenu); kadr gry = najnowszy artifacts/gate3/*/*/cam/<kamera>.png
    uv run --project tools/refs python tools/refs/mapillary_fetch.py --region bialystok-industrial-c --contact-sheet-only
    # atrybucja: oznacz użyte zdjęcia i wygeneruj docs/ATTRIBUTION-mapillary.md
    uv run --project tools/refs python tools/refs/mapillary_fetch.py --region bialystok-industrial-c --use <id> [<id>...] --attribution

Wyjścia: `Data/raw/mapillary/<region>/<id>.jpg`, `manifest.jsonl` (id, page_url, autor, data, sha256, licencja, kamery gry),
cache odpowiedzi `.cache/`, arkusze `artifacts/refs/mapillary/<region>/sheet_<kamera>.jpg`, lista użytych
`Data/Regions/<id>/mapillary_used.json` (w gicie). Limity: opóźnienie między zapytaniami, backoff na 429/5xx, cache,
`--max`, `--pano` włącza panoramy.

Testy (bez sieci i tokenu): `uv run --project tools/refs pytest tests/refs -q`

## Otwarte źródła referencji (D43, ADR 0066)

Bez kluczy i kont. Trasa = 55 ujęć z `docs/owner/PHOTO-LIST.md` (`refs_common.parse_photo_list`). Wyniki w `Data/raw/refs/<źródło>/`
(poza gitem, `manifest.jsonl`), montaże w `artifacts/refs/<źródło>/shot_NN.jpg`. Tylko CC0/PDM/CC BY/CC BY-SA; NC/ND odrzucane.

    uv run --project tools/refs python tools/refs/open_sources.py --source kartaview|panoramax|commons|openverse [--only-weak]
    uv run --project tools/refs python tools/refs/open_sources.py --source commons --categories
    uv run --project tools/refs python tools/refs/gugik_ortho.py            # WMS GUGiK, okno 160 m, EPSG:2180
    uv run --project tools/refs python tools/refs/bialystok_open_data.py --catalog   # ArcGIS Online Miasta Białystok

Przegląd wyników: `docs/REFERENCES.md` (tabela źródeł). Testy: `uv run --project tools/refs pytest tests/refs -q`.
