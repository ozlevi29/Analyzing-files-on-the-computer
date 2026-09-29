@echo off
rem Runs the tool with administrator rights (needed to clean Windows system folders).
powershell -NoProfile -Command "Start-Process -FilePath '%~dp0start.bat' -Verb RunAs"
