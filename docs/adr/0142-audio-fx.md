# ADR 0142 — Efekty ElevenLabs (sekcje B–G + REGEN-02), turbo v2, miks kabiny, usunięcie „syreny”
Status: Proposed (agent audio, s13), 2026-11-12. Ocena brzmienia: właściciel (telefon, głośnik i słuchawki).
Kontynuacja ADR 0137/0138: przełącznik synteza/ElevenLabs obejmuje teraz cały zestaw dźwięków pojazdu.

## Kontekst
- Po 0137/0138 tylko silnik, hamulec wydechowy, start/stop, klekot, wastegate i retarder grały z ElevenLabs. Pozostałe
  efekty z partii 1 (sekcje B–G) i z REGEN-01 były przeanalizowane, ale niewpięte.
- Opinia właściciela o APK 0138 (`1fa46ca6ad`): silnik ElevenLabs lepszy od syntezy i ma zostać bez zmian. Trzy rzeczy
  przeszkadzają: (1) **„syrena”**, czyli wycie co kilka sekund na postoju i w jeździe, w obu trybach; (2) turbo brzmi
  sztucznie albo go nie słychać; (3) w kabinie silnik jest za głośny względem opon, wiatru i otoczenia.
- W trakcie zadania właściciel dostarczył partię REGEN-02: 28 WAV (turbo, stop w kabinie, wycieraczki, przejazdy).

## 1. „Syrena” — przyczyna i naprawa
Dźwięk z filmu właściciela (`artifacts/audio-fx/owner-video/`, 15,6 s, wyciągnięty przez ffmpeg) ma na spektrogramie
łuki tonu **380 → 900 → 380 Hz** z 2. i 3. harmoniczną. Łuki powtarzają się co **4,0 s** (szczyty 3,8 / 7,8 / 11,8 s).
Między nimi są odcinki **1 kHz** w rytmie 1,25 Hz. Dokładnie tak działa proceduralny **wózek widłowy** z tła
(`sfx_layers.forklift_loop`): sinus silnika trakcyjnego o częstotliwości 380 + 520·prędkość robi 2 manewry na 8 s pętli,
a w fazach cofania gra beeper 1 kHz. Warstwa należy do `AmbientAudio`, więc grała w obu zestawach, niezależnie od obrotów
i prędkości. Przeskan pętli (`tools/audio/siren_scan.py`, ton > 12 dB w > 30 % ramek, ACF obwiedni > 0,45 przy okresie
≥ 1,5 s) oznacza w obu zestawach tylko wózek (ACF 0,55/0,67) i sygnał cofania (gra tylko na biegu R, z założenia rytmiczny).
Turbo, sprężarka i tło: ACF ≤ 0,2.
**Naprawa:** `AmbientAudio.forkliftVolume = 0` (w obu zestawach). Wózek wraca dopiero po przeprojektowaniu
(nieokresowe manewry, bez czystego sinusa) albo z nagraniem. Dowód: `verify/owner_siren_before.png`,
`verify/siren_before_after.png` (film właściciela, tor tła przed zmianą, tor tła po zmianie), `siren_scan.txt`.

## 2. Turbo
- v1 (synteza, nadal w trybie synteza): prawie czysty sinus 3,2 kHz z FM 0,4 %, gain 0,11·boost^1,5.
- **v2 (zestaw ElevenLabs), dwie warstwy w `EngineAudio`:**
  - **gwizd:** `TURBO_WHISTLE_LOOP (6)` z REGEN-02. Linia 2757 Hz, 13,8 dB nad tłem (próg 12), rozrzut 1,7 % (`el_regen02.py`,
    PASS). Linię przestrajam okresowo do 2600 Hz. Wysokość tonu to 0,55 + 0,9·boost (wał turbo kręci się na biegu jałowym),
    gain boost^1,5·(0,35 + 0,65·gaz).
  - **szum wlotu:** synteza (`tools/audio/turbo2.py`), czyli pasmowy szum 2,2/4,6 kHz. Gain ~ przepływ:
    0,15·rpmN + 0,85·boost^1,2·(0,4 + 0,6·rpmN), dodatkowo skalowany gazem.
  - Kabina dostaje wersje prerenderowane filtrem `cab_filter mech` (−15 dB). Na zewnątrz miks 0,10/0,18, w kabinie
    0,20/0,30 tych klipów (`WORKING_VALUE`). Syk upustowy: dalej `TURBO_WASTEGATE (4)` (0137).
  - Podmiana: `el_fx.TURBO = {"whine": "<plik>", "rush": None|"<plik>"}`. Bez nagrania używany jest `turbo2.whine_loop`.
  - Doładowanie: `Engine.Boost` ma w fizyce lag pierwszego rzędu (`boostTimeConstant`). Gwizd nie oscylował,
    nie był przyczyną „syreny”.

