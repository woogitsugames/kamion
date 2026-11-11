# Niezależna recenzja SBS r1
Recenzent: sbs_visual_review, tylko odczyt, bez Unity, generatorów i testów. Werdykt przed poprawkami: warunkowy PASS narzędzia po usunięciu luk integralności. Bramka wizualna świata: UNVERIFIED, bez PASS.

1. P1: grupy capture mogły mieszać świat, materiały, commit, tier lub światło. Wymagana wspólna epoka oraz jawny tryb historyczny.
2. P2: odczyt SHA przed długim oczekiwaniem na slot mógł opisywać nieaktualne wejście. Wymagane odczyt po Acquire i kontrola po renderze.
3. P2: compose odrzucał jedynie C, zamiast dopuszczać tylko A/B; błędne wartości mogły przejść do dowodów.
4. P2: Commons omijał część walidacji korekt, horyzontu i wysokości oka. Potrzebna wspólna walidacja i jawna obsługa opcji rektyfikacji.
5. P2: nadal brakuje odpowiadających punktów na obu panelach oraz błędu w pikselach (J7). Bez tego nie awansować C na podstawie dopasowania samego punktu zbiegu.
6. P3: ADR wymaga aktualizacji po zakończeniu walidacji.

Ocena obrazów: 326454-probe-08 poprawia punkt zbiegu, lecz pozostaje C z powodu roll, skali jezdni i innych rozbieżności. Oryginalny kompas nie naprawia 962702/810896. J2 nie ma jednoznacznie przyjętego rozwiązania. Oba Commons pozostają C. Horyzont 2948 ma sensowne linie, ale pozostałe różnice pozy nie uzasadniają awansu.
Atrybucja źródeł jest uczciwa, a rozdzielenie 25 B i 17 C oraz wyłączenie fotometrii są właściwe. Nie dowodzi to zaliczenia bramki świata.

## Poprawki autora po recenzji
Wprowadzono bezpieczną listę klas, wspólną walidację korekt, odrzucanie mieszanych epok, sprawdzanie SHA świata i materiałów oraz wymiarów capture. Dane źródłowe są odczytywane po Acquire i sprawdzane ponownie po renderze. Rekonstrukcja starszych danych wymaga --historical, a migawki wejść --inputs. Bieżące testy pojedynczego pliku: 33/33, przez pulę heavy. Żadna klasa C nie została awansowana.
