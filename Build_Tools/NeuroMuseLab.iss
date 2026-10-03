#define AppVersion GetStringFileInfo("..\NeuroMuseLab\NeuroMuseLab.exe", "ProductVersion")

[Setup]
AppId={{B6473C63-C82B-4E8D-833C-64BCE51B5F09}
AppName=НейроМьюзЛаб
AppVerName=НейроМьюзЛаб {#AppVersion}
AppVersion={#AppVersion}
VersionInfoVersion={#AppVersion}
VersionInfoTextVersion={#AppVersion}
VersionInfoProductVersion={#AppVersion}
VersionInfoProductTextVersion={#AppVersion}
AppPublisher=Frommer-droid
DefaultDirName={code:GetDefaultDir}
UsePreviousAppDir=no
DefaultGroupName=НейроМьюзЛаб
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=NeuroMuseLab_v{#AppVersion}_Setup
SetupIconFile=..\logo.ico
UninstallDisplayIcon={app}\NeuroMuseLab.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=no
LanguageDetectionMethod=none

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные задачи:"

[Files]
Source: "..\NeuroMuseLab\NeuroMuseLab.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\NeuroMuseLab\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\NeuroMuseLab\logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\NeuroMuseLab\VERSION"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\NeuroMuseLab\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "installed.marker"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\НейроМьюзЛаб"; Filename: "{app}\NeuroMuseLab.exe"
Name: "{autodesktop}\НейроМьюзЛаб"; Filename: "{app}\NeuroMuseLab.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\NeuroMuseLab.exe"; Description: "Запустить НейроМьюзЛаб"; Flags: nowait postinstall skipifsilent

[Code]
function GetDefaultDir(Param: string): string;
begin
  if DirExists('D:\') then
    Result := 'D:\Apps\NeuroMuseLab'
  else
    Result := 'C:\Apps\NeuroMuseLab';
end;
