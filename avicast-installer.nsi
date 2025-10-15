; AVICAST Wildlife Monitoring System Installer Script
; NSIS (Nullsoft Scriptable Install System) Installer

!define PRODUCT_NAME "AVICAST Wildlife Monitoring System"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "AVICAST Development Team"
!define PRODUCT_WEB_SITE "https://github.com/your-org/platform-avicast"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\AVICAST.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; MUI (Modern UI) Configuration
!include "MUI2.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Welcome page
!insertmacro MUI_PAGE_WELCOME

; License page
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"

; Directory page
!insertmacro MUI_PAGE_DIRECTORY

; Instfiles page
!insertmacro MUI_PAGE_INSTFILES

; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\start-avicast.bat"
!define MUI_FINISHPAGE_RUN_TEXT "Start AVICAST System"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "AVICAST-Setup-${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES\AVICAST"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

; Request application privileges for Windows Vista
RequestExecutionLevel admin

; Version Information
VIProductVersion "${PRODUCT_VERSION}.0"
VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey "Comments" "Wildlife Monitoring and Analytics Platform"
VIAddVersionKey "CompanyName" "${PRODUCT_PUBLISHER}"
VIAddVersionKey "LegalCopyright" "© 2024 AVICAST Development Team"
VIAddVersionKey "FileDescription" "${PRODUCT_NAME} Installer"
VIAddVersionKey "FileVersion" "${PRODUCT_VERSION}"

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  
  ; Main executable
  File "dist\AVICAST.exe"
  
  ; Application files
  File /r "templates"
  File /r "static"
  File /r "apps"
  File /r "avicast_project"
  File /r "management"
  File /r "scripts"
  File /r "tools"
  File /r "config"
  File /r "tests"
  
  ; Configuration files
  File "env.example"
  File "requirements.txt"
  File "requirements-processing.txt"
  File "requirements-dev.txt"
  File "pyproject.toml"
  File "CHANGELOG.md"
  File "AGENTS.md"
  
  ; Create directories
  CreateDirectory "$INSTDIR\media"
  CreateDirectory "$INSTDIR\staticfiles"
  CreateDirectory "$INSTDIR\logs"
  CreateDirectory "$INSTDIR\backups"
  
  ; Startup script
  File "start-avicast.bat"
  
  ; Uninstaller
  File "uninstall.bat"
  
  ; Documentation
  File /r "docs"
  File "README.md"
  
  ; Create desktop shortcut
  CreateShortCut "$DESKTOP\AVICAST.lnk" "$INSTDIR\start-avicast.bat" "" "$INSTDIR\AVICAST.exe" 0
  
  ; Create start menu shortcuts
  CreateDirectory "$SMPROGRAMS\AVICAST"
  CreateShortCut "$SMPROGRAMS\AVICAST\AVICAST.lnk" "$INSTDIR\start-avicast.bat" "" "$INSTDIR\AVICAST.exe" 0
  CreateShortCut "$SMPROGRAMS\AVICAST\Uninstall.lnk" "$INSTDIR\uninstall.bat" "" "$INSTDIR\AVICAST.exe" 0
  CreateShortCut "$SMPROGRAMS\AVICAST\Documentation.lnk" "$INSTDIR\docs\README.md" "" "$INSTDIR\docs\README.md" 0

SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\AVICAST\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\AVICAST\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\AVICAST.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\AVICAST.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd

Section Uninstall
  ; Stop any running processes
  ExecWait 'taskkill /f /im AVICAST.exe' $0
  
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\start-avicast.bat"
  Delete "$INSTDIR\uninstall.bat"
  Delete "$INSTDIR\AVICAST.exe"
  
  ; Remove directories
  RMDir /r "$INSTDIR\templates"
  RMDir /r "$INSTDIR\static"
  RMDir /r "$INSTDIR\apps"
  RMDir /r "$INSTDIR\avicast_project"
  RMDir /r "$INSTDIR\management"
  RMDir /r "$INSTDIR\scripts"
  RMDir /r "$INSTDIR\tools"
  RMDir /r "$INSTDIR\config"
  RMDir /r "$INSTDIR\tests"
  RMDir /r "$INSTDIR\docs"
  RMDir /r "$INSTDIR\media"
  RMDir /r "$INSTDIR\staticfiles"
  RMDir /r "$INSTDIR\logs"
  RMDir /r "$INSTDIR\backups"
  
  ; Configuration files
  Delete "$INSTDIR\env.example"
  Delete "$INSTDIR\requirements.txt"
  Delete "$INSTDIR\requirements-processing.txt"
  Delete "$INSTDIR\requirements-dev.txt"
  Delete "$INSTDIR\pyproject.toml"
  Delete "$INSTDIR\CHANGELOG.md"
  Delete "$INSTDIR\AGENTS.md"
  Delete "$INSTDIR\README.md"
  
  ; Remove shortcuts
  Delete "$DESKTOP\AVICAST.lnk"
  Delete "$SMPROGRAMS\AVICAST\AVICAST.lnk"
  Delete "$SMPROGRAMS\AVICAST\Uninstall.lnk"
  Delete "$SMPROGRAMS\AVICAST\Website.lnk"
  Delete "$SMPROGRAMS\AVICAST\Documentation.lnk"
  
  RMDir "$SMPROGRAMS\AVICAST"
  RMDir "$INSTDIR"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd
