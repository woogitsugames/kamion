# STATUS audio-fx (ADR 0142) — agent audio, s13

## 2026-11-12 krok 1: rozpoznanie
- Przejrzane arkusze analizy sekcji B–G (audio-el, audio-regen01), kod TruckAudioController/EngineAudio/AmbientAudio/importer.
- Zdarzenia z fizyki/sterowania już w kodzie: zwolnienie hamulca, postojowy, osuszacz, AMT, kierunkowskaz, opony, wiatr, sprężarka.
- Brak w grze: drzwi, klakson, wycieraczki, deszcz (brak interakcji/pogody) -> API + odsłuch w ustawieniach.
- NASTĘPNY KROK: `cd tools/audio; uv run python el_fx.py` (przetwarzanie wybranych plików C–G).

## krok 2: przetwarzanie efektów (el_fx.py)
- `tools/audio/el_fx.py`: 38 klipów (25 ID źródłowych) -> ElevenLabs/Clips/sfx, grupa "fx" w el_manifest; 0 FAIL (szwy < 1, HF < 6 dB, krawędzie, szczyt ≤ −1,5 dBFS). Arkusz `verify/fx_sheet.png` obejrzany.
- Zakres rozszerzony przez lidera (opinia właściciela o APK 0138): (1) turbo — wiarygodny gwizd od doładowania, cichy w kabinie, syk upustowy; (2) kabina vs zewnątrz — silnik w kabinie ciszej względem opon/wiatru/otoczenia, poziomy z danych dB(A). REGEN-02: łatwa podmiana plików.
- NASTĘPNY KROK: wpięcie w C# (VehicleAudioLibrary, importer, TruckAudioController, AmbientAudio, PerspectiveLoop.SetClips).

## krok 3: C# + błąd „syreny”
- Wpięte: VehicleAudioLibrary (pola el*), importer, TruckAudioController (ApplySoundSet, PlaySet, UpdateCues: sprzęg, wyboje, przełączniki, cofanie, klakson, drzwi, wycie skrzyni), EngineAudio (turbo v2, CabEngineScale), PerspectiveLoop.SetClips/SetMix, AmbientAudio.SetBed, Core/AudioCues, ustawienia (Zestaw dźwięków + odsłuch klakson/drzwi), klawisz K = klakson.
- SYRENA: film właściciela -> łuki 380→900→380 Hz z harmonicznymi, okres 4,0 s + piski 1 kHz = proceduralny wózek widłowy (sfx_layers.forklift_loop: sinus silnika 380+520·speed, 2 manewry/8 s, beeper 1,25 Hz). Obecny w obu zestawach. Naprawa: AmbientAudio.forkliftVolume = 0. Dowód: verify/owner_siren_before.png, verify/siren_before_after.png, siren_scan.txt.
- NASTĘPNY KROK: `pwsh scripts/unity-slot.ps1 -Acquire -Owner claude-audio-fx` (czeka na PHONE_RUN) -> import audio + testy PlayMode/EditMode.

## krok 4: REGEN-02, testy, ADR, merge
- REGEN-02: turbo (6) PASS -> gwizd v2; stop kabina (7) PASS -> el_engine_stop_cab_r02; wycieraczki FAIL; przejazdy pominięte (siatka bez zmian).
- Unity: import OK, PlayMode audio 23/23, EditMode audio 20/20 (AudioCuesTests dopisany, nieuruchomiony). A/B: ab/*.ogg (4 × ≤ 30 s).
- ADR 0142, LICENSES (3 wiersze), docs/08. Merge main 7068123a bez konfliktów (main nie dotykał audio).
- Film właściciela i montaże robocze wyjęte z gita (tylko lokalnie + kopia w main/artifacts/audio-fx).
- NASTĘPNY KROK (lider): `git merge audio-fx` w main; APK; odsłuch właściciela (Ustawienia → DŹWIĘK → Zestaw dźwięków; Klakson/Drzwi; klawisz K); opcjonalnie `pwsh scripts/test.ps1 -Platform EditMode -Filter AudioCues`.
