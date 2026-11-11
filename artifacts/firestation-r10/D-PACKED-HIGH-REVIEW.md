# D packed mask — niezależny review High, 2026-11-11

**Werdykt: zakresowy visual nonregression PASS dla ośmiu statycznych ujęć High. Nie jest to pixel-parity ani native G/B/A exact PASS.** Lokalny błąd kompresji jest rzeczywisty i opisany niżej; w obejrzanych kadrach nie tworzy widocznego pasa, podwojenia pęknięć lub rozległej zmiany połysku. Nie oceniam korzyści Low, retencji rozwiązania ani kosztu A16.

## Materiał i kontrola próby

Obejrzano wszystkie osiem par High-clear/High-overcast: `d_wear_lane_old`, `d_wear_missing_uv_2`, `d_wear_newroad_negative`, `d_field_p8_turn`. BEFORE pochodzi z `wear-probe-before`, AFTER z `packed-mask-qa` w D worktree `gpt-surface-wear/artifacts/surface-wear-r1`. Własne pary w `D-packed-high-pairs-960/` są wyłącznie rozmiarowe, bez korekt tonalnych. SHA wszystkich wejść zgadza się z capture proof. Dodatkowo obejrzano cztery pary natywnych cropów 1:1 wokół największych różnic we wskazanych asfaltowych ROI, bez powiększania i bez wzmacniania kontrastu.

Odczytano `packed-mask16-gpu-proof.json`, `packed-mask16-image-metrics.json`, `packed-mask16-capture-proof.json` oraz High run proofs. Oba High uruchomienia mają exit0, cztery świeże klatki i finally restored. Capture proof podaje dokładne runtime camera/vehicle i zaokrąglone counters, shipping 2441 oraz raw 192 zgodne. Produkcyjny shader pozostał przy SHA `1dc7db4e…125edce4`; QA używa osobnego shader copy i jednej tymczasowej kopii `M_road_asphalt`.

Sprawdzono również zakres źródłowy: różnica QA shader to nazwa/ścieżka include, Mask UV×.25 i odpowiedź packed R tylko dla `!_KAMION_WORLD_DETAIL`. High nadal używa poprzedniego zewnętrznego `_CRACKS`; nie dodano mu odpowiedzi Low. Kontroler zachowuje material keywords/global keyword space, texture bindings poza MaskMap oraz przywraca renderer materials i zapisane globals w finally. To spełniony warunek zakresu, a nie powód do pominięcia oglądania obrazu. Nie zmieniono źródeł ani nie uruchomiono Unity/testów w tej sesji.

## Oglądanie i kontrole negatywne

- **Old lane, oba światła:** położenie i ilość istniejących pęknięć pozostają wizualnie takie same. Nie widzę nowej ciemnej sieci nałożonej drugi raz, rozlania AO ani nowej szerokiej mokrej smugi. Przy natywnym ziarnie są drobne różnice pojedynczych jasnych/ciemnych punktów; nie nazywam tekstury identyczną.
- **Missing UV2, oba światła:** te same większe plamy i pęknięcia, bez nowego pasma wzdłuż krawężnika. W natywnym overcast występują lokalne różnice drobnego ziarna, lecz nie czytają się jako nowa plama materiału w 960. Nazwa kamery nie dowodzi braku danych materiału; to kontrola tego konkretnego kadru.
- **New road negative:** bez widocznej nowej sieci cracks, mokrego połysku albo zmiany jasności świeżego asfaltu. Stare ciemne zużycie zebry było w BEFORE i nie jest skutkiem packingu. Kontrola nie daje automatycznego PASS wszystkim świeżym drogom.
- **P8:** kształt i kontrast strzałki zachowane; jej istniejący ciemny fragment pozostaje w tym samym miejscu. Nie widzę nowej utraty czytelności, zmiany tła wokół znaku ani nowego obrysu cracks. Ocena dotyczy tych dwóch widoków, nie dowolnej farby/odległości.

## Lokalny błąd — nie ukrywać go średnią

GPU proof jest z RTX5070/D3D12, przy obu mapach zgłaszanych jako ASTC8/linear. Dla mip0 mean-absolute G/B/A wynosi około **.223/.051/.105 poziomu maski**, ale maxima to **62/18/13**; **2.07% G** ma różnicę ponad 3 poziomy. Źródłowe byte-exact G/B/A nie przetrwało więc jako exact skompresowane kanały. Nie jest to wyłącznie nieistotna cyfra średniej.

Odczytane metryki obrazów High wskazują bliskie zeru signed średnie, lecz ogon lokalnych różnic jest większy. Niezależnie policzono dla tych samych asfaltowych ROI display ΔY z natywnych PNG i obejrzano miejsca maksymalnego błędu:

| Kadr | Max abs ΔY; współrzędna natywna | Największa 8-connected grupa abs ΔY>3 w ROI |
|---|---|---|
| Old lane clear | 8.21; (1218,881), przyciemnienie | 3 piksele, bbox3×2 |
| Missing UV2 clear | 7.07; (1489,934), rozjaśnienie | 3 piksele, bbox2×3 |
| Old lane overcast | 11.07; (1314,706), rozjaśnienie | 8 pikseli, bbox6×3 |
| Missing UV2 overcast | 9.86; (1826,813), rozjaśnienie | 15 pikseli, bbox7×4 |

To grupy pikseli obrazu, nie pomiar fizycznych defektów lub bezpośrednia segmentacja AO. Przy progu abs>3 obejmują około0.122%/0.048%/0.644%/0.260% odpowiednich ROI. Grupy o rozmiarze kilku pikseli natywnych giną w ziarnie pełnego960 kadru; cropy nie pokazują dużej, spójnej zmiany AO/spec. Dlatego traktuję je jako **lokalny drift do ujawnienia**, a nie zauważalną szeroką regresję. Migotanie tych punktów w ruchu pozostaje niezweryfikowane. Own metadata: `native-hotspot-metrics.json`, cropy `*-native-hotspot.png`.

D image metrics dodatkowo podaje old-lane ROI mean abs ΔY .519 clear/.572 overcast, p99 około2.00/2.78. Newroad i P8 mają max abs ΔY≈2 w swoich ROI, bez pikseli przyciemnionych o ponad 3. Zgadza się to z brakiem widocznej zmiany kontroli; nie jest testem fizycznej reflektancji ani gwarancją zerowego błędu całej sceny.

## Granica decyzji

Nie ma tu wykazanej wizualnej przeszkody High w ośmiu kontrolach, ale nie należy podpisywać rozwiązania „High niezmieniony bitowo”. Native kompresja G/B/A faktycznie się różni, a ruch/urządzenie nie zostały ocenione. `runtimeTextureMemory=23,812,936B` dotyczy desktopowego obiektu tej próby, **nie A16**; analityczne 1.333 MiB payload ASTC nie zastępuje tego pomiaru ani pamięci telefonu. Równe estymaty counters nie dowodzą braku kosztu.

ROOT ocenia mały zysk Low i wybiera retain/reject tej jednej próby wraz z pamięcią i ryzykiem temporalnym. Ta recenzja nie proponuje nowego pakowania, próbek, amplitud ani kolejnych renderów.
