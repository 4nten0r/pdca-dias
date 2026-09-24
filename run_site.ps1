# Script para iniciar o site (Node.js) de cadastro das tratativas do PDCA
$playwrightNode = "$env:LOCALAPPDATA\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\playwright\driver\node.exe"

if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "Iniciando site.js com o Node do sistema..." -ForegroundColor Cyan
    node site.js
} elseif (Test-Path $playwrightNode) {
    Write-Host "Iniciando site.js com o Node detectado no sistema..." -ForegroundColor Green
    & $playwrightNode site.js
} else {
    Write-Host "Node.js nao encontrado no PATH. Instale o Node (https://nodejs.org) para rodar o site.js." -ForegroundColor Red
}

