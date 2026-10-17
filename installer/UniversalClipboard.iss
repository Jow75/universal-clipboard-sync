; Script generated for Universal Clipboard Sync Windows Installer
#define MyAppName "Universal Clipboard Sync"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "BAZIQHUE"
#define MyAppURL "https://baziqhue.co.ke/"
#define MyAppUpdatesURL "https://universal-clipboard.netlify.app/"
#define MyAppSupportURL "mailto:gmuraguri75@gmail.com"
#define MyAppExeName "UniversalClipboard.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{5D8B4D68-9A77-4C3D-8BC3-B1B918CE4D5E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppSupportURL}
AppUpdatesURL={#MyAppUpdatesURL}
VersionInfoCompany=BAZIQHUE
VersionInfoDescription=Universal Clipboard Sync Setup Wizard
VersionInfoVersion=1.1.0.0
VersionInfoProductName=Universal Clipboard Sync
VersionInfoProductVersion=1.1.0
VersionInfoCopyright=Copyright (C) 2026 BAZIQHUE. All rights reserved.
DefaultDirName={autopf}\UniversalClipboard
DisableDirPage=no
DisableProgramGroupPage=yes
; Per-user install allows installation without administrator privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=UniversalClipboard-Setup-1.1.0
SetupIconFile=..\desktop\assets\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\desktop\assets\icon.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; NOTE: Do NOT delete %APPDATA%\UniversalClipboard\config.json during uninstall to preserve user keys and pairing
Type: files; Name: "{app}\*.log"
