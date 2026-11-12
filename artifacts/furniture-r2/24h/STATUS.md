# Furniture r2 — stan pracy
Runda rozpoczęta 2026-11-12 około 02:10, po r1 6b48088b. Skopiowano artefakty r1 do main przez robocopy /E /XJ (kod 1, bez błędów).
Scalanie main 522361aa do własnej gałęzi: generated/world_manifest, streetscape_qa oraz street_props.glb przyjęto z main do regeneracji; materiały i licencje połączono addytywnie. Automatycznie scalone furniture/props i wspólne C#/shader przejrzano; zachowują zmiany obu stron.
Budżet, zasoby i obrazy r1 nie są baseline nowego main. Najpierw potrzebna spójna regeneracja i import, następnie bazowe obrazy r2.
NASTĘPNY KROK: przygotować własne skrypty r2 z ownerem heavy gpt-furniture-r2, uruchomić generator w slocie heavy, sprawdzić brak fallback=True; później Unity w slocie gpt-furniture.

2026-11-12T02:11:50.7024067+01:00: przygotowano sekwencyjny baseline.ps1 i skrypty bramek r2. PBR oraz world osobno w heavy gpt-furniture-r2; import i każdy render w Unity gpt-furniture, z przywróceniem ustawień. NASTĘPNY KROK: pwsh artifacts/furniture-r2/24h/baseline.ps1.

2026-11-12T02:22:39.3876622+01:00: heavy pbr before; sukces=True; slot gpt-furniture-r2 zwolniony. NASTĘPNY KROK: sprawdzić log i kontynuować walidację rundy.
