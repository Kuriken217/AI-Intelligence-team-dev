param(
    [string]$TaskName = "AI Intelligence Daily Climate Brief",
    [string]$StartTime = "06:00",
    [string]$PythonPath = ""
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $PSScriptRoot "run_daily_morning_climate.ps1"

if ($PythonPath) {
    [Environment]::SetEnvironmentVariable("AI_INTEL_PYTHON", $PythonPath, "User")
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`"" `
    -WorkingDirectory $RepoRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At $StartTime
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel LeastPrivilege

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Description "Generate the AI Intelligence Unit morning climate brief and save it to Obsidian." `
    -Force

Write-Output "Registered scheduled task '$TaskName' for daily $StartTime."
