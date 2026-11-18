# Podświetlenie legend kabiny — ADR 0112 r3

Źródło ustawień: cab_backlight.json. enabled jest flagą wypieku materiałów: po zmianie uruchomić TruckAssetBuilder.BuildBatch, a następnie WorldTruckInstaller.InstallBatch, każde Unity we własnym slocie. Wyłączenie usuwa keyword i zeruje luminancję istniejącego materiału MI_Cab_Decal. Shadery szyb, zewnętrza i QualityProfile są poza tą zmianą.

_KAMION_CAB_BACKLIGHT dotyczy wyłącznie istniejących ikon w paśmie UV v < 0,5 atlasu Decal. Kratki 0,505–0,87 i szwy 0,88–0,995 nie emitują światła. Kolor atlasu i tint wierzchołków zachowują barwy oznaczeń. Bez nowych tekstur, próbek, materiałów, geometrii i przebiegów. Jest to emisja powierzchni legend, bez dodatkowych świateł oświetlających kabinę.

CabInteriorLighting przekazuje prawdziwą wysokość słońca, ekspozycję i ważność modelu. Brak środowiska i OnDisable zerują ważność. Jasność to min(luminancja * ekspozycja, cap), z łagodnym przejściem 6→0 stopni. Emisja jest dodana po lokalnym rozjaśnieniu ambient, więc nie mnoży jej cabViewEv ani shadow lift. Następnie przechodzi przez istniejący kontrakt toe/fog. Parametry luminancji, barwy, cap i przejścia są WORKING_VALUE, nie pomiarem fizycznego panelu.

Nocne palety ekranów i ich shader pozostają niezmienione. Zdjęcie Volvo Trucks / Jonatan Fernström jest odniesieniem jakościowym, nie skanem ani CC0: artifacts/cab-r2/NIGHT-REFERENCE.md. Nie kopiujemy układu i brandingu.

Test CabBacklightTests renderuje oddzielnie ikonę i pas szwów w kontrolowanej scenie oraz sprawdza wyłączenie, dzień i limit ekspozycji. Fixture musi zachować dodatnie knee 0,004 istniejącego shadow-lift nawet przy zerowej sile, jak w rzeczywistej kabinie. Test nie zastępuje obrazów Low/High, budżetów całej trasy ani pomiaru GPU A16.

## ADR 0296 (D84) — cap 0,45

Pomiar A/B w `cab-switches` (DrivingLab, High -Pc, 1920×1080, wartości sRGB szczytu legend; `artifacts/cabin-d84-s24/ab-legend.ps1`): noc bez podświetlenia 78, cap 0,09 → 106, cap 0,30 → 146 (12 i 60 cd/m² dają ten sam wynik), cap 0,45 → 158–172, cap 0,60 → 201; zmierzch tak samo ±6. Nocą i o zmierzchu `luminancja × ekspozycja` zawsze przekracza cap, więc jasnością legend steruje wyłącznie `max_exposed_linear`; zmiana `legend_luminance_cd_m2` 8 → 12 (D84 s23) nie mogła dać efektu. Przy 0,09 legenda była ciemniejsza niż w dzień (209) i czytała się jak szary nadruk. 0,45 jest `WORKING_VALUE` (bez fotometrii panelu): legendy wyraźnie świecą, 0 % pikseli powyżej 250. Test `CabD84Polish0296Tests` pilnuje pasma 0,30–0,60.
