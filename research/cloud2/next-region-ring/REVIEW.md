# Recenzja wewnętrzna R9 next-region-ring po FIX (2026-11-15)

**Werdykt: PASS z uwagami P2.** Wszystkie punkty FIX z recenzji lidera (`docs/reports/REVIEW-2026-11-14-s20-cloud2-r9.md` §6) są zamknięte, z jednym zastrzeżeniem: liczby dla dróg poniżej primary i dla budynków pochodzą tylko z pomiaru recenzenta. Własne Overpass ponowiłem, ale mirror zwracał 504.

## Sprawdzone
| Punkt | Wynik | Dowód |
|---|---|---|
| F1 UA (P1) | ✓ | `grep -ri kamion fetch.py tools/` → 0 trafień; UA `research-fetch/1.0`; notatka w `sources.md` („Poprawki 2026-11-15”) |
| F2 drogi < primary, budynki (P1) | ✓ (ESTIMATED) | §4a README + `overpass/reviewer_pbf_measure.json` + wiersze R9-394…R9-401; wartości porównane 1:1 z REVIEW §4 (audyt: 3/3 PASS) |
| F3 Commons (P1) | ✓ | `commons_landmarks.py` sprawdza `error`/`query`; 24/24 punktów HTTP 200, L01 37 / L03 82 (zgodne z recenzentem), L05 105 (rec. 116), L19 10 (rec. 7), L23 363 (rec. 357); 5 plików obejrzanych (≥ 1 na L03, L19, L23), licencje CC0 / CC BY-SA 4.0 sprawdzone ponownie w imageinfo |
| F4 opis PR (P2) | ✓ | opis PR: 3 punkty bez kadru (L03, L19, L23), zgodnie z README §7 |
| Stałe id | ✓ | porównanie z manifestem z `e2a3b671`: R9-001…R9-371 mają ten sam `przedmiot`; zmieniły się tylko wartości R9-113/114 (luki → odnośnik do sekcji K) i R9-301/303/305 (zera → 37/82/105) |
| Opisy kadrów Commons | 4 PASS / 1 FIX | ponowne obejrzenie wszystkich 5: CM01 miał „jasną nawierzchnię ścieżki”, na obrazie jest czerwonawa — poprawiono |
| Zdjęcia w repo | ✓ | `files/jpg1600/` 39 plików + INDEX.csv (PX31 = duplikat PX26), 7,9 MB; `files/commons/` 5 plików, ≤ 1600 px; licencje CC BY-SA 4.0 / CC0, autorzy w manifeście |
| Zakaz Google/Bing/Apple/Yandex | ✓ | brak w źródłach |

## Uwagi
- **P2-1:** Overpass dla klas niższych nie powiódł się ponownie: przy 4×4 kafel 2_0, przy 6×6 kafel 0_5, po 5 próbach HTTP 504. Inne serwery przez proxy nie odpowiadają. Liczby §4a mają więc jedno źródło (PBF recenzenta, 2026-11-08). Jeśli lider potrzebuje drugiej metody: `uv run --project tools/worldgen` na tym samym PBF z innym narzędziem (np. osmium tags-filter + ogr) albo Overpass z innego środowiska.
- **P2-2:** L05 105 vs 116 i L19 10 vs 7: różnice między zapytaniami z 2026-11-14 (recenzent) i 2026-11-15 (pakiet). L05 to −9 %, L19 to +3 pliki przy małej liczbie; przyczyny nie wyjaśniłem. Liczby z geosearch traktować jako rząd wielkości.
- **P2-3:** Żaden z obejrzanych plików Commons nie pokazuje celu L03/L19/L23 → nadal potrzebne Mapillary (token lidera) albo zdjęcia właściciela.
- **P2-4 (bez zmiany):** `overpass/*.json` zajmują 2,6 MB w repo (uwaga lidera §7). Nie przenosiłem ich, bo `build_manifest.py` i audyt ich potrzebują.
