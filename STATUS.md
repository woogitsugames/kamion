# STATUS neon-hvfar-s24 (kratownice i przewody WN w dalekim planie; dopisek do ADR 0351)

- Worktree `neon-hvfar-s24`, gałąź `neon-hvfar-s24`. Nie scalane ani nie pushowane.
- [krok 1] Zbadano przyczyny „szarej siatki” (ADR 0351, `far_field.py`, `WorldSurface.shader`, zrzuty build #10 i `hv-wires-s24`):
  - Kompresja radialna zgniata pary wież do 1,6–15 m (`knyszyn-w`: 1,6 m przy d=3,5 km; `dk65-07`: 10,2 m przy d=2,4 km), przy `scale = max(s_h, 0.65)` i 12 poziomych prętach pierścieniowych + 3 poziomach ramion (222 tri/wieża).
  - 7 nieprzezroczystych wstęg przewodów (`FAR_WIRE_PX_FRAC = 0.6`, ~40 cm przy 550 m) bez zanikania z odległością + 245 przęseł SN do 600 m tworzy poziome pasmo siatki na horyzoncie.
  - Odpięto junction `Data/raw/derived` (`cmd /c rmdir`), skopiowano prywatnie `knyszyn-w` i `dk65-07` oraz bazowe sceny Win64 (`knyszyn-w`, `dk65-07` i sąsiedzi `-Neighbours auto`) do lokalnego `game/Assets/_Generated/World/`.
- NASTĘPNY KROK: zająć slot Unity i wyrenderować klatki PRZED (High PC 1920×1080 clear + overcast, `-Neighbours auto` + `none` dla `hv0351-*`):
  `pwsh scripts/unity-slot.ps1 -Acquire -Owner neon-hvfar-s24 && pwsh scripts/visual-qa.ps1 -Scene World_knyszyn-w_High -Width 1920 -Height 1080 -Tier High -Pc -BuildTarget Win64 -Lighting clear -Neighbours auto -Cameras "hv0351-seam-n,hv0351-far-ne,edge-north,edge-east,edge-south,edge-west,cab-view-b-fov70,dk65-fields-nw" -OutputDir artifacts/neon-hvfar-s24/before/knyszyn-w-clear`
