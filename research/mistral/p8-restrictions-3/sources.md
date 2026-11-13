# sources.md — M54 (research/mistral/p8-restrictions-3)

Wszystkie źródła dostępne **2026-11-13** (data dostępu). Cytaty ≤ 25 słów lub wskazanie strony/sekcji.
Licencja „dokument urzędowy" = poza przedmiotem prawa autorskiego (art. 4 ustawy o prawie autorskim).
Nagrania Panoramax: **CC-BY-SA-4.0**; Wikimedia Commons: CC0 / CC BY-SA 3.0 / CC BY-SA 4.0 (per plik).
**Zakazane źródła Google nie były używane.** Mapillary: brak tokenu (UNVERIFIED, nie używano cudzych kluczy).

## 1. OSM (ODbL 1.0, „© OpenStreetMap contributors")

Pobranie bezpośrednie z API 0.6 (api.openstreetmap.org), 2026-11-13; pełne geometrie (`/way/{id}/full.json`) i historie (`/way/{id}/history.json`).

| Way | URL | Cytat/strona |
|---|---|---|
| 23844386, 173985170 (Maczka nad rondem Putry) | https://www.openstreetmap.org/way/23844386 | tags: `bridge=viaduct; layer=1; maxaxleload=11.5; source:maxaxleload=Dz.U. 2011 nr 222 poz. 1321 Art. 2 pkt. 11`; brak `maxheight` |
| 25447143, 173985172 (Andersa nad rondem Putry) | https://www.openstreetmap.org/way/25447143 | j.w. (name=Generała Władysława Andersa, ref=65) |
| 180144451 (Rondo Putry) | https://www.openstreetmap.org/way/180144451 | tags: `junction=roundabout; ref=8;19; maxaxleload=11.5` |
| 197904073, 197904074 (al. Tysiąclecia nad linią 6) | https://www.openstreetmap.org/way/197904073 | tags: `bridge=yes; layer=1; ref=8;19; int_ref=E 67; maxaxleload=11.5`; przecięcie z way 34171047 w pkt 53.16450/23.15006 (test segmentowy) |
| 34171047 (linia kolejowa nr 6) | https://www.openstreetmap.org/way/34171047 | tags: `railway=rail; ref=6; usage=main; operator=PKP Polskie Linie Kolejowe` |
| 615609894, 615614873 (al. JP2 nad rondem Wolnej Ukrainy) | https://www.openstreetmap.org/way/615609894 | tags: `bridge=viaduct; layer=1; maxweight:signed=no`; brak `maxheight`; bbox pokrywa rondo 615607647 |
| 615607647 (Rondo Wolnej Ukrainy) | https://www.openstreetmap.org/way/615607647 | tags: `junction=roundabout; maxheight=default` (wartość ignorowana) |
| 262041391, 175054484, 175054483, 262041392 (rondo Żołnierzy Wyklętych) | https://www.openstreetmap.org/way/262041391 | tags: `bridge=viaduct; layer=1; maxaxleload=11.5`; brak `maxheight` |
| 183639791, 183639792 (S8 nad al. Niepodległości) | https://www.openstreetmap.org/way/183639791 | tags: `bridge=yes; layer=1; ref=S8; toll:hgv=yes; maxaxleload=11.5`; przecięcie z way 297345998 w pkt 53.15960/22.99612 i 53.15948/22.99676 (test segmentowy) |
| 297345998 (al. Niepodległości — segment bez name) | https://www.openstreetmap.org/way/297345998 | tertiary, 16 węzłów, bez `name`; łączy się node 1908957194 z way 180455821 (name=Aleja Niepodległości) |
| 318134414, 661035215 (rondo Kmicica) | https://www.openstreetmap.org/way/318134414 | tags: `junction=roundabout; bridge=yes; layer=1` |
| 318134435, 626485641 (al. Niepodległości, Starosielce) | https://www.openstreetmap.org/way/318134435 | tags: `cutting=yes; maxheight=default; ref=669` |
| 178208423 (Bitwy Białostockiej) | https://www.openstreetmap.org/way/178208423 | tags: `hgv=no; goods=delivery; old_name=I Armii Wojska Polskiego`; v1: 2012-08-27, cs 12883607, user cyunczykg |
| 188396757 (Sokólska) | https://www.openstreetmap.org/way/188396757 | tags: `hgv=no`; v20: 2026-10-22T22:10:17Z, cs 190904727, user Michoo, source: „Geoportal 2: BDOT500…", comment: „Białostoczek - parkingi…" |
| 842154286 (Warszawska) | https://www.openstreetmap.org/way/842154286 | tags: `maxweight=12 t; hgv=no; goods=delivery`; v7: 2025-03-01T17:43:57Z, cs 163097076, user Marek-M, comment: „Korekta geometrii skrzyżowań"; goods od v1: 2020-08-29, cs 90120818 |
| 572651591–572651594 (Branickiego) | https://www.openstreetmap.org/way/572651591 | tags: `maxweight=8`; od v1: 2018-03-24, cs 57486579, user pawka007 |
| 261469444 (Zwierzyniecka) | https://www.openstreetmap.org/way/261469444 | tags: `maxweight=8`; v4: 2014-08-05T12:46:27Z, cs 24555223, user cyunczykg, source: „Wizja lokalna", comment: „znaczniki maxweigt turnlanes i destination" |
| 37 ways `ref=S19;65` (S19 Krynice–Białystok Zachód) | https://www.openstreetmap.org/way/241580472 | tags (wszystkie): `maxaxleload=11.5; maxspeed:hgv=80`; brak `maxheight`; brak `toll:hgv`; 10 ways `bridge=viaduct` = 5 obiektów: 241580472/78 (53.1808/23.0332), 1151531620/21 (53.1732/23.0318), 1449644043/44 (53.1753/23.0324), 1457994933/34 (53.1883/23.0303), 1557429211/12 (53.1615/23.0268) |

