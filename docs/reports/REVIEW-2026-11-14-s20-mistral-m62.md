# Przegląd M62 (P19 brama i mur szpitala, kadr P11-129) — s20, 2026-11-14

**Werdykt: FIX.** Dane OSM są poprawne: id, węzeł bramy, obrys, portiernia, ogrodzenie i odległości. Seed audytu da się odtworzyć, a licencje są czyste. Część o kadrach nie spełnia jednak kryteriów i w wielu miejscach przeczy obrazowi. Bramę P11-129 pokazuje tylko jeden kadr (F01); kryterium wymaga ≥ 12 kadrów z ≥ 3 stron. Pozostałe „kadry bramy” (F06, F15, F19) przedstawiają inne obiekty. Opisy 4 kadrów są zmyślone (wnętrza i autobus opisane jako „ulica”). Kierunek wjazdu jest odwrócony: ulica leży po stronie NE, a nie SW. Mur nie jest czerwony. Jest 5 tablic, a nie 4. Daszek źle odczytano. Blok poprawek: `docs/owner/MISTRAL-FIXES-12.md` § M62-FIX. Nic nie scalono i nic nie scommitowano. W PR nie ma komentarza.

## 1. Zakres i metoda

- PR #53, gałąź `origin/research/mistral-p19-hospital-gate` @ `4c8d7ba62` (2 commity od main). `git diff --stat main...` pokazuje tylko 5 plików w `research/mistral/p19-hospital-gate/` (README, manifest 63 wiersze, sources, audit, .gitignore). Poza katalogiem nie zmieniono nic. Pliki obejrzano przez `git archive` w scratchu.
- **ZIP `mistral-p19-hospital-gate-files.zip` (70 462 757 B, sha256 `f38b38a0…`) nie dotarł** do `research/_incoming` ani do Pobranych. Kadry pobrałem więc sam z Commons przez `thumb.php` (1600 px). F01 wziąłem z `research/_incoming/mistral-p11-dojlidy-photos-v2b/files/P11-129.jpg`. **Obejrzałem 14 kadrów** (F01–F08, F12–F16, F19), pomniejszonych do 960 px. Z F01 zrobiłem wycinki 2,5–3× (zestaw znaków, tablice na murze, daszek, B-2 w głębi, mur do liczenia warstw cegieł).
- OSM: `Data/raw/osm/podlaskie-261108.osm.pbf`, pyosmium (venv worldgen, `python -I`), układ lokalny od węzła bramy (X = wschód, Z = północ).
- Znaki: kody według Dz.U. 2019 poz. 2310, wymiary według poz. 2311. Nie sprawdzałem stron PDF z cytatów 2311.

## 2. Kryteria akceptacji M62

| Kryterium | Wynik |
|---|---|
| ≥ 12 obejrzanych kadrów bramy z ≥ 3 stron | **NIE.** Bramę P11-129 pokazuje tylko F01 (1 kadr, 1 strona). F06, F15 i F19 to inne obiekty (§3). README powołuje się na „interpretację zaakceptowaną przez właściciela 2026-11-13”. W `HANDOVER.md` ani w `docs/owner` nie ma takiej decyzji. Nawet przy tej interpretacji wynik to 1 kadr, a nie 4. |
| Mur, słup, daszek: po ≥ 2 niezależne odczyty wymiaru | **NIE.** Za „drugi odczyt muru” (wysokość „~człowieka”) uznano F19. To inna brama (stalowa przesuwna z siatką, przy nowym białym 4-kondygnacyjnym budynku w budowie, 190 m na SE). Słup i daszek nie mają wymiarów (UNVERIFIED). |
| Wszystkie znaki z wysokością zamocowania | **NIE.** Są tylko zakresy normowe (min. 2,0 m itd.), bez odczytu dla tej instalacji. Strona zestawu znaków to UNVERIFIED, choć F01 i OSM ją rozstrzygają (§4). |
| Środek bramy z OSM z id | **TAK.** node 2448457849 (lift_gate, fee=yes) = 53.1094568, 23.1906473 ✓ |
| Brak RGB z pikseli | **TAK.** |

