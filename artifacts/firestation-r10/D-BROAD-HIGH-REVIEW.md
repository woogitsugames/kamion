# D BROAD — niezależny review High 28 par, 2026-11-11

**Werdykt: PASS braku widocznej nowej regresji w tym zestawie High; FAIL wykazania odczuwalnej poprawy szerokiego zużycia asfaltu. Efekt trzech zmian jest prawie niewidoczny.** To nie zamyka 21 zgłoszonych przypadków sterylnego asfaltu i nie jest oceną całego D ani Low. O przyjęciu ograniczonej korekty bez istotnego zysku wyglądu decyduje ROOT.

## Materiał i zakres przyczynowy

Oglądnięto **wszystkie 28 par** before/after: 14 dokładnych ID z `wear-probe-camera-ids.txt`, High-clear i High-overcast. Każdy pełny kadr obu faz obejrzano w 960px, bez korekty ekspozycji/kontrastu i bez alignowania. Ze względu na chwilowy brak gotowych przeglądów AFTER utworzono wyłącznie rozmiarowe podglądy we własnym `D-broad-high-pairs-960/`. Ich `view-inputs.json` zawiera SHA wszystkich 56 źródłowych PNG; porównano je z odpowiednimi capture proof. Źródła obrazów: D worktree `gpt-surface-wear/artifacts/surface-wear-r1/wear-probe-{before,after}`.

Odczytano aktualny `broadwear-plan-proof-current-r2.json` i patch, następnie świeże `wear-probe-before-proof.json`, `wear-probe-after-start-proof.json`, `wear-probe-after-proof.json`, `wear-probe-metrics.json` i dwa jawne signal-delta JSON. Stary plan INACTIVE odnosił się do etapu przed aktywacją; aktualne AFTER ma source **619a32e0**. Zakres to wyłącznie trzy bloki: polish .12→.18×istniejące macro, gutter×macro oraz 12% kontaktu kół dla longitudinal paint z realnymi danymi pasa. Gate signed branch i dotychczasowa kalibracja transverse nie są nową poprawką BROAD.

### Dwa materiały signal — kontrolowany stan, nie regresja wear

BEFORE przy pierwszej serializacji straciło tylko `_EMISSION` w `M_signal_green_on.mat` i `M_signal_red_on.mat`; pozostałe2439 cached i 192 raw pozostały zgodne. START AFTER przywrócił dokładnie te dwa pliki do START BEFORE. AFTER proof podaje 56 klatek, 2441 cached i 192 raw zgodne oraz dokładne runtime camera/vehicle i zaokrąglone counters. Odczyt `wear_probe_proof.py:9,17–23` potwierdza, że kontrola AFTER używa **`wear-probe-before-final-fixture.json`**, czyli END AFTER porównuje się do END BEFORE, a nie do wcześniejszego stanu początkowego. To kontrolowane powtórzenie serializacji, nie podstawa do odrzucania dowodu jako „brudnego Unity”. Nie wykonałem ponownie tego helpera/testów. Główki sygnalizatorów są poza `d_field_signal_oil`; nie wyciągam wniosków o emisji lamp z nieistniejącego ROI.

## Wynik oglądania

