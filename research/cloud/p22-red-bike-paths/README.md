# M65 — drogi dla rowerów z czerwonego asfaltu: trasa C i Dojlidy (cloud p22-red-bike-paths)

Gałąź `research/cloud-p22-red-bike-paths`. Blok: `docs/owner/MISTRAL-TASKS-10.md` § M65 (z różnicami z briefu zespołu cloud: id `C65-NNN`, bez ZIP — `fetch.py` + sha256). Plik generowany: `python3 -I tools/build_readme.py` (tekst: `data/readme_text.md`).

## 0. Najważniejsze ustalenia (dla generatora nawierzchni)

1. **W Dojlidach DDR NIE są z czerwonego asfaltu.** Wszystkie obejrzane odcinki przy ul. Dywizjonu 303, Kuronia, Mickiewicza, Hake, Ciołkowskiego, Karpińskiego to **szary asfalt** z białą linią osiową przerywaną i symbolami P-23, obok chodnika z jasnej kostki. Czerwone są tam wyłącznie **pola przejazdów przez wloty** (9 z 21 przecięć z jezdniami), m.in. przejazd z kadru P11-056 (wlot ul. Spadochroniarzy, C65-144). **Weryfikacja na kadrach (dopisane po odblokowaniu Commons, miniatury 1600 px): wniosek POTWIERDZONY z jednym doprecyzowaniem.** P11-001 (C65-240): DDR przy ul. Kuronia nie jest jaskrawoczerwona — to ciemny asfalt o lekko brunatnofioletowym odcieniu (cieplejszy niż jezdnia), z białą linią osiową i krawędziową; obok chodnik z szarej kostki, zjazd do bramy przerywa DDR. Dla tekstury: „ciemny asfalt z ciepłym, brunatnym odcieniem”, nie „szary neutralny” i nie „czerwony”; czy to spłowiała masa barwiona — nierozstrzygnięte. P11-056 (C65-241): przejazd przez wlot ma czerwone pole z białymi kwadratami i zebrę — zgodnie z orto; DDR zasłonięta trawą.
2. **W regionie C czerwonobrązowy (bordowy, spłowiały) asfalt DDR występuje** — w rejonie ronda pod estakadą (Al. Tysiąclecia/Maczka/łącznice), przy ul. Bitwy Białostockiej koło ronda Pamięci Bieżeństwa i na ciągach wzdłuż estakady Andersa: 9 odcinków, ok. 1,71 km w kaflu (+ 1 spłowiały różowoszary, 270 m). Wzdłuż Al. Tysiąclecia na południe od ronda DDR są szare; ciągi pieszo-rowerowe przy ul. Andersa to jasna kostka (10 odcinków) albo wąskie pasy z czerwonej kostki (4 odcinki).
3. **Czerwone pole przejazdu ≠ kolor DDR.** Tam, gdzie DDR jest czerwonobrązowa (rondo pod estakadą), przejazdy przez jezdnie są tylko białe (P-11); tam, gdzie DDR jest szara (Sokólska, Wileńska, Hake, wloty w Dojlidach), przejazdy mają jaskrawoczerwone pole. Standard miasta: **RAL 3020, masa chemoutwardzalna uszorstniona** (wytyczne ZDM, str. 16) — to powłoka na asfalcie jezdni.
4. **Przez wjazdy do posesji** w Dojlidach DDR się urywa (zjazd z kostki/betonu przecina ją, P-23 po obu stronach, bez czerwieni); w C spotyka się czerwone prostokąty bez białych kwadratów na wyjazdach z parkingu/posesji (C65-153, C65-157).
5. **OSM nie ma tagów `colour`/`width` na żadnym z 93 odcinków** — kolor i szerokość trzeba brać z tej paczki (ESTIMATED z orto), nie z OSM.

## 1. Zapytanie Overpass i metoda

- Endpoint `https://maps.mail.ru/osm/tools/overpass/api/interpreter`, 2026-11-14T16:49:07Z, `timestamp_osm_base` 2026-11-14T16:48:34Z; treść: `overpass-query.ql`; surowy wynik: `overpass-result.json` (1,41 MB).
- Definicja odcinka DDR/CPR (`tools/inventory.py`): `highway=cycleway` **albo** `highway=path|footway|pedestrian` z `bicycle=designated`; way musi mieć ≥ 5 cm długości w kaflu regionu (kafle z `Data/Regions/*/region.yaml`, przeliczenie `tools/geo.py`). Długość: haversine po węzłach (całe way) + długość części w kaflu (przycięcie w EPSG:2180, skala lokalna).
- Jezdnia równoległa: próbki co 5 m wzdłuż DDR; kandydaci = odcinki `highway` klasy motorway…service w promieniu 40 m o kierunku ±30°; wygrywa way z największą liczbą próbek (drogi `service` tylko gdy nie ma innej), wymagany udział ≥ 30 %; odległość = mediana odległości punkt DDR → oś najbliższej jezdni (przy drogach dwujezdniowych jest to oś BLIŻSZEJ jezdni).
- Przecięcia (`tools/crossings.py`): wspólne węzły OSM odcinka DDR i jezdni (`kind=jezdnia`) lub drogi `service` (`kind=wjazd`).
- Kolor, szerokości, rozdzielenie: **ortofotomapa GUGiK 5 cm** (WMS HighResolution; nalot 2025-04-18 albo 2024-03-30 — patrz `sources.md` §2): przekroje `tools/transect.py` (obrót do osi DDR, linijka co 1 m, odczyt ±0,3 m), wycinki przejazdów `tools/crossing_crop.py` + profil jasności `tools/crossing_profile.py` (±0,15 m; przejazdy ukośne ±0,5 m). Kolor wyłącznie opisem słownym.
- Brakujące tagi wpisane jako „brak tagu”. Typ rozdzielenia od jezdni — z przekroju orto (kolumna „układ od jezdni”); wysokości krawężników z orto nie da się odczytać.

## 2. Inwentarz odcinków (kontrola sum)

- **C**: 71 odcinków, suma długości wg OSM **9888,1 m** (całe way) / **7734,2 m** w granicach kafla.
- **Dojlidy**: 22 odcinków, suma długości wg OSM **13252,8 m** (całe way) / **8120,4 m** w granicach kafla.

Tagi kontrolne w OSM (93 odcinki): `colour` 0, `surface:colour` 0, `width` 0, `oneway` 0, `lit` 3, `smoothness` 2, `segregated` 63, `surface` 86. Dwa odcinki regionu C (1562298579, 1562298580) to `highway=cycleway` + `surface=dirt` + `access=forestry` — leśne drogi gruntowe, nie DDR miejskie (zostawione w inwentarzu, bo spełniają definicję).

