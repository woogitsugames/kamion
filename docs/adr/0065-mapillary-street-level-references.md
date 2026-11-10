# ADR 0065: Mapillary jako źródło referencji ulicznych

Status: przyjęty (geo-worldgen), 2026-11-10. Źródło: `docs/11` D41, D42. Uzupełnia ADR 0002 (źródła danych, zakaz Google).

## Kontekst
Do dopasowania kadrów (kamery gate3, photo_match) i kalibracji koloru potrzebujemy zdjęć ulicznych trasy startowej.
Własne zdjęcia właściciela (D41) są w drodze; D42 dopuszcza Mapillary jako referencję. Google Maps/Street View/Earth/3D
Tiles pozostają zakazane (także zrzuty z Gemini).

## Decyzja
- Narzędzie `tools/refs/mapillary_fetch.py` pobiera z Mapillary Graph API v4 (`graph.mapillary.com/images`) miniatury
  `thumb_2048_url` wraz z metadanymi (autor, data, azymut, geometria, sekwencja, flaga pano).
- Token ze zmiennej środowiskowej `MAPILLARY_TOKEN`, a gdy jej brak z `%USERPROFILE%\.kamion\secrets.env` (poza repo), wysyłany nagłówkiem `Authorization`; nie trafia do repo,
  logów, argumentów ani manifestu. Brak tokenu daje czytelny błąd z instrukcją dla właściciela.
- Dane surowe w `Data/raw/mapillary/<region>/` (poza gitem, jak inne surowe źródła), z `manifest.jsonl` (URL strony,
  autor, data, SHA256, licencja). Zapytania: kafle bbox <= 0,01 deg2, opóźnienie, backoff, cache, `--max`, panoramy
  domyślnie pomijane.
- Atrybucja: `docs/ATTRIBUTION-mapillary.md` generowana z manifestu dla zdjęć oznaczonych jako faktycznie użyte
  (`--use`, lista w `Data/Regions/<id>/mapillary_used.json`), linkowana z `docs/LICENSES.md`.

## Licencja: zasada użycia
Zdjęcia Mapillary (CC BY-SA 4.0) są REFERENCJĄ: wzór, dopasowanie kadru, kalibracja koloru. Nie wchodzą do builda.
Jeśli kiedykolwiek piksele zdjęcia trafią do tekstury (wycinek, retusz, projekcja), tekstura jest utworem zależnym i
podlega CC BY-SA 4.0 (share-alike) oraz wymaga atrybucji. To wymaga osobnej decyzji właściciela i przeglądu prawnego
przed wydaniem, bo wiąże licencję pochodnej, nie całej gry (zbiorcze użycie vs adaptacja: do oceny prawnej). Do tego
czasu: bez wycinania pikseli. Kalibracja koloru z pomiaru (np. średnia barwa asfaltu) jest liczbą, nie kopią utworu,
ale każde użycie zapisujemy w `--use`.

## Konsekwencje
Nowa zależność narzędziowa: `tools/refs` (uv: requests, pillow, pyproj, pyyaml). Testy bez sieci: `tests/refs`.
Warunki Mapillary API (rate limit) szanowane przez opóźnienie i backoff; nie robimy masowego scrapowania poza
potrzebnymi kafelkami.