| Grupa kamer, oba światła | Co widać przed/po i werdykt zakresowy |
|---|---|
| `d_wear_lane_old` | Asfalt pozostaje podobnie równy i ziarnisty. Nie potrafię wskazać w AFTER wyraźnie lepszej czytelności pasów hamowania/polerowania w widoku drogi. W overcast zmiana jest równie słaba jak w clear. Brak nowej mokrej wstęgi; brak mocnego dowodu poprawy sterylności. |
| `d_field_bus464_close`, `d_field_signal_oil` | Z bliska nadal widać te same plamy, kruszywo i drobne nierówności. Nie pojawia się przekonująco nowy pas polish; stare plamy nie są sukcesem tej zmiany. Bez widocznego rozlania brudu lub zmiany całej ekspozycji. |
| `d_field_patch_large`, `d_field_patch_putry` | Istniejące łaty i pęknięcia są czytelne, lecz pełne kadry przed/po wyglądają praktycznie tak samo. Nie zaliczam ich obecności jako nowego rozwiązania zużycia. |
| Krawędzie i gutter w powyższych oraz `d_wear_missing_uv_1/2` | Nie widzę nowej jednolitej obwódki brudu ani zabrudzenia środka jezdni. Jednocześnie przerwanie/osad przy gutter nie staje się od razu zauważalnie bardziej naturalny. Sama modulacja w kodzie nie jest wizualnym zamknięciem celu. |
| `d_wear_newroad_negative` | Nie widać nowej mokrej koleiny ani przybrudzenia świeżej powierzchni. Istniejące czarne ślady na zebrze były już BEFORE; nie przypisuję ich temu patchowi. PASS ograniczonej kontroli ubocznej zmiany, nie twierdzenie, że cała scena przedstawia idealnie nową drogę. |
| `d_field_glyph_unknown`, `d_wear_missing_uv_1/2` | Bez zauważalnego nowego zużycia na unknown hatch lub artefaktu wynikającego z domyślnego/nieznanego UV. Nie jest to dowód pokrycia wszystkich możliwych unknown geometrii świata. |
| `d_field_glyph_supported`, `d_field_p8_turn`, `d_wear_crossing` | Diagonalne hatch, kierunek P8 i zebra pozostają czytelne. Nie widzę wymazania konturu, nowych prześwitów psujących znak ani mokrego połysku na bieli. Ciemniejszy fragment grotu P8 był już BEFORE. Longitudinal kontakt 12% nie daje tu widocznego skoku realizmu. |
| `d_gate_pair_entry/exit` | Zachowują wygląd wcześniejszego gate R2; nie widać nowej mokrej wstęgi lub utraty czytelności. Ich uprzednia poprawa fade i wcześniejsze ograniczenie słabego drugiego exit-clear nadal obowiązują — nie liczyć ich drugi raz jako zasługi BROAD. |

## Metryki wspierające, bez sztucznego PASS

W odczytanym komplecie High whole-frame mean-absolute RGB wynosi około **0.015–0.324LSB**. To jest zgodne z bardzo małym efektem oglądanym w 960; dodatnia różnica nie dowodzi lepszej jakości. W ROI old asphalt mean ΔY wynosi +0.041 clear / +0.188 overcast, MAE około.138/.343LSB. Nie wskazuje to na globalne ciemnienie asfaltu, ale ten jeden ROI nie zastępuje segmentacji całej drogi.

Kontrole autora: new asphalt mean ΔY +.050/+.161LSB; unknown hatch mean i mean-absolute ΔY=0 w obu High; supported hatch mean ΔY około+.004/+.036; P8 około+.002/+.030; crossing około+.303/+.274. To maski kontekstu i display luma, nie fizyczne albedo, powierzchnia farby lub automatyczny wynik czytelności. Patrzenie na pełne kadry jest podstawą powyższego werdyktu.

Równe liczniki i brak nowych texture sample tokens nie stanowią dowodu darmowej pracy GPU. Nie oceniano ruchu, zmian kąta połysku, telefonu ani nowych shaderów na urządzeniu. Statyczny clear/overcast nie może mocno potwierdzić realistycznego brake polish, jeśli efekt jest ledwie widoczny nawet w tych kontrolach.

## Wniosek dla ROOT

Nie znalazłem powodu do odrzucenia trzech bloków jako widocznej regresji High 28. Nie ma jednak przekonującego skoku jakości: główne wrażenie asfaltu i oznakowania pozostaje niemal takie samo. Jeżeli patch zostanie zatrzymany, raport powinien nazywać go **subtelną korektą bez wykazanej istotnej poprawy szerokiego zużycia**, a nie zakończeniem całej listy asphalt critic. Dalszego tuningu, nowych renderów ani zmian hero nie zlecono tą recenzją. ROOT łączy wynik z własnym Low 28 i decyduje o dalszej walidacji/retencji.