| id | region | way_id | highway | surface | segregated | długość [m] | w kaflu [m] | jezdnia równoległa (way) | oś–oś [m] | nawierzchnia wg orto | szer. [m] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C65-001 | C | 173956082 | cycleway | asphalt | brak tagu | 406,5 | 270 | trunk_link (606396470) | 4,8 | wyblakły, różowoszary asfalt | 2,35 |
| C65-002 | C | 173985179 | cycleway | asphalt | brak tagu | 47,3 | 47,3 | Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP (257367428) | 11,5 | czerwonobrązowy asfalt | 2,6 |
| C65-003 | C | 173985180 | cycleway | asphalt | brak tagu | 35,8 | 35,8 | Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP (257367428) | 16,1 | nieczytelne | — |
| C65-004 | C | 174538881 | cycleway | asphalt | brak tagu | 12,8 | 12,8 | trunk_link (173956081) | 11,2 | — | — |
| C65-005 | C | 174538884 | path | paving_stones | no | 345,3 | 345,3 | Generała Władysława Andersa (249640399) | 14,3 | jasna kostka | 3,7 |
| C65-006 | C | 177876101 | path | paving_stones | no | 188 | 188 | Generała Władysława Andersa (552161976) | 14,5 | jasna kostka | 3,7 |
| C65-007 | C | 177895162 | path | paving_stones | no | 22 | 22 | Rondo Pamięci Bieżeństwa 1915 roku (553285004) | 13,4 | — | — |
| C65-008 | C | 177895175 | cycleway | brak tagu | brak tagu | 66,9 | 66,9 | trunk_link (177895172) | 8,1 | czerwona (kostka?) | 2,2 |
| C65-009 | C | 177903955 | cycleway | asphalt | brak tagu | 164,8 | 164,8 | trunk_link (182399965) | 10,8 | czerwonobrązowy asfalt | 2,35 |
| C65-010 | C | 177946177 | path | brak tagu | no | 7,4 | 7,4 | — | — | — | — |
| C65-011 | C | 177946178 | path | paving_stones | no | 70,9 | 70,9 | trunk_link (177895172) | 8,1 | jasna kostka | 3,5 |
| C65-012 | C | 177948304 | path | paving_stones | no | 156,7 | 42 | Generała Władysława Andersa (278213211) | 9 | jasna kostka | 3,5 |
| C65-013 | C | 177948306 | cycleway | paving_stones | brak tagu | 67,9 | 67,9 | Generała Władysława Andersa (266084685) | 11,7 | czerwona (kostka?) | 2,1 |
| C65-014 | C | 236107486 | path | paved | yes | 101,6 | 101,6 | — | — | przejazd przez jezdnię z czerwoną powierzchnią między liniami P-11 | — |
| C65-015 | C | 236107938 | path | paved | yes | 575,4 | 140,6 | Aleja Tysiąclecia Państwa Polskiego (913217370) | 23,1 | szary asfalt | 3,2 |
| C65-016 | C | 236110049 | path | paved | yes | 44,5 | 44,5 | Sokólska (999223598) | 7,3 | nieczytelne | — |
| C65-017 | C | 238234011 | cycleway | asphalt | brak tagu | 680,4 | 332,7 | — | — | czerwonobrązowy asfalt | 3,2 |
| C65-018 | C | 257367430 | cycleway | asphalt | brak tagu | 12,1 | 12,1 | trunk_link (257367449) | 5,9 | — | — |
| C65-019 | C | 257367436 | path | paved | yes | 535,1 | 535,1 | Aleja Tysiąclecia Państwa Polskiego (238861874) | 9,2 | ciemna nawierzchnia z brunatnym odcieniem, w cieniu drzew | 3,3 |
| C65-020 | C | 257367441 | cycleway | asphalt | brak tagu | 179 | 179 | trunk_link (249431348) | 7,8 | czerwonobrązowy asfalt | 2,2 |
| C65-021 | C | 268470360 | path | asphalt | yes | 39,1 | 39,1 | Aleja Tysiąclecia Państwa Polskiego (197904074) | 7,6 | jasnoszara nawierzchnia na wiadukcie | — |
| C65-022 | C | 268470393 | path | paved | yes | 1008,8 | 388 | Aleja Tysiąclecia Państwa Polskiego (771649419) | 11,2 | ciemna nawierzchnia z brunatnym odcieniem, w cieniu drzew | 3,1 |
| C65-023 | C | 282244166 | cycleway | asphalt | brak tagu | 255 | 255 | trunk_link (606396459) | 11,3 | czerwonobrązowy asfalt | 3,3 |
| C65-024 | C | 284396205 | cycleway | asphalt | brak tagu | 63,5 | 63,5 | Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP (180144451) | 9,9 | — | — |
| C65-025 | C | 284396207 | path | paved | yes | 287,2 | 287,2 | Generała Władysława Andersa (266084694) | 18,9 | czerwonobrązowy asfalt | 3,2 |
| C65-026 | C | 284396209 | cycleway | asphalt | brak tagu | 279,9 | 279,9 | trunk_link (268473388) | 6,9 | czerwonobrązowy asfalt | 2,8 |
| C65-027 | C | 308399785 | path | brak tagu | no | 25,9 | 25,9 | Generała Władysława Andersa (560802657) | 33,1 | — | — |
| C65-028 | C | 344253261 | path | paved | yes | 358,4 | 358,4 | Aleja Tysiąclecia Państwa Polskiego (946729183) | 6,5 | szary asfalt | 2,8 |
| C65-029 | C | 350559280 | cycleway | brak tagu | brak tagu | 51,8 | 51,8 | Generała Władysława Andersa (552161976) | 14,1 | czerwona (kostka?) | 2,2 |
| C65-030 | C | 435369083 | cycleway | paved | brak tagu | 6,4 | 6,4 | — | — | — | — |
| C65-031 | C | 435369088 | cycleway | paved | brak tagu | 17,4 | 17,4 | Generała Władysława Andersa (560802656) | 11,7 | — | — |
| C65-032 | C | 435369090 | cycleway | paved | brak tagu | 17 | 17 | Generała Władysława Andersa (560802656) | 15,7 | — | — |
| C65-033 | C | 435369091 | path | paved | no | 108,5 | 108,5 | Generała Władysława Andersa (560802655) | 13 | czerwona (kostka?) | 3,65 |
| C65-034 | C | 549997876 | path | paving_stones | no | 36,2 | 36,2 | Generała Władysława Andersa (560802658) | 9,5 | jasna kostka | 3,5 |
| C65-035 | C | 549997879 | path | paving_stones | no | 199,7 | 199,7 | tertiary_link (177861600) | 9,4 | jasna kostka | 3,5 |
| C65-036 | C | 549997880 | path | paving_stones | no | 15,3 | 15,3 | trunk_link (177895172) | 7,5 | — | — |
| C65-037 | C | 549997881 | path | paving_stones | no | 86,3 | 86,3 | trunk_link (606396457) | 8,1 | jasna kostka | 3,4 |
| C65-038 | C | 549997883 | path | paving_stones | no | 88,9 | 88,9 | Generała Władysława Andersa (266084685) | 13,4 | jasna kostka | 3,6 |
| C65-039 | C | 552614904 | path | paving_stones | no | 21,8 | 21,8 | tertiary_link (177861600) | 12,4 | — | — |
| C65-040 | C | 591358181 | path | paved | yes | 154,5 | 154,5 | Bitwy Białostockiej (178208423) | 10,9 | szary asfalt | 2,65 |
| C65-041 | C | 591358203 | cycleway | asphalt | brak tagu | 7,9 | 7,9 | Bitwy Białostockiej (177903961) | 10,3 | — | — |
| C65-042 | C | 591365139 | path | paved | yes | 87,4 | 87,4 | trunk_link (182399965) | 9,5 | czerwonobrązowy asfalt | 3,25 |
| C65-043 | C | 613145836 | cycleway | asphalt | brak tagu | 77,7 | 77,7 | Generała Władysława Andersa (552161980) | 29,9 | czerwonobrązowy asfalt | 3,2 |
| C65-044 | C | 613145837 | path | paved | yes | 26,6 | 26,6 | Generała Władysława Andersa (560802656) | 19,9 | — | — |
| C65-045 | C | 676746632 | path | paved | yes | 125,3 | 125,3 | — | — | szary asfalt | 2,8 |
| C65-046 | C | 741639498 | path | paved | yes | 23 | 23 | living_street (741639500) | 15,4 | — | — |
| C65-047 | C | 741639504 | path | paved | yes | 407,1 | 407,1 | Aleja Tysiąclecia Państwa Polskiego (676746630) | 5,9 | jasnoszara, jednolita | — |
| C65-048 | C | 879051665 | path | paved | yes | 198,4 | 132,9 | Bitwy Białostockiej (178208423) | 9,9 | szary asfalt | 2,65 |
| C65-049 | C | 879051666 | cycleway | asphalt | brak tagu | 20,6 | 20,6 | Bitwy Białostockiej (178208423) | 9 | — | — |
| C65-050 | C | 923506577 | path | asphalt | no | 38,7 | 38,7 | Racławicka (210367044) | 20 | szary asfalt | 3,8 |
| C65-051 | C | 923506578 | path | asphalt | no | 21,9 | 21,9 | — | — | — | — |
| C65-052 | C | 923506579 | path | asphalt | no | 56,4 | 56,4 | residential (100927647) | 22,8 | szary asfalt | 4 |
| C65-053 | C | 946729181 | path | paved | yes | 24,9 | 24,9 | Aleja Tysiąclecia Państwa Polskiego (999223605) | 13,8 | przejazd przez jezdnię z czerwoną powierzchnią między liniami P-11 | — |
| C65-054 | C | 946729182 | path | paved | yes | 564,3 | 130,4 | Aleja Tysiąclecia Państwa Polskiego (913217370) | 9,7 | szary asfalt | 3,1 |
| C65-055 | C | 946729187 | path | asphalt | no | 346,6 | 346,6 | Aleja Tysiąclecia Państwa Polskiego (913217371) | 6,5 | jasnoszara, bez linii | 4,2 |
| C65-056 | C | 999223585 | cycleway | asphalt | brak tagu | 94,6 | 94,6 | living_street (236107492) | 10,3 | szary asfalt | 2,7 |
| C65-057 | C | 1015230186 | path | asphalt | yes | 10,4 | 10,4 | Aleja Tysiąclecia Państwa Polskiego (946729184) | 9,4 | — | — |
| C65-058 | C | 1015230197 | path | paved | yes | 11,1 | 11,1 | Aleja Tysiąclecia Państwa Polskiego (946729184) | 13,6 | — | — |
| C65-059 | C | 1033469394 | cycleway | asphalt | brak tagu | 5,7 | 5,7 | — | — | — | — |
| C65-060 | C | 1093579595 | path | brak tagu | no | 26,2 | 26,2 | service (177719992) | 27,2 | — | — |
| C65-061 | C | 1093579597 | path | brak tagu | no | 17,9 | 17,9 | service (177946995) | 19,2 | — | — |
| C65-062 | C | 1093579599 | path | paving_stones | no | 41,8 | 41,8 | Generała Władysława Andersa (266084685) | 12,1 | jasna kostka | 3,7 |
| C65-063 | C | 1388558721 | path | paving_stones | no | 17,3 | 17,3 | Generała Władysława Andersa (560802657) | 11,8 | — | — |
| C65-064 | C | 1388558723 | path | paving_stones | no | 14 | 14 | tertiary_link (177861600) | 10,9 | — | — |
| C65-065 | C | 1388558724 | path | paving_stones | no | 2,7 | 2,7 | trunk_link (606396458) | 10,7 | — | — |
| C65-066 | C | 1388558725 | path | paving_stones | no | 10,6 | 10,6 | trunk_link (606396458) | 10,8 | — | — |
| C65-067 | C | 1388558726 | path | paving_stones | no | 9,7 | 9,7 | trunk_link (606396458) | 10,8 | — | — |
| C65-068 | C | 1448274978 | path | paving_stones | no | 16,3 | 16,3 | Generała Władysława Andersa (1093579589) | 13,1 | — | — |
| C65-069 | C | 1448274979 | path | paving_stones | no | 134,2 | 134,2 | Generała Władysława Andersa (266084693) | 13 | jasna kostka | 2,75 |
| C65-070 | C | 1562298579 | cycleway | dirt | brak tagu | 459,9 | 459,9 | — | — | niewidoczne | — |
| C65-071 | C | 1562298580 | cycleway | dirt | brak tagu | 146,9 | 146,9 | — | — | niewidoczne | — |
| C65-072 | Dojlidy | 180233649 | path | paved | yes | 1220 | 241 | Jacka Kuronia (275244659) | 9,3 | szary asfalt | 2,8 |
| C65-073 | Dojlidy | 198376011 | path | asphalt | no | 688 | 71,2 | Konstantego Ciołkowskiego (529725120) | 7,3 | jasnoszara nawierzchnia bez linii | 3 |
| C65-074 | Dojlidy | 203348234 | path | paved | yes | 223,7 | 223,7 | Wiewiórcza (1552386427) | 9,5 | nieczytelne | — |
| C65-075 | Dojlidy | 212811558 | path | asphalt | no | 1362,5 | 921,7 | Franciszka Karpińskiego (275237230) | 8,9 | szary asfalt | 3,1 |
| C65-076 | Dojlidy | 212811563 | path | paved | yes | 848,5 | 848,5 | Jacka Kuronia (236885859) | 9,3 | szary asfalt | 2,7 |
| C65-077 | Dojlidy | 237088754 | path | paved | yes | 1443,3 | 1443,3 | Adama Mickiewicza (977514047) | 8,5 | szary asfalt | 2,65 |
| C65-079 | Dojlidy | 285876996 | cycleway | asphalt | brak tagu | 684,8 | 684,8 | Adama Mickiewicza (1563021884) | 10,3 | szary asfalt | 2,7 |
| C65-080 | Dojlidy | 290656135 | cycleway | asphalt | brak tagu | 391,6 | 105,9 | Adama Mickiewicza (236884704) | 12,5 | szary asfalt | 2,8 |
| C65-081 | Dojlidy | 294819728 | cycleway | asphalt | brak tagu | 1077,1 | 133,2 | Konstantego Ciołkowskiego (279876738) | 9,3 | szary asfalt | 2,1 |
| C65-082 | Dojlidy | 538810152 | path | paved | yes | 32,8 | 32,8 | Jacka Kuronia (532805224) | 11,5 | przejazd przez jezdnię: tylko białe linie P-11 | — |
| C65-083 | Dojlidy | 538810153 | path | paved | yes | 1324,3 | 1014,9 | Dywizjonu 303 (443103344) | 8,1 | szary asfalt | 2,6 |
| C65-084 | Dojlidy | 543330143 | path | paved | yes | 1236,7 | 1000,2 | Dywizjonu 303 (538810157) | 9,4 | szary asfalt | 2,45 |
| C65-085 | Dojlidy | 614216218 | path | paved | yes | 128,3 | 128,3 | Wiewiórcza (552379026) | 10,3 | nieczytelne | — |
| C65-086 | Dojlidy | 671082740 | path | paved | yes | 34,5 | 34,5 | Jacka Kuronia (275237234) | 12,6 | przejazd przez jezdnię: tylko białe linie P-11 | — |
| C65-087 | Dojlidy | 671082750 | path | paved | yes | 31,3 | 31,3 | Adama Mickiewicza (258564446) | 11,2 | przejazd przez jezdnię: tylko białe linie P-11 | — |
| C65-088 | Dojlidy | 674080173 | cycleway | brak tagu | brak tagu | 15,2 | 15,2 | Wiewiórcza (553340158) | 11,6 | — | — |
| C65-089 | Dojlidy | 674080174 | path | paved | yes | 16,2 | 16,2 | Wiewiórcza (552379026) | 10 | — | — |
| C65-090 | Dojlidy | 674080176 | path | paved | no | 251 | 251 | Wiewiórcza (552379026) | 10,8 | jasnoszara nawierzchnia bez linii | 4 |
| C65-091 | Dojlidy | 692955707 | cycleway | asphalt | brak tagu | 537 | 537 | Pułkownika Czesława Hake (1564109694) | 10,7 | szary asfalt | 2,45 |
| C65-092 | Dojlidy | 692955719 | cycleway | asphalt | brak tagu | 507,4 | 280,3 | Pułkownika Czesława Hake (609748642) | 10,5 | szary asfalt | 2,15 |
| C65-093 | Dojlidy | 1534813757 | path | paved | yes | 1190,8 | 97,6 | Adama Mickiewicza (977514049) | 8,5 | ciemna nawierzchnia w cieniu drzew | 3,1 |
| C65-094 | Dojlidy | 1534813758 | path | asphalt | yes | 7,8 | 7,8 | Adama Mickiewicza (977514050) | 11 | — | — |