## 2. Dz.U. / ELI

- **Dz.U. 2026 poz. 33** — Rozporządzenie Rady Ministrów z dnia 8 stycznia 2026 r. zmieniające rozporządzenie w sprawie dróg krajowych lub ich odcinków, na których pobiera się opłatę elektroniczną…
  - URL: https://www.dziennikustaw.gov.pl/DU/2026/33 (ELI, dostęp 2026-11-13; tytuł potwierdzony na stronie ELI)
  - Ten sam dokument na MF: https://etoll.mf.gov.pl/media/q05hn11w/rozporz%C4%85dzenie-rady-ministr%C3%B3w-z-dnia-8-stycznia-2026-r-zmieniaj%C4%85ce-rozporz%C4%85dzenie-w-sprawie-dr%C3%B3g-krajowych-lub-ich-odcink%C3%B3w-na-kt%C3%B3rych-pobiera-si%C4%99-op%C5%82at%C4%99-elektroniczn%C4%85-oraz-wysoko%C5%9Bci-stawek-op%C5%82aty-elektronicznej.pdf
  - Kopia w repo: `files/rozp_2026_33.pdf.b64` (base64) — **SHA256 oryginału:** `5e4b80b2f5d4be69affb029ce9451ed5538ac3542812f57fbcb2d40e3ef70d4e`, 211 685 B; dekodowanie: `base64 -d rozp_2026_33.pdf.b64 > rozp_2026_33.pdf`
- **Dz.U. 2022 poz. 1518** (rozporządzenie ws. warunków technicznych pojazdów; § 80 — skrajnia) — cyt. za P8-2 (P8-012/P8-013 w `research/gptpro/p8-truck-restrictions-2`).

## 3. MF e-TOLL ( Ministerstwo Finansów / KAS)

