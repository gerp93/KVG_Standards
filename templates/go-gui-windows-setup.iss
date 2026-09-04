; Windows installer for Wails apps shipped by release-go-gui.yml.
; Defines are passed from CI: MyAppName, MyAppVersion (no v), MyAppTag (with v),
; StageDir, OutputDir. PrivilegesRequired=lowest so it installs per-user under
; %LOCALAPPDATA%\Programs with no UAC, and updates can re-run the same setup.
;
; Operator data (games/, backups/) is NOT in {app}. The app keeps that under
; %APPDATA% and never lets this installer replace it. Staged games/ (seed
; deploy.conf only — backups are gitignored) land in {app}\seed\games.

#ifndef MyAppName
  #define MyAppName "app"
#endif
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#ifndef MyAppTag
  #define MyAppTag "v0.0.0"
#endif
#ifndef MyAppExeName
  #define MyAppExeName MyAppName + ".exe"
#endif

[Setup]
AppId=gerp93.{#MyAppName}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=gerp93
AppPublisherURL=https://github.com/gerp93
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename={#MyAppName}-{#MyAppTag}-windows-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=force
RestartApplications=no
; Do not touch %APPDATA% on uninstall — backups live there.
[UninstallDelete]
; none — leave the user's data directory alone

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; App payload: everything except games/. A recursive copy of games/ into
; {app}\games would clobber operator backups if they ever installed into a
; folder that already had a games tree (old zip extracts).
Source: "{#StageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "games,games\*"
; Seed deploy.conf files only — copied into %APPDATA% by the app on first
; run, and only when that game folder does not already exist.
Source: "{#StageDir}\games\*"; DestDir: "{app}\seed\games"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall
