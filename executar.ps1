param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('sem-mitigacao', 'com-mitigacao')]
    [string]$Cenario
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:CENARIO = $Cenario
$env:MITIGACAO = if ($Cenario -eq 'com-mitigacao') { '1' } else { '0' }
$env:EXECUCAO = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString().Substring(0, 8)
$projeto = 'cloudflare-miniatura'
Write-Host "Cenario: $Cenario | Execucao: $env:EXECUCAO"
docker compose -p $projeto up --abort-on-container-exit --exit-code-from cliente
$resultado = $LASTEXITCODE
$pastaLogs = Join-Path $PSScriptRoot "logs/$Cenario/$env:EXECUCAO"
if (-not (Test-Path -LiteralPath $pastaLogs)) {
    New-Item -ItemType Directory -Path $pastaLogs -Force | Out-Null
}
docker compose -p $projeto logs --no-color | Out-File -FilePath (Join-Path $pastaLogs 'containers.log') -Encoding utf8
docker compose -p $projeto down
Write-Host "Logs: $pastaLogs"
if ($resultado -ne 0) { exit $resultado }