Pełne tagi (JSON), końce WGS84, min/max odległości osi i lista brakujących tagów — w `manifest.csv` (wiersze `odcinek`) i `inventory.json`.

## 3. Szerokości i geometria (ESTIMATED, orto 5 cm, linijka 1 m, ±0,3 m)

| way_id | region | przekrój | nawierzchnia | DDR/ciąg [m] | chodnik [m] | zieleń przy jezdni [m] | układ od jezdni |
|---|---|---|---|---|---|---|---|
| 538810153 | Dojlidy | t00 | szary asfalt | 2,6 | 1,9 | 2,5 | jezdnia | krawężnik | zieleń | DDR | chodnik (kostka jasna) |
| 543330143 | Dojlidy | t01 | szary asfalt | 2,45 | 2,55 | 3,1 | jezdnia | krawężnik | zieleń | DDR | chodnik |
| 212811563 | Dojlidy | t02 | szary asfalt | 2,7 | 2,45 | 3,3 | jezdnia | krawężnik | zieleń | chodnik (kostka jasna) | DDR |
| 180233649 | Dojlidy | t03 | szary asfalt | 2,8 | 2,45 | 3,1 | jezdnia | krawężnik | zieleń | chodnik | DDR |
| 237088754 | Dojlidy | t04 | szary asfalt | 2,65 | 2 | 2,4 | jezdnia | krawężnik | pas żwirowo-trawiasty | chodnik | DDR (przekrój w 25 % długości); w 75 % długości (t05): jezdnia | krawężnik | DDR 2,55 m | chodnik 1,55 m — bez zieleni |
| 285876996 | Dojlidy | t06 | szary asfalt | 2,7 | 2,5 | 2,8 | jezdnia | krawężnik | zieleń | chodnik | DDR |
| 212811558 | Dojlidy | t07 | szary asfalt | 3,1 | — | 3,5 | jezdnia | krawężnik | zieleń | ciąg pieszo-rowerowy |
| 692955707 | Dojlidy | t08 | szary asfalt | 2,45 | 1,8 | 2,9 | jezdnia | krawężnik | zieleń | chodnik (kostka) | zieleń 1,55 m | DDR |
| 692955719 | Dojlidy | t09 | szary asfalt | 2,15 | 1,7 | 2,4 | jezdnia | krawężnik | zieleń | chodnik (kostka) | zieleń 1,5 m | DDR |
| 674080176 | Dojlidy | t11 | jasnoszara nawierzchnia bez linii | 4 | — | — | jezdnia | krawężnik | pas kostki/zieleni | ciąg pieszo-rowerowy |
| 294819728 | Dojlidy | t12 | szary asfalt | 2,1 | 2,2 | 1,9 | jezdnia | krawężnik | zieleń | chodnik | zieleń 0,9 m | DDR |
| 198376011 | Dojlidy | t13 | jasnoszara nawierzchnia bez linii | 3 | — | 1,2 | jezdnia | krawężnik | zieleń | ciąg pieszo-rowerowy |
| 290656135 | Dojlidy | u21 | szary asfalt | 2,8 | — | 3,5 | jezdnia | krawężnik | pas utwardzony jasny ok. 3,7 m | zieleń | DDR |
| 1534813757 | Dojlidy | u26 | ciemna nawierzchnia w cieniu drzew | 3,1 | 2,1 | — | jezdnia | krawężnik | pas żwirowy | chodnik | DDR |
| 174538884 | C | t14 | jasna kostka betonowa | 3,7 | — | — | jezdnia | pobocze żwirowe ok. 6,2 m | ciąg pieszo-rowerowy |
| 177876101 | C | t15 | jasna kostka betonowa | 3,7 | — | 4,4 | jezdnia | krawężnik | zieleń | ciąg pieszo-rowerowy | żółta balustrada U-12 |
| 1448274979 | C | t16 | jasna kostka betonowa | 2,75 | — | 4,7 | jezdnia | krawężnik | zieleń | ciąg pieszo-rowerowy |
| 284396207 | C | t17 | czerwonobrązowy | 3,2 | 3 | — | chodnik (jasny) | DDR | żółta balustrada U-12 | skarpa |
| 257367436 | C | t18 | ciemna nawierzchnia z brunatnym odcieniem, w cieniu drzew | 3,3 | 2,7 | 3,8 | jezdnia | pobocze | zieleń | chodnik (jasny) | DDR |
| 268470393 | C | t19 | ciemna nawierzchnia z brunatnym odcieniem, w cieniu drzew | 3,1 | 2,7 | 4 | jezdnia | krawężnik | zieleń | chodnik (jasny) | DDR |
| 344253261 | C | t20 | szary asfalt | 2,8 | 2,9 | 0 | jezdnia | krawężnik | chodnik (jasny) | DDR | trawnik |
| 946729187 | C | t22 | jasnoszara, bez linii | 4,2 | — | 0 | jezdnia (buspas) | krawężnik | ciąg pieszo-rowerowy | bariera |
| 236107938 | C | t23 | szary asfalt | 3,2 | 2,1 | 2,9 | jezdnia (buspas) | krawężnik | zieleń | DDR | chodnik (jasny) | zieleń |
| 284396209 | C | t24 | czerwonobrązowy | 2,8 | 2,9 | 3,4 | jezdnia łącznicy | krawężnik | zieleń | DDR | chodnik (jasny) |
| 257367441 | C | t25 | czerwonobrązowy | 2,2 | 1,8 | — | jezdnia | bariera | zieleń ok. 1,1 m | DDR | chodnik | ekran/ściana |
| 177903955 | C | t26 | czerwonobrązowy | 2,35 | 2,9 | 0 | jezdnia | krawężnik | chodnik (jasny) | DDR | trawnik |
| 282244166 | C | t27 | czerwonobrązowy | 3,3 | 2,8 | 3 | jezdnia | krawężnik | zieleń | chodnik (jasny) | DDR | żółta balustrada U-12 |
| 591358181 | C | t28 | szary asfalt | 2,65 | 1,7 | 0,8 | jezdnia | krawężnik | wąska zieleń | chodnik | pas z czerwonej kostki ok. 0,4 m | DDR |
| 879051665 | C | t29 | szary asfalt | 2,65 | 1,75 | 2,2 | jezdnia | krawężnik | zieleń | DDR | pas z czerwonej kostki ok. 0,4 m | chodnik | żółta balustrada |
| 173956082 | C | t30 | wyblakły, różowoszary asfalt | 2,35 | 1,7 | — | jezdnia | bariera | zieleń ok. 1,1 m | DDR | chodnik | ściana |
| 238234011 | C | t31 | czerwonobrązowy | 3,2 | 2,6 | — | chodnik (jasny) | zieleń 1,9 m | DDR | trawnik |
| 549997879 | C | t32 | jasna kostka betonowa | 3,5 | — | 3,8 | jezdnia | krawężnik | zieleń | ciąg pieszo-rowerowy | żółta balustrada | droga serwisowa |
| 435369091 | C | t33 | czerwona nawierzchnia bez linii osiowej | 3,65 | — | 2,3 | jezdnia | krawężnik | zieleń | ciąg pieszo-rowerowy |
| 613145836 | C | t34 | czerwonobrązowy | 3,2 | 3 | — | pas żwirowy | chodnik (jasny) | zieleń 1,3 m | DDR | żółta balustrada U-12 |
| 946729182 | C | t35 | szary asfalt | 3,1 | 2,2 | 3 | jezdnia | krawężnik | zieleń | DDR | chodnik (jasny) |
| 173985179 | C | u00 | czerwonobrązowy | 2,6 | 2,2 | — | zieleń | DDR | chodnik (jasny) | zieleń |
| 177895175 | C | u02 | czerwona nawierzchnia bez linii osiowej | 2,2 | — | — | jezdnia | krawężnik | chodnik (jasny) | zieleń | pas czerwony | zieleń | jezdnia |
| 177946178 | C | u03 | jasna kostka betonowa | 3,5 | — | — | jezdnia | krawężnik | zieleń | ciąg | zieleń | jezdnia |
| 177948304 | C | u04 | jasna kostka betonowa | 3,5 | — | 1,7 | jezdnia | krawężnik | zieleń | ciąg | plac |
| 177948306 | C | u05 | czerwona nawierzchnia bez linii osiowej | 2,1 | — | — | jezdnia | krawężnik | szeroki chodnik z jasnej kostki | pas czerwony | trawnik |
| 350559280 | C | u09 | czerwona nawierzchnia bez linii osiowej | 2,2 | — | — | jezdnia | zatoka | peron z jasnej kostki z wiatą | pas czerwony | żółta balustrada U-12 |
| 549997876 | C | u10 | jasna kostka betonowa | 3,5 | — | 0 | jezdnia | krawężnik | ciąg | zieleń |
| 549997881 | C | u11 | jasna kostka betonowa | 3,4 | — | — | jezdnia | krawężnik | zieleń | ciąg | zieleń | jezdnia |
| 549997883 | C | u12 | jasna kostka betonowa | 3,6 | — | — | jezdnia | krawężnik | zieleń | ciąg | skwer |
| 591365139 | C | u13 | czerwonobrązowy | 3,25 | 3,1 | 3 | jezdnia | krawężnik | zieleń | chodnik (jasny) | DDR | trawnik |
| 676746632 | C | u14 | szary asfalt | 2,8 | 2,6 | 0 | jezdnia | żółty separator | DDR | chodnik (jasny) |
| 923506577 | C | u15 | szary asfalt | 3,8 | — | — | ciąg pieszo-rowerowy w zieleni (bez jezdni obok) |
| 923506579 | C | u16 | szary asfalt | 4 | — | — | ciąg pieszo-rowerowy w zieleni |
| 999223585 | C | u17 | szary asfalt | 2,7 | — | 0 | jezdnia (buspas) | żółty separator/opornik | DDR | zieleń |
| 1093579599 | C | u18 | jasna kostka betonowa | 3,7 | — | 3,7 | jezdnia | krawężnik | zieleń | ciąg | trawnik |

