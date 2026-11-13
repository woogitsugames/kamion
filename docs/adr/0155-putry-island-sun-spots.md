# ADR 0155 — plamy słońca na wyspie pod wiaduktem Putry

Status: wariant B po docelowym imporcie, pełnej QA i EditMode; pełny GIS i EditMode PASS, recenzja statyczna PASS; kandydat do integracji lidera. Gałąź `gpt-s16-r3` od r2 `1f81e87ee`, po merge main `e638abf31`.

## Problem i zakres

ADR [0144](0144-junctions-r7.md), punkt otwarty 7, opisuje regularne jasne plamy na żwirze w clear w ujęciach 2818555625124739 i 3970163613102941. Zakres przestrzenny tych referencji to wyspa E≈558/N≈−734 oraz `viaduct_biezenstwa` na Andersa. Zachowano tytuł „Putry” ze zlecenia, ale nie przeniesiono cech innego wiaduktu DK8/Putry. Zdjęcie 4312632558767412 dotyczy innego obiektu i nie uzasadnia tutaj paneli.

Dwa zdjęcia richlv, 2020-08-15, CC BY-SA 4.0, z repo mają zweryfikowane SHA256 (`reference-provenance.json`). Pozy są klasy B; nie ma pomiarowego dopasowania słońca, albedo ani obiektywu. Zdjęcia pokazują szeroki cień i jasny skraj żwiru: celem nie jest zaciemnienie całej wyspy. Bez Google i bez tekstur ze zdjęć.

## Baseline i diagnoza

Baseline generator 544,6 s, import Low/High OK, 122 kamery × clear/overcast × Low/High. Zapisano hashe 193 surowych plików świata zamiast kopii dużego katalogu. Read-only probe potwierdził chunk bridge On, hero LOD0/1 On, LOD2 Off. Efektywny URP w `pipeline.txt`: Low 35 m / 1024 / 1 kaskada / bias 1/1; High 100 m / 2048 / 3 kaskady / bias 0,4/0,3. Bounds prototypu nie oznaczają aktywnego LOD.

Pierwszy ray test obejmował mały północny nos żwirowy i nie uwzględniał hero; jest jawnie ograniczoną diagnostyką, nie wyjaśnieniem plam na głównej wyspie. Dodano osobną kamerę blisko głównej wyspy, wewnątrz zasięgu Low. Baseline ukazuje regularny szereg krótkich jasnych czworokątów; niezależny critic potwierdził obraz.

14 warunków globalnych (7 trybów × Low/High), po 5 pasujących kadrów: baseline, oba bias=0, normal=0, depth=0, sam wypiek, bez wypieku, oba rodzaje cienia wyłączone. `rq_shadow=0` nadal zachowuje baked shadow, więc nie jest kontrolą „wszystkie cienie off”. Normal=0 usuwa szereg; depth=0 i no-baked zachowują go. Globalna ablacja jest dowodem zależności od normal bias realtime, nie poprawką produkcyjną.

A: flagowanie samego hero `viaduct_concrete` nie usuwało plam. Odrzucono tę lokalizację mimo pełnego EditMode 491/491; testy kodu nie dowodzą celu wizualnego. Zachowano zwartą parę odrzuconej próby, a źródłową flagę hero usunięto.

Izolacje materiałów: bridge_concrete=0 dawał drugi szereg, road_asphalt=0 oraz bridge_kerb=0 osobno nie usuwały całości, para beton/asfalt nie wystarczała. All-PBR=0 odtworzyło globalne normal=0, potwierdzając lokalną ścieżkę shadera. Dopiero spójny zestaw **bridge_concrete + road_asphalt + bridge_kerb** usuwa szereg we wszystkich pięciu kadrach Low, zachowując duży cień i jasny skraj. Każda późniejsza próba resetuje wszystkie 139 wspieranych PBR przed wyborem podzbioru. Critic obejrzał 5 arkuszy i 2 pełne PNG zestawu; nie zauważył nowego oczywistego acne. To nie jest jeszcze końcowy PASS B/High/ruchu.

## Rozwiązanie B