## 3. Miks kabina / zewnątrz (zestaw ElevenLabs)
Źródła (poziomy bezwzględne nie zostały znalezione, więc to założenia projektowe `UNVERIFIED`): powyżej ~80 km/h hałas
opona/droga przewyższa w kabinie układ napędowy (Johnson 1996, za: Mohammadi 2022, *Archives of Acoustics* 47(4),
doi:10.24425/aoa.2022.142908). Przy niskich prędkościach i na biegu jałowym dominuje silnik (ta sama praca). Hałas
toczenia dominuje od ~100 km/h na suchej drodze i od ~50 km/h na mokrej (TRL LR601). Docelowo w kabinie przy 80 km/h:
opony ≥ silnik, wiatr kilka dB pod silnikiem, na jałowym prowadzi silnik.
Zmiany (`TruckAudioController.elCab*`, `EngineAudio.CabEngineScale`): silnik w kabinie ×0,7 (−3,1 dB), opony w kabinie
0,55 → 1,35, wiatr 0,35 → 1,45, tło 0,5 → 0,35, żeby na jałowym proporcja silnik/tło była taka jak dotąd (właściciel
chwalił jałowy w kabinie). Wynik z `tools/audio/cab_mix.py` (LUFS klipów × wzmocnienia runtime, `cab_mix.txt`):

| kabina, względem silnika | opony | wiatr | tło |
|---|---|---|---|
| 80 km/h, przed (synteza / 0138) | −9,5 dB | −21,1 dB | −22,1 dB |
| 80 km/h, po (0142) | **+1,4 dB** | **−5,7 dB** | −22,1 dB |
| 50 km/h, przed / po | −16,6 / −5,7 dB | −30,7 / −15,3 dB | −19,9 dB |
| jałowy, przed / po | — | — | −1,3 / −1,3 dB |

Zewnątrz bez zmian. Tryb synteza: dotychczasowe stałe.

## 4. Efekty — co wpięte, skąd, czym sterowane
Przetwarzanie: `tools/audio/el_fx.py` (wybory autorskie z uzasadnieniem liczbowym w kodzie). Kroki: mono, HP 25 Hz, cięcie,
szew 40 ms albo pętla całookresowa, resampling okresowy opon do odniesienia `LayerMath.TyrePitch`, LUFS wg klipu syntezy,
który efekt zastępuje (kabina też), miękki limiter pętli ≤ 4 dB, wersje kabinowe `cab_filter`. Wynik: 43 klipy, 0 FAIL
(szew < 1, szpilka HF < 6 dB, krawędzie, szczyt ≤ −1,5 dBFS), arkusz `verify/fx_sheet.png`.

| zdarzenie (sterowanie) | plik | uwagi |
|---|---|---|
| zwolnienie hamulca (BrakeDemand po ≥ 0,25 s) | BRAKE_SERVICE_HISS (7) | REGEN-01 |
| postojowy zaciąg./zwoln. (Input.ParkingBrake) | AIR_PARKING_APPLY (4) / RELEASE (4) | (1)–(3) to bramkowany szum |
| osuszacz (Air.CompressorLoaded 1→0), naprzemiennie | AIR_DRYER_PURGE (4) / (1) | (2) przesterowany |
| zmiana biegu AMT w górę / w dół (TargetGear vs Gear) | GEAR_UPSHIFT_CAB (6) — tylko klik+klunk (HP 320 Hz + bramka widmowa) / GEAR_DOWNSHIFT_CAB (3) | nagranie w górę zawiera silnik, wycięty |
| sprężarka (CompressorLoaded, ton ~obr.) | AIR_COMPRESSOR_LOOP (2) | rytm 6,6 Hz (ACF 0,39) |
| przekaźnik kierunkowskazu tick/tock (flasher) | CAB_INDICATOR_LOOP (3) | mocny/słaby klik, 90/min |
| przełączniki (zmiana selektora, A/M, dźwigni zwalniacza, tempomatu zjazdu) | CAB_SWITCH (2) | |
| sprzęg siodła (FifthWheel.CouplingEvents) | TRAILER_COUPLE (1) | klunk przy 20 ms |
| wybój (maks. CompressionRate kół > 0,45 m/s, przerwa 0,3 s) | SUSP_BUMP (4) | próg `WORKING_VALUE` |
| sygnał cofania (selektor R, silnik pracuje) | REVERSE_BEEPER_LOOP (4) | 1 okres 1,0 s, szew w przerwie |
| opony: mokra / beton / żwir (ext + kabina) | TYRE_WET_60 (4) / TYRE_PAVERS_20 (2) / TYRE_GRAVEL_15 (3) | bruk, trawa: synteza |
| opony sucha (tylko kabina), wiatr (tylko kabina) | TYRE_ASPHALT_50 (1), AMB_WIND_CAB_80 (3) | zewnątrz: synteza |
| wycie skrzyni (kabina, obciążenie × prędkość) | GEARBOX_WHINE_LOOP (4) | nowa warstwa, 0,10 |
| tło strefy przemysłowej | AMB_INDUSTRIAL_DAY (2) | |
| zgaszenie silnika w kabinie | ENG_STOP_CAB (7) REGEN-02 | wybieg −33,9 dB, zastępuje filtrowany stop zewn. |
| klakson (trzymanie K w labie, przycisk w Ustawieniach) | HORN_AIR (2) | pętla 0,88 s, atak 12 ms, zwolnienie 60 ms |
| drzwi otw./zamk. (`OnDoor`, podgląd w Ustawieniach) | CAB_DOOR_OPEN (7) / CAB_DOOR_CLOSE (1) | brak interakcji drzwi w grze |

