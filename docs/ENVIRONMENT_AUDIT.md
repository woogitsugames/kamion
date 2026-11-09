# Environment audit — 2026-11-09

| Item | Value |
|---|---|
| OS | Windows 11 Home 10.0.26300 |
| CPU | Intel Core Ultra 7 270K Plus (24 cores) |
| GPU | NVIDIA GeForce RTX 5070 |
| RAM | 63.7 GB |
| Disk C: | 1.9 TB, 1.1 TB free (project lives here, not OneDrive) |
| Disk G: | 1.9 TB, 990 GB free |
| git / git-lfs | present (Git for Windows) |
| gh | present, authenticated (matmaxalez, admin on woogitsugames/kamion) |
| Python | 3.14 (launcher `py`), `uv` present |
| .NET SDK | present |
| Blender | 4.2.9 LTS (`blender` in PATH) |
| ffmpeg | 9.0.1 essentials (winget) |
| Unity | not installed at audit time → Unity Hub + 6000.3.28f1 (latest 6.3 LTS, released 2026-11-03, from Unity release API) |
| Node, ImageMagick, 7-Zip, scrcpy, adb | missing at audit time → installed via winget |
| Phone | not checked yet (adb was missing) — see DEVICE_MATRIX.md |

Repo note: `woogitsugames/kamion` is **public** (spec D11 says private). Owner decision pending; see STATUS.md.

## Addendum — Stage 0 build-qa, 2026-11-09
- **MSIX AppData virtualisation breaks Unity batchmode licensing.** Unity Hub, the Claude desktop app and Store PowerShell 7 (`C:\Program Files\WindowsApps\Microsoft.PowerShell_7.6.9.0_…`) are MSIX packages; each sees its own `%LOCALAPPDATA%`. The Unity entitlement licence (`Unity\licenses\UnityEntitlementLicense.xml`) existed only in the Hub's and Claude's package stores, so Unity started from `pwsh` exited with code **198** ("No valid Unity Editor license found"). `scripts/env.ps1` (`Repair-UnityLicenseVisibility`) now copies the newest licence of this machine into the view of the calling process once and logs it. Long-term fix for the owner: install PowerShell 7 from the MSI (not the Store) and/or activate the licence from a non-packaged shell (`Unity.exe -batchmode -quit -username … -serial …` is not needed for Personal; signing in via Hub writes into the Hub store only).
- `dotnet --list-sdks` returns nothing: only the .NET 8 **runtime** is installed, not the SDK (the audit row above said "present"). `tools/physics-runner` outside Unity needs the SDK → doctor reports it as WARN.
- Node is installed in `C:\Program Files\nodejs` but was not on PATH of already-running shells; doctor now also looks in standard install dirs.
- Android toolchain = Unity module only: SDK platforms 34/35/36/37, build-tools 36.0.0, NDK r27c (27.2.12479018), OpenJDK 17.0.18.
- Galaxy A16: `stay_on_while_plugged_in=15` (screen stays on while charging), but a **secure lock screen** is set; the app is paused while the keyguard shows. Scripts never enter the PIN — the owner unlocks the phone before measurements.
