# Megascans R1 — gpt-megascans

- Krok 1: przeczytano kontrakt i zasady; worktree z main 2df87f1. Bez zmian w main, telefonach i ustawieniach projektu.
- NASTĘPNY KROK: `robocopy C:\Users\matma\Documents\Claude\kamion\Data\raw Data\raw /E /XJ /R:1 /W:1`

- Krok 2: Data/raw skopiowane fizycznie /E /XJ; git lfs checkout zakończone. Uruchomiono 3 rozłączne zakresy: procesor Fab, rozmieszczenie, kora/liście.
- NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` (baseline przed integracją).

- Krok 3: obejrzano 7 arkuszy (80 map) i 5 szczegółów. Odrzucono round-manhole-cover (emblemat/napisy), trash-can (żółty emblemat), urban-trash (opakowania/marki), pine-bark (atlas ściółki zamiast kory pnia). Linden Branch zawiera gałąź, nie liście; liście pozostają fallback.
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m fab.prepare` (po zakończeniu procesora).

- Krok 4: procesor kory/krawężnika 4/4 testy. Trzy ZIP-y różnią się od pierwotnego manifestu; potwierdzono CRC, nazwy/ID Quixel i FBX. Przypięto zaobserwowane SHA, zachowując stare wartości; przyczyna rozbieżności UNVERIFIED. Fab nadal wyłącznie lokalnie.
- NASTĘPNY KROK: `uv run --project tools/worldgen python tools/worldgen/fab/prepare.py --blender C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe`.

- Krok 5: baseline build zakończony (64 chunki, 418 MiB High / 91 MiB Low); trwa import baseline z KAMION_DISABLE_FAB=1. Testy Fab 28/28. Niezależny review wykrył brak tangentów w compact mesh: normal mapy wyłączone, AO keyword naprawiony, UV0 Fab jawnie zachowane.
- NASTĘPNY KROK: `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -OutputDir artifacts/megascans-r1/before/Low-overcast` (po imporcie).

- Krok 6: ADR 0084 a użycia/odrzucenia 19 pozycji zapisane w LICENSES. Budżet Python obejmuje zmierzone LOD Fab; UV0/alpha/AO poprawione. Baseline import regeneruje istniejące PBR (stemple świeżego worktree); nadal trwa.
- NASTĘPNY KROK: `Get-Content artifacts/megascans-r1/before-import.log -Tail 10`.
