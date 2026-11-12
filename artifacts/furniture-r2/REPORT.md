# Raport furniture r2 — znaki pionowe, ADR 0120
Gałąź gpt-furniture-r2; zweryfikowany kod i zasoby: 52668015. Baza po merge main: 3fe0c97f; SHA zamknięcia wskazuje historia gałęzi.
Dodano miejscowe, deterministyczne zużycie lic, subtelniejsze blaknięcie czerwieni i dwa dystanse mocujące Low w istniejącym materiale. Kolizje i mocowania High bez zmian tej poprawki.
Odblask korzysta z rzeczywistych socketów i stanu TruckLights, bez nowego światła URP ani przebiegu. Shader zachowuje 9 przebiegów i układ bufora URP Lit; brak źródła wyłącza odpowiedź.
Biblioteka ma 36 lic, a odczyt sceny potwierdził 35 przypisanych materiałów z aktywnym shaderem. Etykiety fasadowe i cudze jawne definicje wykluczono.
Obejrzano także niezależnie [330 par na 60 arkuszach](24h/compare/), Low/High × clear/overcast/dusk, szerokość 960 px; brak nowego widocznego blokera furniture. [Ocena](24h/compare/REVIEW.md).
Wszystkie 330 wariantów: CPU DrawEst mesh +0, instancji osobno +0, cieni mesh +0. Dokładne 165 Low: max tris +0,18998%, poniżej +2%. [Pełne liczniki](24h/frame-budget.csv); nie jest to czas GPU.
Chronione payloady geometrii 6833→6833, zero różnic. Generator 64 chunki, bez fallback=True. Import danych mesh/instancji/kolizji Low 120,7→120,8 MB, High 262,8→262,9 MB; nie PSS.
Night-rig Low/High: 48 PNG, 25/50/100 m i cztery tryby; audyt potwierdził wszystkie 96 rzeczywistych próbek źródeł. [Podglądy i ocena](24h/night-preview/), [stany](24h/night-rig/after3/source-state-audit.json).
EV100=5, gain800, wiązki i zasięg pozostają WORKING_VALUE. Model nieba kończy się na −8°; dusk to −5°. Brak kalibracji folii i okluzji ścieżki światła; nie potwierdzono głębokiej nocy ani praktycznej czytelności.
[Zdjęcie i render](24h/reference-sign-Low-after3.jpg) mają 960 px; poza B i duża rozbieżność sceny nie pozwalają potwierdzić zgodności znaku/uchwytów. Drobne śruby i spasowanie pozostają UNVERIFIED.
Własne pojedyncze Python: 17/17, 9/9, 10/10. FurnitureSignTests: 16/16, w tym rzeczywiste próby GPU versus Lit i obsługa fabryki. Końcowe EditMode: 340/340, bez pominięć.
Końcowy pełny GIS: 644 passed, 1 xfailed, 1 failed w 827,24 s. Jedyna porażka: zastane hashe fidelity dla overrides.yaml i roads/meshing.py; oba wejścia oraz raport niezmienione od bazy r2, co potwierdza audyt.
Physics/gate3: 48 passed w 263,70 s. Nie kopiowano porażki r1 jako wyniku r2. Efekty uboczne wygenerowanych raportów innych dziedzin cofnięto.
Wspólne pliki materials.py i WorldPbrMaterials.cs zmieniono addytywnie za flagą furniture_sign_fronts; zachować ją wraz z furniture_plinth_detail. Po integracji przez lidera regenerować produkty świata.
Brak telefonu, APK/Vulkan, pomiaru GPU/PSS i testu w ruchu. Nie scalano do main, nie pushowano i nie zmieniano barier. Pełna metoda, źródła i ograniczenia: [PACKET.md](24h/PACKET.md).
Następna runda: przystanki, wiaty, kosze i słupki według przygotowanych referencji Mapillary; brak tagu lub bliskość zdjęcia nie dowodzą nieobecności ani obecności obiektu.
