# gpt-s16 r3 — ADR 0155
Gałąź `gpt-s16-r3`; kod/audyty/testy `7526bb1032`; poprzednie dowody `44659ccaf1`, baza r2 `1f81e87ee` + main `e638abf31`. Gotowe do recenzji: TAK (statyczny edytor; telefon u lidera).
Usunięto regularny szereg jasnych plam na wyspie z ADR 0144 pkt 7 (SBS 2818/3970; Bieżeństwa/Andersa, tytuł „Putry” ze zlecenia).
Jawna polityka regionu `shadow_caster_bias.json`: normal-bias scale=0 dla bridge_concrete/bridge_kerb/road_asphalt; zachowany bias głębokości i dawny wariant innych materiałów.
Zakres: wszystkie użycia 3 materiałów w regionie, w chunkach tylko bridge/road; road nie rzuca cienia. Pozostałe mosty objęte pełną QA.
Bez zmian geometrii, roads/*, overrides, barier, krawężników, globalnego QualityProfile, słońca i bake; ten sam Cull i 3 przebiegi shadera, zero nowych materiałów/renderers.
Baseline generator 544,6 s, końcowy B 542,0 s, bez fallback; import Low/High OK. 193 surowe pliki świata identyczne SHA256.
122 kamery × 4 warunki: na każdej delta scene/instance/shadow draws=0 i dokładnych tris=0, w Low i High; globalny URP identyczny przed/po.
Każda kamera: CAMERAS.md i camera-counts.json; są to estymaty/liczniki CPU, nie GPU/SRP lub wynik telefonu.
Materiały natywne: 455/458 identycznych SHA, 3 wskazane różnią się tylko keyword/scale=0; zero nowych, reszta danych bez zmian (native-material-audit.json).
Po pełnym EditMode cofnięto 138 udowodnionych szumów serializacji, zachowując 3 właściwe korekty; zero pozostałych testowych plików policy w game/Temp.
Dowody ≤960 px: 488 par, 26 zbliżeń (w tym 2 dodatkowe near), 8 foto; autor obejrzał całość w 24 arkuszach i szczegółach. Critic PASS statycznej poprawki B.
Regularne plamy znikają w Low/High clear i overcast; duży cień i jasny skraj zachowane; brak nowego oczywistego acne na obejrzanych pomostach/podporach.
Zdjęcia richlv 2020, CC BY-SA 4.0, SHA sprawdzone; pozy B i światło niekalibrowane. Pełne fotograficzne D51/Gate3 pozostają otwarte.
Testy: EditMode 493 passed, 0 failed/skipped (9 nowych przypadków, także usunięcie wpisu/pliku i natywny zakres 3 materiałów); fidelity B exit0. Pełny GIS 986 passed, 4 xfailed, 945,46 s.
A tylko hero i pojedyncze materiały odrzucono wizualnie; rozstrzygające ablacje i zwarte dowody zachowane. Usunięto 2 zastąpione duplikaty arkuszy.
Wspólne pliki tylko addytywnie za danymi: WorldPBR.shader i RegionImporter.cs + helper. Możliwe konflikty także generated/fidelity_qa.json i world_manifest.json; unia źródeł i regeneracja/import.
Odtworzenie: baseline-world.ps1 -Stage after → import.ps1 → render.ps1 -Stage after; opcjonalna polityka resetuje bias po usunięciu wpisu/pliku. Skrypty używają slotów MAIN i PHONE_RUN.
Telefon, ASTC, GPU p95, termika i ruch UNVERIFIED — lider. Main i telefony nietknięte; push wyłącznie gpt-s16-r3, recenzja/integracja r1→r2→r3 przez lidera.
