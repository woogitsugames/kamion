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

2026-11-12T02:34:36.6274164+01:00: Unity sign-probe first Low overcast; sukces=False. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:34:37.1771192+01:00: próba znaków nie przeszła (exit=1). Własny import/render pozostaje wstrzymany przez PAUSE_UNITY do odczytu logu i naprawy. NASTĘPNY KROK: odczytać sign-probe-first.log oraz XML, usunąć marker dopiero po usunięciu błędu kompilacji.

2026-11-12T02:37:07.1255554+01:00: pierwsza próba: 2 passed, 6 failed; ForwardLit niedostępny w fixture bez aktywnego tagu pipeline, licznik passCount sam nie wystarczał. Wzmocniono sprawdzenie obecności ForwardLit i dodano jawny tag URP tylko na czas testu, z przywróceniem globali. Oryginalne nieudane wyniki zachowane w probe-first. NASTĘPNY KROK: ponowić wyłącznie FurnitureSignTests w slocie Unity i sprawdzić rzeczywiste wyniki, PAUSE_UNITY nadal własny.

2026-11-12T02:37:30.7972782+01:00: Unity sign-probe second Low overcast; sukces=False. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:37:31.3893840+01:00: próba znaków nie przeszła (exit=1). Własny import/render pozostaje wstrzymany przez PAUSE_UNITY do odczytu logu i naprawy. NASTĘPNY KROK: odczytać sign-probe-first.log oraz XML, usunąć marker dopiero po usunięciu błędu kompilacji.

2026-11-12T02:39:03.5433794+01:00: druga próba: 5 passed, 3 failed. Potwierdzono poprzedni pusty tag pipeline; po ustawieniu URP oba shadery mają rzeczywiście po 9 przebiegów. Off/no-source/alpha/publisher przeszły. Zbadano za słaby zwrot: dodano pomiar GPU samego współczynnika HDR bez kodowania gamma. Test dystansu teraz utrzymuje stały kąt obserwacji zamiast mieszać oba zjawiska. UsePass zapisano wielkimi literami zgodnie z dokumentacją Unity. NASTĘPNY KROK: ponowić wyłącznie próbę znaków, z zachowaniem nieudanych XML.

2026-11-12T02:39:27.5426397+01:00: Unity sign-probe third Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:42:39.6920904+01:00: trzecia próba GPU 10/10 passed, bez pominięć. Potwierdzono liniowy HDR współczynnika 1 i 800, zgodność off/no-source z URP Lit, alpha, przód/tył, kąt, dystans i 9→9 przebiegów. Generator bazowy zdobył slot heavy i działa. Dodano nieaktywną bez flagi fabrykę znaków do wspólnego C# oraz test jej trwałości i wycofania do Lit; manifest świata nadal bez flag znaku. NASTĘPNY KROK: izolowana próba fabryki i socketów high-only; własny import/render czeka na markerze.

2026-11-12T02:43:01.4134427+01:00: Unity sign-probe factory Low overcast; sukces=False. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:43:01.9909113+01:00: próba znaków nie przeszła (exit=1). Własny import/render pozostaje wstrzymany przez PAUSE_UNITY do odczytu logu i naprawy. NASTĘPNY KROK: odczytać sign-probe-first.log oraz XML, usunąć marker dopiero po usunięciu błędu kompilacji.

2026-11-12T02:46:40.3169847+01:00: próba fabryki: 11 passed, 1 failed na zbyt silnej tożsamości managed wrappera po AssetDatabase reimport. Test teraz kontroluje trwały GUID materiału i tekstury, shader oraz flagi. Przygotowano obsługę całej rodziny znaków przez jawną flagę plate_back: tylko aktualne identyfikatory z props_meta, bez etykiet fasad i bez nadpisywania cudzych jawnych definicji. Pozwala objąć tablice kierunkowe bez listy hashy; flaga nadal nieaktywna w bazowym świecie. NASTĘPNY KROK: dokończyć testy fabryki/rodziny w slocie Unity, sprawdzić bazowy generator.

