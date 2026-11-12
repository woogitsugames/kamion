# Furniture r2 — stan pracy
Runda rozpoczęta 2026-11-12 około 02:10, po r1 6b48088b. Skopiowano artefakty r1 do main przez robocopy /E /XJ (kod 1, bez błędów).
Scalanie main 522361aa do własnej gałęzi: generated/world_manifest, streetscape_qa oraz street_props.glb przyjęto z main do regeneracji; materiały i licencje połączono addytywnie. Automatycznie scalone furniture/props i wspólne C#/shader przejrzano; zachowują zmiany obu stron.
Budżet, zasoby i obrazy r1 nie są baseline nowego main. Najpierw potrzebna spójna regeneracja i import, następnie bazowe obrazy r2.
NASTĘPNY KROK: przygotować własne skrypty r2 z ownerem heavy gpt-furniture-r2, uruchomić generator w slocie heavy, sprawdzić brak fallback=True; później Unity w slocie gpt-furniture.

2026-11-12T02:11:50.7024067+01:00: przygotowano sekwencyjny baseline.ps1 i skrypty bramek r2. PBR oraz world osobno w heavy gpt-furniture-r2; import i każdy render w Unity gpt-furniture, z przywróceniem ustawień. NASTĘPNY KROK: pwsh artifacts/furniture-r2/24h/baseline.ps1.

2026-11-12T02:22:39.3876622+01:00: heavy pbr before; sukces=True; slot gpt-furniture-r2 zwolniony. NASTĘPNY KROK: sprawdzić log i kontynuować walidację rundy.

2026-11-12T02:23:20.1485209+01:00: PBR po scaleniu zakończony w452s; world czeka na osobny slot heavy. Przygotowano poza Assets prototyp materiału znaku zgodnego z URP Lit (9→9 przebiegów) i czytnik istniejącego TruckLights oraz prawdziwych socketów. Zapisano źródła zasad kątów, licencję szkieletu, hashe i ograniczenia (brak kalibracji folii/occlusion). To nie jest wdrożony ani zweryfikowany efekt. NASTĘPNY KROK: dokończyć bazowy world/import/render; przed zmianą wykonać także Low/High dusk, potem przenieść i sprawdzić prototyp GPU oraz rzeczywistym riggiem.

2026-11-12T02:29:09.6966270+01:00: prototyp uzupełniono o osobne pozycje i stany świateł mijania/drogowych oraz projekt testów GPU: zgodność off z URP Lit, brak źródła, alpha, przód/tył, kąt i dystans; testy jeszcze nieuruchomione. Prototyp fabryki zachowuje bazową teksturę/UV po wyłączeniu opcjonalnego odblasku. Bieżące renderery mają m_RenderingMode=0 (Forward). NASTĘPNY KROK: odczytać żywy baseline (sesja 72293); nie uruchamiać duplikatu, dokończyć bazowe obrazy i dusk przed przenoszeniem prototypu do Assets.

2026-11-12T02:34:08.7719984+01:00: nowe pliki prototypu przeniesiono do Assets wyłącznie do izolowanej próby GPU. Żaden materiał świata nie używa nowego shadera, a nowe globale nie są czytane przez dotychczasowe shadery. Python i fabryka materiałów świata bez zmian. Własny PAUSE_UNITY wstrzymuje przyszły import/render bazowy do zakończenia próby; nie dotyka cudzych blokad. NASTĘPNY KROK: pwsh artifacts/furniture-r2/24h/sign-probe.ps1.
