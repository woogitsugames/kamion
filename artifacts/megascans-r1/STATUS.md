# Megascans R1 — gpt-megascans

- Krok 1: przeczytano kontrakt i zasady; worktree z main 2df87f1. Bez zmian w main, telefonach i ustawieniach projektu.
- NASTĘPNY KROK: `robocopy C:\Users\matma\Documents\Claude\kamion\Data\raw Data\raw /E /XJ /R:1 /W:1`

- Krok 2: Data/raw skopiowane fizycznie /E /XJ; git lfs checkout zakończone. Uruchomiono 3 rozłączne zakresy: procesor Fab, rozmieszczenie, kora/liście.
- NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` (baseline przed integracją).

- Krok 3: obejrzano 7 arkuszy (80 map) i 5 szczegółów. Odrzucono round-manhole-cover (emblemat/napisy), trash-can (żółty emblemat), urban-trash (opakowania/marki), pine-bark (atlas ściółki zamiast kory pnia). Linden Branch zawiera gałąź, nie liście; liście pozostają fallback.
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m fab.prepare` (po zakończeniu procesora).
