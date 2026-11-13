# ADR 0155 — plamy słońca na wyspie pod wiaduktem Putry

Status: WIP / diagnoza; gałąź gpt-s16-r3. Baza: r2 1f81e87ee, origin/main e638abf31.

ADR 0144 punkt otwarty 7 opisuje jasne plamy na żwirze w clear, w ujęciach 2818555625124739 i 3970163613102941. Zdjęcia repo richlv (2020-08-15, CC BY-SA 4.0) mają przybliżone pozy klasy B; nie są kalibracją fotometryczną ani potwierdzeniem identycznego słońca.

Zakres przestrzenny wynika z konkretnych referencji ADR 0144: wyspa E≈558/N≈−734 i `viaduct_biezenstwa` na Andersa. Zachowujemy tytuł zlecenia „Putry”, ale nie przenosimy cech innego obiektu DK8/Putry na ten wiadukt. Obejrzane 4312632558767412 dotyczy innego obiektu i nie uzasadnia tutaj żadnych paneli.

Najpierw odtwarzamy generator i baseline na scalonej bazie. Porównamy Low i High, clear i overcast; do wszystkich kamer kontrolnych/G3 dodano SBS i dwa zbliżenia wyspy. Geometria dróg, overrides, bariery i pozostałe chronione obszary są poza zakresem edycji.

Inspekcja źródłowa: warstwa bridge już rzuca cień (On), road go nie rzuca. ShadowCaster WorldSurface ma Cull Back; generowane spody mogą mieć normalne w dół. Świat korzysta również z WorldSkyBake/KamionFarShadow poza kaskadami. To hipotezy, nie potwierdzona przyczyna. Wstępne promienie po GLB znajdują powierzchnie skierowane do światła nad większością próbek wyspy, więc sama dwustronność nie gwarantuje naprawy.

Plan: pasujące rendery i ablacje istniejącymi rq_shadowbias/rq_shadownormal/rq_shadow, inspekcja natywnych casterów; potem najmniejsza potwierdzona korekta, bez nowych przebiegów Low, bez udawanej ciemnej farby lub zamykania rzeczywistej szczeliny bez źródła.

## Baseline i granice diagnostyki

Generator baseline 544,6 s, import obu tierów OK; 193 surowe pliki zapisane jako SHA256. Read-only probe potwierdził `bridge` On i hero LOD0/1 On, LOD2 Off. Profile mają Low 35m/1024/1, bias 1/1; High 100m/2048/3, bias 0,4/0,3. Efektywne wartości z VQA są osobno zapisywane jako `pipeline.txt`. Lokalnych bounds prototypu nie przedstawia się jako aktywnego LOD.

Pierwszy ray test obejmował jedynie mały północny nos żwirowy, nie główną wyspę, i pomijał instancje hero. Wystarcza jako ograniczona diagnostyka geometrii tego nosa, nie jako wyjaśnienie docelowych plam. Te ograniczenia i korekta są jawne w `island-rays.json` oraz STATUS.

Baseline obrazy pokazują regularny rząd jasnych prostokątnych plam na żwirze. Próby są rozdzielone: zero bias, wyłącznie wypiek (`rq_shadow=0`), bez wypieku (`rq_worldsun=0`) oraz oba wyłączone. Osobna bliska kamera obejmuje główną wyspę w zasięgu Low. Zdjęcia zawierają zarówno szeroki cień, jak i jasny żwir na pierwszym planie; celem nie jest zaciemnienie całego materiału.

## Ablacje i kandydat korekty

14 warunków diagnostycznych (7 trybów × Low/High), po 5 tych samych kadrów: baseline, oba bias=0, normal=0, depth=0, sam wypiek, bez wypieku, oba rodzaje cienia wyłączone. Efektywny URP zapisano w każdym `pipeline.txt`. Niezależny critic obejrzał wszystkie 10 pełnych arkuszy bazowych ablacji, 6 arkuszy rozdzielonych biasów i 2 natywne pełne kadry normal=0.

Normal=0 usuwa regularny rząd plam w obu profilach; depth=0 i no-baked pozostawiają go. To dowód zależności obrazu od biasu normalnych w realtime, nie od koloru kamienia ani samego wypieku. Nie przyjęto zmiany bake, globalnego QualityProfile, kierunku słońca, geometrii pomostu czy szczeliny. Brak oczywistego nowego acne w ocenionych ablacjach nie zastępuje pełnej oceny docelowego materiału.

Kandydat: tylko istniejące `viaduct_concrete` ma jawne `shadow_normal_bias_scale: 0.0`. `WorldShadowCasterBias.Apply` obsługuje skończoną liczbę 0…1; brak/zła wartość daje 1 i wyłącza keyword, także przy ponownym użyciu materiału. Nie zapisuje domyślnej wartości do niezmienionych cache innych materiałów.

WorldPBR dodaje właściwość domyślnie 1 i lokalny keyword wyłącznie w istniejącym ShadowCaster. Bez opt-in shader kompiluje dawny `ApplyShadowBias` bez dodatkowych operacji. W wariancie opt-in skaluje tylko składnik offsetu normalnego, zachowując dokładnie składnik głębokości `ld * _ShadowBias.x` z zainstalowanego URP (Shadows.hlsl:533–541). ForwardLit i DepthOnly nie mają nowego wariantu ani zmienionej formuły oświetlenia. Nadal 3 przebiegi; nie dodano materiału, renderera ani geometrii. Nie twierdzimy, że zmierzono koszt GPU.

7 nowych testów EditMode sprawdza brak serializacyjnej zmiany legacy, opt-in/usunięcie flagi przy zachowaniu innych pól i liczby passów, odrzucenie NaN/infinity/out-of-range w ponownie używanym materiale oraz docelowy zakres natywny (wyłącznie M_viaduct_concrete). Pełne testy i docelowe after pozostają w toku; kandydat nie ma jeszcze końcowego PASS.
