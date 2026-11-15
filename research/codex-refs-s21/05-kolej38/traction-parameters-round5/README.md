# Linia38 — źródłowy typ sieci i zasilanie

Cel: oddzielić tag OSM3000V od danych publikowanych przez PKPPLK. SOURCED [traction.csv, wskazane komórki i podrozdział]: załącznik2.12, arkusz „Załącznik2.12dane”, A351:F351: linia38 BIAŁYSTOK–GŁOMNO, torN, km4,298–98,598, typYzC120-2C. Arkusz opisowy A8 wyjaśnia N jako nieparzysty, a nie liczbę torów. Daty nagłówka: wydruk08.10.2026, stan25.10.2026; zachowano dosłownie.

Sam arkusz nie zawiera napięcia. Pełny bieżący Regulamin sieci2025/2026 v45, aktualizacja12.11.2026, podrozdział2.3.9ust.1 na s24 wskazuje3kV DC dla zelektryfikowanych linii PLK; ust.6 odsyła do załącznika2.12. Koordynator odczytał tekst i obejrzał wyrenderowaną stronę. **SOURCED [oba źródła]: zasilanie3000V DC dla elektryfikowanego odcinka z wiersza351 jest wnioskiem z dwóch dokumentów**, nie wynikiem pomiaru i nie polem napięcia w arkuszu.

TypYzC120-2C zapisano literalnie. Nie wyprowadzono z kodu rozstawu/wysokości słupów, przekrojów przewodów ani modelu3D. Prędkość w kolumnieG jest parametrem sieci dla odbieraka, nie obowiązującą prędkością każdego pociągu; nie przeniesiono jej do generatora ruchu. Nie rozszerzono odczytu na całą linię38, a kategorie przejazdów pozostająUNVERIFIED.

0zdjęć, 2rekordy dokumentacyjne, bez kopii oryginalnego XLSX/PDF w gicie. Binaria i render poza gitem w Data/raw/refs/codex-s21/05-kolej38/traction-parameters-round5. XLSX123617B ma poprawne CRC wszystkich elementówZIP; odczyt read-only w dostarczonym runtime. Dwa wcześniejsze przerwane urllib zapisano w ograniczeniach; udane pobraniecurl bez automatycznychretry. Hash, dokładne źródła i komórki w source-review.json. Treści źródeł nie redystrybuowano; własna parafraza/fakty.
