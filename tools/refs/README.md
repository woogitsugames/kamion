# tools/refs: referencje uliczne z Mapillary

Pobiera zdjęcia uliczne z Mapillary API v4 (CC BY-SA 4.0, decyzja D42, ADR 0065) jako REFERENCJĘ: wzór, dopasowanie
kadru, kalibracja koloru. Google Maps/Street View/Earth: zakaz. Zdjęcia surowe: `Data/raw/mapillary/<region>/` (poza gitem).

Token tylko ze zmiennej środowiskowej (brak tokenu = komunikat z instrukcją dla właściciela):

    $env:MAPILLARY_TOKEN = '<Client Token z mapillary.com/dashboard/developers>'

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