- **Pełna lista odcinków dróg płatnych od 10.02.2026 r.** (PDF):
  https://etoll.mf.gov.pl/media/pmlhwkrm/pe%C5%82na-lista-odcink%C3%B3w-dr%C3%B3g-p%C5%82atnych-od-1022026-r.pdf — dostęp 2026-11-13, HTTP 200.
  Kopia: `files/full_list_2026-02-01.pdf.b64` — **SHA256:** `57f2cd6b20b824f9c5839e48cc0259e32d0819edd3fa31edc1af97585f7c4f4c`, 715 477 B.
  Strona nadrzędna: https://etoll.mf.gov.pl/system-e-toll/siec-drog-platnych („Sieć dróg płatnych").
  Odczyt sekcji (S8 Rzędziany–Tykocin 5470 m; Tykocin–Choroszcz 3490 m; węzeł Choroszcz 960 m; DK8 tylko Augustów; DK19/65: brak) — cyt. za **P8-2** (dekodowanie tekstu; fonty CID w ObjStm — tekst nieekstraktowalny standardowo).
- **Lista nowych odcinków dróg płatnych w e-TOLL od 10.02.2026 r.** (PDF):
  https://etoll.mf.gov.pl/media/skpplztd/lista-nowych-odcink%C3%B3w-dr%C3%B3g-p%C5%82atnych-w-e-toll-od-1022026-r.pdf — dostęp 2026-11-13, HTTP 200.
  Kopia: `files/new_sections_2026-02-01.pdf.b64` — **SHA256:** `657c97d334666be19dbc9574f716e1535de081534e5bc368ec287dbfc17604f7`, 200 877 B.
- **Artykuł:** „Zmiany w systemie e-TOLL od 1 lutego 2026 r.", 19.01.2026:
  https://etoll.mf.gov.pl/artykuly/zmiany-w-systemie-e-toll-od-1-lutego-2026-r — dostęp 2026-11-13, HTTP 200. PDF rozporządzenia linkowany z tego artykułu.
- **Lista artykułów (84 karty, daty):** https://etoll.mf.gov.pl/artykuly/ — dostęp 2026-11-13. Kluczowe pozycje: „Złóż wniosek o zwrot niewykorzystanych środków…" (10.11.2026 — najnowszy), „Zmiana adresu serwisu IKK" (21.10.2026), „Zmiany w systemie e-TOLL od 1 lutego 2026 r." (19.01.2026 — ostatni dot. sieci). 16 artykułów nowszych niż 19.01.2026 — 0 dot. sieci/odcinków (kontrola programowa w audycie).

## 4. MI / GDDKiA (S19)

- **Ministerstwo Infrastruktury**, 20.10.2026: „S19 Krynice - Białystok Zachód oddana do ruchu":
  https://www.gov.pl/web/infrastruktura/s19-krynice--bialystok-zachod-oddana-do-ruchu — dostęp 2026-11-13. Cytaty:
  - „Oddany do ruchu 20 października 2026 r. odcinek będzie częścią ekspresowej, północno-zachodniej obwodnicy Białegostoku." (M54-016)
  - „Odcinek S19 Krynice – Białystok Zachód ma 10,2 km długości." (M54-016)
  - „Droga przystosowana jest do przyjęcia ciężkiego ruchu (11,5 t/oś)." (M54-017)
  - „powstały cztery mosty (z funkcją przejść dla zwierząt), 12 przejść dla zwierząt oraz 8 wiaduktów, w tym nad obecną drogą krajową nr 65" (M54-018/019)
  - „W ramach budowy węzła przebudowana została też S8 na długości 1,9 km." (M54-022)
  - „oddanie do użytku planowane jest na pierwszy kwartał 2029 r." (M54-023)
  - „Wykonawcą było konsorcjum firm PORR i Unibep, a wartość kontraktu w systemie Projektuj i buduj wyniosła 405,6 mln zł." (M54-022)
