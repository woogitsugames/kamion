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