Wnioski: DDR asfaltowe dwukierunkowe mają zwykle **2,1–2,8 m** (Dojlidy) i **2,2–3,3 m** (C, czerwonobrązowe); chodnik obok **1,7–3,0 m**; pas zieleni między krawężnikiem jezdni a ciągiem **1,9–4,7 m** (bywa 0 — DDR/chodnik przy samym krawężniku). Wytyczne ZDM: DDR dwukierunkowa min. 2,0 m, jednokierunkowa min. 1,5 m (str. 18).

Krawężnik: wytyczne ZDM, rys. nr 9 (str. 18) — krawężnik/obrzeże najazdowe „k1” 25×12×100 cm z odsłonięciem „+3” (cm — jednostka niepodana na rysunku); 16 cm tylko przy przystankach (str. 4). **Wysokość krawężnika jezdni przy DDR i skosy wjazdów: UNVERIFIED** (brak w dokumentach, nieczytelne z orto).

## 4. Przejazdy dla rowerzystów (przez jezdnie)

Przepis: Dz.U. 2019 poz. 2311, zał. 2, pkt 4.2.2 — „nie może być mniejsza niż: – 1,8 m – w przypadku przejazdu jednokierunkowego, – 3,0 m – w przypadku przejazdu dwukierunkowego” (str. 569); „zaleca się dodatkowe oznaczenie powierzchni przejazdu barwą czerwoną” (str. 570); przejazd połączony z przejściem „oznacza się barwą czerwoną” (str. 571). „s” = odległość między zewnętrznymi krawędziami rzędów kwadratów P-11 (przy przejeździe połączonym: od rzędu kwadratów do krawędzi zebry).

