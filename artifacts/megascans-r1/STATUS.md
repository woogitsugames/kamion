# Megascans R1 — gpt-megascans

- Krok 1: przeczytano kontrakt i zasady; worktree z main 2df87f1. Bez zmian w main, telefonach i ustawieniach projektu.
- NASTĘPNY KROK: `robocopy C:\Users\matma\Documents\Claude\kamion\Data\raw Data\raw /E /XJ /R:1 /W:1`

- Krok 2: Data/raw skopiowane fizycznie /E /XJ; git lfs checkout zakończone. Uruchomiono 3 rozłączne zakresy: procesor Fab, rozmieszczenie, kora/liście.
- NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` (baseline przed integracją).
