# Przegląd wizualny 2026-11-18 (s24): kabina D84, światła tylne nocą (ADR 0197), Knyszyn P1 (ADR 0295) + ekrany (ADR 0293)

Recenzent: visual-critic (niezależny, ocena tylko z obrazów). Standard: `docs/06` §2, `CLAUDE.md` zasady 4–5.
Źródło: wyłącznie rendery z edytora (kamery QA) — **brak zrzutu z buildu Windows w żadnym zestawie**, więc żaden zestaw nie spełnia `docs/06` §5 pkt 2 (render + zrzut z playera). Pomiary: ImageMagick, sRGB 0–255, średnia z wycinka (x,y w pikselach wskazanego obrazu).

| Zestaw | Werdykt |
|---|---|
| 1. Kabina z fotela D84 | **FAIL** |
| 2. Światła tylne nocą | **FAIL** |
| 3. Knyszyn P1 + ekrany akustyczne | **FAIL** (ekrany: zmiana kierunkowo dobra, obraz nadal FAIL) |

---

## 1. Kabina D84 — FAIL

Pliki: `artifacts/cabin-d84-s24/view/ab-*.jpg` (góra = A, dół = B), `artifacts/cab-view-s24/small/start-cab-view-b-fov70-hud.jpg`.

**Co odróżnia render od zdjęcia z kabiny:** realna kabina ma wyraźne szczeliny paneli, różne tworzywa (ziarnisty mat deski, satynowe przełączniki, guma), odbicie deski w szybie, kurz widoczny pod światło, a nocą podświetlenie zegarów i przełączników rozlewające się na otoczenie. Tu: deska jako „topiąca się” bryła jednego koloru, prawie zerowa różnica A/B, noc = jednolita czerń.

### Różnica A/B
Zmiana D84 jest **prawie niewidoczna** z fotela (driver/dash/hub/seat/materials A vs B różnią się na poziomie szumu JPEG; widać jedynie inne podświetlenie legend nocą w `ab-legend-night-crops.png` i żebra tacek w zbliżeniu). Średnia luminancja kadru driver A/B: clear 96.9/97.1, dusk 34.9/35.0, noc 12.4/12.5. Polish, którego kierowca nie zobaczy, nie jest polishem z jego perspektywy.

### Problemy
| # | Prio | Gdzie | Problem | Propozycja |
|---|---|---|---|---|
| K1 | **P1** | `ab-High-night-cab-driver.jpg`, cały kadr | Noc: średnia 12.4/255; niebo (300..700, 0..150) = 12.1; deska pod zegarami (330..630, 460..540) = 12.0 — **kabina, niebo i droga w tej samej jasności**, zero separacji. Zegary nie oświetlają ani obręczy kierownicy, ani deski. Słupek A (130..190, 200..400) = 17.5 — jaśniejszy od otoczenia bez źródła światła (podejrzany ambient/emisja). Low ciemniej: 8.7. | Spill od klastra (mały point/area light lub emisja na lightmapie deski), nocne niebo z gradientem i łuną miasta, sprawdzić słupek A. Cel: krawędzie deski wokół klastra co najmniej 20–25/255. |
| K2 | **P1** | `ab-High-clear-cab-dash.jpg` lewy dół (0..300, 780..980); `ab-High-clear-cab-hub.jpg` (0..230, 60..230); `ab-High-clear-cab-driver.jpg` (0..200, 420..500) | Cień słońca na desce i słupku: **schodkowe, poszarpane krawędzie shadow mapy** (aliasing kaskady) i jasna smuga o ostrej krawędzi — „kamuflaż”. Pierwsze, co widać z fotela w słoneczny dzień. | Kabina w bliższym splicie / wyższa rozdzielczość kaskady 0 na High, soft shadows/PCF, korekta normal bias; ewentualnie cienie kabiny bakowane + dynamiczne tylko od słupków. |
| K3 | **P1** | `ab-Low-clear-cab-materials.jpg` (200..560, 220..520) | Bryła deski „topi się”: bulwiaste przejścia bez krawędzi, bez szczelin montażowych i podziału paneli — czerwona flaga `docs/06` §2. Jeden szaroniebieski mat na desce, osłonie zegarów i boczku. | Twarde krawędzie łączeń (szczelina 2–4 mm + AO), deska z 3–4 paneli o różnym roughness/ziarnie (górna mat ok. 0.8, dolne ok. 0.6, wykończenia satynowe ok. 0.4). |
| K4 | P2 | `start-cab-view-b-fov70-hud.jpg` | Lusterko lewe (30..130, 10..240) to płaski prostokąt w powietrzu — brak obudowy i ramienia; prawe ucięte krawędzią. Dolna część kadru (y > 420) to jednolita czarna masa; brak odbicia deski w szybie (`docs/06` §4). | Obudowa lusterka z grubością i ramieniem; subtelne odbicie deski w szybie na High. |
| K5 | P2 | `ab-*-cab-driver.jpg` (ok. 245, 530) | Biały glif HUD przy lewej krawędzi w kadrze kamery kontrolnej. | Wyłączyć w kamerach QA albo opisać. |
| K6 | P2 | `ab-High-clear-cab-trays.jpg` | Żebra tacek są, kurz w kadrze niewidoczny; boczek drzwi z brązowym „drewnopodobnym” pasem (750..960, 160..300) wygląda jak okleina z lat 90., nie tworzywo ciężarówki. | Boczek na szare tworzywo; kurz w maskach zagłębień, kontrola pod niskim słońcem (`after-High-lowsun-*`). |
| K7 | P2 | `ab-legend-night-crops.png` | Legendy nocą czytelne, ciepła biel OK, ale bez halo i bez podświetlenia klawisza — wyglądają jak naklejki emisyjne. | 1–2 px glow na High, minimalna emisja tła klawisza. |

