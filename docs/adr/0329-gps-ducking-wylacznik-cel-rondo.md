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