## 3. Oględziny kadrów — „co widać” Mistrala a obraz

| Kadr | Opis M62 | Co widać | Ocena |
|---|---|---|---|
| F01 = P11-129 | brama, 2 słupy z daszkami, mur czerwony, 4 tablice pionowe, znaki, tablica IP biała z niebieskim | patrz §4 | częściowo ✗ |
| F02 | ulica, przystanek z wiatą, ogrodzenie, latarnie | pętla/przystanek, autobus przegubowy, czerwona wiata, toaleta przenośna, maszt kratowy | ✓ |
| F03 | „ulica/przystanek” | **wnętrze autobusu** (kasownik, fotele) | ✗ zmyślone |
| F04 | ulica/przystanek | skrzyżowanie z zebrą, łąka, domy | ✓ (drobne) |
| F05 | REJECTED: brama „po południowej stronie”, „bloki osiedlowe” | ogrodzenie z ceglanymi słupami i stalowymi przęsłami, **B-2** na bramie, wielospadowy budynek z masztem kratowym. To ten sam obiekt co F06 (maszt = node 8220945933, teren `landuse=military`, way 236884785, **na E od Żurawiej**). Nie są to bloki ani szpital | odrzut słuszny, uzasadnienie ✗ |
| F06 | „budynek szpitala (białe ściany, ciemny dach)”, tło za bramą | ten sam budynek z masztem co F05, za zieloną siatką; **nie szpital i nie tło P11-129** | ✗ |
| F07 | ulica/przystanek | skrzyżowanie z zebrą, samochód nauki jazdy, parking | ✓ (drobne) |
| F08 | brama WORD | WORD, baner, brama; STOP w tej skali nieczytelny | ✓ |
| F12 | „ulica/osiedle” | **korytarz przychodni/szpitala** (krzesła, drzwi) | ✗ zmyślone |
| F13 | „ulica/osiedle” | **korytarz** (wnętrze) | ✗ zmyślone |
| F14 | ulica Żurawia wzdłuż | ✓ jezdnia, chodnik z kostki, płot z ceglanymi słupami, maszt. **URL w sources.md daje 404**; prawdziwa nazwa to `20200726_084417_Żurawia_Street_in_Białystok.jpg` (bez „_July_2020”) | ✓ / URL ✗ |
| F15 | „front szpitala, ogrodzenie z siatki” | parterowy budynek z blachy falistej z zielonymi pasami, **inna instytucja** (ośrodek medycyny pracy, napis — nie odtwarzamy), 2 samochody za siatką | ✗ (inny obiekt) |
| F16 | „front szpitala/ulica” | **wejście** do tego samego budynku z blachy, daszek nad wejściem | ✗ |
| F19 | mur ceglany z tablicami, daszki, 4 kondygnacje | **stalowa brama przesuwna z siatką**, słupek z jasnej cegły, tablice „DROGA POŻAROWA” i żółte „TEREN BUDOWY”, koparka, biały budynek 4 kond. w budowie; **nie mur P11-129** | ✗ |

**Wynik: 6/14 zgodnych, 8/14 niezgodnych (57 %).** Cztery opisy (F03, F12, F13, F16) wyglądają jak szablon. Obrazu najpewniej nie oglądano. Stwierdzenie „24 kadry obejrzane” przeczy też samemu README: F09 ma adnotację „nie oglądnieto”. F11/F22 i F17/F23 to te same pliki (…03, …05) liczone dwa razy.

## 4. F01 (P11-129) — szczegóły na wycinkach