Wersjonowany `Data/Regions/bialystok-industrial-c/shadow_caster_bias.json` jawnie ustawia normal-bias scale=0 tylko dla istniejących trzech materiałów. Polityka ma zakres wszystkich ich zastosowań w tym regionie; warstwa road nie rzuca cienia, bridge go rzuca. To nie jest zmiana wyłącznie pojedynczego renderera. Dlatego końcowa QA musi obejmować także pozostałe mosty. Nie skopiowano ani nie zmieniono chronionych definicji roads/*, geometrii, overrides, barier i krawężników.

`RegionImporter.CreateMaterial` nakłada opcjonalną politykę po istniejącej fabryce, także dla niestandardowych materiałów PBR. `WorldShadowCasterBias` czyta plik i waliduje schemat oraz skończone wartości 0…1 dopasowanych używanych wpisów. Brak pliku lub wpisu przywraca skalę 1 i usuwa keyword; błędny schemat zatrzymuje import. Domyślna wartość nie jest zapisywana do niezmienionego legacy cache.

WorldPBR dodaje właściwość domyślnie 1 i lokalny keyword wyłącznie w istniejącym ShadowCaster. Bez opt-in kompiluje dawny `ApplyShadowBias` bez nowych operacji. Wariant opt-in skaluje tylko składnik normalnego insetu, zachowując dokładnie `ld * _ShadowBias.x` z zainstalowanego URP `Shadows.hlsl:533–541`. ForwardLit i DepthOnly nie mają nowego wariantu ani formuły światła. Nadal 3 przebiegi, ten sam Cull; bez nowego materiału, renderera, geometrii lub pełnoekranowego efektu. Nie zmieniono WorldSurface, QualityProfile, globalnego biasu, słońca ani bake.

## Weryfikacja końcowa

9 nowych przypadków EditMode: legacy bez serializacyjnej zmiany, opt-in/reset bez zmiany pozostałych pól/passów, nieprawidłowe liczby, usunięcie wpisu/pliku regionu, zły schemat oraz natywny zakres dokładnie trzech materiałów. Pliki testowe tworzone i usuwane tylko we własnym `game/Temp`.

Przed B przywrócono 458 bazowych SHA materiałów po ścisłym porównaniu zmian diagnostycznych. Guard początkowo zatrzymał dodatkowe nieaktywne `_RECEIVESHADOWS_ON`/`_ZWRITE_ON`; po obejrzeniu diff dopuszczono tylko te nowe wpisy, właściwość/keyword biasu i znany legacy SrcBlend. Przywrócenie objęło 141 plików, bez innych zmian. Końcowy audyt zachowa trzy zamierzone opt-in i cofnie wyłącznie udowodniony szum serializacji.

Końcowy generator B: 542,0 s bez fallback, import obu tierów OK. Wszystkie 193 surowe pliki świata mają identyczny SHA z bazą. 122 pasujące kamery × 4 warunki mają delta scene/instance/shadow draws oraz dokładnych tris równe 0. Globalny URP jest identyczny tekstowo przed/po; pełne tabele w CAMERAS.md i camera-counts.json. To liczniki/estymaty CPU, nie GPU/SRP.

Native audit: 455/458 materiałów ma identyczny SHA; 3 wskazane różnią się tylko keyword i scale=0, bez nowych materiałów lub innych zmian właściwości. Po pełnym EditMode cofnięto 138 zweryfikowanych zapisów szumu cache, zachowując właściwą korektę. Żaden testowy plik policy nie pozostał w game/Temp. Zastąpione dwa duplikaty arkuszy usunięto; duże native PNG i prywatne kopie cache nie są w Git ani w pakiecie dla lidera.

Autor obejrzał wszystkie 24 author-overviews (488 par), 26 zbliżeń (w tym dwie dodatkowe bliskie pary) oraz 8 foto. Critic obejrzał wszystkie 44 overviews, 26 zbliżeń, 8 foto i dodatkowe native PNG. PASS dotyczy statycznego usunięcia regularnego szeregu przy zachowaniu dużego cienia i jasnego brzegu; nie znaleziono nowej konkretnej regresji do poprawy. Wzory „warstwic” na asfalcie wokół Bieżeństwa występują już w baseline. Nie deklaruje się naprawy tego odrębnego problemu.

Pełny EditMode B: 493 passed, 0 failed/skipped. Fidelity B zakończone exit0; pełny GIS: 986 passed, 4 xfailed w 945,46 s. Po teście ponownie potwierdzono193identyczneSHAświata oraz455identycznych materiałów i3wyłączneflagi. Telefon, ASTC, GPU, termika, migotanie i acne w ruchu pozostają u lidera. Pełne fotograficzne D51/Gate3 nie są zamykane przez tę korektę.
