$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'web/node_modules/three'))) {
    & npm ci --prefix (Join-Path $projectRoot 'web')
    if ($LASTEXITCODE -ne 0) { throw 'npm ci failed' }
}
& wsl -d Ubuntu-D -- python3 /mnt/d/openvela/tools/start_final_demo.py
exit $LASTEXITCODE