| id | region | node | lat, lon | jezdnia (way) | czerwone pole | s [m] | zebra [m] | wyspa | sygnalizacja (OSM) | wycinek |
|---|---|---|---|---|---|---|---|---|---|---|
| C65-144 | Dojlidy | 5825973689 | 53.104500, 23.176802 | Spadochroniarzy (616185295) | TAK | 2,05 | 2,9 | nie | uncontrolled | c00 |
| C65-148 | Dojlidy | 6505679117 | 53.108557, 23.173730 | Spadochroniarzy (616185295) | TAK | 1,55 | 3,85 | nie | brak tagu | c01 |
| C65-145 | Dojlidy | 5906745186 | 53.107333, 23.183920 | Karola Modzelewskiego (553323256) | TAK | 2,5 | 2,6 | nie | brak tagu | c02 |
| C65-143 | Dojlidy | 5810311651 | 53.110623, 23.186443 | Karola Modzelewskiego (553323256) | TAK | 2,5 | 3,05 | nie | marked | c03 |
| C65-138 | Dojlidy | 3889955473 | 53.093687, 23.193534 | Grabowa (171563407) | TAK | 2,8 | — | nie | uncontrolled | c04 |
| C65-131 | Dojlidy | 2895147443 | 53.110899, 23.180902 | Adama Mickiewicza (353943956) | TAK | 2,7 | 3,95 | tak | traffic_signals | c05 |
| C65-132 | Dojlidy | 2895147444 | 53.110942, 23.181063 | Adama Mickiewicza (616184917) | TAK | 2,6 | 3,95 | tak | traffic_signals | c06 |
| C65-141 | Dojlidy | 5775179569 | 53.110972, 23.180681 | Pułkownika Czesława Hake (609748643) | TAK | 2,7 | 4,35 | tak | traffic_signals | c07 |
| C65-142 | Dojlidy | 5775179571 | 53.111044, 23.180623 | Pułkownika Czesława Hake (13960984) | TAK | 2,65 | 4,1 | tak | traffic_signals | c08 |
| C65-130 | Dojlidy | 2226186646 | 53.103293, 23.186700 | Franciszka Karpińskiego (275237230) | nie | 2,8 | 3,85 | nie | brak tagu | c09 |
| C65-133 | Dojlidy | 2999986094 | 53.106420, 23.192319 | Żurawia (107761065) | nie | 4 | 3,8 | nie | brak tagu | c10 |
| C65-137 | Dojlidy | 3867824994 | 53.105453, 23.197215 | Myśliwska (353943959) | nie | 3,3 | 3,9 | nie | brak tagu | c11 |
| C65-129 | Dojlidy | 2163381064 | 53.105472, 23.185316 | Jacka Kuronia (691820491) | nie | 3,05 | 4,05 | tak | traffic_signals | c12 |
| C65-139 | Dojlidy | 5169862895 | 53.105457, 23.184733 | Dywizjonu 303 (691820490) | nie | 2,35 | 4 | tak | traffic_signals | c13 |
| C65-128 | Dojlidy | 2163381053 | 53.105296, 23.185034 | Adama Mickiewicza (258564447) | nie | 2,3 | 4 | tak | traffic_signals | c14 |
| C65-146 | Dojlidy | 6284342138 | 53.105641, 23.184994 | Adama Mickiewicza (691820489) | nie | 2,65 | 4,05 | tak | traffic_signals | c15 |
| C65-100 | C | 1882953779 | 53.151509, 23.167291 | Bitwy Białostockiej (177903962) | TAK | 3,1 | — | tak | brak tagu | c16 |
| C65-101 | C | 1882953782 | 53.151562, 23.167150 | Bitwy Białostockiej (177903961) | TAK | — | — | tak | brak tagu | c17 |
| C65-107 | C | 2641555452 | 53.150587, 23.154705 | Aleja Tysiąclecia Państwa Polskiego (999223605) | TAK | 3 | 4 | tak | traffic_signals | c18 |
| C65-111 | C | 3032448286 | 53.150942, 23.154713 | Aleja Tysiąclecia Państwa Polskiego (536419697) | TAK | 3,05 | 4,1 | tak | traffic_signals | c19 |
| C65-126 | C | 9224916295 | 53.150764, 23.154972 | Kombatantów (999223596) | TAK | 2,9 | — | tak | traffic_signals | c20 |
| C65-105 | C | 2441701386 | 53.150716, 23.154405 | Sokólska (188396757) | TAK | 3 | — | tak | traffic_signals | c21 |
| C65-119 | C | 6942794456 | 53.155076, 23.152683 | Aleja Tysiąclecia Państwa Polskiego (913217363) | TAK | 3,1 | — | tak | traffic_signals | c22 |
| C65-116 | C | 5940539335 | 53.154765, 23.152488 | Wileńska (741639499) | TAK | 3 | — | tak | traffic_signals | c23 |
| C65-097 | C | 1852129028 | 53.158392, 23.151960 | trunk_link (173956081) | nie | 2,7 | — | tak | traffic_signals | c24 |
| C65-108 | C | 2882674810 | 53.158491, 23.151775 | Aleja Tysiąclecia Państwa Polskiego (257367421) | nie | 2,55 | 3,9 | UNVERIFIED | traffic_signals | c25 |
| C65-099 | C | 1859438371 | 53.158760, 23.151329 | Aleja Tysiąclecia Państwa Polskiego (284541843) | nie | — | — | UNVERIFIED | traffic_signals | c26 |
| C65-109 | C | 2882674819 | 53.159178, 23.152052 | trunk_link (173956083) | nie | — | — | nie | traffic_signals | c27 |
| C65-114 | C | 4391371828 | 53.153181, 23.164549 | residential (536419670) | brak oznakowania | — | — | nie | uncontrolled | c28 |
| C65-104 | C | 2274001610 | 53.150437, 23.153856 | Sokólska (673971629) | brak oznakowania | — | — | nie | brak tagu | c29 |
| C65-095 | C | 1748446221 | 53.150841, 23.154933 | Kombatantów (673971630) | TAK | 3 | 4,1 | tak | traffic_signals | c30 |
| C65-117 | C | 6337303569 | 53.154996, 23.152899 | living_street (741639500) | TAK | 2,85 | — | tak | traffic_signals | c31 |
| C65-110 | C | 3032448284 | 53.150620, 23.154880 | Aleja Tysiąclecia Państwa Polskiego (236107504) | TAK | — | — | UNVERIFIED | traffic_signals | x00 |
| C65-123 | C | 8763628068 | 53.150912, 23.154546 | Aleja Tysiąclecia Państwa Polskiego (946729184) | TAK | — | — | UNVERIFIED | traffic_signals | x00 |
| C65-127 | C | 9224916298 | 53.150639, 23.154460 | Sokólska (999223598) | TAK | — | — | UNVERIFIED | traffic_signals | x00 |
| C65-118 | C | 6337303579 | 53.154698, 23.152530 | Wileńska (741639503) | TAK | — | — | UNVERIFIED | traffic_signals | x12 |
| C65-120 | C | 6942794457 | 53.155048, 23.152526 | Aleja Tysiąclecia Państwa Polskiego (685674626) | TAK | — | — | UNVERIFIED | traffic_signals | x12 |
| C65-121 | C | 6942794461 | 53.154931, 23.152946 | living_street (741639501) | TAK | — | — | UNVERIFIED | traffic_signals | x12 |
| C65-136 | Dojlidy | 3051047427 | 53.105579, 23.185248 | Jacka Kuronia (275237234) | nie | — | — | UNVERIFIED | traffic_signals | x16 |
| C65-140 | Dojlidy | 5169862896 | 53.105355, 23.184812 | Dywizjonu 303 (631663133) | nie | — | — | UNVERIFIED | traffic_signals | x16 |
| C65-135 | Dojlidy | 3051047426 | 53.105333, 23.185211 | Adama Mickiewicza (275237231) | nie | — | — | UNVERIFIED | traffic_signals | x16 |
| C65-147 | Dojlidy | 6284342139 | 53.105599, 23.184816 | Adama Mickiewicza (258564446) | nie | — | — | UNVERIFIED | traffic_signals | x16 |
| C65-098 | C | 1852129061 | 53.158518, 23.151989 | trunk_link (173985177) | nie | — | — | UNVERIFIED | traffic_signals | x02 |
| C65-134 | Dojlidy | 2999994950 | 53.109512, 23.182326 | Praw Kobiet (107760272) | brak oznakowania | — | — | UNVERIFIED | brak tagu | x20 |