- **GDDKiA Oddział Białystok**, 20.10.2026: „Dwie „eski" połączone koło Białegostoku":
  https://www.gov.pl/web/gddkia-bialystok/dwie-eski-polaczone-kolo-bialegostoku — dostęp 2026-11-13. Cytaty:
  - „zbudowaliśmy cztery mosty (z funkcją przejść dla zwierząt), w tym te na rzekach Supraśl i Biała" (M54-019)
  - „Umowę z konsorcjum firm PORR i Unibep podpisaliśmy 19 maja 2021 r." (M54-022)
  - „tzw. Południowa Obwodnica Białegostoku, czyli odcinek S19 od węzła Białystok Zachód do węzła Deniski nad Narwią" (M54-023)
  - „W marcu 2024 r. przekazaliśmy wykonawcy plac budowy." (M54-022)

## 5. BIP Białystok (dokumenty urzędowe)

- **Zarządzenie nr 295/26**: https://www.bip.bialystok.pl/akty_prawne/zarzadzenia_prezydenta/zarzadzenia-prezydenta-20242029/zarzadzenie-nr-29526.html (dostęp 2026-11-13, HTTP 200; skan PDF bez warstwy tekstowej — identyfikacja tematu UNVERIFIED)
- **Zarządzenie nr 462/26**: https://www.bip.bialystok.pl/akty_prawne/zarzadzenia_prezydenta/zarzadzenia-prezydenta-20242029/zarzadzenie-nr-46226.html (dostęp 2026-11-13, HTTP 200; skan — j.w.)
- **Zarządzenie nr 786/26**: https://www.bip.bialystok.pl/akty_prawne/zarzadzenia_prezydenta/zarzadzenia-prezydenta-20242029/zarzadzenie-nr-78626.html (dostęp 2026-11-13, HTTP 200; skan — j.w.)
- Rejestr: https://www.bip.bialystok.pl/akty_prawne/zarzadzenia_prezydenta/ (dostęp 2026-11-13)
- Komunikaty bialystok.pl (dostęp 2026-11-13): 20.11.2025 — Bitwa Białostockiej, droga dojazdowa (ruch jednokierunkowy, nie hgv); 05.10.2026 — Sokólska, remont mostku nad rzeką Białą (nie hgv).
- Ewidencja ZDM Białystok — brak publicznego rejestru organizacji ruchu: cyt. za **P8-040** (`research/gptpro/p8-truck-restrictions-2`).

## 6. Panoramax (CC-BY-SA-4.0)

Interfejs: https://panoramax.openstreetmap.fr/ ; API: https://api.panoramax.openstreetmap.fr/ — dostęp 2026-11-13.

- **Rondo Putry — 10 kadrów** (id, dystans od centrum ronda, data):
  35224dcb-99e7-472f-8b41-9fff1f150fdd (15 m, 2019-08-15T15:32); 6fc62548-c122-4cba-9e9c-aadceb92e266 (18 m); 3eba62ce-2ff5-4256-974b-050dc4eff3e0 (20 m); 07820d85-61df-4880-8a82-914cb24b3574 (31 m); 844e35c7-bcd0-43e7-a8ac-16931cf7e96b (60 m); 6ded8ec0-a24e-45d0-a6a0-ff0e4ab164a5 (63 m); 239c71e8-1f79-4c72-8bb2-fef6d8be3120 (80 m, 2019-09-01T10:22); 3717771d-33ba-4abd-8c92-1b2b0208d5b3 (92 m); f16bbe61-0a2c-44ef-9fb3-e6303faa34c0 (97 m); 03ec4841-1311-4c3c-95ec-4a52ba4b2184.
  Przykład kadru: https://panoramax.openstreetmap.fr/#focus=map&zoom=17&picture=35224dcb-99e7-472f-8b41-9fff1f150fdd
- **Al. Tysiąclecia — 4 najbliższe kadry** (z 10 pobranych w rejonie):
  412f2d02-8d4b-4b61-a3ba-09c25f3b3b5f (14 m); b294cf11 (38 m); 1bbb5f28 (47 m); 86106e2b (73 m) — daty 2019-08-15 / 2019-09-01.
  Przykład: https://panoramax.openstreetmap.fr/#focus=map&zoom=17&picture=412f2d02-8d4b-4b61-a3ba-09c25f3b3b5f
