# ---------------------------------------------------------------------------
#  Package dist\Qapshyq (made by PyInstaller) as an MSIX for the Microsoft Store.
#  The package is left unsigned: the Store signs it for free after upload.
#  Usage (after scripts\build_windows.bat):
#      powershell -ExecutionPolicy Bypass -File scripts\build_msix.ps1
#  Result: dist\Qapshyq-<version>.msix
# ---------------------------------------------------------------------------
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

# --- Inputs ------------------------------------------------------------------
$identity = Get-Content "installer\msix\store-identity.json" -Raw | ConvertFrom-Json
$appVersion = (Select-String -Path "app\__init__.py" -Pattern '__version__ = "([\d.]+)"').Matches[0].Groups[1].Value
$msixVersion = "$appVersion.0"          # MSIX needs 4 parts; the Store requires the last one to be 0
if (-not (Test-Path "dist\Qapshyq\Qapshyq.exe")) { throw "Build the app first: scripts\build_windows.bat" }

# --- Stage the package folder --------------------------------------------------
$stage = Join-Path $root "build\msix"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
Copy-Item "dist\Qapshyq" $stage -Recurse
Copy-Item "installer\msix\Assets" (Join-Path $stage "Assets") -Recurse

$manifest = Get-Content "installer\msix\AppxManifest.template.xml" -Raw
$manifest = $manifest.Replace("{{IDENTITY_NAME}}", $identity.identity_name)
$manifest = $manifest.Replace("{{PUBLISHER}}", $identity.publisher)
$manifest = $manifest.Replace("{{PUBLISHER_DISPLAY_NAME}}", $identity.publisher_display_name)
$manifest = $manifest.Replace("{{VERSION}}", $msixVersion)
[IO.File]::WriteAllText((Join-Path $stage "AppxManifest.xml"), $manifest, (New-Object Text.UTF8Encoding $false))

# --- Pack with makeappx.exe from the Windows SDK --------------------------------
$makeappx = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\makeappx.exe" -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending | Select-Object -First 1
if (-not $makeappx) { throw "makeappx.exe not found. Install the Windows SDK: https://developer.microsoft.com/windows/downloads/windows-sdk/" }

$output = Join-Path $root "dist\Qapshyq-$appVersion.msix"
& $makeappx.FullName pack /d $stage /p $output /o
if ($LASTEXITCODE -ne 0) { throw "makeappx failed" }
Write-Host "Done: $output  (identity: $($identity.identity_name), version $msixVersion)"