Bilans (54 przecięcia DDR z jezdniami wg OSM): C — 16 czerwonych, 5 tylko białych, 2 bez oznakowania, 10 nieoglądanych (drobne uliczki osiedlowe); Dojlidy — 9 czerwonych, 11 tylko białych, 1 bez oznakowania. Zmierzone „s”: czerwone mediana 2,83 m (1,55–3,10; n=18), białe mediana 2,70 m (2,30–4,00; n=9) — około połowy poniżej normatywnych 3,0 m.

Znaki pionowe: D-6b potwierdzony na kadrach ulicznych tylko przy rondzie pod estakadą (C65-208, C65-218, C65-221); dla pozostałych przejazdów C-13/C-16, D-6a/D-6b — **UNVERIFIED** (z ortofotomapy nieczytelne). Sygnalizacja — z tagu OSM `crossing` (maszty widoczne na orto na skrzyżowaniach x00, x12, x16, x18).

Kadr P11-056 (C65-241) potwierdza z poziomu ulicy czerwone pole i zebrę przejazdu C65-144.

### 4a. Przecięcia DDR z wjazdami (38 węzłów OSM, 12 obejrzanych)

| id | region | node | DDR (way) | wycinek | co widać |
|---|---|---|---|---|---|
| C65-170 | Dojlidy | 2226186747 | 212811563 | w00 | Dojlidy, ul. Kuronia — wjazd z bramą ok. 13 m od stanowiska kadru P11-001: DDR (szary asfalt) URYWA SIĘ po obu stronach; przez wjazd biegnie jasna nawierzchnia zjazdu, bez czerwieni i bez P-11; linie DDR kończą się na krawędzi zjazdu |
| C65-168 | Dojlidy | 1237947065 | 212811563 | w01 | Dojlidy, ul. Kuronia — zjazd z szarej kostki przecina DDR; DDR urywa się, pary P-23 po obu stronach; przy krawędziach chodnika krótkie pasy czerwonej i żółtej kostki; bez czerwieni na zjeździe |
| C65-175 | Dojlidy | 3867825003 | 212811563 | w02 | Dojlidy, ul. Kuronia — zjazd z różowoczerwonej kostki przecina chodnik i DDR; DDR urywa się, P-23 po obu stronach; w kadrze wygrodzony wykop |
| C65-177 | Dojlidy | 3884485530 | 285876996 | w03 | Dojlidy, ul. Mickiewicza — zjazd z szarej kostki; DDR urywa się, P-23 po obu stronach, białe pasy poprzeczne; narożniki z czerwonej kostki |
| C65-182 | Dojlidy | 6610648268 | 538810153 | w04 | Dojlidy, ul. Dywizjonu 303 (obok przejazdu z P11-056) — zjazd jasny, DDR urywa się, P-23 po obu stronach, żółta płyta ostrzegawcza na chodniku |
| C65-180 | Dojlidy | 6592100364 | 543330143 | w05 | Dojlidy, ul. Dywizjonu 303 — wjazd na budowę z płyt betonowych przecina DDR; linia osiowa DDR przerwana |
| C65-150 | C | 1852129002 | 284396209 | w06 | C, rondo Putry — przejazd przez drogę serwisową: białe P-11 (dwa rzędy kwadratów, ok. 2,6 m) + zebra; DDR czerwonobrązowa po obu stronach, czerwień nie przechodzi przez jezdnię |
| C65-149 | C | 1166108041 | 741639504 | w07 | C, Al. Tysiąclecia — przejazd przez wlot drogi serwisowej z CZERWONYM polem (ok. 2,9 m, rząd kwadratów + zebra), ciemne ślady kół na czerwieni |
| C65-165 | C | 5645777754 | 591358181 | w08 | C, ul. Bitwy Białostockiej — zjazd o zniszczonej nawierzchni (łaty, ubytki); wytarte białe kwadraty P-11; DDR szara z P-23, wzdłuż niej wąski pas czerwonej kostki |
| C65-156 | C | 3097201643 | 1448274979 | w09 | C, ul. Andersa — wlot drogi serwisowej: tylko zebra, bez P-11 (ciąg pieszo-rowerowy z kostki) |
| C65-157 | C | 3509934924 | 344253261 | w10 | C, Al. Tysiąclecia — wyjazd z parkingu: CZERWONE pole ok. 2,9 × 9 m bez białych kwadratów, linia osiowa DDR przechodzi przez pole (ciągłość DDR przez wjazd oznaczona samą czerwienią) |
| C65-153 | C | 1883463881 | 591358181 | w11 | C, ul. Bitwy Białostockiej — wjazd: CZERWONE pole ok. 3,2 × 7 m bez białych kwadratów; DDR po obu stronach z P-23 |

