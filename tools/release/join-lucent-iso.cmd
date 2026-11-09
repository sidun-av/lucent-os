@echo off
rem Lucent OS: double-click this file to join the installer ISO parts in this
rem folder and check them. It runs join-lucent-iso.ps1 (next to this file)
rem with the PowerShell that comes with Windows; nothing to install.
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0join-lucent-iso.ps1" %*
exit /b %ERRORLEVEL%
