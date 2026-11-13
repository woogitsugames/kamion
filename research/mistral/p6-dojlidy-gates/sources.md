# sources.md — M49 mistral-p6-dojlidy-gates

Wszystkie źródła dostępne 2026-11-13. Cytaty ≤ 25 słów. Google Maps/Street View/Earth/3D Tiles — nieużyte (zakaz). Mapillary — brak tokenu, nieużyte.

## 1. Ortofotomapa GUGiK (PZGIK) — dane otwarte
- **WCS High Resolution** (pomiary szerokości/promieni, RS16): `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WCS/HighResolution?service=WCS&version=1.0.0&request=GetCoverage&coverage=Orthoimagery_High_Resolution&crs=EPSG%3A2180&bbox=<E,N,E,N>&width=<w>&height=<h>&format=image%2Fjpeg` (bboxy per brama w manifest.csv, kolumna `url_źródła`; okna narożników 40×40 m @0,1 m/px, format PNG). Licencja: dane otwarte GUGiK/PZGIK (geoportal.gov.pl).
- **Skorowidz WFS** (aktualność nalotu): `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze` — dla wszystkich bram `akt_rok=2025`, GSD 0,05 m (G09: 0,10 m); dokładna data zobrazowania niepublikowana (tylko rok).

## 2. OSM — ODbL 1.0, © OpenStreetMap contributors (api.openstreetmap.org, API 0.6, dostęp 2026-11-13)
- Node'y bram: /node/12126375017 (G01, lift_gate), /node/10024132807 (G02, lift_gate), /node/6596800253 (G03, gate), /node/4656499172 (G04, lift_gate), /node/2814000970 (G05, gate), /node/6085185775 (G06, gate), /node/9306871344 (G07, lift_gate), /node/6448194342 (G08, lift_gate), /node/3465808562 (G10, gate — brama kolejowa na way 339393639 railway=disused), /node/5161111758 (wjazd PZZ od Elewatorskiej), /node/2999986083 (G11, lift_gate), /node/3954799626 (brama ciężarowa EC, gate, access=no), /node/10875232003 (G13, gate), /node/6539179208 (G14, gate).
- G07/G08 szerokości (SOURCED): cięciwy końców ways barrier=fence — nodes 9289975821/9289975834 (15,5 m) i 9289965580/9289975827 (12,6 m).
- RS16: trunk way 70546087 („Szosa Zabłudowska"); traffic_signals node 2075991238 (Zabłudowska × Stoczni Gdańskiej); parking way 1504105385; wjazd serwisowy node 14120425290 (way 1552091563); ul. Stoczni Gdańskiej ways 280925985, 347897304.
- Organizacja ruchu (STAN 2026-11-13): `https://api.openstreetmap.org/api/0.6/way/353943959` (Myśliwska, hgv=no maxweight=3.5 — jak 25447110, 221209014, 279872888, 1564083903, 1564083904); Dojlidy Fabryczne ways 173446727/729, 221209008/010/016/017, 229136624, 623410842, 985226457/458 (hgv=no maxweight=3.5); Suchowolca ways 210488455, 221207572/573; Mickiewicza maxweight=8 ways 236884704, 258564444, 258564446, 353943956, 553323253, 553323254, 691820489, 1563021884, 616184917, 616184920, 616184922, 671082727; rondo Meyera ways 552379031, 623410840 (bez tagów hgv/maxweight); Franciszka Karpińskiego way 275237230 (bez ograniczeń); przystanek „Mickiewicza/Ciołkowskiego" node 3682310640.
- G09: service way 550896624, wjazd node 5320426952, granica terminala way 972362712.

## 3. BIP Białystok / ZDM — dokumenty urzędowe (art. 4 pr. aut., materiał niezabezpieczony)
- **PFU 2020, sprawka ZDM-IV.271.16.2020.PR, Załącznik nr 8** (.docx): `https://www.bip.bialystok.pl/resource/70985/77057/Za%C5%82%C4%85cznik%20nr%208_PFU_09.09.2020%20r..docx` — cytat: „DK 19 na wjeździe do miasta od strony Zabłudowa oddalona jest od stałego punktu kontroli w odległości ok. 1295m". Dodatkowo: przekrój 1×3 (pasy 2×3,5 m i 1×3,0 m), strona prawa, kierunek do miasta.
- **PFU 2015, skan** (Załącznik nr 8): `https://www.bip.bialystok.pl/resource/70409/76369/Za%C5%82%C4%85cznik%20nr%208_PFU%20%28skan%29.pdf` — cytat: „Punkt zlokalizowany na parkingu przy DK 19" (tekst wyekstrahowany własnym skryptem PDF z kopii w files/docs/PFU-2015-skan.pdf). UWAGA: binarny PDF nie został wypchnięty do gita (transport tekstowy przez API skaziłby plik) — kopia w archiwum ZIP artefaktu.
- **Komunikat ZDM/miasta 19.11.2025** „Zmiany w ruchu wokół ulicy Suchowolca": `https://www.bialystok.pl/pl/wiadomosci/aktualnosci/zmiany-w-ruchu-wokol-ulicy-suchowolca.html` — cytaty: „ciężarówki powyżej 3,5 t przestaną korzystać z części ul. Suchowolca oraz ul. Dojlidy Fabryczne"; „na fragmencie ul. Mickiewicza – pomiędzy Kuronia a Ciołkowskiego – wprowadzony zostanie zakaz wjazdu dla pojazdów ciężarowych powyżej 8 ton"; „z wlotu od Dojlidy Fabryczne można jechać prosto z dawnego pasa do skrętu w lewo". Numer zarządzenia: niepublikowany online (rejestr ZDM, ul. Składowa 11 — ustalenie P8).

## 4. Publicystyka (fakty, nie kopiowanie treści)
- **TVP3 Białystok 10.12.2025** „Dojlidy bez tranzytu ciężarówek od stycznia": `https://bialystok.tvp.pl/90478426/dojlidy-bez-tranzytu-ciezarowek-od-stycznia-wideo` — cytat: „Ulice Dojlidy Fabryczne i księdza Stanisława Suchowolca będą zamknięte dla ciężarówek o masie powyżej 3,5 tony"; wejście w życie: styczeń 2026.
- Kopie komunikatu ZDM: bialystokonline.pl (20.11.2025), akadera.bialystok.pl (20.11.2025), radio.jard.pl — spójne z oryginałem na bialystok.pl.

## 5. Strona firmowa PZZ S.A. (fakt rejestrowy)
- `https://pzz.bialystok.pl/kontakt` (dostęp 2026-11-13, ponowna weryfikacja w audycie) — cytat: „ul. Elewatorska 14, 15-959 Białystok"; pełna nazwa: „Podlaskie Zakłady Zbożowe S.A. w Białymstoku / Elewatorska 14, 15-959 Białystok". KRS 0000038920. Fraza „Zbożowa" na stronie nie występuje.

## 6. Materiały własne (reprodukowalne)
- Skrypty pomiarowe sesji (profile asfaltu, RANSAC okręgów, transformacja EPSG:2180) — metody opisane w README sekcja 2; wyniki pośrednie w work/ (poza repo): radius-final.json, fitcorners2.json, fence-openings.json, widths-driveway.json, skorowidz.json.
- Wycinki ortofoto JPG (≤1600 px): files/M49-G01…G14(+context), M49-RS16-detail/context/pad — w archiwum ZIP `mistral-p6-dojlidy-gates-files.zip` (artefakt poza repo), zgodnie z zasadą „JPG nie do gita".