- **Kierunek i strony (OSM + F01):** Żurawia (way 73881451) biegnie N–S około **16 m na E/NE** od bramy. Obrys szpitala i budynek A (way 236884780) leżą na W/SW. Mistral ma to odwrotnie. Way **883955523** (brama → 3323248759 → **874174759, węzeł Żurawiej**) to dojazd OD ULICY. Way **73881452** (brama → 874174701) prowadzi już po terenie szpitala; 874174701 łączy się z wewnętrznymi service 642905692 i 1552407066. Kierunek wjazdu = **~242°** (oś 62°/242°). Mistral podaje „62,3° z SW na NE”. Kamera F01 patrzy więc na SW, w głąb terenu. Po lewej (SE) jest mur wzdłuż ogrodzenia 883955509, które biegnie równolegle do Żurawiej. Po prawej (N/NW) są portiernia 296211509 i zestaw znaków. Szkic w README §6 (ulica „16 m S/SW”, 874174701 jako „skrzyżowanie z Żurawią”) trzeba odwrócić.
- **Mur:** cegła **jasna** (szarobeżowa, prawdopodobnie silikatowa lub jasny klinkier; materiał UNVERIFIED), **nie czerwono-brązowa**. Nakrywa płaska, betonowa. Na końcu muru stoi ceglany filar z płaską nakrywą, bez daszka. Wysokość według recenzenta to około 24 warstwy cegieł. Przy module 75 mm (65 + 10 mm, założenie) daje to **~1,8 m bez nakrywy** (ESTIMATED, jeden odczyt). Zakres Mistrala 1,7–2,0 m przypadkiem jest zgodny, ale jego metoda (F19) jest błędna.
- **Tablice na murze:** **5**, nie 4. Prostokątne **poziome** (nie pionowe), bordowe z jasnym napisem, w 2 kolumnach (2 + 3). Treść: napisy instytucji i klinik — nie odtwarzamy.
- **Słupy i daszek:** po prawej stoją **dwa ceglane filary połączone wspólnym daszkiem**: jasna belka lub gzyms, na niej ciemna blacha trapezowa, ze spadkiem. Wygląda to na przejście lub zadaszenie przy portierni. Nie są to „płaskie betonowe daszki na obu słupach bramy”. Lewy filar (przy murze) nie ma daszka. P19-033/034/035 są błędne. Audyt dał P19-033 wynik PASS.
- **Znaki (prawa strona = N, przy portierni):** na słupku przy słupie szlabanu, od góry: **C-2** (strzałka w górę, potem w prawo = skręt za znakiem), **B-33 „20”** i mała tabliczka z naklejoną żółtą kartką (nieczytelna). **B-20 STOP** wisi na ceglanym filarze, nie na wspólnym słupku. Pod nim na filarze jest niebieska tablica „WJAZD NA PODSTAWIE przepustki / skierowania / biletu wjazdowego” (pominięta). Na ramieniu szlabanu jest tabliczka „OPŁATA ZA WJAZD 3 zł” (pominięta, zgodna z OSM fee=yes). **B-2** jest wyraźny, ale stoi osobno, w głębi terenu, na własnym słupku przed niskim beżowym budynkiem, około 20–30 m za bramą (odległość ESTIMATED). **Nie należy do zestawu przy bramie**, więc P19-046 „prawdopodobny w zestawie” jest błędne. Wysokości zamocowania da się oszacować z F01 (kotwica: B-20 średni = koło wpisane 800 mm), ale Mistral tego nie zrobił.
- **Tablica izby przyjęć:** **niebieska z żółtym i białym napisem** („NIE FUNKCJONUJE IZBA PRZYJĘĆ I SZPITALNY ODDZIAŁ RATUNKOWY” + drobny tekst). Stoi na **własnym białym słupku** przed filarem, nie na słupie bramy. P19-049/050 są błędne. Uwaga dla gry: to tablica informacyjna z treścią instytucji. Odtwarzamy tylko formę, bez napisu.
- **Szlaban:** ramię biało-czerwone, opuszczone, słupek napędu czerwony, po prawej (N) ✓.
- **Nawierzchnia:** dojazd asfaltowy, mokry, z łatami ✓. Chodnik po lewej to **kostka betonowa** (szara, z czerwonym pasem). Da się to rozstrzygnąć, więc korekta audytu P19-054 → UNVERIFIED jest zbędna.
- **Tło:** budynki niskie, **1–2 kondygnacje**, ściany beżowe i żółte, dachy płaskie lub niskie. W głębi stoją **dwa wysokie smukłe kominy** (kotłownia), po lewej ciemna wyższa bryła. Wpis „min. 4 kondygnacje, jasne” (P19-057) pochodzi z F06/F19, czyli z innych obiektów. Jest błędny.
- Latarnia: wysoki słup z oprawą na wysięgniku za zestawem znaków ✓ (P19-060 ESTIMATED OK).

