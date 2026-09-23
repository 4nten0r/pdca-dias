# Script para iniciar o site local de cadastro do PDCA
$playwrightNode = "$env:LOCALAPPDATA\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\playwright\driver\node.exe"

if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "Iniciando site.js com o Node do sistema..." -ForegroundColor Cyan
    node site.js
} elseif (Test-Path $playwrightNode) {
    Write-Host "Iniciando site.js com o Node detectado no sistema..." -ForegroundColor Green
    & $playwrightNode site.js
} else {
    Write-Host "Iniciando formulário em Python nativo (site.py)..." -ForegroundColor Yellow
    python site.py
}

