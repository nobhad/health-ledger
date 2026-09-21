<#
    Build HealthLedger.exe and wrap it in a .zip for download.

        powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1

    Output: dist\HealthLedger-<version>-windows-x64.zip

    The build uses its own virtual environment (build\venv) so the project's
    venv, which has the test tooling and WeasyPrint in it, cannot leak into
    the bundle.
#>
$ErrorActionPreference = 'Stop'

Set-Location (Join-Path $PSScriptRoot '..')
$Root = (Get-Location).Path
$BuildVenv = Join-Path $Root 'build\venv'
$Py = Join-Path $BuildVenv 'Scripts\python.exe'

$configText = Get-Content -Raw (Join-Path $Root 'config.py')
$Version = [regex]::Match($configText, '(?m)^APP_VERSION\s*=\s*["''](.+?)["'']').Groups[1].Value
$ZipName = "HealthLedger-$Version-windows-x64"

Write-Host "==> Health Ledger $Version for Windows (x64)"

if (-not (Test-Path $Py)) {
    Write-Host '==> Creating the build environment in build\venv'
    python -m venv $BuildVenv
}

Write-Host '==> Installing build requirements'
& $Py -m pip install -q --disable-pip-version-check --upgrade pip
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'build') | Out-Null
# WeasyPrint is stripped from the runtime list: the bundle cannot carry its
# GTK libraries, and the app falls back to the browser's print dialog.
$runtimeReqs = Join-Path $Root 'build\requirements-runtime.txt'
Get-Content (Join-Path $Root 'requirements.txt') |
    Where-Object { $_ -notmatch '^(?i)weasyprint' } |
    Set-Content $runtimeReqs
& $Py -m pip install -q --disable-pip-version-check -r $runtimeReqs -r (Join-Path $Root 'packaging\requirements-build.txt')

Write-Host '==> Drawing the icons'
& $Py (Join-Path $Root 'packaging\make_icons.py') --no-render

Write-Host '==> Building the executable'
$DistApp = Join-Path $Root 'dist\HealthLedger'
if (Test-Path $DistApp) { Remove-Item -Recurse -Force $DistApp }
& $Py -m PyInstaller (Join-Path $Root 'packaging\health_ledger.spec') --noconfirm `
    --distpath (Join-Path $Root 'dist') --workpath (Join-Path $Root 'build\pyinstaller')

if (-not (Test-Path (Join-Path $DistApp 'HealthLedger.exe'))) {
    throw "Build produced no executable at $DistApp\HealthLedger.exe"
}

Write-Host '==> Building the zip'
Copy-Item (Join-Path $Root 'LICENSE') (Join-Path $DistApp 'LICENSE.txt') -ErrorAction SilentlyContinue
$Zip = Join-Path $Root "dist\$ZipName.zip"
if (Test-Path $Zip) { Remove-Item -Force $Zip }
Compress-Archive -Path $DistApp -DestinationPath $Zip

Write-Host ''
Write-Host "==> Done: dist\$ZipName.zip"
$size = [math]::Round((Get-Item $Zip).Length / 1MB, 1)
Write-Host "    size: $size MB"
Write-Host ''
Write-Host '    The executable is not code-signed, so SmartScreen shows'
Write-Host '    "More info -> Run anyway" on the first launch. INSTALL.md says so.'
