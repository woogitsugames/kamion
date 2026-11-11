# Status vegetation r1
Rozpoczęcie: 11 listopada 2026, sesja 24 h. Baza: main 4c9905b1.
Przeczytano wymagane instrukcje, budżety i recenzję roślinności. Zakres wyłącznie vegetation, ADR 0109.
Utworzono worktree gpt-vegetation na gałęzi gpt-vegetation-r1. Istniejąca starsza gałąź gpt-vegetation-r2 jest zajęta; nie zostanie zmieniona.
Następny krok: przygotowanie kopii danych i junctionów, git lfs checkout; potem baseline WorldC Low/High clear/overcast.
Kopie wymaganych danych i _Generated oraz junctiony tylko do odczytu przygotowane. Wykonano git lfs checkout.
Zapisano ADR 0109 r1: kontekst suchości, światowe pola metrów i budżet bez dodatkowych draws. Generator bazy działa; kopiowanie Library trwa. Następny krok: kontrola baseline-build.log, import z blokadą Unity, macierz before.
Dodatkowo skopiowano Library i lokalne pochodne materiałów, aby zachować bazę renderów.
Przygotowano review_images.py: wszystkie kamery, draws statyczne i instancje osobno, stałe ROI i odchylenie średnich bloków 32 px. Brak jeszcze nowych pomiarów. Następny krok: uv run --project tools/worldgen python artifacts/vegetation-r1/review_images.py
Zapisano PLAN.md z hipotezami trawy, pokrywy żywopłotu i koron. Regeneracja bazowa działa. Następny krok: kontrola logu, import bazowy i before. Pliki generatorów Blender pozostają poza edycją (własność).
Przygotowano sekwencyjną kolejkę: czeka na koniec generatora, odrzuca fallback, pobiera slot, importuje i renderuje bazę. Następny krok: pwsh artifacts/vegetation-r1/baseline-pipeline.ps1
Wywołania Acquire ustawiają StaleHours 1000000, aby skrypt nie sprzątał cudzych slotów. Owner pozostaje gpt-vegetation. Następny krok: dokończyć sekwencyjny baseline; nie zmieniać shaderów przed końcem before.
Przygotowano wyłącznie syntetyczną hipotezę masek ground_candidate.py: osobno jawny trawnik, pobocze i teren niekoszony. To nie render ani dowód poprawy. Następny krok: obejrzeć ground-mask-hypothesis.jpg i ocenić kandydat na końcu before.
Obejrzano syntetyczny podgląd maski i zapisano GROUND-CANDIDATE.md. Potwierdzono 15 zasobów Megascans ready. To nie dowód renderu; czekamy na bazę. Następny krok: zakończenie baseline-pipeline, potem wdrożenie i A/B.