## 5. Czerwona nawierzchnia — wygląd (do tekstur)

- **Asfalt barwiony DDR (C):** czerwonobrązowy/bordowy, matowy, mniej nasycony i ciemniejszy od pól przejazdów; miejscami spłowiały do różowoszarego; białe P-1d/P-23 na czerwonym tle; krawędź prosta przy obrzeżu, obok chodnik z jasnej kostki. Kodu RAL/Munsell dla masy barwionej **nie ma** w wytycznych ZDM (jest tylko wymóg „wyraźnie inny kolor”, str. 19) → UNVERIFIED.
- **Pola przejazdów:** jasna, żywa czerwień — **RAL 3020** wg wytycznych ZDM (str. 16: „Przejazdy rowerowe w kolorze czerwonym – kolor RAL 3020, wykonane z masy chemoutwardzalnej ze środkiem uszorstniającym.”). Granica ostra: rząd białych kwadratów albo krawędź zebry; kształt prostokąt/trapez. **Zużycie:** czerwień wytarta do ciemnego asfaltu w śladach kół (C65-100, C65-101, C65-149).
- **Czerwona kostka:** pasy rowerowe 2,1–2,2 m przy ul. Andersa, pas separacyjny ok. 0,4 m między DDR a chodnikiem (Bitwy Białostockiej), krótkie pola przy krawężnikach przed przejściami.
- Faktura kruszywa, plamy oleju, łaty, uszczelnienie spoiny czerwony/szary, wygląd zimą — **UNVERIFIED** (wymaga kadrów z poziomu pieszego; patrz §9).

## 6. Kadry

Manifest: 241 wierszy: odcinek 93, przejazd 92 (w tym 38 wjazdów), nawierzchnia 21, kadr 35. Kadry uliczne obejrzane w pomniejszeniu do 960 px (+ wycinki 130–300 % dla znaków): 7 Panoramax + 8 KartaView = 15 z regionu C + **2 Commons z Dojlid (P11-001, P11-056 — miniatury 1600 px)**; z przejazdem rowerowym w kadrze: 3 pewne (D-6b) + 2 niepewne. Dodatkowo obejrzano 17 wycinków zbiorczych ortofotomapy (6 C, 11 Dojlidy; 15 z przejazdem), 64 przekroje odcinków, 32 wycinki przejazdów i 12 wycinków wjazdów (pliki przy wierszach `odcinek`/`przejazd`).

| id | źródło | data | lat, lon | kierunek | way (odl.) | przejazd w kadrze |
|---|---|---|---|---|---|---|
| C65-208 | api.panoramax.xyz | 2019-08-15 | 53.158866, 23.151440 | 121 | way 284396205 (C65-024), odległość kamery od osi 12.6 m | tak (znaki D-6b) |
| C65-209 | api.panoramax.xyz | 2019-08-15 | 53.159066, 23.151981 | 53 | way 173985179 (C65-002), odległość kamery od osi 4.5 m | nie (tylko zebra, znaki D-6) |
| C65-210 | api.panoramax.xyz | 2019-08-15 | 53.162912, 23.151808 | 42 | way 257367436 (C65-019), odległość kamery od osi 6.8 m | nie |
| C65-211 | api.panoramax.xyz | 2019-08-15 | 53.163476, 23.151471 | 32 | way 257367436 (C65-019), odległość kamery od osi 3.5 m | nie |
| C65-212 | api.panoramax.xyz | 2019-08-15 | 53.166082, 23.148670 | 39 | way 268470393 (C65-022), odległość kamery od osi 9.5 m | nie (w głębi przejście ze znakami D-6) |
| C65-213 | api.panoramax.xyz | 2019-09-01 | 53.167168, 23.148070 | 165 | way 268470393 (C65-022), odległość kamery od osi 22.0 m | nie (tylko zebra) |
| C65-214 | api.panoramax.xyz | 2019-09-01 | 53.159678, 23.151453 | 242 | way 173985179 (C65-002), odległość kamery od osi 63.6 m — POZA regułą 25 m, kadr kontekstowy | nie (tylko zebra) |
| C65-215 | api.kartaview.org | 2018-03-23 | 53.154866, 23.152718 | 156 | way 741639504 (C65-047), odległość kamery od osi 16.4 m | niepewne (zebra na wlocie, białe znaki wytarte) |
| C65-216 | api.kartaview.org | 2018-03-23 | 53.151238, 23.154498 | 162 | way 344253261 (C65-028), odległość kamery od osi 12.5 m | nie |
| C65-217 | api.kartaview.org | 2018-03-23 | 53.151052, 23.154586 | 162 | way 344253261 (C65-028), odległość kamery od osi 12.7 m | niepewne (rząd białych prostokątów przed zebrą) |
| C65-218 | api.kartaview.org | 2018-03-23 | 53.158899, 23.151281 | 172 | way 257367441 (C65-020), odległość kamery od osi 12.3 m | tak (D-6b + P-11) |
| C65-219 | api.kartaview.org | 2021-06-23 | 53.151901, 23.167647 | 302 | way 177895162 (C65-007), odległość kamery od osi 25.7 m — POZA regułą 25 m, kadr kontekstowy | nie |
| C65-220 | api.kartaview.org | 2021-06-23 | 53.158987, 23.151816 | 307 | way 173985179 (C65-002), odległość kamery od osi 17.8 m | nie |
| C65-221 | api.kartaview.org | 2019-08-04 | 53.158852, 23.151445 | 123 | way 284396205 (C65-024), odległość kamery od osi 11.2 m | tak (znak D-6b) |
| C65-222 | api.kartaview.org | 2019-08-25 | 53.158963, 23.151821 | 303 | way 173985179 (C65-002), odległość kamery od osi 18.3 m | nie |
| C65-240 | commons.wikimedia.org | 2024-06-23 | 53.106512, 23.189265 | 93 | way 212811563 (C65-076), odległość kamery od osi 2.2 m | nie |
| C65-241 | commons.wikimedia.org | 2023-08-14 | 53.104182, 23.176891 | UNVERIFIED | way 538810153 (C65-083), odległość kamery od osi 5.1 m | tak (czerwone pole + zebra) |

