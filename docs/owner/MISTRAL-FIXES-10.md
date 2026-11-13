# Poprawki dla Mistrala — runda 10 (s19, 2026-11-13)

Przegląd: `docs/reports/REVIEW-2026-11-13-s19-mistral-m51-m53-m50v2.md`. M50 (p9-furniture-3, 3b34a98df) przyjęty — bez bloku. FIX-9 (M52-FIX-3, M47-FIX-2, M54-FIX-2, M49-FIX-2) nadal niewykonane — wkleić ponownie z `MISTRAL-FIXES-9.md`.

Bloki poniżej są opcjonalne, jeśli lider scali PR #49/#50 z erratą w REVIEW-NOTE; wtedy Mistral robi je na tych samych gałęziach po `git rebase origin/main`.

## M51-FIX-2 — P10 zieleń (`research/mistral-p10-greenery-3`)

```
Repo woogitsugames/kamion, gałąź research/mistral-p10-greenery-3 (commity do tej gałęzi, nie nowy PR). Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p10-greenery-3/.
Przegląd s19 (docs/reports/REVIEW-2026-11-13-s19-mistral-m51-m53-m50v2.md §3): korony i przypisanie ulic przyjęte. Do poprawy:
(1) M51-214 USUŃ, a w M51-112 wpisz „brak żywopłotu” — na zdjęciu po prawej jest trawnik z zaparkowanymi autami (ten sam błąd zgłaszano już w s17).
(2) Kadry M51-119…126 i odcinki M51-219…222 nie mają plików w ZIP (walk_*.jpg to inne kadry: 125420, 125821, 131152, 131202, 131205, 131327, 131342, 131431). Dołóż brakujące JPG (Commons 20220725_123952, 123959, 124049, 125403, 125410, 125414, 125438, 132358, 132511, 132717) i popraw ZAWARTOSC_v2.txt.
(3) Odcinki: M51-227 i M51-231 to rzędy drzew/zadrzewienie, nie żywopłot — przenieś do osobnej kategorii „szpaler/zadrzewienie”. M51-232 wysokość 1,0–1,5 m (nie 2,5–3). M51-229, M51-230 to rabaty ozdobne, nie strzyżony pas — popraw typ.
(4) Nakładki overlays/*.png są odwrócone północ–południe i mają znaczniki tylko w lewym-górnym ~⅓ obrazu (zła skala px). Wygeneruj ponownie: obraz north-up (wiersz 0 = północ), skala znaczników = rozmiar px okna / 300 m. Sprawdź wzrokowo, że kółka leżą na koronach drzew.
(5) Filtr nie-roślinności nie działa (usunął 1 obiekt). Zielony autobus na Al. Tysiąclecia (ok. 53,1556 N, 23,1524 E) nadal jest „koroną”. Dodaj filtr kształtu (wydłużenie > 2, prostokątność) albo wyklucz poligony jezdni z OSM.
(6) M51-301: 2739 → 2738 liściaste (zgodnie z README).
W PR komentarz z SUROWYM `git diff --stat origin/main` i listą 1–6. NIE scalaj. Na końcu „M51-FIX-2 gotowe” i koniec.
```

## M53-FIX-2 — P3 zabudowa (`research/mistral-p3-buildings-2`)

```
Repo woogitsugames/kamion, gałąź research/mistral-p3-buildings-2 (commity do tej gałęzi, nie nowy PR). Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p3-buildings-2/.
Przegląd s19 (docs/reports/REVIEW-2026-11-13-s19-mistral-m51-m53-m50v2.md §4): w próbie 18 przyjętych 3 błędne. Każde zdjęcie OBEJRZYJ (po jednym na wywołanie); nie pisz co_widac bez obrazu.
(1) M53-010 → ODRZUCONY: na zdjęciu 20230729 105139 napisu „Zagumienna 9/1” ani „Słoneczna 13” nie ma, środek kadru to szczyt „Zagumienna 40”, a kąt kamera→obrys 180° oznacza cel za kamerą (kadr patrzy ok. 320°).
(2) M53-035: na narożniku zielonego budynku przy wejściu jest numer „8”. To prawdopodobnie Al. Tysiąclecia 8 (OSM way 264944866), nie 6. Przypisz do 8 z LoD1/OSM albo ODRZUCONY.
(3) M53-029: popraw co_widac — logo Biedronki jest na DACHU, parter zasłaniają drzewa, zdjęcie zrobione z dużej odległości. Kondygnacje: policz rzędy widoczne nad drzewami albo UNVERIFIED.
(4) Kolumna `adres` jest niezgodna z geometrią w rekasygnacjach: 011 → „ul. Białostoczek 29”, 012 → „ul. Zagumienna 40”, 014 → „ul. Białostoczek 4/1” (010 → Zagumienna 9/1, ale ODRZUCONY).
(5) M53-012 (szczyt bez okien) i M53-021 (góra punktowca ucięta kadrem): kondygnacje_ze_zdjęcia = UNVERIFIED (niepoliczalne).
(6) kamera_d_m / kamera_kat_deg dla 007, 029, 044, 045, 046, 049: współrzędne Commons to pozycja OBIEKTU, nie kamery (np. 029: 1,9 m przy zdjęciu z daleka). Wpisz UNVERIFIED albo ustal pozycję kamery z treści kadru i opisz jak.
(7) Usuń manifest_v2.csv (to kopia manifest.csv 1:1). Licencję Borawskiego ujednolić: „CC BY-SA 3.0 (tylko referencja)” we wszystkich 6 wierszach.
(8) Po (1)–(2) przyjętych jest 28. Dołóż ≥ 2 nowe budynki z napisem adresowym widocznym na zdjęciu (każde obejrzane, co_widac + numer odczytany z obrazu).
W PR komentarz z SUROWYM `git diff --stat origin/main` i licznikami OK / OK-POŚREDNIE / ODRZUCONY. NIE scalaj. Na końcu „M53-FIX-2 gotowe” i koniec.
```
