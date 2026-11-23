# ADR 0328 — Głos nawigacji GPS „Kamion GPS” (ElevenLabs Voice Design + TTS) i odtwarzacz w kabinie

Status: propozycja (gałąź `gps-voice-s24`, nie scalone). Zgoda właściciela: 2026-11-23 (czat z liderem) — jeden głos z
Voice Design + paczka komunikatów z `docs/owner/ELEVENLABS-GPS-VOICE.md`, nic poza tym.

## Kontekst

`NavVoice` / `NavVoiceDriver` / `NavVoiceAnnouncer` (ADR 0150, 0168, navlog s24) wybierają zdania pakietu GPS_Bxx #i
i wołają hak `NavVoiceAnnouncer.Spoken`, ale gra nie miała ani nagrań, ani odtwarzacza.

## Decyzja

1. **Głos:** Voice Design (`eleven_multilingual_ttv_v2`, seed 2411) z opisu prompt packa (spokojna, wyraźna polska
   lektorka ok. 35 lat, sucho, bez pogłosu). Z 3 podglądów wybrany obiektywnie (`tools/audio/gps/voice_qa.py`): #3 —
   pełne pasmo, cyfrowa cisza między zdaniami, F0 ok. 208 Hz; odrzucone: #2 (pasmo obcięte do 4,5 kHz + szum),
   #1 (pasmo 8,5 kHz). Zapisany jako „Kamion GPS”. Ocena brzmienia należy do właściciela (próbki w
   `artifacts/gps-voice-s24/demo/`).
2. **Zakres paczki = to, co kod zleca:** 96 zdań (B01–B05 ×8, B06 ×10, B07 ×7, B08 ×7, B09 ×5, B10 #5 i #11, B12 ×12,
   B13 ×11, B14 ×2; `tools/audio/gps/pack.py`). Nieużywane zdania prompt packa (B01 #9, reszta B10, B11) nie są
   generowane, dopóki kod ich nie zleca. Jedna wersja zamiast dwóch (oszczędność kredytów).
3. **Generacja:** TTS Multilingual v2, partie zdań rozdzielone `<break time="1.5s" />`, cięcie po ciszy z kontrolą liczby
   zdań. Kontrola tempa mowy (sylaby/s, `MAX_SYL_PER_S = 8`, `WORKING_VALUE`) wykryła partię B12 z połkniętymi słowami
   (9–11 sylab/s): B12 #2–#9 wygenerowane ponownie pojedynczo, #1 z próbki testowej. Konektor nie udostępnia ustawień
   stability/similarity — użyte domyślne ustawienia głosu (inaczej niż tabela §2 prompt packa). Format źródła: MP3 128 kb/s
   44,1 kHz (WAV niedostępny przez konektor).
4. **Obróbka:** −16 LUFS na klip (docs/08, `WORKING_VALUE`; rozrzut zmierzony 0,86 LU), limiter look-ahead do −1 dBFS,
   margines 40 ms i zanik 5 ms (brak kliknięć: próbki brzegowe = 0). Klipy: `game/Assets/_Project/Audio/Voice/Gps/`
   (LFS), manifest `Audio/Voice/gps_manifest.json` (tekst, plik, sha256, id generacji, głos, model, LUFS).
5. **Import (zasada 7):** `Game.Editor.Audio.GpsVoiceImporter` buduje `NavVoiceBank`
   (`Audio/Generated/Resources/GpsVoice/`, poza gitem) z manifestu; wołany z `VehicleAudioImporter.ImportIfNeeded`
   (czyli przed każdym buildem). Ustawienia importu: mono, Decompress On Load, Android Vorbis 0,6, Windows PCM (ADR 0286);
   osobny postprocesor (`GpsVoicePostprocessor`) — klipy nie leżą pod `ElevenLabs/Clips`, żeby nie dziedziczyć reguł pętli
   silnika.
6. **Odtwarzanie:** `NavVoicePlayer` (Game.Core.Navigation — `Game.Audio` nie widzi `Game.Core`, a zmiana asmdef należy do
   lidera): jedno AudioSource 2D (głośnik radia w kabinie), priorytet 16, głośność `Volume × AudioMixLevels.Ui` (brak
   miksera w projekcie, ADR 0270). Kolejka `NavVoiceClipQueue`: klipy komunikatu po kolei z przerwą 80 ms, komunikaty
   nigdy się nie nakładają (≥ 0,6 s przerwy); komunikat, który jeszcze nie zaczął mówić, jest zastępowany nowszym, a ten,
   który mówi, kończy się. Zero alokacji na klatkę. Podpięcie: `NavigationInstaller` → `NavVoicePlayer.Install(host, nav.Voice)`.

## Konsekwencje

- Gra mówi po polsku na trasie; brak banku = cisza + jedno ostrzeżenie.
- `Duck01` (0..1) jest wystawione, ale ściszanie silnika i wyłącznik w ustawieniach nie są jeszcze podpięte (osobne zadanie:
  TruckAudioController + panel ustawień).
- Zauważone w kodzie nawigacji (nie zmieniane): dla `Maneuver.Arrive` `PlanBand` mówi „Jesteś u celu” już w paśmie dalekim
  (np. 500 m przed celem), a po manewrze rondowym słychać „Na rondzie zjedź …” + „na rondzie Putry” (dwa razy „na
  rondzie”). Do decyzji nawigacji.
- Warunki szczegółowe Voice Design/TTS: `UNVERIFIED` (docs/LICENSES.md, `audio-elevenlabs-tts-gps-voice`).