### Oceny (1–10)
| Materiały | Światło | Zużycie/osadzenie | Powtarzalność | Skala | Polskie realia | Artefakty |
|---|---|---|---|---|---|---|
| 4 | 3 | 4 | 6 | 7 | 6 (PL legendy, „Brak mapy tego obszaru”) | 4 |

Werdykt słowny: z fotela w dzień — przyzwoity prototyp w stylu gry mobilnej z 2016; nocą — czarny ekran z zegarami. D84 nie poprawia obrazu w miejscu, gdzie patrzy kierowca.

---

## 2. Światła tylne nocą (ADR 0197) — FAIL

Pliki: `artifacts/lights-79-s24/view/cmp2-*.jpg` (panele: pozycyjne | pozycyjne+stop | pozycyjne+awaryjne), `cmp-plates.jpg` (naczepa noc | ciągnik solo noc | zmierzch stop).

**Co odróżnia render od zdjęcia nocą:** na każdym nocnym zdjęciu tylne pozycyjne są **najjaśniejszym, najbardziej nasyconym czerwonym elementem** tyłu (rdzeń bliski przepalenia, poświata na kloszu i obudowie, czerwony odblask na zderzaku i drodze). Tablica jest jaśniejsza od otoczenia, ale nie dominuje nad lampami. Tu jest odwrotnie.

### Pomiary
| Element | Wycinek | Średnia RGB | Max |
|---|---|---|---|
| Pozycyjne ciągnik High | cmp2-High-night-lamp-truck (283,163) 26x36 | **55,8,7** | 70,12,13 |
| Stop ciągnik High | (923,163) | 197,18,18 | 251,27,31 |
| Pozycyjne naczepa High | cmp2-High-night-lamp-trailer (298,195) | **48,7,7** | 69,12,12 |
| Stop naczepa High | (970,195) | 158,15,15 | 253,27,27 |
| Pozycyjne naczepa Low | cmp2-Low-night-lamp-trailer (300,198) | 53,3,3 | 67,6,8 |
| Stop naczepa Low | (972,198) | 176,12,12 | 253,24,25 |
| Awaryjne (amber) ciągnik | cmp2-High-night-lamp-truck (1522,163) | 195,101,23 | 255,130,38 |
| Tablica naczepy | cmp2-High-night-lamp-trailer (545,185) | **206,203,198** | 255,255,253 |
| Pozycyjne naczepa z dystansu | cmp-plates (150,168) | **32,17,17** | 45,25,25 |
| Pozycyjne ciągnik solo z dystansu | cmp-plates (785,162) | **38,20,20** | 45,26,26 |
| Tablica (dystans) | cmp-plates (275,180) | 204,201,196 | - |
| Obudowa tuż obok stopu | cmp2-High-night-lamp-truck (340,160) | 5,5,5 | 12,9,9 |
| Korpus pod lampą (pozycyjne / stop) | (300,240) / (940,240) | 4,4,4 / 4,4,4 | - |

