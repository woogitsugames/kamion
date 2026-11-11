# Następny strumień: C r13 / ADR 0108

Nie uruchamiać przed zamknięciem bieżącego G. Wykonawca: fab_processor, nowe worktree gpt-light-r13 z main aktualnego w chwili startu. Sprawdzić istniejące gałęzie/worktree przed utworzeniem, niczego nie nadpisywać. Nie scalać ani nie pushować main. Reread task/feedback/rules oraz aktualne źródła; nie kopiować źródeł D/G jako rzekomo scalonych.

Przygotowanie według GPT-TASK-02: LFS checkout, fizyczne kopie derived/CC0/Fab produktów/Megascans/_Generated, wejściowe junctiony tylko odczyt. Potwierdzić15 gotowych produktów Fab i brak fallbacku. Kanoniczne build/install pojazdów PRZED ostatecznym normalnym importem i BEFORE; po BEFORE bez reinstalacji. Nowa runda ma własny token/release i guard PHONE_RUN/GPT_UNITY_HOLD bezpośrednio przed każdym Unity, także po długiej pracy CPU. Marker unieważnia token na stałe do nowego jawnego release ROOT.

Źródła przygotowawcze w głównym artifacts:
- car-paint-r1/C13-PREFLIGHT.md
- firestation-r10/C13-INSTRUMENTATION-PREFLIGHT.md i nieaktywny C13CameraProbeFeature.cs
- surface-wear-r1/C13-URP-API-VERIFICATION.md oraz przypięte źródła URP17.3

Najpierw naprawić warunkowanie Execute w nieaktywnym szkicu, skompilować tymczasowy observer i wykazać domyślną zgodność probe OFF/ON. Bez zmiany ProjectSettings, Packages ani cache URP. Zapisać niezmienne dane descriptor/source/final PRZED postprocessingiem; nie odczytywać później mutowanego UniversalCameraData jako dowodu rozdzielczości wewnętrznej. CPU ustawienia i material keywords nie dowodzą wykonania EASU/RCAS. Potrzebny dowód rzeczywistych drawów z rozmiarami i wariantem albo jawne UNVERIFIED oraz ograniczona diagnostyka uzgodniona z ROOT.

P0: ablacją rzeczywistego upscale RCAS0/.25/.5/.75 wybrać ostrość bez powrotu pieprzu. Natywne High scale1 nie dowodzi działania FSR. Prawdziwe70% to1638x756 wewnętrzne do2340x1080, bez bilinear-proxy. Zachować Low/Medium fixed.75 i FragFast z0106 oraz sky pre-LUTditherOFF/finalditherON. Porównać detal do sensownego obecnego .75 reference, nie do rozmytego zera; jawnie oddzielić kontrole diagnostyczne od polityki shipping.

Pozostały zakres0108: płaskie ściany (przyczynowe kontrole normal/base/detail), faliste cienie lowsun, dalekie piony/mgła, AO pod wiaduktem po0105, struktura nieba, white-car exposure/tonemapping bez pigmentu. Komin pochylenie sprawdzić i naprawić w dozwolonym zakresie albo dokładnie przekazać liderowi. Mały focus i review przed pełną macierzą. WIP+STATUS po kroku, meaningful GIS/EditMode, ADR0108 i czytelny REPORT z uczciwymi ograniczeniami; kopia artefaktów bez prywatnych map. B r3/0109 dopiero jako następny priorytet po tej rundzie.
