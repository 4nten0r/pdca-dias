@echo off
setlocal
set "PLAYWRIGHT_NODE=%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\playwright\driver\node.exe"

where node >nul 2>nul
if %errorlevel% equ 0 (
    echo Iniciando site.js com o Node do sistema...
    node site.js
) else if exist "%PLAYWRIGHT_NODE%" (
    echo Iniciando site.js com o Node detectado no sistema...
    "%PLAYWRIGHT_NODE%" site.js
) else (
    echo Node.js nao encontrado. Instale o Node ^(https://nodejs.org^) para rodar o site.js.
)
pause