Wniosek: **tak, pozycyjne są za ciemne.** Ok. 48–55/255 z bliska i **32–38/255 (prawie szare, nienasycone) z kilkunastu metrów** — to wygląda jak niezapalony klosz łapiący ambient. Tablica jest **ok. 4x jaśniejsza (sRGB) z bliska i ok. 6x z dystansu** od pozycyjnych — hierarchia odwrócona. Stosunek stop/pozycyjne w liniowym ok. 0.56/0.04 = 14x — kierunkowo w duchu ECE R7 (pozycyjne 4–17 cd, stop 60–185 cd; `UNVERIFIED` — sprawdzić z tekstem regulaminu), ale podstawa jest za nisko. Stop i kierunkowskazy: kolor i kształt wiarygodne.

### Problemy
| # | Prio | Gdzie | Problem | Propozycja |
|---|---|---|---|---|
| L1 | **P1** | wszystkie cmp2 panel 1; cmp-plates panele 1–2 | Pozycyjne 48–55/255 (dystans 32–38) — nieczytelne jako zapalone; ciągnik solo z tyłu nocą praktycznie niewidoczny poza tablicą. | Emisja pozycyjnych: rdzeń LED R co najmniej 200 przy G,B poniżej 40, średnia segmentu co najmniej 150. Stop zostaje w clipie, ale zyskuje większą powierzchnię świecenia/halo, by różnica była widoczna. |
| L2 | **P1** | cmp2: obudowa (340,160) = 5,5,5; korpus (300,240)/(940,240) = 4,4,4 w obu stanach | **Zero poświaty i rozlewu**: stop o średniej 197 obok obudowy 5/255; ani piksela czerwieni na kloszu, ramie, zderzaku, trójkątach odblaskowych czy drodze. Wygląda jak naklejka emisyjna. | Bloom z progiem tylko dla HDR powyżej 1 (High, subtelny), mały czerwony point/spot dla stopu albo decal-spill na zderzak/drogę, lekka emisja korpusu klosza (rozproszenie w tworzywie). Low: co najmniej decal-spill. |
| L3 | **P1** | cmp-plates panel 1 (275,180); cmp2 trailer (545,185) | Tablica 204–206/255, max 255 — przepalona, bielsza niż cokolwiek w scenie. Na zdjęciach nocnych podświetlona tablica jest jasnoszara i czytelna, nie neonowa. | Obniżyć oświetlenie tablicy do średnio ok. 130–160, z gradientem od lampki (jaśniej przy górnej krawędzi). |
| L4 | P2 | cmp2-Low-night-lamp-trailer, tablica | Low: „BI 8N402” rozmazany do nieczytelności z ok. 3 m. | Mip bias / wyższa rozdzielczość tekstury tablicy na Low albo SDF. |
| L5 | P2 | cmp2 panel 3 | Awaryjne: bursztyn wiarygodny; brak dowodu rytmu 1–2 Hz i narastania. | Dołączyć sekwencję klatek/wideo. |
| L6 | P2 | cmp-plates panel 1, tablice ECE 70 (140..220, 230..255) | Tablice wyróżniające i trójkąty odblaskowe są (dobry detal EU/PL), ale bez reflektorów z tyłu nie da się ocenić retrorefleksji. | Kadr z samochodem za naczepą na światłach mijania. |

### Oceny (1–10)
| Materiały | Światło | Zużycie/osadzenie | Powtarzalność | Skala | Polskie realia | Artefakty |
|---|---|---|---|---|---|---|
| 6 | 3 | 5 | 7 | 7 | 7 (tablice PL, ECE 70, trójkąty) | 6 |

Werdykt słowny: stop i kierunkowskazy w porządku; pozycyjne wyglądają na wyłączone, a tablica świeci jak reklama. Nocny tył zestawu — poziom gry mobilnej.

---