- **S8/Choroszcz — 10 kadrów** (165–190 m od mostu): 94dd9f98 (165 m), 671cb8f5 (169 m), 25c37bd1 (173 m), 151afdbb (185 m), 95b3a736, 3e661f95, 3c44481e, 6ac337cc, 8d4b7a85, 0a2121ca — daty 2019-08-15 / 2019-09-01. Analiza wizyjna niewykonana (limit narzędzia) — pliki w ZIP.
- **Rondo Wolnej Ukrainy — 10 kadrów, wszystkie ≥576 m od ronda** (brak obserwacji): 061c603a, 2173e4fe, 24999ac7, 4ac8cbd1 i in.
- **0 kadrów** w rejonach: rondo Żołnierzy Wyklętych, Starosielce, Bitwy Białostockiej, Sokólska, Warszawska, Branickiego, Zwierzyniecka (odpytania API — wyniki puste, udokumentowane w sesji).
- Metadane wszystkich pobrań (id, lat/lon, datetime, licencja, URL sd.jpg) w ZIP: `pano/*.json`.

## 7. Wikimedia Commons

- **File:7204 May 2021 in Białystok.jpg** — https://commons.wikimedia.org/wiki/File:7204_May_2021_in_Bia%C5%82ystok.jpg — CC0, autor Rakoon, 2021-05-03, GPS 53.158496/23.153233 (rondo Putry). Dostęp 2026-11-13.
- **File:Krzysztof Putra Roundabout in Białystok.jpg** — https://commons.wikimedia.org/wiki/File:Krzysztof_Putra_Roundabout_in_Bia%C5%82ystok.jpg — CC BY-SA 4.0, autor Henryk Borawski, 2014-09-17.
- **File:Andersa, Maczka streets in Białystok 1.jpg** — https://commons.wikimedia.org/wiki/File:Andersa,_Maczka_streets_in_Bia%C5%82ystok_1.jpg — CC BY-SA 3.0, autor Henryk Borawski, 2013-09-13.
- **File:Andersa, Maczka streets in Białystok 2.jpg** — https://commons.wikimedia.org/wiki/File:Andersa,_Maczka_streets_in_Bia%C5%82ystok_2.jpg — CC BY-SA 3.0, autor Henryk Borawski, 2013-09-13.
- Metadane (licencje/daty/autorzy) potwierdzone przez API Commons (`imageinfo`, dostęp 2026-11-13). Pobrane pliki (miniatury) w ZIP: `commons/`.
- Kategoria: https://commons.wikimedia.org/wiki/Category:Krzysztof_Putra_Roundabout_in_Bia%C5%82ystok (dostęp 2026-11-13).

## 8. KartaView — ograniczenie techniczne

Metadane serii przy badanych obiektach dostępne (katalog `kv/` w ZIP), ale pobranie zdjęć niemożliwe w sesji: storage `*.kartaview.org` — NXDOMAIN / CDN HTTP 502 (kontrola 2026-11-13). Zdjęcia KartaView: **NIEDOSTĘPNE** — udokumentowane jako ograniczenie, nie wpływa na wartości manifestu (żadna pozycja nie cytuje KartaView).

## 9. Cytowania wewnętrzne projektu

- `research/gptpro/p8-truck-restrictions-2/` (P8-001…P8-041): dekodowanie sekcji listy e-TOLL (S8/DK8/DK19/DK65 w regionie), **P8-040** (rejestr ZDM), lokalizacja mostów nad rondem Żołnierzy Wyklętych.
- `research/g10-truck-restrictions/README.md` — założenie o „S8 nad al. Niepodległości w Starosielcach" (skorygowane w M54-009).
- `docs/owner/RESEARCH-PACK-03-MISTRAL.md` — specyfikacja M54.