Klakson i drzwi grają w obu zestawach, bo synteza nie ma tych dźwięków. Pozostałe nowe zdarzenia (sprzęg, wybój,
przełączniki, cofanie, wycie skrzyni) działają tylko w zestawie ElevenLabs. Tryb synteza zachowuje się jak przed 0142.

**Niewpięte:** `CAB_WIPERS_LOOP`, bo żaden wariant (5)–(12) nie trzyma rytmu (REGEN-02 (11): okres 0,33 s, CV 8,6 %),
a gra nie ma przełącznika wycieraczek. `CAB_RAIN_ROOF_LOOP`: brak pogody. `BRAKE_SQUEAL_STOP`: brak linii pisku.
`BRAKE_ROLL_LOOP`: wybuchy w każdym wariancie. `TRAILER_RATTLE_LOOP`: brak sygnału ładunku i nierówności.
`AMB_PASSING_CAR`: brak ruchu. `AMB_YARD_LOGISTICS`, `TURBO_SPOOL`. Przejazdy REGEN-02 (`ENG_*_SWEEP`): siatka silnika
zostaje jak w 0138 (decyzja właściciela).

## Kod
`VehicleAudioLibrary` (pola `el*`, `HasElevenLabsFx`), `VehicleAudioImporter` (grupa fx), `TruckAudioController`
(`ApplySoundSet` przy starcie i zmianie ustawienia: podmiana klipów `PerspectiveLoop.SetClips`, bez nowych obiektów;
`PlaySet`; `UpdateCues`), `EngineAudio` (turbo v2, `CabEngineScale`), `AmbientAudio.SetBed`, `Game.Core.AudioCues`
(skrzynka UI → audio), Ustawienia: **DŹWIĘK → Zestaw dźwięków: synteza / ElevenLabs** + przyciski Klakson / Drzwi.
Klawisz K w labie trzyma klakson. Przycisk klaksonu na HUD to zadanie dla gameplay-ui. `el_prepare.py` zachowuje
grupę fx przy ponownym uruchomieniu.

## Wyniki
- PlayMode 23/23 (`ElevenLabsFxAudioTests` 4: biblioteka, przełącznik z podmianą klipów i powrotem do syntezy, zdarzenia
  + klakson, **0 B GC** w 300 aktualizacjach `TruckAudioController` + `EngineAudio`; `ElevenLabsEngineAudioTests`,
  `AudioLayersTests`, `ControlSettingsPanel`, `DrivingLabScene`). EditMode audio 20/20. `AudioCuesTests` dopisany po
  przebiegu, jeszcze nieuruchomiony.
- Odsłuchy A/B (≤ 30 s): `artifacts/audio-fx/ab/ab_{pneumatics,cab,loops,turbo}.ogg`.

## Konsekwencje
- RAM: +43 klipy (pętle ADPCM, zdarzenia Vorbis Decompress On Load). Do zmierzenia na A16 (PSS).
- Wszystkie poziomy nowych zdarzeń to `WORKING_VALUE`, do oceny właściciela.
- Licencje: `docs/LICENSES.md` → `audio-elevenlabs-sfx-v3-fx`, `-regen02`, `audio-procedural-turbo2`.