2026-11-12T02:47:40.1495412+01:00: test rozszerzono na faktyczne lica całej biblioteki props_meta: tablice kierunkowe, komplet tekstur, zachowanie cudzej jawnej definicji i brak rejestracji po usunięciu flagi rodziny. Wciąż brak aktywacji w świecie bazowym. NASTĘPNY KROK: pwsh artifacts/furniture-r2/24h/sign-probe.ps1 -Phase family.

2026-11-12T02:48:08.1939883+01:00: Unity sign-probe family Low overcast; sukces=False. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:48:08.8948054+01:00: próba znaków nie przeszła (exit=1). Własny import/render pozostaje wstrzymany przez PAUSE_UNITY do odczytu logu i naprawy. NASTĘPNY KROK: odczytać sign-probe-first.log oraz XML, usunąć marker dopiero po usunięciu błędu kompilacji.

2026-11-12T02:50:55.7468006+01:00: próba rodziny 12 passed, 1 failed. Niezależny odczyt danych wyjaśnił 43 vs36: regex testu liczył 7 nazw prototypów (sign_post, gantry i g3), nie materiały. Fabryka poprawnie czytała wyłącznie listy materials. Poprawiono parser oczekiwanego zestawu, bez osłabiania wymogu pokrycia wszystkich rzeczywistych lic. Test GUID/wycofania do Lit i high-only przeszedł. NASTĘPNY KROK: ponowić FurnitureSignTests -Phase family-final.

2026-11-12T02:51:18.2860778+01:00: Unity sign-probe family-final Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:51:40.9599394+01:00: heavy world before; sukces=True; slot gpt-furniture-r2 zwolniony. NASTĘPNY KROK: sprawdzić log i kontynuować walidację rundy.

2026-11-12T02:52:44.8504475+01:00: końcowa próba znaków 13/13 passed, 0 skipped. Biblioteka ma 36 rzeczywistych lic drogowych; rejestracja obejmuje kierunkowe i pomija fasadowe oraz zachowuje jawne cudze definicje. Generator bazowy zakończył 64 GLB w715,7s, zapisano manifest/QA/props przed zmianami. Własny PAUSE_UNITY usunięty po sukcesie; sekwencja bazowa kontynuuje import i cztery rendery. NASTĘPNY KROK: odczytać sesję72293, po jej zakończeniu dodać baseline Low/High dusk; nie aktywować flagi świata przed kompletem before.

2026-11-12T02:53:06.4803513+01:00: Unity import before Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:53:36.9446836+01:00: Unity render before Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:54:02.7360427+01:00: Unity render before Low clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:54:42.3795780+01:00: Unity render before High overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:54:43.2256959+01:00: zapisano ADR i licencję wariantu URP oraz skrypt dodatkowego baseline dusk po zakończeniu dziennej sekwencji. Wyraźnie rozdzielono zmierzch (-5 stopni), pełną noc i kalibrację folii. NASTĘPNY KROK: odczytać zakończenie sesji72293; dopiero potem pwsh artifacts/furniture-r2/24h/baseline-dusk.ps1.

2026-11-12T02:55:12.5530885+01:00: Unity render before High clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:55:13.0653759+01:00: bazowe obrazy po scaleniu main gotowe. NASTĘPNY KROK: policzyć kompletność kamer i obejrzeć znaki przed zmianą.

2026-11-12T02:56:56.8954010+01:00: sekwencja72293 zakończyła się exit0. Cztery dzienne warianty mają po55 PNG (razem220). Przygotowano finish-baseline.ps1: dwa rendery zmierzchu, potem hashe chronionej geometrii w heavy. NASTĘPNY KROK: pwsh artifacts/furniture-r2/24h/finish-baseline.ps1; po sukcesie wdrożyć flagę/materiale, zużycie i Low mocowania z kandydatów.

2026-11-12T02:57:23.9113856+01:00: Unity render before Low dusk; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:57:52.5156759+01:00: Unity render before High dusk; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T02:57:52.9274336+01:00: bazowy zmierzch Low/High ukończony. Preset dusk ma słońce -5 stopni: to zmierzch, nie dowód pełnej nocy ani kalibracji folii. NASTĘPNY KROK: snapshot geometrii w heavy, wdrożenie własnego zużycia/mocowań/flagi i pojedyncze testy; potem generator kandydata.
