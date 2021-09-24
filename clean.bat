@echo off

del /F /Q "setup.inf"
del /F /Q "setup.rpt"
del /F /Q "out\*"
del /F /Q "data\*.dll"
del /F /Q "srv\*"
xcopy /Y /Q "template\index.html" "srv\"
