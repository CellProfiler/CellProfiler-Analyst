; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{4390bf18-af8c-44ce-85e9-66be314fdb5e}
AppName=CellProfilerAnalyst
#include "version.iss"
AppPublisher=Broad Institute
AppPublisherURL=http://www.cellprofiler.org
AppSupportURL=http://www.cellprofiler.org
AppUpdatesURL=http://www.cellprofiler.org
DefaultDirName={pf}\CellProfilerAnalyst
DefaultGroupName=CellProfilerAnalyst
OutputDir=.\output
SetupIconFile=.\icons\cpa.ico
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: ".\dist\cpa.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\vcredist_x86.exe"; DestDir: "{tmp}"
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\CellProfilerAnalyst"; Filename: "{app}\cpa.exe"; WorkingDir: "{app}"
Name: "{group}\{cm:ProgramOnTheWeb,CellProfilerAnalyst}"; Filename: "http://www.cellprofiler.org"
Name: "{group}\{cm:UninstallProgram,CellProfilerAnalyst}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\CellProfilerAnalyst"; Filename: "{app}\cpa.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{tmp}\vcredist_x86.exe"; Parameters: "/q"
Filename: "{app}\cpa.exe"; Description: "{cm:LaunchProgram,CellProfilerAnalyst}"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"
