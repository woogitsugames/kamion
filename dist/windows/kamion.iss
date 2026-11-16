; Inno Setup script template for the Kamion Windows player (ADR 0271). NOT used by default — the default
; distribution is the zip from scripts/package-windows.py. Not compiled or tested in this repository.
;
; Licence note (docs/12_DYSTRYBUCJA_PC.md §3): Inno Setup's LICENSE.TXT permits any use incl. commercial, but since
; 6.5.0 the author REQUESTS (not requires) that commercial users buy a licence (jrsoftware.org/isorder.php, 2026-11-15).
; Use it only after the owner decides. Compile (Windows, Inno Setup 6.x):
;   iscc /DAppVersion=0.1.0 /DAppSha=4ee3e02626 /DSourceDir="..\..\artifacts\dist\kamion-0.1.0-4ee3e02626-win64" dist\windows\kamion.iss
; SourceDir = the folder unpacked from the package zip (already without *_DoNotShip, *.pdb, build metadata).

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef AppSha
  #define AppSha "0000000"
#endif
#ifndef SourceDir
  #error Pass /DSourceDir=<unpacked package folder>
#endif

[Setup]
; AppId must stay constant for the life of the product (upgrades/uninstall). Generated once for this template.
AppId={{6F0C6E1B-3F4A-4E8B-9C55-2B7D0A1E7C42}
AppName=Kamion
AppVersion={#AppVersion}
AppVerName=Kamion {#AppVersion} ({#AppSha})
AppPublisher=woogitsugames
DefaultDirName={autopf}\Kamion
DefaultGroupName=Kamion
DisableProgramGroupPage=yes
; Per-user install by default (no admin prompt); the user can still choose all users.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19043
OutputDir=..\..\artifacts\dist
OutputBaseFilename=kamion-{#AppVersion}-{#AppSha}-win64-setup
Compression=lzma2/max
SolidCompression=no
; Unity *.unity3d / *.resS data is already compressed (LZ4HC); solid LZMA mostly costs time on a ~5 GB payload.
DiskSpanning=no
; No EULA page (LicenseFile) until the owner has one; notices are shown as information, not as an agreement.
InfoBeforeFile={#SourceDir}\README.txt
InfoAfterFile={#SourceDir}\THIRD_PARTY_NOTICES.txt
UninstallDisplayIcon={app}\Kamion.exe
WizardStyle=modern

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Kamion"; Filename: "{app}\Kamion.exe"
Name: "{autoprograms}\Kamion - zbierz logi"; Filename: "{app}\Zbierz-logi.cmd"
Name: "{autodesktop}\Kamion"; Filename: "{app}\Kamion.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\Kamion.exe"; Description: "{cm:LaunchProgram,Kamion}"; Flags: nowait postinstall skipifsilent

; Player.log and settings live in %USERPROFILE%\AppData\LocalLow\woogitsugames\Kamion and are kept on uninstall
; on purpose (saves/settings). Do not add [UninstallDelete] for that folder without an owner decision.
