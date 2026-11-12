# Podświetlenie legend kabiny — ADR 0112 r3

Źródło ustawień: cab_backlight.json. enabled jest flagą wypieku materiałów: po zmianie uruchomić TruckAssetBuilder.BuildBatch, a następnie WorldTruckInstaller.InstallBatch, każde Unity we własnym slocie. Wyłączenie usuwa keyword i zeruje luminancję istniejącego materiału MI_Cab_Decal. Shadery szyb, zewnętrza i QualityProfile są poza tą zmianą.

_KAMION_CAB_BACKLIGHT dotyczy wyłącznie istniejących ikon w paśmie UV v < 0,5 atlasu Decal. Kratki 0,505–0,87 i szwy 0,88–0,995 nie emitują światła. Kolor atlasu i tint wierzchołków zachowują barwy oznaczeń. Bez nowych tekstur, próbek, materiałów, geometrii i przebiegów. Jest to emisja powierzchni legend, bez dodatkowych świateł oświetlających kabinę.

CabInteriorLighting przekazuje prawdziwą wysokość słońca, ekspozycję i ważność modelu. Brak środowiska i OnDisable zerują ważność. Jasność to min(luminancja * ekspozycja, cap), z łagodnym przejściem 6→0 stopni. Emisja jest dodana po lokalnym rozjaśnieniu ambient, więc nie mnoży jej cabViewEv ani shadow lift. Następnie przechodzi przez istniejący kontrakt toe/fog. Parametry luminancji, barwy, cap i przejścia są WORKING_VALUE, nie pomiarem fizycznego panelu.

Nocne palety ekranów i ich shader pozostają niezmienione. Zdjęcie Volvo Trucks / Jonatan Fernström jest odniesieniem jakościowym, nie skanem ani CC0: artifacts/cab-r2/NIGHT-REFERENCE.md. Nie kopiujemy układu i brandingu.

Test CabBacklightTests renderuje oddzielnie ikonę i pas szwów w kontrolowanej scenie oraz sprawdza wyłączenie, dzień i limit ekspozycji. Fixture musi zachować dodatnie knee 0,004 istniejącego shadow-lift nawet przy zerowej sile, jak w rzeczywistej kabinie. Test nie zastępuje obrazów Low/High, budżetów całej trasy ani pomiaru GPU A16.
