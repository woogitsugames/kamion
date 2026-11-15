# Recenzja wewnętrzna R2 direction-signs-route-c (2026-11-15)

**Werdykt: PASS z uwagami (P2).** Pakiet spełnia wymagania z bloku „Dokończenie” CLOUD2-PROMPT: ≥ 20 obejrzanych kadrów (27) i dodana ul. gen. Andersa. Wymiarów tablic nie ma (UNVERIFIED); pakiet mówi o tym otwarcie.

## Sprawdzone
| Wymóg | Wynik | Dowód |
|---|---|---|
| ≥ 20 obejrzanych kadrów | ✓ 27 | 12 Panoramax (2019) + 15 KartaView (2021). Arkuszy stykowych nie liczyłem |
| ul. gen. Andersa | ✓ | R2-058…R2-068 (11 kadrów, od wykopu przy rondzie Bieżeństwa do estakady przed rondem Putry), 8 tablic/zespołów R2-073…R2-081 |
| Opis = to, co widać | ✓ | 6 wierszy z próby obejrzałem ponownie (seed 20261115): 5 PASS, 1 FIX. W R2-058 była treść dalszej tablicy bez wycinka; zmieniona na „czytelne tylko Warszawa” |
| Kierunek geograficzny | ✓ | `kurs_toru_deg` z toru sekwencji. `heading` KartaView (kompas) różni się od niego o ≤ 1° na tych kadrach |
| Kamery kontrolne | ✓ (poprawione) | dla nowych tablic filtr „w FOV kadru i oś kamery < 90° od kursu toru”, więc kamera widzi lico, a nie tył |
| Licencje / marki | ✓ | KartaView CC BY-SA 4.0, Panoramax CC BY-SA 4.0. Napisy firmowe na billboardach i stacjach oznaczyłem „nie odtwarzamy” |
| UA | ✓ | `research-client/1.0 (generic)` (pobieranie KartaView) i `research-client/1.0` (`fetch.py`) |
| Tylko własny katalog | ✓ | zmiany wyłącznie w `research/cloud2/direction-signs-route-c/` |

## Uwagi
- **P2-1:** wymiary tablic, wysokość liter i normatyw Dz.U. 2019 poz. 2311 nie zostały zrobione (UNVERIFIED). To temat pakietu R1 (katalog znaków); tu go nie dublowałem.
- **P2-2:** stan na 2021 r. W 2021 r. „Centrum” było zaklejone krzyżem (R2-081). Stan 2026 nieznany (UNVERIFIED).
- **P2-3:** kierunek SE (Putry → rondo Bieżeństwa) i sekwencja KartaView 2769366 (2019) nie są obejrzane.
- **P2-4:** pozycja tablicy = pozycja kadru. Odległość kadru od tablicy jest UNVERIFIED (ortofoto GUGiK pozwoliłoby ją zmierzyć).
- **P2-5:** numer drogi wojewódzkiej w żółtym polu na R2-079/080/081 wygląda w wycinku na „675”, a na R2-073 (kierunek przeciwny) jest „676”. Zostawiłem jako UNVERIFIED.
