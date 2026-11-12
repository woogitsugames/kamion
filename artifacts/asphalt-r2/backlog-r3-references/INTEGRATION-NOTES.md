# Przygotowanie integracji następnej rundy

Odczyt main 2026-11-12 około10:24: 419e7d1be171b6ebcfb7aaf4745a48ac5a0562dc. Nie jest to baza r3 — przed rozpoczęciem trzeba ponownie odczytać i scalić aktualny main.

W porównaniu z bazą r2 4992c434 plik materials.py ma nowy addytywny blok _underdeck_pier_paint/_underdeck_pier_weather z ADR0119. Aktualny feedback s12 wymaga unii dopisywanych bloków. Przy merge r3 zachować zarówno opcjonalne efekty asfaltu/krawężnika/kostki0118, jak i pigment oraz weathering filarów0119; nie wybierać całego pliku ours/theirs. Nie zmieniamy parametrów filarów w sesji asphalt.

Nowe generated i manifesty przy konflikcie pochodzą z main i wymagają regeneracji pod slotem heavy. Nowy świat/baseline jest konieczny po merge; r2 PNG nie stają się baseline r3 tylko przez zmianę nazwy. Liczbę kamer trzeba wyprowadzić ze świeżego zestawu, a nie zakładać82/328. Probe placu wymaga sprawdzenia aktualnego GLB i faktycznego materialID, wysokości oraz seat=file; sąsiednie geotagi fotografii nie są dopasowaną pozą zdjęcia3 ani dowodem obrysu całego PCRT.
