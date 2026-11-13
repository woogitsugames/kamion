# P13 — materiały binarne (poza gitem)

Zdjęcia i dokumenty binarne **nie trafiają do repozytorium** (connector przyjmuje tylko pliki tekstowe;
zdjęcia NIE DO GITA zgodnie z zasadami zadania). Właściciel przekazuje liderowi archiwum:

- **Nazwa:** `mistral-p13-andersa-viaducts-files.zip`
- **Rozmiar:** 8 736 124 B (8,33 MiB)
- **sha256:** `de50ff754894ff86d3ad5a28dbe2bc3c86ed430ce7f3909494e304dbf84e97cc`
- **Zawartość (47 plików, prefiks `p13/`):**
  - `p13/photos/commons/` — 12 kadrów Wikimedia Commons (≤1600 px; 6× CC0, 4× CC BY 3.0, 2× CC BY-SA 3.0 = referencja)
  - `p13/photos/pano/` — 11 kadrów Panoramax (≤1600 px, CC BY-SA 4.0 = referencja)
  - `p13/photos/orto/` — 4 klatki ortofoto GUGiK WMS (HR+SR, obiekty A i B, 1600 px)
  - `p13/docs/pfu_ekrany_siwz_61046.pdf` — PFU BIP (264 029 B, md5 `e34b42bcb705066affa2ebbe32a30bb2`)
  - `p13/pages/` — 6 snapshotów HTML stron źródłowych (z 13.11.2026)
  - metadane JSON: `commons_meta12.json`, `pano_items.json`, `orto_urls.json`, `bridge_geoms.json`, `chains.json`, `rows_debug.json`

Oryginały Panoramax (sd 2048 px) celowo NIE są w archiwum (limit zadania: JPG ≤ 1600 px);
URL-e oryginałów są w `pano_items.json` w archiwum i w `manifest.csv`.
