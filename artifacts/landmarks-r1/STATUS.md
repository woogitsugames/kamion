# Stan sesji landmarks, runda 1

Przeczytano zadanie 05, HANDOVER s10, zasady, budżety, decyzje D48–D50 i recenzje remizy oraz wiaduktu. Worktree gpt-landmarks, gałąź gpt-landmarks-r1 utworzone z main 5f2aa277.
Zakres: wyłącznie remiza, podpomostowa część wiaduktu i kominy. Bez push, scalania do main i telefonów. Unity wyłącznie przez slot Owner gpt-landmarks, zwalniany po każdym uruchomieniu.
Krok 1: przygotowanie danych i audyt bieżącej remizy. Historyczne artifacts/firestation-r10 zawierają obce aktualizacje i nie są stanem tej sesji.
NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r1/bootstrap.ps1

Krok 2: prywatne kopie derived, CC0, Megascans i _Generated wykonane; Library w kopiowaniu. Przygotowano wrapper unity-step.ps1: Acquire/Release Owner gpt-landmarks osobno wokół każdego importu, renderu i testu, restore efektów ubocznych w finally. Zachowano zdjęcie referencyjne Commons 7197, Rakoon, CC0. Uruchomiono świeży generator bazowy; wynik jeszcze niezweryfikowany.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/baseline-world.log -Tail 20

Krok 3: bootstrap zakończony, git lfs checkout OK, wszystkie pięć junctionów wejściowych gotowe. Trwa świeża regeneracja świata i pełnych materiałów, testy GIS rozpoczęte. Przygotowano ADR 0116 oraz helper porównania wszystkich kamer z osobnym raportowaniem siatek i instancji. Baseline wizualny i wartości barw UNVERIFIED.
NASTĘPNA KOMENDA: po zakończeniu generatorów: pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Import
