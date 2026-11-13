# gpt-s16 r3 — ADR 0155 (WIP B)
Gałąź `gpt-s16-r3`; baza r2 `1f81e87ee` + main `e638abf31`. Gotowe do recenzji: NIE — docelowa QA/testy B w toku.
Zakres z ADR 0144 pkt 7: zdjęcia 2818/3970, wyspa E558/N−734 i hero Bieżeństwa na Andersa; tytuł „Putry” ze zlecenia.
Baseline generator 544,6 s, import obu tierów OK, 122 kamery × 4 warunki; 193 pliki świata zapisane hashami bez kopii całego katalogu.
Zdjęcia richlv 2020, CC BY-SA 4.0, z repo: SHA sprawdzone, pozy klasy B; bez kalibracji słońca/albedo i bez Google.
Efektywny URP Low 35m/1024/1/bias1/1; High 100m/2048/3/bias0,4/0,3. Chunk bridge On, hero LOD0/1 On, LOD2 Off.
14 globalnych ablacji × 5 ujęć: normal=0 usuwa szereg plam, depth=0 i no-baked go zachowują; to diagnoza, nie wynik docelowy.
A tylko viaduct_concrete: FAIL wizualny mimo EditMode 491/491; źródłowa flaga usunięta, zwarta para zachowana w inspection/candidate/.
Izolacje materiałów wykazały potrzebę zestawu bridge_concrete/road_asphalt/bridge_kerb; deck-triple usuwa wzór w 5 kadrach Low, critic potwierdził kierunek.
B: jawny regionalny shadow_caster_bias.json, 3 istniejące materiały; bez edycji roads/*, geometrii, globalnego QualityProfile/biasu lub bake.
WorldPBR: lokalny keyword tylko istniejącego ShadowCaster, depth bias zachowany, dawna ścieżka pozostałych materiałów; bez nowych materiałów/renderers/passów.
Polityka obejmuje wszystkie użycia tych 3 materiałów w regionie; dlatego pełna QA obejmuje też pozostałe mosty. Hero ma ustawienie bazowe.
9 nowych testów sprawdza m.in. reset po usunięciu pliku/wpisu, błędny schemat, legacy bez zmiany i natywny zakres dokładnie 3 materiałów.
Eksperymentalny cache cofnięty po ścisłym diff; 458 bazowych SHA przywrócone. Generator B w toku, potem import/pełna QA/testy/audyt i critic.
Dowody ≤960 px: ablation-sheets/, split-bias-sheets/, material-ablation-sheets/ i reference-sheet.jpg; pełne PNG tylko lokalne.
Telefon, ASTC, GPU i ruch UNVERIFIED; D51/Gate3 nie są zamykane. Ostateczne draws/tris i wyniki testów B jeszcze wymagane.
NASTĘPNY KROK: pwsh artifacts/gpt-s16-r3/verify-after.ps1 po generatorze B.
