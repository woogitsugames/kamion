# orientation (ADR 0147) — STATUS
2026-11-12 19:35 — kod + testy EditMode napisane (ScreenOrientationLock: wymuszenie poziomu dla wydłużonego okna w pionie). Czekam na slot Unity (PHONE_RUN aktywny).
NASTĘPNY KROK: pwsh scripts/unity-slot.ps1 -Acquire -Owner orientation; pwsh scripts/test.ps1 -Platform EditMode -Filter "OrientationPhoneTests|SteerFoldTests"
