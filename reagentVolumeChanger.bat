@echo off
setlocal
set "current_dir=%~dp0"
rem cd Path\To\Python\Project\reagentVolumeChanger
python reagentChanger.py %current_dir:~0,-1%
endlocal
