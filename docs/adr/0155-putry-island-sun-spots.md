# ADR 0155 — plamy słońca na wyspie pod wiaduktem Putry

Status: WIP / diagnoza; gałąź gpt-s16-r3. Baza: r2 1f81e87ee, origin/main e638abf31.

ADR 0144 punkt otwarty 7 opisuje jasne plamy na żwirze w clear, w ujęciach 2818555625124739 i 3970163613102941. Zdjęcia repo richlv (2020-08-15, CC BY-SA 4.0) mają przybliżone pozy klasy B; nie są kalibracją fotometryczną ani potwierdzeniem identycznego słońca.

Najpierw odtwarzamy generator i baseline na scalonej bazie. Porównamy Low i High, clear i overcast; do wszystkich kamer kontrolnych/G3 dodano SBS i dwa zbliżenia wyspy. Geometria dróg, overrides, bariery i pozostałe chronione obszary są poza zakresem edycji.

Inspekcja źródłowa: warstwa bridge już rzuca cień (On), road go nie rzuca. ShadowCaster WorldSurface ma Cull Back; generowane spody mogą mieć normalne w dół. Świat korzysta również z WorldSkyBake/KamionFarShadow poza kaskadami. To hipotezy, nie potwierdzona przyczyna. Wstępne promienie po GLB znajdują powierzchnie skierowane do światła nad większością próbek wyspy, więc sama dwustronność nie gwarantuje naprawy.

Plan: pasujące rendery i ablacje istniejącymi rq_shadowbias/rq_shadownormal/rq_shadow, inspekcja natywnych casterów; potem najmniejsza potwierdzona korekta, bez nowych przebiegów Low, bez udawanej ciemnej farby lub zamykania rzeczywistej szczeliny bez źródła.