Uwaga: kadry KartaView z 2018 r. (C65-215…C65-218) pokazują stan sprzed pojawienia się czerwonych pól na skrzyżowaniach Al. Tysiąclecia — nie używać ich jako dowodu „braku czerwieni” dziś. Kadry z estakady (C65-214, C65-219, C65-220, C65-222) są dalej niż 25 m od osi DDR albo nad nią — kadry kontekstowe (czerwona opaska na estakadzie to chodnik techniczny, nie DDR).

## 7. Rozbieżności OSM ↔ zdjęcie/ortofotomapa

| id | obiekt | rozbieżność |
|---|---|---|
| C65-002 | way/173985179 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=asphalt) |
| C65-008 | way/177895175 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=brak tagu) |
| C65-009 | way/177903955 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=asphalt) |
| C65-013 | way/177948306 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=paving_stones) |
| C65-015 | way/236107938 | OSM surface=paved — orto pokazuje asfalt |
| C65-017 | way/238234011 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=asphalt) |
| C65-020 | way/257367441 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=asphalt) |
| C65-023 | way/282244166 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=asphalt) |
| C65-025 | way/284396207 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=paved) |
| C65-026 | way/284396209 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=asphalt) |
| C65-028 | way/344253261 | OSM surface=paved — orto pokazuje asfalt |
| C65-029 | way/350559280 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=brak tagu) |
| C65-033 | way/435369091 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=paved) |
| C65-040 | way/591358181 | OSM surface=paved — orto pokazuje asfalt |
| C65-042 | way/591365139 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=paved) |
| C65-043 | way/613145836 | ROZBIEŻNOŚĆ OSM↔orto: nawierzchnia czerwona, a w OSM brak colour/surface:colour (surface=asphalt) |
| C65-045 | way/676746632 | OSM surface=paved — orto pokazuje asfalt |
| C65-048 | way/879051665 | OSM surface=paved — orto pokazuje asfalt |
| C65-054 | way/946729182 | OSM surface=paved — orto pokazuje asfalt |
| C65-072 | way/180233649 | OSM surface=paved — orto pokazuje asfalt |
| C65-076 | way/212811563 | OSM surface=paved — orto pokazuje asfalt |
| C65-077 | way/237088754 | OSM surface=paved — orto pokazuje asfalt |
| C65-083 | way/538810153 | OSM surface=paved — orto pokazuje asfalt |
| C65-084 | way/543330143 | OSM surface=paved — orto pokazuje asfalt |
| C65-095 | node/1748446221 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-100 | node/1882953779 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-101 | node/1882953782 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-105 | node/2441701386 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-107 | node/2641555452 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-111 | node/3032448286 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-114 | node/4391371828 | ROZBIEŻNOŚĆ OSM↔orto: bicycle=yes, a na ortofotomapie brak linii P-11 |
| C65-116 | node/5940539335 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-117 | node/6337303569 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-119 | node/6942794456 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-126 | node/9224916295 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-131 | node/2895147443 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-132 | node/2895147444 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-138 | node/3889955473 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-141 | node/5775179569 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-142 | node/5775179571 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-143 | node/5810311651 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-144 | node/5825973689 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-145 | node/5906745186 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-148 | node/6505679117 | ROZBIEŻNOŚĆ OSM↔orto: czerwona powierzchnia przejazdu nieodnotowana w tagach węzła (brak crossing:markings=*/surface:colour) |
| C65-191 | https://www.bip.bialystok.pl/resource/103311/Za%C5%82.+nr+5_Wytyczne+do+projektowania.pdf | ROZBIEŻNOŚĆ standard↔orto: na ul. Kuronia i Mickiewicza (Dojlidy) oraz Al. Tysiąclecia (C) chodnik leży bliżej jezdni niż DDR (patrz wiersze odcinków) |

Dodatkowo (ogólne): (a) `highway=cycleway` + `foot=no` na ul. Mickiewicza (285876996) i innych, choć chodnik biegnie w tej samej płaszczyźnie tuż obok (w OSM brak osobnego `footway`); (b) wytyczne ZDM („DDR między chodnikiem a jezdnią”) a stan: na Kuronia, Mickiewicza i części Al. Tysiąclecia chodnik jest bliżej jezdni niż DDR; (c) P11-001 / P11-056: opis w manifeście p11 nie wspomina DDR ani przejazdu; wg pozycji P11-056 leży 5 m od way 538810153 i ok. 35 m od przejazdu C65-144 (czerwony), P11-001 — 2 m od way 212811563 (szary asfalt wg orto) i ok. 13 m od wjazdu C65-170.

## 8. Samokontrola 20 %

Seed `random.Random(20261114).sample(ids, 48)` (48/239 = 20,1 %). Sprawdzono: ponowne zapytanie OSM API 0.6 o 15 way i 19 węzłów (wszystkie istnieją, tagi zgodne), ponowne obejrzenie 30 obrazów pobranych niezależnie przez `fetch.py` (nowe arkusze z linijką), HTTP 200 dla 4 kadrów ulicznych, 5 cytatów w tekście PDF. Wynik: **38 PASS, 10 POPRAWIONO**. Najważniejsza poprawka: odczyty szerokości przejazdów „na oko” miały rozrzut do ±0,4 m → dla wszystkich 32 wycinków policzono profil jasności (`tools/crossing_profile.py`) i podmieniono wartości; 3 nieczytelne przejazdy dostały brak wartości. Szczegóły: `audit_20_percent.json`.

## 9. Luki (uczciwie)

1. **Wikimedia Commons: `upload.wikimedia.org` i API dawały HTTP 429 przez całą sesję**; na końcu udało się pobrać przez `thumb.php` tylko **miniatury 1600 px** P11-001 i P11-056 (obejrzane, C65-240/241; sha256 dotyczy miniatury, nie oryginału; licencja/autor wg manifestu p11). Pozostałych kadrów ulicznych z Dojlid nie ma (Panoramax i KartaView: 0 zdjęć) — kryterium „≥ 10 kadrów z Dojlid” spełnione tylko zastępczo ortofotomapą (11 wycinków zbiorczych + przekroje).
2. Region C: 15 kadrów ulicznych to ujęcia z kabiny samochodu, DDR widać w nich słabo; tylko 3 pewne kadry z przejazdem rowerowym (kryterium ≥ 5 — CZĘŚCIOWO; uzupełnione ortofotomapą).
3. Data ortofotomapy niejednoznaczna (2025-04-18 albo 2024-03-30).
4. Szerokości wyłącznie ESTIMATED z orto; dokumentów projektowych/przetargowych BIP dla tych odcinków nie znaleziono; OSM `width` — brak.
5. Wysokość krawężników, skosy wjazdów, znaki pionowe przy przejazdach (poza rondem pod estakadą), faktura i stan nawierzchni z bliska, lato/zima, RAL asfaltu barwionego DDR — UNVERIFIED.
6. 27 krótkich odcinków C (463 m łącznie) i 3 w Dojlidach (39 m) oraz 10 drobnych przecięć w C i 26 wjazdów — nieoglądane (tylko dane OSM).
7. Odcinki o niepewnym kolorze: 257367436 i 268470393 (cień lasu; możliwy spłowiały asfalt barwiony), 741639504, 946729187, 203348234, 614216218, 236110049, 173985180.

## 10. Pliki

`manifest.csv` (25 kolumn = kolumny bloku + `url_pliku`, `sha256`) · `fetch.py` (135 plików, 69 393 145 B, w tym 2 PDF 29,6 MB; `--skip-pdf`) · `overpass-query.ql`, `overpass-result.json` · `inventory.json`, `crossings.json` · `data/` (indeksy wycinków, odczyty `observations.py`, opisy kadrów, cytaty) · `tools/` (geo, inventory, crossings, transect, crossing_crop, crossing_profile, build_manifest, build_readme) · `audit_20_percent.json` · `sources.md` · `STATUS.md`. Zdjęć i PDF w gicie nie ma (`.gitignore`).
