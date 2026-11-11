Gałąź gpt-vegetation-r1. Kod wariantu B: 51bd2559; baza: 4c9905b1. Dowody mają hashe źródeł w evidence-summary.json.
Runda daje ograniczoną poprawkę edytorową trawy i pokrywy berberysu, nie zamyka całego backlogu roślinności.
Rozdzielono jawne trawniki OSM od poboczy; suchość ma pola 8 m i 2,5 m, bez wymyślania odsłoniętej gleby. Shader mnoży fotograficzne albedo zamiast zastępować detal stałą barwą.
Zapisano i oceniono 322 obrazy przed i 322 po: 67 kamer Low/High w clear/overcast oraz 27 kadrów zdjęciowych w dwóch profilach.
Stały obszar samej trawy, odchylenie średnich bloków 32 px przed/po: Low-overcast 3,614/5,170; Low-clear 4,416/5,476; High-overcast 2,981/3,900; High-clear 3,179/3,495.
Mediana jasności tego obszaru rośnie też o około 18–19 jednostek sRGB. To roboczy wygląd suchości, nie pomiar wilgotności. Mieszany starszy ROI obejmuje chodnik i nie służy jako dowód samej trawy.
Wszystkie 322 porównania kamer: delta draws 0, delta triangles 0%. Draws statyczne i instancji osobno w all-camera-costs.csv; nie jest to pomiar czasu GPU.
Cztery aktywne żywopłoty mają 18 402 trójkąty przed i po. Lokalna wysokość pokrywy i rdzenia naprawia przebijanie berberysu; inne prototypy zachowano.
Korony trzech kamer kontrolnych mają te same statystyki na stałej masce przed/po. Samocień nie poprawił Putry i został wycofany. Wariant A odrzucono i zachowano w candidate-a-rejected.
Testy celowane 12/12; Unity EditMode 261/261. Pełny GIS na końcu rundy: 495 passed, 1 xfailed, 1 failed w 612,15 s.
Jedyny błąd GIS to test_road_fidelity.py::test_report_not_stale. Raport był nieaktualny już w bazie, a siedem wskazanych źródeł dróg pozostaje niezmienionych; dowód w fidelity-stale-baseline-proof.json. Nie regenerowano cudzej dziedziny.
Audyt po testach nie wykazał driftu źródeł ani zmian wyjść użytych w renderach. Megascans: 15 gotowych zasobów, fallback false przed i po. Surowy hash assetu kolizji nie potwierdza równości geometrii po zmianie identyfikatorów Unity.
Pary zdjęcie/przed/po do 960 px: photo-pairs, np. High-clear-photo-2048x1536-sbs-g3-b-209622370971977.jpg; wszystkie źródła, daty i licencje w photo-references.json. Pozy pozostają UNVERIFIED; większość zestawu dokumentuje także wiadukt.
Niezależny visual-critic: PASS ograniczonej poprawki edytorowej, ogólny realizm FAIL. Szczegóły w VISUAL-CRITIC.md oraz docs/reports/visual/2026-11-11-vegetation-0109-r1.md.
Otwarte: jasne korony High Putry, sylwetki sosen i tui, nasadzenia Putry, bryłowy wygląd berberysu, powiązanie trawy z użytkowaniem miejsca. Telefony, GPU A16, ruch i popping: UNVERIFIED.
Zmiany współdzielone są addytywne za istniejącymi flagami gruntu w WorldPBR i WorldSurface; brak nowych próbek, przebiegów i pól QualityProfile. Potencjalne konflikty tam oraz w danych generowanych: main i regeneracja. Pełne migawki metadanych są w snapshot-candidate-b-pretests.
Nie scalano do main i nie pushowano. Następna runda zachowa obcy dawny gpt-vegetation-r2, wybierze wolny numer i będzie kontynuować otwarty priorytet koron z backlogu.
