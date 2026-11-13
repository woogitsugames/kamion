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
