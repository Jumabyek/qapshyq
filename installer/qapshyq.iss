; ---------------------------------------------------------------------------
;  Inno Setup script: turns dist\Qapshyq\ into one Qapshyq-Setup-x.y.z.exe
;  Build:  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\qapshyq.iss
;  (scripts\build_windows.bat does this for you)
; ---------------------------------------------------------------------------
#define AppName "Qapshyq"
#define AppVersion "1.0.0"
#define AppPublisher "Qapshyq"
#define AppURL "https://github.com/Jumabyek/qapshyq"
#define AppExe "Qapshyq.exe"

[Setup]
; Unique ID of this app - never change it after the first public release.
AppId={{203D6CE5-885D-4E09-9505-60A7F9A91B11}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=Qapshyq-Setup-{#AppVersion}
SetupIconFile=..\assets\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Let the user choose "only for me" (no admin rights needed) or "for everyone".
PrivilegesRequiredOverridesAllowed=dialog
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "openwith"; Description: "Add Qapshyq to ""Open with"" for .zip, .rar, .7z, .tar, .gz"; GroupDescription: "File types:"

[Files]
Source: "..\dist\Qapshyq\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; One "Qapshyq.Archive" file type, then listed under "Open with" for each extension.
; This does NOT take over the default app - Windows lets the user decide.
Root: HKA; Subkey: "Software\Classes\Qapshyq.Archive"; ValueType: string; ValueName: ""; ValueData: "Archive"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Qapshyq.Archive\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExe},0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Qapshyq.Archive\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.zip\OpenWithProgids"; ValueType: string; ValueName: "Qapshyq.Archive"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.rar\OpenWithProgids"; ValueType: string; ValueName: "Qapshyq.Archive"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.7z\OpenWithProgids"; ValueType: string; ValueName: "Qapshyq.Archive"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.tar\OpenWithProgids"; ValueType: string; ValueName: "Qapshyq.Archive"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.gz\OpenWithProgids"; ValueType: string; ValueName: "Qapshyq.Archive"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