## 3. Knyszyn P1 (ADR 0295) + ekrany akustyczne (ADR 0293) — FAIL

Pliki: `artifacts/knyszyn-p1-s24/sbs/*.jpg` (góra = przed, dół = po), `artifacts/screens-s24/cmp/*.jpg`, referencje `Data/raw/refs/owner-knyszyn-2026-11-15/` (1–3 ratusz i ośrodek kultury, 5 i 7 rynek/park z domami drewnianymi, 9 i 11 rondo DK65 z drona).

**Co odróżnia render od zdjęć właściciela:**
1. **Zieleń wysoka.** Na 9 i 11 każda działka ma drzewa owocowe, tuje, żywopłoty; rynek (3, 5, 7) to dojrzałe lipy i klony. W renderze działki są gołe, a pojedyncze drzewa to niskopoligonowe „brokuły na patyku” (`dk65-outlet-nw` 610..860, 80..260).
2. **Kolor i kontrast pól.** Ref 11, pola (380,130 250x60): **122,149,115** (G-R = +27). Render po (500,700 300x150): **114,119,92** (G-R = +5, oliwkowe khaki). Kontrast całego kadru: ref sigma 63, render sigma 35 — płasko i brudno.
3. **Domy drewniane.** Ref 7: deski **malowane** (czerwonobrązowe, grafitowe/niebieskoszare), okna w obramieniach. Render: surowa jasna sosna jak panele podłogowe.
4. **Rondo.** Ref 9: wyspa środkowa z brukowanym pierścieniem i obsadzeniem, wyniesione wyspy dzielące, zjazdy do posesji. Render: układ trafiony (D51 — rozpoznawalne), wyspa środkowa to płaski biały dysk.

### Problemy
| # | Prio | Gdzie | Problem | Propozycja |
|---|---|---|---|---|
| N1 | **P1** | `rondo-owner-11-before-after.jpg` dół, pionowa krawędź x ok. 820 (y 660..870); `rondo-dk65-top-before-after.jpg` x ok. 237; `rondo-dk65-above-before-after.jpg` klin (150..300, 620..900) | **Szwy kafli/masek terenu widoczne i niezmienione przed i po.** x 820: 123,127,101 vs 138,139,110 (delta ok. 15); x 237: 120,123,82 vs 98,106,71 (delta ok. 22). ADR 0295 sam przyznaje „kafel C do przebudowy”. | Przebudować kafel C; blend 20–50 m przez granicę kafli; walidator: delta luminancji na granicy poniżej 4. |
| N2 | **P1** | `rondo-dk65-top` (220..300, 380..470) i (620..680, 110..160); `rondo-dk65-above` (200..270, 390..470) | Na asfalcie wlotów **koncentryczne „ośmiokątne” pierścienie** jak warstwice — artefakt siatki/UV/normalnych jezdni. Niezmienione. | Wireframe + normalne tego wlotu, retriangulacja / smooth normals. |
| N3 | **P1** | `rondo-owner-11` dół, prawe pola (450..830, 680..870) | „Mozaika pól” po zmianie to blade ukośne smugi w jednym prostokącie; sigma wycinka spadła z 16 do 13 — mniej zróżnicowania niż przed. Nie przypomina podlaskiej szachownicy wąskich pasów (ref 11). | 4–6 upraw (zieleń zbóż, brąz orki, szare ściernisko, sezonowo żółty rzepak), pasy 15–40 m x 200–600 m z działek/landuse, miedze 1–2 m. Kolor bazowy w zieleń (G-R ok. +20…+30). |
| N4 | **P1** | całe `rondo-owner-11`, `rondo-dk65-above`; drzewa w `dk65-outlet-nw` i `screens-s24/cmp/dk65-High-s8-corner-eye.jpg` (830..930, 100..200) | Gołe działki i drzewa „bonsai” z płaskich kęp — największa różnica render vs dron i główny powód werdyktu „gra mobilna”. | Rozsiew drzew owocowych/tui na działkach mieszkalnych, gęstsze korony + impostory z własnego generatora. |
| N5 | P2 | `look-dom-klattow-before-after.jpg` / `klattow-crop-before-after.jpg` dół | Deski: szczyt pionowo, ściana poziomo, obramienia okien — kierunkowo dobrze. Ale: surowe jasne drewno z kafelkującym wzorem (ten sam sęk na ścianie 450..840, 920..1040), jedno okno na ok. 15 m ściany, pionowy szew x ok. 720 (930..1040), rynna kończy się w cokole bez kolana, brak gąsiorów na kalenicy. | Malowane deski (paleta z ref 7), skan z wariantami, rytm okien co 3–4 m, gąsiory, kolano rynny. |
| N6 | P2 | `dk65-outlet-nw-before-after.jpg` dół | Odsunięcie zapory zamykającej DK65 NW — lepiej, koniec świata nie wali w oczy (PASS jako zmiana). Wyspa azylu (470..630, 820..990) bez znaku C-9 i słupka U-5. | C-9 + U-5 na czole wyspy. |
| N7 | P2 | `screens-s24/cmp/maczka-High-wb-zoom.jpg` prawy ekran (830..875, 160..400); lewy (60..620, 200..420) | Ekrany przezroczyste — kierunek właściwy. Ale ekran widziany skośnie to **białe nieprzezroczyste płyty** (158,162,163 — jaśniej niż niebo za nim 150,151,156), bez cokołu nad trawą. Szyby frontalnie bez odbicia nieba i bez pasów antyptasich, ze sztucznym gradientem ku dołowi. Słupy (68,220) 104,108,110 — płaskie i jasne. | Fresnel (przy kącie ostrym odbicie nieba, nie biała ścianka), tint 5–10 %, pionowe pasy antyptasie, cokół betonowy, słupy z profilem. |
| N8 | P2 | `dk65-High-s8-corner-eye.jpg` dół (580..960, 820..990) | Klin P-21 obecny i czytelny. Kreskowanie wychodzi poza trójkąt, brak linii ciągłej zamykającej klin. | Zamknąć klin linią ciągłą, przyciąć kreskowanie. |
| N9 | P2 | `maczka-High-screen-close-0293.jpg` (180..220, 300..540); `maczka-High-screen-wb-eye-0293.jpg` (300..450, 300..540) | Trawa na skarpach rozciągnięta wzdłuż spadku (UV stretch) + ostry ciemny pas w rowie. | Triplanar / world-UV dla skarp. |

