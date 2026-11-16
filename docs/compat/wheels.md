# Zgodność kierownic i pedałów PC (ADR 0263)

Dokument roboczy. Nazwy producentów i modeli występują **tylko tutaj i w profilu danych** (`game/Assets/_Project/Input/Resources/Controls/wheel_profiles.json`) — gra nie pokazuje marek ani logo (HUD: „kierownica”). Bez SDK producentów.

## Jak gra widzi kierownicę
- Unity Input System (1.20.1 w projekcie) tworzy automatycznie urządzenie `Joystick` dla HID z usage `GenericDesktop/Joystick`, `Gamepad` lub `MultiAxisController`; pierwsze osie X/Y = `stick`, reszta wg nazw HID (`z`, `rz`, `slider`, `button1`… ). Źródło: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.11/manual/HID.html. Układy automatyczne są „best effort” — dlatego ścieżki w profilach są **UNVERIFIED** do czasu sprawdzenia na urządzeniu.
- Dopasowanie profilu: VID+PID → fragment nazwy produktu (z tym samym VID) → profil „tylko producent” → `generic`. Gracz może wymusić profil (`WheelSettings.profileOverride`).
- Bez kalibracji: pierwszy odczyt = środek kierownicy / pedał zwolniony, zakres uczony z ruchu. Kalibracja z kreatora (min/max/środek, odwrócenie, martwe strefy) jest zapisywana per profil w PlayerPrefs `controls.wheel`.
- Zakres obrotu w grze 270–900° (nie więcej niż obraca urządzenie). Jeżeli sterownik producenta ustawia mniejszy zakres sprzętowy, trzeba go wpisać jako zakres urządzenia (kreator / `deviceRangeDeg`), inaczej kąty będą przeskalowane.

## Tabela urządzeń
| profil | urządzenie | VID | PID | źródło ID | zakres sprzętowy | mapowanie osi/przycisków | FFB w grze |
|---|---|---|---|---|---|---|---|
| `lg-g29` | Logitech G29 | 0x046d | 0xc24f | Linux `drivers/hid/hid-ids.h` | 900° WORKING_VALUE (dane producenta, niesprawdzone) | UNVERIFIED | brak backendu (Null) |
| `lg-g920` | Logitech G920 | 0x046d | 0xc262 | `hid-ids.h` | 900° WORKING_VALUE | UNVERIFIED; czy Windows bez sterownika producenta pokazuje go jako HID-joystick — UNVERIFIED | brak backendu |
| `lg-g923` | Logitech G923 (Xbox/PC) | 0x046d | 0xc26e | `hid-ids.h` | 900° WORKING_VALUE | UNVERIFIED | brak backendu |
| `lg-g923` | Logitech G923 (PS/PC) | 0x046d | UNVERIFIED (dopasowanie po nazwie „G923”) | — | 900° WORKING_VALUE | UNVERIFIED | brak backendu |
| `tm-t300` | Thrustmaster T300 RS (warianty) | 0x044f | 0xb66d, 0xb66e, 0xb66f | `hid-ids.h` (VID), `hid-tmff2/src/hid-tmff2.h` (PID) | 900° WORKING_VALUE | UNVERIFIED | brak backendu |
| `tm-t150` | Thrustmaster T150 | 0x044f | UNVERIFIED (dopasowanie po nazwie „T150”) | — | 1080° WORKING_VALUE | UNVERIFIED | brak backendu |
| `ft-csl` | Fanatec CSL DD / CSL Elite / CSL Elite PS4 (baza) | 0x0eb7 | 0x0020, 0x0e03, 0x0005 | `hid-fanatecff/hid-ftec.h` | 1080° WORKING_VALUE | UNVERIFIED; pedały CSL to osobne USB (0x6204–0x6206) — wymagają drugiego źródła wejścia (propozycja) | brak backendu |
| `generic` | dowolna kierownica HID | — | — | — | 900° WORKING_VALUE | `stick/x` kierownica, reszta przez kreator | brak backendu |

Źródła ID (tylko liczby, kod GPL nie kopiowany):
- https://github.com/torvalds/linux/blob/master/drivers/hid/hid-ids.h (GPL-2.0)
- https://github.com/Kimplul/hid-tmff2 (GPL-2.0)
- https://github.com/gotzl/hid-fanatecff (GPL-2.0)
- Thrustmaster: Linux `hid-thrustmaster.c` rozpoznaje T150RS/T300RS po kodzie modelu, nie po PID: https://github.com/torvalds/linux/blob/master/drivers/hid/hid-thrustmaster.c

## Znane ograniczenia (v1)
- **FFB**: model sił w grze gotowy (`ForceFeedbackModel`), wyjście do urządzenia czeka na natywny backend (ADR 0263: SDL3 → Windows.Gaming.Input → surowe HID). Do tego czasu kierownica działa jak bez FFB (sterownik urządzenia zwykle trzyma własną sprężynę centrującą).
- **Pedały łączone na jednej osi** (stare tryby sterowników): gaz i hamulec wciśnięte naraz są nierozróżnialne.
- **H-shifter**: bieg absolutny przekazywany jako `TargetGear`, ale AMT przyjmuje dziś tylko zmianę o 1 na zbocze — przeskok 4→2 zmieni bieg o 1 (propozycja dla fizyki).
- **Sprzęgło** czytane (`DriverIntent.Clutch`), fizyka go jeszcze nie używa (AMT ze sprzęgłem automatycznym).
- **Wiele urządzeń USB** (osobne pedały/shifter): v1 obsługuje jedno urządzenie na profil.
- Gamepad: przygotowany w Input System, nieimplementowany (zgodnie z zakresem).

## Jak zweryfikować urządzenie (właściciel / lider, Windows)
1. Podłącz kierownicę, uruchom grę (edytor lub build), w konsoli Input Debugger (`Window > Analysis > Input Debugger`) odczytaj nazwy kontrolek i VID/PID (`capabilities`).
2. Popraw ścieżki w profilu (`wheel_profiles.json`), ustaw `"status": "VERIFIED"`, `calibrated: true` dla osi z wpisanymi wartościami min/max.
3. Sprawdź kierunek: obrót w prawo → kierownica w kabinie w prawo, ciężarówka skręca w prawo (test automatyczny kierunku: `PcWheelInputTests.Direction_RightRimGivesPositiveSteerInEveryMapping`).
4. Zapisz wynik w tej tabeli (data, wersja sterownika, tryb sterownika).
