# Recenzja wewnętrzna R4 bialystok-building-typology (2026-11-15)

**Werdykt: PASS z uwagami (P2).** Wymagania z bloku „Dokończenie” są spełnione: ≥ 30 kadrów (40 obejrzanych, 37 z elewacją), w tym Dojlidy (16 obejrzanych, 15 z elewacją), oraz opisy elewacji. Statystyki BDOT/LoD i NMPT z 2026-11-14 się nie zmieniły (audyt 26/26 PASS).

## Sprawdzone
| Wymóg | Wynik | Dowód |
|---|---|---|
| ≥ 30 kadrów | ✓ | 16 (Panoramax/KartaView) + 24 (Commons). Kadry bez elewacji (R4-140, 144, 150) są w liczbie obejrzanych, ale nie w liczbie kadrów elewacji |
| Dojlidy | ✓ | R4-127…R4-142 |
| Opisy elewacji | ✓ | tabela w README i kolumna `opis_co_widać`: kondygnacje z rzędów okien (ESTIMATED), kolory słownie, dachy, ogrodzenia |
| Opis = obraz | ✓ | ponowne obejrzenie 5 z 24 (seed 20261115): 4 PASS, 1 FIX (R4-148: 9 → 8–9 kondygnacji) |
| Stare wiersze bez zmian | ✓ | R4-001…126 identyczne z poprzednim commitem. Pomyłkę z sha256 przy przebudowie zauważyłem i naprawiłem (`data/frames_sha_2026-11-14.json`) |
| Licencje / marki | ✓ | 23 × CC0, 1 × CC BY-SA 3.0 (autor w manifeście). Szyldy firmowe opisane jako „nie odtwarzamy”. Tablice rejestracyjne nie są opisywane |
| UA | ✓ | `research-client/1.0 (generic)` (commons_get), `research-script/1.0 (generic)` (fetch.py) |

## Uwagi
- **P2-1:** wszystkie 23 kadry CC0 mają jednego autora, więc próba jest wąska. Panoramax i KartaView nie mają zdjęć Dojlid.
- **P2-2:** brak przypisania kadrów do way OSM. Pozycja w manifeście to pozycja aparatu, a kierunek jest UNVERIFIED (Commons nie podaje azymutu).
- **P2-3:** bloki wielkiej płyty z bliska tylko na 2 kadrach. Kolorów po termomodernizacji dla osiedli Białostoczka nadal nie opisano (pakiet `mistral/p3-buildings-2` je ma).
- **P2-4:** możliwe pokrycie z `mistral/p11-dojlidy-photos` (te same tytuły Commons). Nie sprawdzałem tego kadr po kadrze.
