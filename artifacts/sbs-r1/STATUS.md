# Stan rundy sbs r1
Przeczytano zlecenie i zasady. Gałąź gpt-sbs-r1, baza main 4c9905b1.
Trwa przygotowanie lokalnych danych worktree; nie uruchomiono Unity.
Następny krok: uv run --project tools/refs python tools/refs/sbs_gate3.py --help

Dane worktree skopiowane; junctiony referencji tylko do odczytu. Dodano klasy A/B/C; J1, J2 i J3 wy??czone z domy?lnego zestawu dowodowego do kalibracji. Fotometria domy?lnie wy??czona do sprawdzenia masek. Skrypt SBS pobiera i zwalnia slot przed ka?dym startem Unity.
Nast?pny krok: uv run --project tools/refs python tools/refs/sbs_gate3.py prepare
## Kalibracja i przygotowanie renderu
Ukończono kopiowanie danych i cache Library bez Bee/BuildPlayerData/PackageCache. Przygotowano 40 referencji z jawną klasyfikacją pozy. Dla 2948 wskazano dwie krawędzie jezdni na wyprostowanym zdjęciu; ich przecięcie wyznacza horyzont roboczy, z zastrzeżeniem spadku drogi.
Następny krok: pwsh scripts/sbs-gate3.ps1 -EditMode
## Pokrycie początku trasy
Przeszukano lokalny manifest; brak kandydatów z pierwszych 300 m G3-A w promieniu 100 m. Próba pobrania dodatkowych zdjęć: błąd DNS graph.mapillary.com. Przygotowano 40 prób pozy bocznej dla ośmiu par J2 (−6, −3, 0, +3, +6 m). Nie zmieniono geometrii świata.
Następny krok: Get-Content artifacts/sbs-r1/render-validation.log -Tail 20
