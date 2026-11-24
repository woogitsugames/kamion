# ADR 0329 — Głos GPS: ducking, wyłącznik, „cel” tylko na miejscu, bez podwójnego „na rondzie”

Status: propozycja (gałąź `gps-polish-s24`, nie scalone). Uzupełnia ADR 0328 (właściciel zaakceptował głos, D97).

## Decyzje

1. **Ducking.** `NavVoicePlayer.Duck01` narasta w 150 ms i opada w 400 ms (`DuckAttackS`, `DuckReleaseS`, `WORKING_VALUE`) i jest
   publikowane do `AudioMixLevels.VoiceDuck01`. `TruckAudioController` mnoży gain silnika i otoczenia przez
   `AudioMixLevels.DuckGain = 1 - DuckDepth * Duck01`, `DuckDepth = 0,5` (−6 dB, `WORKING_VALUE`, do oceny na ucho przez
   właściciela). Gain jest zapisywany tylko przy zmianie wersji miksu albo ducku; brak alokacji. Sygnały kabiny (`ClusterChime`) nie są ściszane.
2. **Wyłącznik.** `PcVolumeSettings.gpsVoice` (domyślnie `true`; plik sprzed pola daje `true`, schemat nadal 1), przełącznik
   „Głos nawigacji GPS” w zakładce Audio (sekcja NAWIGACJA), `AudioMixLevels.GpsVoice`. Wyłączony: `Enqueue` nic nie kolejkuje,
   a wyłączenie w trakcie mówienia zatrzymuje klip i czyści kolejkę.
