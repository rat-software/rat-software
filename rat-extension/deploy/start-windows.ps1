# Starts Chrome for Testing / Chromium with the RAT extension and a dedicated profile.
# Usage:  powershell -ExecutionPolicy Bypass -File deploy\start-windows.ps1 -Chrome "C:\path\to\chrome.exe"
# Branded Google Chrome 137+ ignores --load-extension. In that case load the extension once via
# chrome://extensions ("Load unpacked") in the dedicated profile; the profile remembers it.
param(
  [string]$Chrome = "",
  [string]$Profile = "$env:LOCALAPPDATA\RAT-Scraper-Profile"
)
$ext = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $Chrome) {
  foreach ($c in @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe", "$env:ProgramFiles\Chromium\Application\chrome.exe")) {
    if (Test-Path $c) { $Chrome = $c; break }
  }
}
if (-not $Chrome -or -not (Test-Path $Chrome)) { Write-Error "chrome.exe not found. Pass -Chrome <path>."; exit 1 }

# Keep the PC awake while this launcher runs (display may turn off, but do not lock the session).
Add-Type -Namespace Win -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[void][Win.Power]::SetThreadExecutionState(0x80000003)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED

New-Item -ItemType Directory -Force -Path $Profile | Out-Null
Write-Host "Chrome: $Chrome`nProfile: $Profile`nExtension: $ext"
& $Chrome "--user-data-dir=$Profile" "--disable-extensions-except=$ext" "--load-extension=$ext" `
  "--no-first-run" "--disable-background-timer-throttling" "--disable-renderer-backgrounding" "--disable-backgrounding-occluded-windows" `
  "about:blank" | Out-Null
