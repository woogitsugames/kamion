# gpt-s16 r3 — ADR 0155 (WIP)
Gałąź gpt-s16-r3; baza r2 1f81e87ee + origin/main e638abf31. Gotowe do recenzji: NIE — docelowy after/testy w toku.
Zakres z ADR0144 pkt7: ujęcia2818/3970, wyspa E558/N−734 i hero Bieżeństwa na Andersa; tytuł „Putry” zachowany ze zlecenia.
Baseline generator544,6s, import Low/High OK, 122kamery×4warunki. 193pliki surowego świata zapisane hashami bez kopii dużego katalogu.
Zdjęcia richlv2020 CC BY-SA4.0 z repo: SHA zweryfikowane, pozy klasy B; brak kalibracji kierunku światła/albedo. Obejrzone, bez Google.
Natywnie bridge On, hero LOD0/1 On i LOD2 Off. Low35m/1024/1/bias1/1; High100m/2048/3/bias0,4/0,3; efektywny URP osobno pipeline.txt.
14ablacji×5kadrów rozdziela bias normalnych/głębokości i wypiek/realtime; normal=0 usuwa rząd plam w obu tierach, depth=0 i no-baked go pozostawiają.
Dowody ≤960px: ablation-sheets/ (10), split-bias-sheets/ (6), inspection/baseline/ (4), reference-sheet.jpg; critic potwierdził obserwację.
Kandydat tylko viaduct_concrete: shadow_normal_bias_scale=0, lokalny keyword ShadowCaster PBR. Pozostałe materiały mają dawną ścieżkę; depth bias zachowany.
Bez zmian geometrii dróg/pomostu, overrides, kierunku słońca, QualityProfile i bake; bez nowych materiałów/renderers/passów. Budżet docelowych kamer czeka na after.
Dodano7testów EditMode: legacy bez zmiany serializacji, reset flagi, invalid dane, niezmienione inne pola/passy i natywny zakres jednego materiału; uruchomienie po import after.
W toku generator after, potem import/render wszystkich czterech warunków, audyt/cache cleanup, pełny GIS/EditMode i końcowy critic.
Telefon/GPU/ASTC/ruch pozostają UNVERIFIED i u lidera. Globalna ablacja nie jest wynikiem produkcyjnym.
NASTĘPNY KROK: pwsh artifacts/gpt-s16-r3/import.ps1 -Label after; pwsh artifacts/gpt-s16-r3/render.ps1 -Stage after