3. **Cel.** Paczka nie ma zdania „za X metrów cel”, więc `NavVoice.PlanBand` dla `Maneuver.Arrive` zwraca „Jesteś u celu”
   (B10 #11) tylko w paśmie „teraz”, jako jedyny klip (bez ulicy, „a następnie”, pasa). W pasmach dalekich i bliskich cisza.
4. **Rondo.** B07 „Na rondzie zjedź …” + B14 „na rondzie Putry.” dawały dwa razy „na rondzie”, więc B14 nie jest już
   zlecane (`RoundaboutNameClip` zostaje w kodzie).

## Brakujące klipy (do ewentualnego nagrania, poza zakresem tego zadania)

Nazwa ronda w mianowniku, bez „na rondzie”: „Rondo Krzysztofa Jakuba Putry.” (lub „Rondo Putry.”) i „Rondo Pamięci Bieżeństwa.”.
Z nimi można mówić np. „Na rondzie zjedź drugim zjazdem.” + „Rondo Putry.” albo dodać wariant „Zjedź … zjazdem z ronda”.
Do czasu nagrania B14 w paczce jest nieużywane (2 klipy). Nie generowano żadnych nagrań.

## Testy

`Nav0168Tests` / `tools/nav-runner/Tests/NavVoiceTests.cs` (Arrive tylko „teraz” i samotny; brak B14), `NavVoicePlayer0328Tests`
(ducking 150/400 ms, wyłącznik, zapis i stary plik). `Sim.csproj` wyklucza `NavVoicePlayer`/`NavVoiceBank` (zależne od `UnityEngine.Audio`).

## Dopisek (s24, agent `gps-ringnames-s24`): blok B15 — nazwy rond w mianowniku

Zgoda właściciela D96 obejmuje generowanie komunikatów GPS głosem „Kamion GPS” (`QsH1g7itRvwZbnuW1zc5`, model `eleven_multilingual_v2`, ustawienia domyślne głosu — jak w paczce, ADR 0328). Wygenerowano dokładnie dwa klipy, po jednej próbie (bez ponowień):

| Klip | Tekst | Generacja ElevenLabs | Kredyty | LUFS / szczyt | Tempo |
|---|---|---|---|---|---|
| `GPS_B15_01` | „Rondo Krzysztofa Jakuba Putry.” | `zu1PKMApKUX6yqBbZket` | 30 | −16,0 / −1,28 dBFS, 1,99 s | 5,2 sylab/s |
| `GPS_B15_02` | „Rondo Pamięci Bieżeństwa.” | `nZI6TQI6g5gkDrDd5yUb` | 25 | −16,0 / −2,53 dBFS, 1,51 s | 5,6 sylab/s |

Razem 55 kredytów. Nazwa w grafie to „Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP” (pełna) i „Rondo Pamięci Bieżeństwa 1915 roku”; klipy mówią skróconą formę z planu zadania, dopasowanie po prefiksie (jak B14). Obróbka jak w paczce (`process_pack.py --only 15`: −16 LUFS, szczyt ≤ −1 dBFS, cisza przycięta, kontrola tempa sylab); `--only` scala blok z istniejącym manifestem bez ruszania 96 pozostałych klipów (ich sha256 bez zmian).

`NavVoice.PlanBand`: po `RoundaboutExitClip` (B07 „Na rondzie zjedź … zjazdem.”) dodaje `RoundaboutNominativeClip(RingName(...))` (B15), czyli osobne zdanie „Rondo Putry.” — bez drugiego „na rondzie”. Pierścień spoza listy: bez dodatkowego klipu. Maks. 6 klipów w zdaniu (bufor 6) bez zmian. B14 pozostaje w paczce, niezlecane. Liczba kluczy do nagrania: 98.

Testy: `NavVoiceTests` (nav-runner) i `Nav0168Tests`/`NavVoicePlayer0328Tests` (EditMode) — B15 bezpośrednio po B07 #2 na trasie G03, linia logu `B07#2,B15#1`, brak B14, manifest 98 kluczy. Demo: `artifacts/gps-ringnames-s24/demo_200m_rondo_2zjazd_putry.wav` (B03 #8 + B07 #2 + B15 #1). Ocena na ucho (płynność złożenia, prozodia „Rondo …”) — właściciel.

## Dopisek (s24, agent `neon-ringname-s24`): audyt ronda na DK65 (build #7) oraz poprawka `m_EdgeFirstPoint` / `NavVoice.RingName`

1. **Rondo na DK65 z logu buildu #7 (`t≈1326–1367 s`, `clips=B05#8,B07#2`, bez `ring=` i bez B15) — sprawdzone, bez nazwy w rzeczywistości i w danych.**
   - Pierwsze komunikaty (500 m, 100 m) padają jeszcze z kafla `dk65-05` (`Studzienna`), ale samo rondo leży 114 m na północ od szwu (`y = 603391,0` EPSG:2180), w kaflu **`dk65-06`** (`EPSG:2180 (767640, 603505)`, WGS84 `53,22917°N, 23,01145°E` — rejon DK65 / Krynice / Dobrzyniewo Duże).
   - Źródła sprawdzone: OSM `Data/raw/osm/podlaskie-261108.osm.pbf` (`way/1151531611`, `way/1560819266` — `highway=primary`, `junction=roundabout`, `ref=65`, brak tagu `name`; wszystkie 6 ramion wjazdowych/zjazdowych, sąsiednie węzły i relacje również bez nazwy ronda), `Data/Regions/dk65-06/roads.graph.json` i `dk65-06_route.bytes` (6 krawędzi ronda, wszystkie `name=""`), GUGiK BDOT10k (`bdot10k-2002` `OT_SKDR_L`/`OT_SKJZ_L` — wyłącznie `NUMERDROGI=65` i `1395B`, brak nazwy własnej), a także brak uchwały nadającej nazwę w źródłach publicznych. Tak zostaje: brak `ring=` i brak klipu B15 są poprawne.
   - *(Uwaga poboczna: lokalne rondo w `dk65-05` na zbiegu Lipowa/Szkolna w Dobrzyniewie Dużym, `way/1270347375`/`1362045957`/`1362045958`, jest poza trasą DK65 i również nie ma nazwy w OSM/BDOT10k. Rondo w Knyszynie na skrzyżowaniu DK65/DW671, `way/1426801304`, także nie ma nazwy w OSM/BDOT10k ani w rzeczywistości.)*
2. **Naprawiony błąd `RoutePlanner.BuildGeometry` + `NavVoice.RingName`.**
   - Dotychczas `m_EdgeFirstPoint[i]` było ustawiane na `p.Count - 1` przed `AppendRange`. Gdy osie jezdni z ADR 0144 mają przerwę > 1 cm na wjeździe na rondo (0,125–1,569 m), `p.Add` nie nadpisywało poprzedniego punktu — `p.ManPoint[man]` wskazywało na ostatni punkt krawędzi **wjazdowej** zamiast na pierścień. Dodatkowo `NavVoice.RingName` skanowało do `from + 12` zamiast kończyć przed krawędzią zjazdową.
   - Skutki przed poprawką: (a) na 4 z 29 manewrów rondowych ze złotego zestawu C (`G05`, `G18`, `G24`, `G29` — wjazd na Rondo Putry z al. Tysiąclecia oraz na Rondo Pamięci Bieżeństwa z Bitwy Białostockiej) `RingName` zwracało nazwę ulicy wjazdowej, przez co znikał klip B15 (`25/29 → 29/29` po poprawce); (b) bezimienne rondo w Knyszynie (`t≈2173–2211 s` w buildzie #7) dostawało w logu fałszywe `ring="Obozowa"` (ulica wjazdowa).
   - Poprawka: `RoutePlanner` wyznacza `m_EdgeFirstPoint[i]` jako faktyczny pierwszy punkt krawędzi `i` (uwzględniając deduplikację `< 1 cm`) oraz zapamiętuje `m_EdgeLastPoint[i]`, ustawiając `ManEndPoint` na `m_EdgeLastPoint[j - 1]` (koniec ostatniej krawędzi pierścienia — zachowuje co do 0,0 m dystans do zjazdu z testu `Dk6506_RoundaboutGuidanceStaysUntilExit`). `NavVoice.RingName` skanuje wyłącznie pierścień (`ManPoint[man] .. ManEndPoint[man] - 1`), bez alokacji.
3. **Brakujące klipy B15 dla nazwanych rond na trasie C → Tykocin (poza C; nagrań NIE generowano):**
   - `bialystok-maczka` (`t≈198–215 s`, `ring="Rondo Jana Nowaka-Jeziorańskiego"`): proponowany tekst B15 — `Rondo Jana Nowaka-Jeziorańskiego.`
   - `bialystok-knyszynska` (`t≈540–558 s`, `ring="Rondo Pamięci Męczeństwa Kresowian"`): proponowany tekst B15 — `Rondo Pamięci Męczeństwa Kresowian.`
4. **Testy:** `NavVoiceTests` (nav-runner) i `Nav0168Tests` (EditMode) — regresje dla `dk65-06` (`RingName == null`), `knyszyn` (`RingName == null`, bez wycieku `"Obozowa"`/`"Tykocka"`), wjazdu z nazwanej ulicy z przerwą osi (`G05` Putry → `B15 #1`, `G18` Bieżeństwa → `B15 #2`) oraz syntetycznego ronda bez nazwy między nazwanymi drogami.

## Dopisek (s24, agent `gps-ringnames2-s24`): B15 #3 i #4 — rondo Nowaka-Jeziorańskiego i Męczeństwa Kresowian

Zamknięcie punktu 3 powyżej (zgoda właściciela D96 na generowanie komunikatów głosem „Kamion GPS”). Wygenerowano dokładnie dwa klipy, po jednej próbie, tym samym głosem (`QsH1g7itRvwZbnuW1zc5`) i modelem (`eleven_multilingual_v2`, ustawienia domyślne głosu) co paczka:

| Klip | Tekst | generation id | Kredyty | Po obróbce | Tempo |
|---|---|---|---|---|---|
| `GPS_B15_03` | „Rondo Jana Nowaka-Jeziorańskiego.” | `fEc10YgtpHptsewVlKur` | 33 | −16,0 LUFS / −1,15 dBFS, 1,83 s | 6,9 sylab/s |
| `GPS_B15_04` | „Rondo Pamięci Męczeństwa Kresowian.” | `ebsm0Yus1QCBR8zGNVHM` | 35 | −16,1 LUFS / −1,0 dBFS, 1,86 s (limiter 1,0 dB) | 6,2 sylab/s |

Razem 68 kredytów. Obróbka: `process_pack.py --only 15` (−16 LUFS, szczyt ≤ −1 dBFS, cisza przycięta, kontrola tempa; limit 8 sylab/s). Pozostałe klipy bez zmian (sha256 jak wcześniej). Spektrogram: `artifacts/gps-ringnames2-s24/spec.png` (brak oczywistych kliknięć; w #4 pojedynczy szerokopasmowy wybuch ok. 0,27 s, zgodny z zwarto-wybuchową „d” w „Rondo” — do oceny na ucho). `NavVoice.RoundaboutNominativeClip`: prefiksy „Rondo Jana Nowaka-Jeziorańskiego” → B15 #3, „Rondo Pamięci Męczeństwa Kresowian” → B15 #4 (prefiks „Rondo Pamięci Bieżeństwa” jest rozłączny). Liczba kluczy do nagrania: 100. Testy: nav-runner (`RoundaboutNominativeClip` #3/#4 i nieznane = (0,0)), EditMode `NavVoicePlayer0328Tests` (100 kluczy, manifest pokrywa wszystkie). Ocena na ucho — właściciel.
