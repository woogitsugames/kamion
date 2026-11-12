Runda r3: kominy EC Białystok i korekta podpór po recenzji s12. Gałąź gpt-landmarks-r3; walidowany checkpoint geometrii b4da1f8e, baza main 14ccbaf1. Stan: gotowe do recenzji, fotograficznie PARTIAL.
Dwa stare kominy zastąpiono dwoma autorskimi modelami: jeden i trzy wyloty, biały dół, galerie i rytm pasów. Wysokości 120 m z technicznych źródeł; szczegóły głowic, średnica multi i malowanie WORKING_VALUE.
Trójkąty LOD0/LOD1: single 700/204 → 676/292, multi 700/204 → 636/274. Materiały na obu LOD: 4/3 → 3/3; bez nowych shaderów i przebiegów.
Runtime Unity potwierdza obie osie 0°. XY i yaw bez zmian, Z +3/+9 mm przez różne próbkowanie NMT. Nie prostowano geometrii według wyglądu obrazu.
Naprawiono P1/P2 z recenzji: wszystkie fazy w tej samej musztardowej farbie, przywrócony pigment, usunięta ukośna plama. Pomosty i brak schodów zachowane, netto −16 tris podpór; istniejącej rury nie zdublowano.
244 pary: 61 kamer × Low/High × clear/overcast; obejrzano wszystkie 32 arkusze, 95 PNG identycznych. Low: 122 pomiary, draws siatek +0 i instancji +0, suma tris −0,3185% do +0,3718%; to estymaty, bez pomiaru A16.
Pary foto|render 960 px: review/photo-after-corrected/Low-overcast-ec-ref073128.jpg oraz Low-overcast-heads.jpg. Filary before|after 840 px: review/pier-final-native-pair.jpg.
Zdjęcie Rakoon CC BY 3.0, lokalna kopia 3840×2160; oryginału nie zweryfikowano. Poza z resekcji dwóch osi jest robocza. Starsze zdjęcie Hiuppo CC BY-SA 2.5 potwierdza jasny dół; EMKA użyto tylko jako tekst H120 m.
W stałych oknach Low-overcast niezgodność czerwone/nie-czerwone spadła: multi 49,0→21,1%, single 55,5→0,0%. Nie jest to walidacja reflektancji ani geodezji.
Fotograficznie PARTIAL: kominy nadal za gładkie i szare, detale głowic i lokalizacja rury przy wiadukcie pozostają otwarte. Iglaki remizy wymagają następnej rundy.
Audyt: 125468 instancji poza EC i roads_qa identyczne; 7283 pozostałe prymitywy w 128 GLB bajtowo zachowane. Zmiana materiałów świata ograniczona do color pier_yellow; pełne hashe chunków z podporami zmieniły się.
Generator finalny 472,9 s, bez fallback=True; pojedyncze pliki EC 18/18 i podpomost 15/15. EditMode 317/317. Końcowy GIS: 643 PASS, 1 XFAIL, 1 FAIL (stale fidelity dla overrides.yaml i roads/meshing.py, oba niezmienione od bazy; stale-fidelity-proof.json). Physics/gate3: 48/48 PASS.
Cache 64 High + 64 Low + 64 instancje przed/po testach: wszystkie sumy zgodne z manifestem, brak zmian względem wyrenderowanego checkpointu. Nie wykonywano telefonu ani niezależnej akceptacji; bramka 3 otwarta.
Konflikty integracji: hero_building.py i landmarks.py — unia integracji EC; materials.py zachować oba bloki; agregaty generated i biblioteka props — main + regeneracja. Kod dróg i budynków Claude, globalna roślinność, shadery i profile nietknięte.
Następna runda: świeży merge main i nieregularne korony iglaków remizy w istniejącym budżecie. Bez push i scalania do main.