## 5. OSM — sprawdzenie liczb (PBF 2026-11-08)

Zgodne: node 2448457849 (lift_gate, fee, foot, payment:coins), way 239477156 (amenity=hospital, przechodzi przez węzeł bramy), 296211509 Portiernia (narożnik 3000014175 = +0,9/+3,4), 883955509 fence (koniec 8220895799 = +1,3/−3,1), 883955508, 236884780 (A), 276840492 parking, traffic_mirror 14123795058 (+13,9/−3,1), gate 3323248741 (+31,7/−8,3), post_box 10202945270. Cięciwa 8220895799 → 3000014175 wynosi **6,53 m** (Mistral: 6,58 m). OK, ale to wartość pochodna z geometrii OSM, nie pomiar. Status lepiej „ESTIMATED (geometria OSM)” niż SOURCED. Żurawia: dodatkowo **maxspeed=40** (pominięte), hgv=no, maxweight=3.5 ✓. **Błędne:** role dróg 73881452 i 883955523 oraz kierunek ulicy (§4).

## 6. Licencje, marki, samokontrola

- Licencje są czyste: CC0 (Rakoon), CC BY 3.0 pl (PUW, „referencja, nie tekstura”), ODbL, GUGiK, Dz.U. Google nie ma. Mapillary nie był sondowany (brak tokenu). Panoramax i KartaView dały 0 wyników; to jest wiarygodne.
- Marki i instytucje: napisy z tablic nie trafiają do opisów gry ✓. W README §3 jest `operator`/`loc_name` z OSM (dane położenia, dopuszczalne). F15/F16 opisano jako „szpital”, choć to inna instytucja.
- Dz.U.: w sources.md tytuł 2311 to „w sprawie znaków i sygnałów drogowych”. To błąd: **poz. 2311 = szczegółowe warunki techniczne** (wymiary, wysokości), a **poz. 2310 = znaki i sygnały** (kody, znaczenie). Wymiary słusznie wzięto z 2311.
- Samokontrola 20 %: seed 20261113 da się odtworzyć (`python -I`: te same 13 id) ✓. Merytorycznie audyt jest słaby. P19-033 (daszki „na obu słupach”) dostał PASS, a jest błędny. P19-054 skorygowano w złą stronę. Na kadrach audyt sprawdzał głównie F01. Bez ZIP nie da się odtworzyć „ponownego obejrzenia”.

## 7. Dla lidera

- **Nie scalać** w obecnej postaci. Jeśli hospgate-0189 korzysta już z tych danych (przekazanych jako niezweryfikowane), trzeba mu **natychmiast** przekazać: (1) ulica jest po stronie **E/NE**, wjazd na ~242°; (2) mur z **jasnej** cegły, ~1,8 m, z nakrywą betonową; (3) **5 poziomych bordowych tablic** w układzie 2 + 3; (4) po stronie N są dwa filary ze **wspólnym daszkiem z ciemnej blachy trapezowej na jasnej belce**, a lewy filar nie ma daszka; (5) STOP wisi na filarze, a C-2 i B-33 „20” na słupku przy szlabanie; (6) tablica IP jest niebieska, na osobnym słupku; (7) tło to niskie budynki i dwa kominy, nie 4-kondygnacyjny blok; (8) B-2 stoi w głębi, osobno.
- **Możliwa errata do naszego przeglądu M47-FIX-2 (P11-129: „strzałka zakrzywiona = C-1”):** strzałka w F01 biegnie w górę i skręca w prawo, czyli oznacza skręt **za** znakiem = **C-2** według opisów z Dz.U. 2019 poz. 2310. Mistral (C-2) ma tu rację. Przed poprawką manifestu P11 warto sprawdzić to na piktogramie z załącznika.
- ZIP M62 nie dotarł do repo ani do `_incoming`. Jeśli właściciel go ma, warto go rozpakować do `research/_incoming/mistral-p19-hospital-gate/`, bo ułatwi przegląd FIX.