### Oceny (1–10)
| Materiały | Światło | Zużycie/osadzenie | Powtarzalność | Skala | Polskie realia | Artefakty |
|---|---|---|---|---|---|---|
| 4 | 5 | 4 | 4 | 7 | 6 (A-7, D-6, P-10, kostka, ogrodzenia z cegły i sztachet trafione; brak C-9, pola i drzewa nie podlaskie) | 3 |

Werdykt słowny: rondo DK65 jest rozpoznawalne z drona (D51 — układ OK), ale jako obraz to nadal „gra mobilna z 2016”: oliwkowe pola ze szwami kafli, gołe działki, drzewa-brokuły, deski jak panele podłogowe. Poprawki P1 z ADR 0295 są realne, ale drobne wobec różnicy do zdjęć; najważniejsza (kafel C) nie została zrobiona.

---

## Blokujące P1 (zbiorczo)
1. K1 — noc w kabinie: brak spillu zegarów, kabina = niebo = droga (ok. 12/255); słupek A jaśniejszy bez źródła.
2. K2 — schodkowe cienie kaskady na desce i słupku z fotela.
3. K3 — „topiąca się” bryła deski bez szczelin, jeden materiał.
4. L1 — pozycyjne 48–55/255 (z dystansu 32–38) — wyglądają na wyłączone.
5. L2 — zero poświaty/rozlewu (obudowa 5/255 obok stopu 197).
6. L3 — tablica 204–206/255, przepalona, 4–6x jaśniejsza od pozycyjnych.
7. N1 — szwy kafli terenu (delta 15–22), niezmienione; kafel C.
8. N2 — pierścienie-warstwice na asfalcie wlotów ronda.
9. N3 — mozaika pól mniej zróżnicowana niż przed (sigma 16 do 13), khaki zamiast zieleni.
10. N4 — gołe działki, drzewa niskopoligonowe.

Przy ponownym przeglądzie dołączyć zrzuty z playera Windows (`build-windows.ps1 -SkipBuild -Run`) w tych samych kadrach.
